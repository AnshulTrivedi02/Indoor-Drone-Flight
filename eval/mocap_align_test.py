"""Tests of eval/mocap_align.py's window rule (2026-10-11 fixes; synthetic flights from mocap_align_validate).
  - the default early window covers the PRE-ARM sync wiggle (the old arm-anchored default started after it);
  - defaults are computed only for missing windows; a log with no ARM record (a disarmed hand-carry) stops with a clear
    request for explicit windows, and runs when they are given;
  - grid points outside the mocap record are masked (mocap starting inside a fit window).
Run: ~/venv-ardupilot/bin/python3 -m pytest eval/mocap_align_test.py -q"""
import os, sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mocap_align as MA
import mocap_align_validate as MV

BOOT, T = 12.0, 200.0                   # synth_flight: wiggles at BOOT+10 +-3 and BOOT+T-12 +-3, arm at BOOT+15


def _flight(seed=1, disarm=True):
    fc, mo, tr, _, _, init = MV.synth_flight(seed, T=T, boot=BOOT, wiggle_gain=2.0)   # |w| peaks > 2 rad/s (card D6)
    if disarm:
        fc["arm"] = fc["arm"] + [(BOOT + T - 20.0, 0)]                           # landed at T-25, disarmed at T-20
    return fc, mo, tr, init


def _mapped_err_ms(tr, mo, to_fc):
    tf_true = (mo["t"] - tr["O_s"] + tr["k"] * tr["tf0"]) / (1 + tr["k"])
    return 1e3 * float(np.abs(to_fc(mo["t"]) - tf_true).max())


def test_default_early_window_covers_prearm_wiggle_and_recovers_map():
    fc, mo, tr, _ = _flight()
    early, late, init, src = MA.resolve_windows(fc)
    assert early[0] <= BOOT + 7.5 and early[1] >= BOOT + 12.5 and early[1] <= BOOT + 15.0 + 1e-9   # the wiggle, pre-arm
    assert late[0] <= BOOT + T - 14.5 and late[1] >= BOOT + T - 9.5 and late[0] >= BOOT + T - 20.0 - 1e-9
    old_early = (BOOT + 15.0, BOOT + 40.0)                                    # the pre-fix default: arm .. arm + 25 s
    assert old_early[0] > BOOT + 13.0                                         # ... started after the wiggle had ended
    res, _, _, to_fc = MA.align(fc, mo, early, late, init)
    assert _mapped_err_ms(tr, mo, to_fc) < 1.0
    assert all(w["corr"] > 0.9 for w in res["clock"]["windows"])


def test_no_arm_record_needs_explicit_windows():
    fc, mo, tr, init = _flight()
    fc["arm"] = []                                                            # a disarmed hand-carry log
    fc["rfnd"] = np.zeros((0, 2))                                             # ... with no reading above 0.5 m
    with pytest.raises(SystemExit) as e:
        MA.resolve_windows(fc)
    assert "--early" in str(e.value) and "--late" in str(e.value) and "--init-seg" in str(e.value)
    with pytest.raises(SystemExit):
        MA.resolve_windows(fc, early=(BOOT + 5, BOOT + 15))                   # partly given: still needs the rest
    with pytest.raises(SystemExit):
        MA.legacy_windows(fc)                                                 # the old rule: a clear exit, not IndexError
    ew, lw = (BOOT + 5.0, BOOT + 15.0), (BOOT + T - 16.0, BOOT + T - 8.0)
    early, late, i, src = MA.resolve_windows(fc, ew, lw, init)
    assert (early, late, i) == (ew, lw, tuple(init)) and set(src.values()) == {"given"}
    res, _, _, to_fc = MA.align(fc, mo, early, late, i)
    assert _mapped_err_ms(tr, mo, to_fc) < 1.0


def test_only_missing_windows_are_defaulted_and_missing_wiggle_is_reported():
    fc, mo, tr, init = _flight()
    lw = (BOOT + T - 16.0, BOOT + T - 8.0)
    early, late, _, src = MA.resolve_windows(fc, late=lw)
    assert late == lw and src["late"] == "given" and src["early"].startswith("default")
    fc2, _, _, _ = _flight(disarm=False)                                     # log ends armed: no post-disarm wiggle
    with pytest.raises(SystemExit) as e:
        MA.resolve_windows(fc2)
    assert "--late" in str(e.value) and "--early (" not in str(e.value)


def test_mocap_starting_inside_the_window_is_masked_not_held():
    fc, mo, tr, _ = _flight(seed=2)
    early, late, init, _ = MA.resolve_windows(fc)
    tf_true = (mo["t"] - tr["O_s"] + tr["k"] * tr["tf0"]) / (1 + tr["k"])
    keep = tf_true >= BOOT + 9.0                                              # the mocap take starts mid-wiggle
    mo2 = {k: v[keep] for k, v in mo.items()}
    res, _, _, to_fc = MA.align(fc, mo2, early, late, init)
    assert res["clock"]["windows"][0]["valid_fraction"] < 0.8                 # the part before the take is excluded
    assert _mapped_err_ms(tr, mo2, to_fc) < 1.0


