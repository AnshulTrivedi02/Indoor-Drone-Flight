#!/usr/bin/env python3
"""Read-only check of docs/thesis/ablation/step0_report.md and preregistration_draft.md (EXPLORATORY ablation, Step 0).

Verifies:
  1. every quoted stored value against its json key (phase4_<ds>_arms.json, rerun_<ds>_evo.json, f1_test.json,
     scorer_gate.json), and every derived value (gaps, bands) recomputed from the unrounded values and rounded ONCE;
  2. numbers.md / e4_results.md / METHODOLOGY / FGO_DESIGN line quotes (line contains the quoted text);
  3. code file:line quotes, read at the pinned commit with `git show 2683ab4:<path>`;
  4. GTSAM 4.2.1 source-tarball line quotes (~/opt/src/gtsam-4.2.1);
  5. stored timing (timing_and_fwd.npz), job walls (final2_phase4 / final2_F jobs.log), [batch] solve times, the cost
     arithmetic, and that each formatted value appears in the report;
  6. the numbers.md freeze (tools/check_numbers_frozen.py).
Exit 0 iff every check passes. Usage: python3 docs/thesis/ablation/check_step0.py
"""
import json, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PIN = "2683ab4"
H = os.path.expanduser("~")
G = f"{H}/opt/src/gtsam-4.2.1"
REP = open(os.path.join(HERE, "step0_report.md")).read()
PRE = open(os.path.join(HERE, "preregistration_draft.md")).read()
n_ok = n_bad = 0


def ok(cond, what):
    global n_ok, n_bad
    if cond:
        n_ok += 1
    else:
        n_bad += 1
        print("FAIL:", what)


def r(v, n):                       # round ONCE, to n dp, as a string
    return f"{v:.{n}f}"


def in_doc(s, doc=REP, name="report"):
    ok(s in doc, f"{name} lacks {s!r}")


# ---------- 1. stored values, gaps, bands ----------
A = {ds: json.load(open(f"{REPO}/eval/results/phase4_{ds}_arms.json")) for ds in ("fwdc", "fwdplainc")}
RR = {ds: json.load(open(f"{REPO}/eval/results/rerun_{ds}_evo.json"))["trials"] for ds in ("fwdc", "fwdplainc")}
v = lambda t, k: A[t.split("_")[0]][t][k]["evo"]["ate_a_cruise"]["+0.00"]
BAGS = [f"{ds}_tex_r{i}" for ds in ("fwdc", "fwdplainc") for i in (1, 2, 3)]
for t in BAGS:
    for arm in ("heading", "baseline"):
        f, u = v(t, f"FGO_{arm}"), v(t, f"UKF_{arm}")
        in_doc(f"| {t} | {f:.6f} | {u:.6f} | {r(u - f, 3).replace('-', '−')} |")
    # control equals rerun_<ds>_evo.json
    ds = t.split("_")[0]
    ok(RR[ds][t]["est"]["FGO"]["ate_a_cruise"]["+0.00"] == v(t, "FGO_baseline"), f"{t} rerun FGO != phase4 baseline")
    ok(RR[ds][t]["est"]["UKF"]["ate_a_cruise"]["+0.00"] == v(t, "UKF_baseline"), f"{t} rerun UKF != phase4 baseline")
gaps = {t: v(t, "UKF_heading") - v(t, "FGO_heading") for t in BAGS}
ok(all(g > 0 for g in gaps.values()), "a heading gap is not > 0")
in_doc("gaps 0.071 / 0.072 / 0.074 m", PRE, "prereg")
ok([r(gaps[f"fwdc_tex_r{i}"], 3) for i in (1, 2, 3)] == ["0.071", "0.072", "0.074"], "fwdc gaps")
in_doc("gaps 0.038 / 0.057 / 0.028 m", PRE, "prereg")
ok([r(gaps[f"fwdplainc_tex_r{i}"], 3) for i in (1, 2, 3)] == ["0.038", "0.057", "0.028"], "fwdplainc gaps")
for ds in ("fwdc", "fwdplainc"):
    for arm in ("heading", "baseline"):
        vals = [v(f"{ds}_tex_r{i}", f"FGO_{arm}") for i in (1, 2, 3)]
        b = r(max(vals) - min(vals), 3)
        in_doc(f"| {ds} | {arm} | {b} (", PRE, "prereg")
