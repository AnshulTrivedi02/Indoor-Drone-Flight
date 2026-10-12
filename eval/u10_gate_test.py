"""Synthetic tests of eval/u10_gate.py against the SIGNED docs/u10_replay_gate_band.md (2026-10-12): a PASS case and a
FAIL case for every criterion of the traceability table (handover 2026-10-12_u10_g5_audit_rebase.md §2). Everything is
synthetic: a dataflash .BIN written with df_reader.write_fmt/write_rec, tiny CSVs and a score JSON carrying that
.BIN's sha256. Plus the G5-computability checks of the rung-1 drift rule on rung-1-like and H-like profiles, using
real_score.drift_metric with the SIGNED docs/rung1_preregistration.json `drift` section.

Run: ~/venv-ardupilot/bin/python -m pytest eval/u10_gate_test.py -q
"""
import contextlib, copy, hashlib, io, json, os, sys, tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import u10_gate as G  # noqa: E402
from df_reader import write_fmt, write_rec  # noqa: E402

ARM_T, XUKF_T, XUKS_T, RUKF_T, RUKS_T = 101, 250, 251, 230, 229
ARM_US = 20_000_000                                   # first ArmState = 1 at 20 s
W = [30.0, 90.0]                                       # the window W (s)


def make_bin(path, arm=True, fork=True, replayed=True, rukf_dpd=0.0, rukf_dpn=0.0, ruks_dfx=0, ruks_ra=None,
             redeclare=False, undeclared=False, tag=0):
    """A synthetic Replay output: ARM, and (fork=True) onboard XUKF/XUKS plus (replayed=True) replayed RUKF/RUKS at
    the same TimeUS (10 Hz from 5 s to 100 s). rukf_dpd/rukf_dpn: replayed - onboard offsets from 20 s on."""
    b = bytearray()
    b += write_fmt(ARM_T, "ARM", "QB", "TimeUS,ArmState")
    b += write_fmt(XUKF_T, "XUKF", "Qffff", "TimeUS,PN,PE,PD,Yaw")
    b += write_fmt(XUKS_T, "XUKS", "QIII", "TimeUS,FXa,FYa,Ra")
    b += write_fmt(RUKF_T, "RUKF", "Qffff", "TimeUS,PN,PE,PD,Yaw")
    b += write_fmt(RUKS_T, "RUKS", "QIII", "TimeUS,FXa,FYa,Ra")
    b += write_fmt(200, "TAG", "Q", "TimeUS")
    b += write_rec(200, "Q", tag)                     # makes each synthetic log's sha256 distinct
    if arm:
        b += write_rec(ARM_T, "QB", 1_000_000, 0) + write_rec(ARM_T, "QB", ARM_US, 1)
    for k, t in enumerate(range(5_000_000, 100_000_001, 100_000)):
        late = t >= 20_000_000
        if fork:
            b += write_rec(XUKF_T, "Qffff", t, 0.01 * k, 0.0, -1.2, 10.0)
            b += write_rec(XUKS_T, "QIII", t, k, k, k)
        if replayed:
            b += write_rec(RUKF_T, "Qffff", t, 0.01 * k + (rukf_dpn if late else 0.0), 0.0,
                           -1.2 + (rukf_dpd if late else 0.0), 10.0)
            b += write_rec(RUKS_T, "QIII", t, k + (ruks_dfx if late else 0), k, k if ruks_ra is None else ruks_ra)
    if redeclare:
        b += write_fmt(RUKF_T, "ZZZZ", "QB", "TimeUS,X")
    if undeclared:
        b += b"\xa3\x95" + bytes([77]) + b"\x00" * 9
    with open(path, "wb") as f:
        f.write(bytes(b))


GEOM = ("range_lever,5249,0,0,0.12\nflow_lever,5557,0,0,0.25\nmode,log\nresolved_at_ms,5750\n"
        "flow_delay_ms,10,log_parm\nhorizon_ms,60,hgt_delay,60,log_parm,bcn_delay,50,log_parm\n"
        "rng1_min_max,0.05,40,log_parm\n")


