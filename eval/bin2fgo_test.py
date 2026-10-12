"""Tests of eval/bin2fgo.py's capture-delay configuration (2026-10-12) and of the converter acceptance band checker
(eval/bin2fgo_accept.py). No log needed. Run: ~/venv-ardupilot/bin/python -m pytest eval/bin2fgo_test.py -q"""
import copy, json, os, sys, tempfile
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bin2fgo as B

GOOD = {"name": "rung1_capture_delays", "status": "PRE-REGISTERED", "delays_ms": {"flow": 16.0, "range": 40.0, "imu": 0.0},
        "uncertainty_ms": {"flow": 2.5, "range": 10.0},
        "measured_on": [{"log": "V1.BIN", "sha256": "ab", "sortie": "V"}], "method": "sensor_timing_from_log.py"}


def _args(**k):
    base = dict(delays_json=None, result_flight=False, flow_delay_ms=None, range_delay_ms=None, imu_delay_ms=None)
    base.update(k)
    return NS(**base)


def _write(d, obj, name="d.json"):
    p = f"{d}/{name}"; json.dump(obj, open(p, "w")); return p


def test_cli_and_json_forms_give_the_same_delays_and_record_the_source():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, GOOD)
        dj, sj = B.resolve_delays(_args(delays_json=p))
        dc, sc = B.resolve_delays(_args(flow_delay_ms=16.0, range_delay_ms=40.0))
    assert dj == dc == {"flow": 16.0, "range": 40.0, "imu": 0.0}
    assert sj["kind"] == "delays_json" and sj["status"] == "PRE-REGISTERED" and len(sj["sha256"]) == 64
    assert sc == {"kind": "command_line"}


def test_strictness_and_the_result_flight_rule():
    with tempfile.TemporaryDirectory() as d:
        for bad in ({**GOOD, "status": "TEMPLATE"},
                    {**GOOD, "delays_ms": {"flow": None, "range": 40.0, "imu": 0.0}},
                    {**GOOD, "delays_ms": {"flow": 16.0, "range": 40.0}},
                    {**GOOD, "measured_on": []},
                    {**GOOD, "extra": 1},
                    {k: v for k, v in GOOD.items() if k != "uncertainty_ms"}):
            with pytest.raises(SystemExit):
                B.load_delays(_write(d, bad))
        prov = _write(d, {**GOOD, "status": "PROVISIONAL"}, "prov.json")
        B.resolve_delays(_args(delays_json=prov))                                   # usable, with a warning
        with pytest.raises(SystemExit):
            B.resolve_delays(_args(delays_json=prov, result_flight=True))           # not for a result flight
        with pytest.raises(SystemExit):
            B.resolve_delays(_args(flow_delay_ms=16.0, range_delay_ms=40.0, result_flight=True))
        with pytest.raises(SystemExit):                                              # both forms at once
            B.resolve_delays(_args(delays_json=_write(d, GOOD), flow_delay_ms=16.0))
        with pytest.raises(SystemExit):                                              # no silent default
            B.resolve_delays(_args(flow_delay_ms=16.0))
    with pytest.raises(SystemExit):                                                  # the shipped template is refused
        B.load_delays(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs",
                                   "rung1_capture_delays_TEMPLATE.json"))