in_doc("0.127 m, larger than every gap (0.028–0.057 m)", PRE, "prereg")
in_doc("0.007 m, about a tenth of the 0.071–0.074 m gap", PRE, "prereg")
# scorer gate
sg = json.load(open(os.path.join(HERE, "scorer_gate.json")))
ok(sg["n"] == 24 and sg["n_equal"] == 24, "scorer gate not 24/24"); in_doc("**Gate result: 24/24 EQUAL.**")
# F1 context
F1 = json.load(open(f"{REPO}/eval/results/f1_test.json"))
rob = [F1[f"fwdplainc_tex_r{i}"]["FGO_robust"]["yaw_rms_deg"] for i in (1, 2, 3)]
hard = [F1[f"fwdplainc_tex_r{i}"]["FGO_hard"]["yaw_rms_deg"] for i in (1, 2, 3)]
in_doc(f"RMS {r(min(rob), 2)}–{r(max(rob), 2)}° against {r(min(hard), 2)}–{r(max(hard), 2)}°")

# ---------- 2. document line quotes ----------
def line(path, n):
    with open(path) as fh:
        return fh.read().split("\n")[n - 1]


DOCQ = [("docs/thesis/numbers.md", 291, "0.127 / 0.134 / 0.137"), ("docs/thesis/numbers.md", 292, "0.06 / 0.06 / 0.06"),
        ("docs/thesis/numbers.md", 294, "0.19 / 0.15 / 0.25"), ("docs/thesis/numbers.md", 295, "0.150 / 0.094 / 0.221"),
        ("docs/thesis/numbers.md", 299, "margin 0.03–0.06 m"), ("docs/thesis/numbers.md", 299, "shrinks to 0.01–0.03 m"),
        ("docs/thesis/numbers.md", 301, "FAILED Phase 3 validation (0/3"), ("docs/thesis/numbers.md", 270, "4.47 / 2.26 / 4.54"),
        ("docs/thesis/numbers.md", 271, "4.96 / 1.78 / 4.96"), ("docs/thesis/numbers.md", 273, "4.54 / 4.52 / 4.74"),
        ("docs/thesis/numbers.md", 274, "5.02 / 11.19 / 10.82"), ("docs/thesis/numbers.md", 230, "take-off kick"),
        ("docs/thesis/numbers.md", 447, "37–40"), ("docs/thesis/numbers.md", 479, "D28"),
        ("docs/thesis/tier1/e4_results.md", 16, "H-E4.3 FAIL 7/12"), ("docs/thesis/tier1/e4_results.md", 20, "converged at every window"),
        ("docs/thesis/tier1/e4_results.md", 20, "0.0009 m"), ("docs/thesis/tier1/e4_results.md", 23, "14.35–15.13 ms"),
        ("docs/thesis/tier1/e4_results.md", 24, "278.25–303.36 ms"), ("docs/thesis/tier1/e4_results.md", 55, "| 141.3 |"),
        ("docs/thesis/tier1/e4_results.md", 57, "| 486.3 |"), ("docs/thesis/tier1/e4_results.md", 58, "| 964.8 |"),
        ("docs/thesis/tier1/e4_results.md", 60, "| 146.2 |"), ("docs/thesis/tier1/e4_results.md", 37, "Contamination check"),
        ("docs/thesis/tier1/e4_results.md", 161, "iteration counts were not logged"),
        ("docs/thesis/tier1/e4_results.md", 175, "0.0043321"), ("docs/thesis/tier1/numbers_tier1.md", 376, "## E4"),
        ("METHODOLOGY.md", 710, "4.47 / 4.44 / 3.72 m"), ("METHODOLOGY.md", 724, "RMS 0.029 m"),
        ("METHODOLOGY.md", 14276, "the FGO has NO flow or range innovation gate"),
        ("METHODOLOGY.md", 14304, "DOCUMENTED AS A DESIGN DEVIATION"),
        ("FGO_DESIGN.md", 476, "Huber(k=1.345)"), ("FGO_DESIGN.md", 477, "on the flow factor only"),
        ("FGO_DESIGN.md", 580, "median 96 /"), ("FGO_DESIGN.md", 581, "48 / ~29 ms at 1.0 / 0.5 / 0.25 s")]
for p, n, s in DOCQ:
    ok(s in line(os.path.join(REPO, p), n), f"{p}:{n} lacks {s!r}")

# ---------- 3. code quotes at the pinned commit ----------
_cache = {}


def gline(path, n):
    if path not in _cache:
        _cache[path] = subprocess.run(["git", "-C", REPO, "show", f"{PIN}:{path}"], capture_output=True, text=True,
                                      check=True).stdout.split("\n")
    return _cache[path][n - 1]