# ---------------- 2026-10-12: the 25 Hz IMU path (no RISI records, or only the IMU log rate) ----------------
def _imu_25hz(fc, rate=25.0, fcut=20.0, log_lag=0.0):
    """The FC's logged IMU record from the synthetic RISI-like truth: the INS 2-pole low-pass (fcut), sampled at `rate`,
    stamped at the sample time + log_lag (the record's TimeUS is the logging time)."""
    from scipy.signal import lfilter, lfilter_zi
    g = fc["gyro"]; ohm = np.tan(np.pi * fcut / 400.0); c = 1 + 2 * np.cos(np.pi / 4) * ohm + ohm ** 2
    b0 = ohm ** 2 / c; b = np.array([b0, 2 * b0, b0])
    a = np.array([1.0, 2 * (ohm ** 2 - 1) / c, (1 - 2 * np.cos(np.pi / 4) * ohm + ohm ** 2) / c]); zi = lfilter_zi(b, a)
    gf = np.column_stack([lfilter(b, a, g[:, k], zi=zi * g[0, k])[0] for k in (1, 2, 3)])
    k = np.arange(0, len(g), int(round(400 / rate)))
    out = dict(fc); out["gyro"] = np.c_[g[k, 0] + log_lag, gf[k]]
    out.update(gyro_src="IMU", params={"INS_GYRO_FILTER": fcut}, risi_dadt_median_s=None)
    return out


def test_imu_25hz_path_recovers_map_on_sync_wiggles():
    """The 2026-10-10 failure (-431 ms) was on SITL's arm-anchored windows with no wiggle; on the sync wiggles the 25 Hz
    path works. Accuracy cost (stated in mocap_align's docstring): ~+0.5 ms bias, plus the logging lag (<= 1 loop)."""
    for seed in (0, 3, 5):
        fc, mo, tr, _ = _flight(seed)
        fi = _imu_25hz(fc)
        early, late, init, _ = MA.resolve_windows(fi)                     # the default wiggle windows at 25 Hz
        res, _, _, to_fc = MA.align(fi, mo, early, late, init)
        tf_true = (mo["t"] - tr["O_s"] + tr["k"] * tr["tf0"]) / (1 + tr["k"])
        e = 1e3 * (to_fc(mo["t"]) - tf_true)
        assert 0.0 < np.mean(e) < 1.0 and np.abs(e).max() < 1.5, (seed, np.mean(e), np.abs(e).max())
        assert abs(res["clock"]["gyro_filter_delay_ms_compensated"] - 1e3 * np.sqrt(2) / (2 * np.pi * 20)) < 1e-9
        fl = _imu_25hz(fc, log_lag=0.0025)                                # logged one 400 Hz loop late
        res, _, _, to_fc = MA.align(fl, mo, *MA.resolve_windows(fl)[:3])
        e = 1e3 * (to_fc(mo["t"]) - tf_true)
        assert 2.0 < np.mean(e) < 3.6, (seed, np.mean(e))                 # the uncorrected lag adds as a bias


def test_gyro_src_auto_falls_back_to_imu(monkeypatch):
    from types import SimpleNamespace as NS

    def msgs(with_risi):
        out = [NS(get_type=lambda: "PARM", TimeUS=0, Name="INS_GYRO_FILTER", Value=20.0),
               NS(get_type=lambda: "ARM", TimeUS=5_000_000, ArmState=1)]
        for i in range(200):
            t = 1_000_000 + 40_000 * i
            out.append(NS(get_type=lambda: "IMU", TimeUS=t, I=0, GyrX=0.1, GyrY=0.0, GyrZ=0.0))
            if with_risi:
                out.append(NS(get_type=lambda: "RFRH", TimeUS=t))
                out.append(NS(get_type=lambda: "RISI", I=0, DAX=0.001, DAY=0.0, DAZ=0.0, DADT=0.0025))
        return out

    class Fake:
        def __init__(self, rows): self.rows = rows
        def recv_match(self, type):
            while self.rows:
                r = self.rows.pop(0)
                if r.get_type() in type:
                    return r
            return None
    for with_risi, want in ((False, "IMU"), (True, "RISI")):
        monkeypatch.setattr(MA.mavutil, "mavlink_connection", lambda p, w=with_risi: Fake(msgs(w)))
        fc = MA.read_fc("x.bin", gyro_src="auto")
        assert fc["gyro_src"] == want
        assert fc["gyro_src_auto"].startswith("IMU fallback" if want == "IMU" else "RISI records")
        assert abs(fc["gyro_period_ms_median"] - 40.0) < 1e-6