def shadow_rows(t0=5.0, t1=100.0, dt=0.04, ss=65803, healthy=1, age=30, gap=None, bad_at=None, col=None):
    """ukf_shadow.csv text. ss 65803 has bit 3 set. gap=(a, b): no rows in (a, b). bad_at: time at which `col` is
    set to a failing value."""
    out = ["TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,SVN,SVE,SS,Healthy,FlowAgeMs,FXa,FYa,Ra"]
    for t in np.arange(t0, t1 + 1e-9, dt):
        if gap and gap[0] < t < gap[1]:
            continue
        s, h, a = ss, healthy, age
        if bad_at is not None and abs(t - bad_at) < dt / 2:
            s = 65803 & ~(1 << 3) if col == "SS" else s
            h = 0 if col == "Healthy" else h
            a = 5000 if col == "FlowAgeMs" else a
        out.append(f"{int(round(t * 1e6))},0,0,-1.2,0,0,0,0,0,10,0.02,0.02,{s},{h},{a},1,1,1")
    return "\n".join(out) + "\n"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def score_for(binp, ukf=0.20, ekf=0.15, drift=0.40, drift_error=None, ukf_phys="RUKO", ukf_rec="XUKO", other_sha=False,
              extra_row_sha=None):
    s = sha(binp)
    dr = {"error": drift_error} if drift_error else {"final_h_m": drift, "segment_fc_s": [40.0, 45.0],
                                                     "init_segment_extent_h_m": 2.0}
    est = {"UKF": {"record": ukf_rec, "physical_record": ukf_phys, "sha256": "0" * 64 if other_sha else s,
                   "evo_ape_a_se3": {"rmse_m": ukf}, "drift_start_aligned": dr},
           "EKF3": {"record": "XKF1@100", "physical_record": "XKF1", "sha256": s, "evo_ape_a_se3": {"rmse_m": ekf}},
           "FGO": {"record": "TUM", "sha256": "f" * 64, "evo_ape_a_se3": {"rmse_m": 0.1}}}
    if extra_row_sha is not None:
        est["EKF3_onboard"] = {"record": "XKF1@0", "physical_record": "XKF1", "sha256": extra_row_sha,
                               "evo_ape_a_se3": {"rmse_m": 0.1}}
    return {"window_s": W, "prereg": {"resolved": {"metrics": {"max_gap_s": 0.5}}}, "estimators": est}


class Case:
    """One synthetic Replay directory + score; .run() gates it and returns the flight record."""

    def __init__(self, root, name="F", bin_kw=None, shadow=None, geom=GEOM, stats="name,value\nn_chol_retry,0\nn_chol_fail,0\n",
                 score_kw=None, md5="3c3b62bbe51d515b6ff0789a19fe1136", score=True, score_edit=None):
        self.d = os.path.join(root, name); os.makedirs(self.d + "/logs")
        self.binp = self.d + "/logs/00000001.BIN"
        make_bin(self.binp, **(bin_kw or {}))
        open(self.d + "/ukf_shadow.csv", "w").write(shadow_rows() if shadow is None else shadow)
        if geom is not None:
            open(self.d + "/ukf_geometry.csv", "w").write(geom)
        if stats is not None:
            open(self.d + "/ukf_stats.csv", "w").write(stats)
        open(self.d + "/replay.log", "w").write("thesis shadow UKF: end of run: n_chol_retry=0 n_chol_fail=0\n")
        if md5:
            open(self.d + "/binary.md5", "w").write(f"{md5}  Replay\n")
        self.score = None
        if score:
            sc = score_for(self.binp, **(score_kw or {}))
            if score_edit:
                score_edit(sc)
            self.score = self.d + "/score.json"; json.dump(sc, open(self.score, "w"))
        self.name = name

    def run(self, *extra):
        argv = ["flight", "--replay-dir", self.d, "--name", self.name, "--json", self.d + "/gate.json", *extra]
        if self.score:
            argv += ["--score", self.score]
        with contextlib.redirect_stdout(io.StringIO()):
            return G.main(argv)