FR, FC, MM = "src/estimators/fgo/fgo_replay.py", "src/estimators/fgo/fgo_core.py", "src/estimators/measurement_models.py"
CODEQ = [(FR, 57, 'os.environ["FGO_OUT_ROOT"]'), (FR, 105, '"/ground_truth/pose"'), (FR, 118, "f_filter_forward"),
         (FR, 125, "WINDOW = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0"),
         (FR, 126, "LM_ITERS = int(sys.argv[3]) if len(sys.argv) > 3 else 2"), (FR, 128, "kf_dt=1.0/30.0"),
         (FR, 129, 'fwd_gate=(float("inf") if FV["F_ROBUST"] else FWD_CHI2_GATE)'), (FR, 132, 'fgo.batch_record = bool(FV["F_BATCH"])'),
         (FR, 189, "while tt >= t_kf_next"), (FR, 191, "t0 = time.perf_counter_ns()"), (FR, 199, "step_ns.append"),
         (FR, 216, "t_kf_next += fgo.kf_dt"), (FR, 230, "t_keyframe_ns"), (FR, 315, 'if FV["F_BATCH"]'),
         (FR, 320, "setMaxIterations(50); prm.setRelativeErrorTol(1e-6)"), (FR, 39, "EVENTS MODE"),
         (FC, 27, "1.53125e-3"), (FC, 28, "2.8125e-6"), (FC, 29, "5.0e-6"), (FC, 30, "1.25e-8"), (FC, 31, "1e-8"),
         (FC, 35, "setBiasAccOmegaInit(np.zeros((6, 6)))"), (FC, 39, "GYRO_B0 = 0.043633"), (FC, 40, "ACCEL_B0 = 0.2"),
         (FC, 44, "YAW0_SIGMA = np.radians(1)"), (FC, 48, "ROLLPITCH0_SIGMA = np.radians(5)"), (FC, 51, "YAW_DT = 0.14"),
         (FC, 52, "ATT_VAR_GATE = 0.04"), (FC, 85, "warm-started"), (FC, 89, "lm.setMaxIterations(lm_maxiter)"),
         (FC, 90, "BatchFixedLagSmoother(window, lm)"), (FC, 97, "Sigma(2, 0.25)"), (FC, 98, "Sigma(1, 0.5)"),
         (FC, 99, "Sigma(1, 0.5)"), (FC, 102, "if fwd_robust"), (FC, 106, "noiseModel.Robust.Create"),
         (FC, 107, 'fwd_sigma["omega"]'), (FC, 154, "deltaTij() <= 0"), (FC, 161, "CombinedImuFactor(X(km1), V(km1), X(k), V(k)"),
         (FC, 184, "abs(flow_xy[0]) < 4.2"), (FC, 192, "ts = {X(k): t, V(k): t, B(k): t}"),
         (FC, 193, "self.smoother.update(g, vals, _tsmap(ts))"), (FC, 196, "batch_drop_yawcap"), (FC, 229, "def reanchor"),
         (FC, 310, "np.linalg.inv(self._info("), (FC, 318, "nis <= self.fwd_gate"),
         (MM, 186, "FWD_CHI2_GATE = 9.0"), (MM, 191, '"fwdc": {"psi": np.radians(0.148), "omega": np.radians(0.162)}'),
         (MM, 192, '"fwdplainc": {"psi": np.radians(0.126), "omega": None}'), (MM, 321, 'if any(v[k] for k in v if k != "F_TAG")'),
         (MM, 322, "F_TAG is required"), (MM, 328, 'if not (v.get("F_HDG_FROM_CRUISE") or v.get("F_MASK"))'),
         ("src/estimators/ukf_replay.py", 93, "TARGET_DT = 0.0125"), ("src/estimators/ukf_replay.py", 95, "DT_STEP = math.ceil"),
         ("src/estimators/ukf_core.py", 21, "DT_REF = 0.0125"), ("src/estimators/ukf_core.py", 25, "0.015, 0.35"),
         ("src/estimators/ukf_core.py", 26, "0.001, 0.02"), ("src/estimators/ukf_core.py", 44, "FLOW_GATE=300, FLOW_MAX=2.5"),
         ("src/estimators/ukf_core.py", 293, "p['FLOW_MAX']"), ("eval/three_way_eval.py", 45, "TRIALS_DIR = f\"{HOME}/thesis_data/trials\""),
         ("eval/three_way_eval.py", 71, "def ekf3_tums"), ("eval/three_way_eval.py", 171, 'sub, f = path.split("/")'),
         ("eval/run_jobs_resumable.sh", 17, 'ST="$HOME/thesis_data/batches/$NAME"'), ("eval/final_rerun_pipeline.sh", 43, "OPENBLAS_NUM_THREADS=1"),
         ("batches/phase4_replays.jobs", 4, "fgo_replay.py fwdc_tex_r1 0.25 2 heading"),
         ("batches/f4_replays.jobs", 4, "F_ROBUST=cauchy:2.385"),
         ("src/estimators/fgo_cpp/tools/heavy.py", 55, "O_EXCL"), ("src/estimators/fgo_cpp/tools/heavy.py", 76, 'OPENBLAS_NUM_THREADS="1"'),
         ("src/estimators/fgo_cpp/tools/heavy.py", 77, "os.nice(19)")]
