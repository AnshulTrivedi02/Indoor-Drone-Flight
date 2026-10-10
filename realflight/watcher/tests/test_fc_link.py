"""G4 / G5 / G6 (config check) / G11: the MAVLink link to a fake FC on loopback UDP (ephemeral ports)."""
import time

import pytest

from realflight.watcher.fc_link import FcLink, expected_params
from realflight.watcher.tests.fakes import GOOD_PARAMS, FakeFC, wait_for


@pytest.fixture
def fc():
    f = FakeFC(); f.start()
    try:
        yield f
    finally:
        f.close()


def link(fc, **kw):
    return FcLink(f"udpout:127.0.0.1:{fc.port}", 211, log=lambda s: None, **kw)


def test_g11_refuses_sysid_255_and_the_fc_id(fc):
    with pytest.raises(ValueError):
        FcLink(f"udpout:127.0.0.1:{fc.port}", 255)
    with pytest.raises(ValueError):
        FcLink(f"udpout:127.0.0.1:{fc.port}", 1, fc_sysid=1)


def test_g5_heartbeat_carries_the_watchers_own_sysid_and_refreshes_the_fc_timer(fc):
    L = link(fc)
    try:
        L.send_heartbeat()
        hb = wait_for(lambda: fc.received("HEARTBEAT", src=211), 2)
        assert hb and hb[0][3].type == 6 and hb[0][3].autopilot == 8      # MAV_TYPE_GCS, MAV_AUTOPILOT_INVALID
        assert fc.gcs_last_seen > 0
    finally:
        L.close()


def test_g5_g6_param_check_passes_on_the_template_values(fc):
    L = link(fc)
    try:
        exp = expected_params(211)
        L.request_params(list(exp))
        wait_for(lambda: (L.poll(), L.verify_params(exp)[0] is not None)[1], 3)
        assert L.verify_params(exp) == (True, "ok")
    finally:
        L.close()


@pytest.mark.parametrize("name,value,frag", [
    ("MAV_GCS_SYSID", 255, "MAV_GCS_SYSID"),             # G11: default ID -> masked
    ("MAV_GCS_SYSID_HI", 250, "range"),                  # G11: an ID range
    ("FS_GCS_ENABLE", 0, "FS_GCS_ENABLE"),               # G5: failsafe off
    ("FS_GCS_TIMEOUT", 5, "FS_GCS_TIMEOUT"),             # G5: default 5 s, not the pre-registered 3 s
    ("FS_OPTIONS", 0, "RC override"),                    # B10
    ("ARMING_SKIPCHK", -1, "AUX_AUTH"),                  # G6: all checks skipped
    ("ARMING_SKIPCHK", 1 << 17, "AUX_AUTH"),             # G6: aux auth skipped
    ("ARMING_RUDDER", 2, "ARMING_RUDDER"),               # G6(i): stick arming on
    ("MAV_OPTIONS", 1, "sysid-255"),
])
def test_g5_g6_param_check_rejects_unsafe_values(name, value, frag):
    params = dict(GOOD_PARAMS); params[name] = value
    f = FakeFC(params=params); f.start()
    L = link(f)
    try:
        exp = expected_params(211)
        L.request_params(list(exp))
        wait_for(lambda: (L.poll(), L.verify_params(exp)[0] is not None)[1], 3)
        ok, why = L.verify_params(exp)
        assert ok is False and frag in why, why
    finally:
        L.close(); f.close()


def test_g4_land_is_retried_only_until_acked_then_never_again():
    f = FakeFC(drop_first_commands=2); f.start()
    L = link(f, land_retry_s=0.1)
    try:
        L.send_heartbeat()                                   # FC learns our address
        L.command_land("test breach")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 1.5:
            L.poll(); L.service(); time.sleep(0.01)
        assert L.land["acked"] and L.land["tries"] == 3
        assert len(f.lands()) == 3 and f.mode == 9
        L.command_land("second breach in the same episode")   # idempotent within the episode
        for _ in range(30):
            L.poll(); L.service(); time.sleep(0.01)
        assert len(f.lands()) == 3
    finally:
        L.close(); f.close()


def test_g4_land_gives_up_after_max_tries_without_ack():
    f = FakeFC(ack=False); f.start()
    L = link(f, land_retry_s=0.05, land_max_tries=4)
    try:
        L.send_heartbeat(); L.command_land("x")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 1.0:
            L.poll(); L.service(); time.sleep(0.01)
        assert L.land["tries"] == 4 and not L.land["acked"] and len(f.lands()) == 4
    finally:
        L.close(); f.close()


def test_g11_never_sends_rc_override_or_manual_control(fc):
    L = link(fc)
    try:
        L.send_heartbeat(); L.request_params(["FS_GCS_ENABLE"]); L.request_streams(); L.statustext("x")
        L.command_land("x")
        time.sleep(0.3)
        types = {r[1] for r in fc.received(src=211)}
        assert types and not types & {"RC_CHANNELS_OVERRIDE", "MANUAL_CONTROL"}
        assert set(L.sent) & {"RC_CHANNELS_OVERRIDE", "MANUAL_CONTROL"} == set()
    finally:
        L.close()


def test_g11_detects_another_sender_using_the_watchers_sysid(fc):
    from pymavlink import mavutil
    L = link(fc)
    try:
        L.send_heartbeat()
        wait_for(lambda: fc.received("HEARTBEAT", src=211), 2)
        # a rogue process with the watcher's ID, delivered to the watcher's link (as MAVProxy would route it)
        rogue = mavutil.mavlink_connection(f"udpout:127.0.0.1:{L.conn.port.getsockname()[1]}", source_system=211,
                                           source_component=1)
        rogue.mav.heartbeat_send(6, 8, 0, 0, 4)
        ev = wait_for(lambda: [e for e in L.poll() if e[0] == "collision"], 2)
        rogue.close()
        assert ev and "211" in ev[0][1]
    finally:
        L.close()


def test_fake_fc_model_documents_the_stock_arming_gap(fc):
    """G6 finding, on OUR MODEL of events.cpp/AP_Arming_Copter: if the watcher was never seen, the stock FC has no
    GCS failsafe and arms; once seen and then lost, failsafe.gcs latches and arming is refused."""
    time.sleep(0.5)
    assert fc.try_arm()[0]                                 # never seen -> stock FC arms (needs Lua aux auth / G6)
    fc.armed = False
    L = link(fc)
    try:
        L.send_heartbeat()
        wait_for(lambda: fc.gcs_last_seen > 0, 2)
        assert wait_for(lambda: fc.fs_gcs, 4.5)            # heartbeat stopped -> failsafe after 3 s
        ok, why = fc.try_arm()
        assert not ok and "GCS failsafe on" in why
    finally:
        L.close()