@pytest.fixture
def root():
    with tempfile.TemporaryDirectory() as d:
        yield d


def fails(out, crit):
    return out["pass"] is False and out[crit]["pass"] is False


# ------------------------------------------------------------------------------------------- base
def test_base_gated_flight_passes(root):
    out = Case(root).run()
    assert out["verdict"] == "PASS", out
    assert out["G6"]["applies"] is True and out["d_max_m"] == 1.0


# ------------------------------------------------------------------------------------------- preconditions / N5 / rule 2
def test_N5_score_of_another_log_fails(root):
    assert fails(Case(root, score_kw={"other_sha": True}).run(), "preconditions")


def test_N5_any_log_row_of_another_log_fails_and_TUM_row_is_exempt(root):
    ok = Case(root, "a", score_kw={"extra_row_sha": None}).run()        # FGO TUM row has its own sha: passes
    assert ok["preconditions"]["pass"] is True
    bad = Case(root, "b", score_kw={"extra_row_sha": "1" * 64}).run()  # a log row computed elsewhere
    assert fails(bad, "preconditions")


def test_N5_missing_sha_key_fails_without_crash(root):
    out = Case(root, score_edit=lambda s: s["estimators"]["UKF"].pop("sha256")).run()
    assert fails(out, "preconditions")


def test_rule2_UKF_read_from_onboard_XUKO_fails(root):
    assert fails(Case(root, score_kw={"ukf_phys": "XUKO", "ukf_rec": "XUKO@onboard"}).run(), "preconditions")


def test_integrity_redeclared_id_fails(root):
    assert fails(Case(root, bin_kw={"redeclare": True}).run(), "preconditions")


def test_integrity_undeclared_type_fails(root):
    assert fails(Case(root, bin_kw={"undeclared": True}).run(), "preconditions")


# ------------------------------------------------------------------------------------------- G1
def test_G1_source_not_log_parm_fails(root):
    assert fails(Case(root, geom=GEOM.replace("flow_delay_ms,10,log_parm", "flow_delay_ms,10,default")).run(), "G1")


def test_G1_mode_not_log_fails(root):
    assert fails(Case(root, geom=GEOM.replace("mode,log", "mode,sitl")).run(), "G1")


def test_G1_never_resolved_fails(root):
    assert fails(Case(root, geom=GEOM.replace("resolved_at_ms,5750\n", "")).run(), "G1")


def test_G1_missing_geometry_fails(root):
    assert fails(Case(root, geom=None).run(), "G1")


def test_G1_init_after_arming_fails(root):
    assert fails(Case(root, shadow=shadow_rows(t0=21.0)).run(), "G1")


def test_G1_header_only_shadow_fails_never_initialised(root):
    out = Case(root, shadow=shadow_rows().splitlines()[0] + "\n").run()
    assert fails(out, "G1") and "never initialised" in " ".join(out["G1"]["why"])


# ------------------------------------------------------------------------------------------- N3 (G1 late PARM, ARM)
def test_N3_late_parm_same_value_passes(root):
    assert Case(root, geom=GEOM + "warning_late_parm,30000,EK3_FLOW_DELAY,10\n").run()["G1"]["pass"] is True


def test_N3_late_lever_arm_passes(root):
    g = GEOM + "warning_late_parm,30000,FLOW_POS_Z,0.3\nwarning_late_parm,30000,RNGFND1_POS_Z,0.1\n"
    assert Case(root, geom=g).run()["G1"]["pass"] is True


def test_N3_late_parm_changing_value_fails(root):
    assert fails(Case(root, geom=GEOM + "warning_late_parm,30000,EK3_FLOW_DELAY,25\n").run(), "G1")