for p, n, s in CODEQ:
    ok(s in gline(p, n), f"{PIN}:{p}:{n} lacks {s!r}")
ok("fgo_replay.py fwdc_tex_r1 0.25 2 heading" in line(f"{H}/thesis_data/batches/final_rerun2/final2_phase4.fgo.jobs", 2), "final2 jobs:2")

# ---------- 4. GTSAM 4.2.1 source tarball ----------
BF, BH, FL = (f"{G}/gtsam_unstable/nonlinear/BatchFixedLagSmoother.cpp", f"{G}/gtsam_unstable/nonlinear/BatchFixedLagSmoother.h",
              f"{G}/gtsam_unstable/nonlinear/FixedLagSmoother.cpp")
GQ = [(BF, 82, "getCurrentTimestamp()"), (BF, 85, "findKeysBefore("), (BF, 97, "result = optimize();"), (BF, 104, "marginalize(marginalizableKeys);"),
      (BF, 164, "linearValues_.exists(key)"), (BF, 189, "linearValues_.size()"), (BF, 214, "do {"), (BF, 224, "while (true) {"),
      (BF, 259, "if (error < result.error)"), (BF, 268, "enforceConsistency_ && (linearValues_.size() > 0)"),
      (BF, 283, "if (lambda >= lambdaUpperBound)"), (BF, 297, "} // end while"), (BF, 301, "result.iterations++;"),
      (BF, 302, "while (result.iterations < maxIterations"), (BF, 310, "void BatchFixedLagSmoother::marginalize("),
      (BF, 318, "set<size_t> removedFactorSlots;"), (BF, 334, "CalculateMarginalFactors("), (BF, 338, "removeFactors(removedFactorSlots);"),
      (BF, 341, "eraseKeys(marginalizeKeys);"), (BF, 344, "insertFactors(marginalFactors);"),
      (BF, 437, "LinearContainerFactor::ConvertLinearGraph(marginalLinearFactors, theta)"),
      (BH, 37, "bool enforceConsistency = true"), (BH, 140, "Values linearValues_;"),
      (FL, 97, "timestampKeyMap_.rbegin()->first"), (FL, 106, "timestampKeyMap_.lower_bound(timestamp)"),
      (f"{G}/gtsam/nonlinear/NonlinearOptimizerParams.h", 41, "size_t maxIterations = 100"),
      (f"{G}/gtsam/nonlinear/NonlinearOptimizerParams.h", 42, "double relativeErrorTol = 1e-5"),
      (f"{G}/gtsam/nonlinear/NonlinearOptimizerParams.h", 43, "double absoluteErrorTol = 1e-5"),
      (f"{G}/gtsam/nonlinear/LinearContainerFactor.cpp", 216, "boost::make_shared<LinearContainerFactor>(f, linearizationPoint)"),
      (f"{G}/gtsam/nonlinear/LinearContainerFactor.cpp", 87, "linearizationPoint_->localCoordinates(csub)")]
for p, n, s in GQ:
    ok(s in line(p, n), f"{p}:{n} lacks {s!r}")
src = open(BF).read() + open(BH).read()
ok(not re.search(r"linearValues_\s*\.(insert|update|tryInsert)\(|linearValues_\s*=", src), "linearValues_ is written somewhere")

# ---------- 5. timing, walls, cost ----------
jl = open(f"{H}/thesis_data/batches/final2_phase4/jobs.log").read()
ok("parallel=6 commit=2cc08a2" in jl.split("\n")[0], "final2_phase4 BEGIN line")
wall = {}
for m in re.finditer(r"DONE\s+fgo__(\S+)__(heading|baseline)\s+wall=(\d+)s", jl):
    wall[(m.group(1), m.group(2))] = int(m.group(3))