# ---------------- the converter acceptance band (eval/bin2fgo_accept.py) on synthetic data ----------------
def _synthetic(flip_gyro_y=False):
    import numpy as np
    import bin2fgo_accept as A
    rng = np.random.default_rng(0); fs = 400.0
    t = np.arange(10.0, 70.0, 1 / fs)
    w = np.c_[2.5 * np.sin(2 * np.pi * 1.5 * t), 1.8 * np.sin(2 * np.pi * 1.1 * t + 0.4), 0.9 * np.sin(2 * np.pi * 0.7 * t)]
    w[(t > 20) & (t < 60)] *= 0.02                                     # wiggles at both ends, quiet between
    acc = np.c_[0.8 * np.sin(2 * np.pi * 0.9 * t), 0.6 * np.cos(2 * np.pi * 1.3 * t), 9.80665 + 0.2 * np.sin(t)]
    still = (t > 16.5) & (t < 19.9)
    w[still] = 0.0; acc[still] = [0.0, 0.0, 9.80665]
    gf, af = A.lpf2p(w, fs, 20.0), A.lpf2p(acc, fs, 20.0)              # the INS-filtered truth, logged at 25 Hz
    k = np.arange(0, len(t), 16)
    s = np.array([1.0, -1.0, -1.0])                                    # FLU -> FRD
    imu = [{"TimeUS": int(round(t[i] * 1e6)) + 1000, "I": 0, "GyrX": gf[i, 0] * s[0], "GyrY": gf[i, 1] * s[1],
            "GyrZ": gf[i, 2] * s[2], "AccX": af[i, 0] * s[0], "AccY": af[i, 1] * s[1], "AccZ": af[i, 2] * s[2]} for i in k]
    g = w.copy()
    if flip_gyro_y:
        g[:, 1] *= -1                                                 # a converter frame error on one axis
    rng_t = np.arange(20.0, 60.0, 0.05); rng_d = 1.0 + 0.001 * rng.normal(size=len(rng_t))
    rfnd = [{"TimeUS": int(round((x + 0.04) * 1e6)), "Instance": 0, "Dist": float(d), "Stat": 4}
            for x, d in zip(rng_t, rng_d)]
    meta = {"imu_instance": 0, "range_instance": 0, "delays_ms": {"flow": 16.0, "range": 40.0, "imu": 0.0},
            "init_range": 0.1, "init_range_source": "range at levelling end", "bin_sha256": "x",
            "parm": {"LOG_REPLAY": 1, "SCHED_LOOP_RATE": 400, "INS_GYRO_FILTER": 20, "INS_ACCEL_FILTER": 20,
                     "RNGFND1_GNDCLR": 0.1},
            "checks": {"dsf_dropped_blocks": 0, "imu_dropped_flags": 0, "imu_dvdt_ne_dadt_gt_0p5ms": 0,
                       "imu_dvdt_vs_frame_dt_n_gt_0p5ms": 0, "imu_frame_period_ms_mean": 2.5, "rofh_equals_of": True,
                       "flow_pos_parm_matches_rofh": True, "range_pos_parm_matches_rrni": True}}
    npz = {"imu_t": t, "imu_gyro": g, "imu_acc": acc, "rng_t": rng_t, "rng": rng_d}
    recs = {"IMU": imu, "RFND": rfnd, "ARM": [{"TimeUS": 20_000_000, "ArmState": 1}]}
    timing = {"flow": {"sign_ok": True, "gain_xy_at_best": [1.0, 1.0], "peak_corr_per_axis_xy": [0.8, 0.7]}}
    return meta, npz, recs, timing


def test_acceptance_band_passes_a_consistent_conversion_and_catches_faults():
    import bin2fgo_accept as A
    meta, npz, recs, timing = _synthetic()
    r = A.evaluate(meta, npz, recs, timing)
    assert r["accepted"], {k: v["pass"] for k, v in r["tests"].items()}
    a5 = r["tests"]["A5_imu_vs_onboard_IMU"]
    assert abs(a5["best_lag_ms"] - 1.0) <= 0.5 and a5["gyro"]["corr_xyz"][0] > 0.99   # the record logged 1 ms late
    assert r["tests"]["A6_rest"]["tested"] and r["tests"]["A6_rest"]["pass"]
    m2, n2, r2, t2 = _synthetic(flip_gyro_y=True)                     # a frame error on one gyro axis
    f = A.evaluate(m2, n2, r2, t2)
    assert not f["accepted"] and not f["tests"]["A5_imu_vs_onboard_IMU"]["pass"]
    m3 = copy.deepcopy(meta); m3["checks"]["rofh_equals_of"] = False
    assert not A.evaluate(m3, npz, recs, timing)["accepted"]
    nt = A.evaluate(meta, npz, recs, None)                            # no flow-sign evidence: not accepted
    assert not nt["accepted"] and nt["tests"]["A10_flow_sign"]["tested"] is False
    m4 = copy.deepcopy(meta); m4["parm"]["SCHED_LOOP_RATE"] = 300
    assert not A.evaluate(m4, npz, recs, timing)["tests"]["A4_imu_rate"]["pass"]
    rr = copy.deepcopy(recs)
    for x in rr["RFND"]:
        x["Dist"] += 0.1                                              # range mis-read by 10 cm
    assert not A.evaluate(meta, npz, rr, timing)["tests"]["A9_range_vs_RFND"]["pass"]