def test_N3_late_other_parameter_fails(root):
    assert fails(Case(root, geom=GEOM + "warning_late_parm,30000,RNGFND2_MIN,0.1\n").run(), "G1")


def test_N3_missing_ARM_fails_gated_flight(root):
    assert fails(Case(root, bin_kw={"arm": False}).run(), "G1")


def test_N3_missing_ARM_not_applicable_on_H(root):
    out = Case(root, bin_kw={"arm": False}, score=False).run()
    assert out["verdict"] == "PLUMBING PASS" and "not applicable" in str(out["G1"]["init_before_arming"])


# ------------------------------------------------------------------------------------------- G2 / N2
@pytest.mark.parametrize("col", ["SS", "Healthy", "FlowAgeMs"])
def test_G2_one_bad_row_in_W_fails(root, col):
    assert fails(Case(root, shadow=shadow_rows(bad_at=50.0, col=col)).run(), "G2")


def test_G2_bad_row_outside_W_passes(root):
    assert Case(root, shadow=shadow_rows(bad_at=25.0, col="Healthy")).run()["G2"]["pass"] is True


def test_G2_flow_age_4999_passes(root):
    assert Case(root, shadow=shadow_rows(age=4999)).run()["G2"]["pass"] is True


def test_N2_gap_inside_W_le_max_gap_passes(root):
    assert Case(root, shadow=shadow_rows(gap=(50.01, 50.43))).run()["G2"]["pass"] is True


def test_N2_gap_inside_W_gt_max_gap_fails(root):
    assert fails(Case(root, shadow=shadow_rows(gap=(50.0, 50.7))).run(), "G2")


def test_N2_gap_at_W_end_fails(root):
    assert fails(Case(root, shadow=shadow_rows(t1=89.0)).run(), "G2")


# ------------------------------------------------------------------------------------------- G3 / rule 1
def test_G3_chol_fail_fails(root):
    assert fails(Case(root, stats="name,value\nn_chol_retry,3\nn_chol_fail,1\n").run(), "G3")


def test_rule1_missing_stats_fails(root):
    assert fails(Case(root, stats=None).run(), "G3")


def test_rule1_stats_without_n_chol_fail_row_fails(root):
    assert fails(Case(root, stats="name,value\nn_chol_retry,0\n").run(), "G3")


def test_G3_retries_without_fail_pass(root):
    assert Case(root, stats="name,value\nn_chol_retry,7\nn_chol_fail,0\n").run()["G3"]["pass"] is True


# ------------------------------------------------------------------------------------------- G4
def test_G4_at_band_passes_and_above_fails(root):
    assert Case(root, "a", score_kw={"ukf": 0.30, "ekf": 0.15}).run()["G4"]["pass"] is True      # 2.0 x
    assert fails(Case(root, "b", score_kw={"ukf": 0.301, "ekf": 0.15}).run(), "G4")


def test_G4_floor_branch(root):
    assert Case(root, "a", score_kw={"ukf": 0.13, "ekf": 0.03}).run()["G4"]["pass"] is True      # 0.03 + 0.10
    assert fails(Case(root, "b", score_kw={"ukf": 0.131, "ekf": 0.03}).run(), "G4")


def test_G4_not_computable_fails(root):
    assert fails(Case(root, score_edit=lambda s: s["estimators"]["UKF"].pop("evo_ape_a_se3")).run(), "G4")


# ------------------------------------------------------------------------------------------- G5 / N1 / D_max
def test_G5_at_D_max_passes_above_fails(root):
    assert Case(root, "a", score_kw={"drift": 1.0}).run()["G5"]["pass"] is True
    assert fails(Case(root, "b", score_kw={"drift": 1.001}).run(), "G5")


def test_N1_not_computable_fails(root):
    out = Case(root, score_kw={"drift_error": "initial segment moves only 0.605 m horizontally"}).run()
    assert fails(out, "G5") and out["G5"]["not_computable"] is True