for t in BAGS:
    for arm in ("heading", "baseline"):
        s = np.load(f"{H}/thesis_data/trials/{t}/fgo_{arm}/timing_and_fwd.npz")["t_keyframe_ns"] / 1e6
        med = A[t.split("_")[0]][t][f"FGO_{arm}"]["timing"]["fgo_keyframe"]["median_ms"]
        ok(abs(np.median(s) - med) < 1e-9, f"{t} {arm} median != arms json")
        in_doc(f"| {t} | {arm} | {len(s)} | {r(np.median(s), 2)} / {r(np.percentile(s, 95), 2)} | {r(s.sum() / 1e3, 1)} | {wall[(t, arm)]} |")
        frac = s.sum() / 1e3 / wall[(t, arm)]
        ok(0.955 <= frac < 0.985, f"{t} {arm} step-sum share {frac:.3f} outside 96–98%")
WH = sum(wall[(t, "heading")] for t in BAGS); WB = sum(wall[(t, "baseline")] for t in BAGS); U = WH + WB
for s_ in (f"6 heading bags **{WH} s**", f"6 baseline bags **{WB} s**", f"all 12 bags **{U} s**"):
    in_doc(s_)
r1s, r2s = 486.3 / 141.3, 964.8 / 141.3
in_doc(f"×{r(r1s, 2)} (1 s) and ×{r(r2s, 2)} (2 s)")
in_doc(f"cap 10 ≈ ×{r(146.2 / 141.3, 2)} cap 2")
rows = {"r0": U, "r1": U, "r2": U, "r3": 2 * U, "r4": r1s * U, "r5": r2s * U, "r6": WH, "r7": 2 * WH}
for k, x in rows.items():
    ok(f"| {r(x, 0)} |" in REP, f"rung {k} projection {r(x, 0)} not in report")
tot = sum(rows.values())
in_doc(f"**{r(tot, 0)} s = {r(tot / 3600, 1)} h**")
in_doc(f"{r(tot - U, 0)} s = {r((tot - U) / 3600, 1)} h")
noctl = tot - (r1s + r2s) * WB
in_doc(f"{r(noctl, 0)} s = {r(noctl / 3600, 1)} h")
in_doc(f"dropping it saves {r((r1s + r2s) * WB / 3600, 1)} h")
in_doc(f"cap 2; {r(U / 60, 0)} min)")
fl = open(f"{H}/thesis_data/batches/final2_F/jobs.log").read()
fw = [int(x) for x in re.findall(r"DONE\s+f2f_fwdc_tex_r\d\s+wall=(\d+)s", fl)]
ok(len(fw) == 3, "final2_F walls")
in_doc(f"job walls {min(fw)}–{max(fw)} s")
bm = np.mean(fw); in_doc(f"stored ≈ {r(bm, 0)} s/bag | {r(12 * bm, 0)} s = {r(12 * bm / 3600, 1)} h")
in_doc(f"Ladder plus full batch is {r((tot + 12 * bm) / 3600, 1)} h")
bt = []; lm = []
for i in (1, 2, 3):
    lg = open(f"{H}/thesis_data/batches/final2_F/logs/f2f_fwdc_tex_r{i}.log").read()
    bt += [float(x) for x in re.findall(r"^\[batch\] .*?, (\d+\.\d) s$", lg, re.M)]
    lm += [float(x) for x in re.findall(r"^\[timing\] per-keyframe update: median=(\d+\.\d)ms", lg, re.M)]
in_doc(f"batch solve {r(min(bt), 1)}–{r(max(bt), 1)} s, 3 iterations")
in_doc(f"(median {r(min(lm), 1)}–{r(max(lm), 1)} ms against")
bmed = [A[t.split("_")[0]][t]["FGO_baseline"]["timing"]["fgo_keyframe"]["median_ms"] for t in BAGS]
in_doc(f"against {r(min(bmed), 1)}–{r(max(bmed), 1)} ms)")
mc = open(os.path.join(HERE, "machine_step0.txt")).read()
ok(re.search(r"Mem:\s+15\s+9\s+\d+\s+\d+\s+\d+\s+6", mc) and "\n12\n" in mc, "machine_step0.txt")

# ---------- 6. freeze ----------
rc = subprocess.run([sys.executable, f"{REPO}/tools/check_numbers_frozen.py"], capture_output=True, text=True).returncode
ok(rc == 0, "numbers.md freeze check")

print(f"check_step0: {n_ok} passed, {n_bad} failed")
sys.exit(0 if n_bad == 0 else 1)
