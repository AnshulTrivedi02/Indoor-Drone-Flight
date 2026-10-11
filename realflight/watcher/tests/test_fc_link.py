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
    # F6 (2026-10-12): the FC now IGNORES every command (mode stays GUIDED, no ACK). Before F6 this test used ack=False,
    # where the fake FC still switched to LAND; that case now stops after one send (rule S2, test below).
    f = FakeFC(drop_first_commands=100); f.start()
    L = link(f, land_retry_s=0.05, land_max_tries=4, land_evidence_s=0.05)
    try:
        L.send_heartbeat(); L.command_land("x")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 2.0:
            L.poll(); L.service(); time.sleep(0.01)
        assert L.land["tries"] == 4 and not L.land["acked"] and len(f.lands()) == 4
        assert "S5" in L.land["stopped"] and f.mode == 4
    finally:
        L.close(); f.close()


def _drive(L, secs, f=None, on_land_applied=None):
    """Run the watcher's poll/service loop for `secs`; call on_land_applied() once, as soon as the fake FC is in LAND."""
    t0, fired = time.monotonic(), False
    while time.monotonic() - t0 < secs:
        if on_land_applied and not fired and f.mode == 9:
            on_land_applied(); fired = True
        L.poll(); L.service(); time.sleep(0.005)


def _guided_seen(L, f):
    """Let the watcher see the FC's GUIDED heartbeat before the breach (M0 = GUIDED, as in flight)."""
    L.send_heartbeat()
    assert wait_for(lambda: (L.poll(), L.fc_mode == 4)[1], 2)


def test_f6_pilot_takes_alt_hold_after_an_accepted_land_whose_ack_is_lost_no_further_land():
    """F6: the FC accepts the LAND but the ACK is lost; the pilot switches to ALT_HOLD 0.33 s later (B10b's measured
    toggle) at the FC's DEFAULT 1 Hz heartbeat, so the watcher may never see LAND in a heartbeat. The old rule re-sent
    LAND every 0.3 s until ACKed (5 sends) and would have overridden the pilot. Now: exactly one LAND."""
    f = FakeFC(ack=False, hb_period=1.0); f.start()
    L = link(f, land_retry_s=0.3)
    try:
        _guided_seen(L, f)
        L.command_land("box breach")

        def pilot():                                            # RC mode switch, ~0.33 s after the LAND took effect
            time.sleep(0.33); f.mode = 2
        _drive(L, 3.0, f, on_land_applied=pilot)
        assert len(f.lands()) == 1, f"{len(f.lands())} LANDs sent: the pilot was overridden"
        assert f.mode == 2 and L.land["tries"] == 1 and not L.land["acked"]
        assert L.land["stopped"] and ("S3" in L.land["stopped"] or "S2" in L.land["stopped"])
    finally:
        L.close(); f.close()


def test_f6_land_lost_then_pilot_takes_alt_hold_no_further_land():
    """F6: the first LAND never reaches the FC (dropped); the pilot then takes ALT_HOLD. No LAND follows (S3/S4):
    the pilot has authority, as the GCS failsafe gives it with FS_OPTIONS bit 4."""
    f = FakeFC(drop_first_commands=1, hb_period=0.2); f.start()
    L = link(f, land_retry_s=0.3)
    try:
        _guided_seen(L, f)
        L.command_land("dependency lost")
        time.sleep(0.05); f.mode = 2                         # pilot switch before the first re-send could be due
        _drive(L, 2.0)
        assert len(f.lands()) == 1 and f.mode == 2 and L.land["tries"] == 1
        assert "ALT_HOLD" in L.land["stopped"]
    finally:
        L.close(); f.close()


def test_f6_pilot_mode_before_the_breach_still_gets_one_land_but_no_resend():
    """The FC is already in ALT_HOLD (pilot) when the watcher decides LAND (B10b(2)): ONE LAND is sent, as before; if it
    is lost, it is NOT re-sent (S3 applies even when M0 is the pilot mode)."""
    f = FakeFC(drop_first_commands=1, hb_period=0.2); f.start()
    f.mode = 2
    L = link(f, land_retry_s=0.1)
    try:
        L.send_heartbeat()
        assert wait_for(lambda: (L.poll(), L.fc_mode == 2)[1], 2)
        L.command_land("box breach")
        _drive(L, 1.5)
        assert len(f.lands()) == 1 and f.mode == 2 and "S3" in L.land["stopped"]
    finally:
        L.close(); f.close()


def test_f6_unacked_land_with_no_mode_change_is_resent_as_before():
    """An unacknowledged LAND with no mode change (FC still in GUIDED after the send): re-sent, 0.3 s apart at the
    earliest, until the FC takes it (here the first two are dropped) and ACKs; then never again."""
    f = FakeFC(drop_first_commands=2, hb_period=0.2); f.start()
    L = link(f, land_retry_s=0.3)
    try:
        _guided_seen(L, f)
        L.command_land("stale pose")
        _drive(L, 3.0)
        lands = f.lands()
        assert len(lands) == 3 and f.mode == 9 and L.land["acked"] and L.land["tries"] == 3
        assert all(b[0] - a[0] >= 0.29 for a, b in zip(lands, lands[1:])), [x[0] for x in lands]
        assert "S1" in L.land["stopped"]
    finally:
        L.close(); f.close()


def test_f6_land_in_heartbeat_without_ack_stops_resending():
    """S2: the FC switched to LAND but the ACK is lost; the next heartbeat shows LAND -> one send only."""
    f = FakeFC(ack=False, hb_period=0.2); f.start()
    L = link(f, land_retry_s=0.05)
    try:
        _guided_seen(L, f)
        L.command_land("x")
        _drive(L, 1.5)
        assert len(f.lands()) == 1 and f.mode == 9 and "S2" in L.land["stopped"]
    finally:
        L.close(); f.close()


def test_f6_other_mode_change_not_commanded_by_the_watcher_stops_resending():
    """S4: after a lost LAND the FC reports a mode other than LAND and other than the pre-LAND mode, and not a pilot
    mode (here BRAKE 17, e.g. an FC-side failsafe action): no re-send."""
    f = FakeFC(drop_first_commands=1, hb_period=0.2); f.start()
    L = link(f, land_retry_s=0.1)
    try:
        _guided_seen(L, f)
        L.command_land("x")
        time.sleep(0.02); f.mode = 17
        _drive(L, 1.5)
        assert len(f.lands()) == 1 and "S4" in L.land["stopped"]
    finally:
        L.close(); f.close()


def test_f6_no_resend_without_a_post_send_heartbeat():
    """R: with no FC heartbeat after the send (FC link silent), nothing is re-sent (the old rule re-sent blindly)."""
    f = FakeFC(drop_first_commands=1, hb_period=0.2); f.start()
    L = link(f, land_retry_s=0.05)
    try:
        _guided_seen(L, f)
        f.hb_period = 1e9                                    # the FC stops sending heartbeats on this link
        time.sleep(0.3); L.poll()
        L.command_land("x")
        _drive(L, 1.0)
        assert len(f.lands()) == 1 and L.land["tries"] == 1 and L.land["stopped"] is None
    finally:
        L.close(); f.close()


def test_f6_heartbeat_rate_is_requested(fc):
    L = link(fc)
    try:
        L.send_heartbeat(); L.request_streams()
        time.sleep(0.3)
        ids = {int(r[3].param1) for r in fc.received("COMMAND_LONG", src=211) if r[3].command == 511}
        assert ids == {30, 0}, ids                          # ATTITUDE and HEARTBEAT intervals
    finally:
        L.close()


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