def test_D_max_default_is_signed_and_other_values_refused(root):
    c = Case(root)
    assert c.run()["G5"]["d_max_m"] == 1.0 == G.D_MAX_M
    assert c.run("--d-max", "1.0")["pass"] is True
    with pytest.raises(SystemExit):
        c.run("--d-max", "1.5")


# ------------------------------------------------------------------------------------------- G6 / N6 / rule 2
def test_G6_does_not_apply_on_stock_flown(root):
    out = Case(root, bin_kw={"fork": False}).run()
    assert out["G6"]["applies"] is False and out["G6"]["pass"] is True


def test_G6_onboard_without_replayed_fails(root):
    assert fails(Case(root, bin_kw={"replayed": False}).run(), "G6")


def test_N6_E1_is_3D_vertical_difference_fails(root):
    out = Case(root, bin_kw={"rukf_dpd": 0.06}).run()      # 0 horizontal, 0.06 m vertical
    assert fails(out, "G6") and out["G6"]["E1_pos3d_max_m"] > 0.05


def test_G6_E1_within_band_passes(root):
    assert Case(root, bin_kw={"rukf_dpn": 0.004}).run()["G6"]["pass"] is True   # max 0.004 <= 0.05, rms <= 0.01


def test_G6_E5_increment_fails(root):
    assert fails(Case(root, bin_kw={"ruks_dfx": 5}).run(), "G6")


def test_G6_pairing_starts_after_later_init_plus_10s(root):
    out = Case(root).run()
    assert out["G6"]["pairing_start_us"] == 15_000_000


# ------------------------------------------------------------------------------------------- H and V modes
def test_H_plumbing_pass_and_fail(root):
    assert Case(root, "a", score=False).run()["verdict"] == "PLUMBING PASS"
    assert Case(root, "b", score=False, stats=None).run()["verdict"].startswith("PLUMBING FAIL")


def test_V_judges_G1_to_G3_only(root):
    v = Case(root, "a", score_kw={"ukf": 5.0, "drift_error": "x"}).run("--verification")
    assert v["verdict"] == "VERIFICATION PASS" and v["G4"]["judged"] is False
    v2 = Case(root, "b", shadow=shadow_rows(bad_at=50.0, col="Healthy")).run("--verification")
    assert v2["verdict"].startswith("VERIFICATION FAIL")


# ------------------------------------------------------------------------------------------- the set
def set_of(root, n, fail_one=False, md5s=None, prefix="R"):
    paths = []
    for k in range(n):
        kw = {"score_kw": {"drift": 2.0}} if (fail_one and k == 0) else {}
        c = Case(root, f"{prefix}{k}", bin_kw={"tag": k}, md5=(md5s[k] if md5s else "3c3b62bbe51d515b6ff0789a19fe1136"), **kw)
        c.run(); paths.append(c.d + "/gate.json")
    return paths


def test_set_four_passing_is_PASS(root):
    assert G.gate_set(set_of(root, 4))["verdict"] == "PASS"


def test_set_one_failing_is_FAIL(root):
    assert G.gate_set(set_of(root, 4, fail_one=True))["verdict"] == "FAIL"


def test_set_three_is_NOT_EVALUABLE(root):
    assert G.gate_set(set_of(root, 3))["verdict"].startswith("NOT EVALUABLE")


def test_N4_mixed_binaries_INVALID(root):
    assert G.gate_set(set_of(root, 4, md5s=["a" * 32] * 3 + ["b" * 32]))["verdict"].startswith("INVALID")


def test_N4_missing_md5_refused(root):
    p = set_of(root, 4, md5s=["a" * 32] * 3 + [None])
    with pytest.raises(SystemExit):
        G.gate_set(p)


def test_set_same_log_twice_refused(root):
    p = set_of(root, 4)
    d = json.load(open(p[0])); d["flight"] = "copy"; json.dump(d, open(p[0] + ".copy.json", "w"))
    with pytest.raises(SystemExit):
        G.gate_set(p + [p[0] + ".copy.json"])


def test_set_duplicate_name_refused(root):
    p = set_of(root, 4)
    d = json.load(open(p[1])); d["flight"] = "R0"; json.dump(d, open(p[1], "w"))
    with pytest.raises(SystemExit):
        G.gate_set(p)


def test_set_refuses_H_and_V_records(root):
    p = set_of(root, 4)
    h = Case(root, "H", score=False); h.run()
    v = Case(root, "V", bin_kw={"tag": 99}); v.run("--verification")
    for extra in (h.d + "/gate.json", v.d + "/gate.json"):
        with pytest.raises(SystemExit):
            G.gate_set(p + [extra])


def test_set_refuses_mixed_G6_bands_and_unsigned_D_max(root):
    p = set_of(root, 4)
    d = json.load(open(p[0])); d["g6_bands"] = [0.1, 0.02, 0.1, 0.002]; json.dump(d, open(p[0], "w"))
    with pytest.raises(SystemExit):
        G.gate_set(p)
    p2 = set_of(root, 4, prefix="S")
    d = json.load(open(p2[0])); d["d_max_m"] = 2.0; json.dump(d, open(p2[0], "w"))
    with pytest.raises(SystemExit):
        G.gate_set(p2)


# ------------------------------------------------------------------------------------------- G5 computability (rung-1 §4.3 rule)
import real_score as RS  # noqa: E402

SIGNED_DRIFT = json.load(open(os.path.join(HERE, "..", "docs", "rung1_preregistration.json")))["drift"]


def _profile(path_xy, t, rate=100.0):
    """Mocap (TUM layout) from a function of time giving (x, y); z = 1.2 m."""
    xy = np.array([path_xy(tt) for tt in t])
    return np.c_[t, xy, np.full(len(t), 1.2), np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))]


def _drift(mo, t0, t1):
    te = np.arange(t0, t1, 0.02)
    gt = np.c_[[np.interp(te, mo[:, 0], mo[:, k]) for k in (1, 2, 3)]].T
    return RS.drift_metric(gt, gt + 0.01, te, mo, t0, t1, SIGNED_DRIFT)


def rung1_like(leg):
    """Hover to 30 s after take-off (t = 0), then out-and-back legs of `leg` m at 0.4 m/s along x."""
    def f(tt):
        s = max(0.0, tt - 30.0) * 0.4; u = s % (2 * leg)
        return (u if u < leg else 2 * leg - u, 0.0)
    return f


def test_rung1_profile_with_2m_legs_makes_G5_computable():
    t = np.arange(0.0, 150.0, 0.01); mo = _profile(rung1_like(2.0), t)
    r = _drift(mo, 25.0, 145.0)
    assert "final_h_m" in r and r["init_segment_extent_h_m"] >= 1.0, r


def test_rung1_profile_with_short_legs_is_refused():
    t = np.arange(0.0, 150.0, 0.01); mo = _profile(rung1_like(0.6), t)
    r = _drift(mo, 25.0, 145.0)
    assert "error" in r and "min_extent_m" in r["error"], r


def test_H_s2v2_like_tag_profile_is_refused():
    """The SITL H_s2v2_r1 shape: the only >1 m move is before W; inside W, +-0.5 m lateral tags from the hover."""
    def f(tt):
        y = min(3.5, max(0.0, (tt - 4.0) * 0.25))           # 3.5 m forward during the climb (before W)
        x = 0.0
        for c in (80.0, 115.0):                              # +0.5, back, -0.5, back: 4 s each at 0.25 m/s
            if c <= tt < c + 16.0:
                u = tt - c; x = 0.5 * np.sin(np.pi * u / 8.0)
        return (x, y)
    t = np.arange(0.0, 200.0, 0.01); mo = _profile(f, t)
    r = _drift(mo, 25.0, 195.0)
    assert "error" in r and "min_extent_m" in r["error"] and r["init_segment_extent_h_m"] < 1.0, r
