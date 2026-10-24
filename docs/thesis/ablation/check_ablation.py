#!/usr/bin/env python3
"""Exact cross-check of docs/thesis/ablation/ablation_numbers.md (EXPLORATORY attribution ablation results).

Independent of ablation_results.py: recomputes every displayed value from the raw score jsons
(~/thesis_data/ablation/scores/<rung>_<arm>.json), the stored eval/results/phase4_<ds>_arms.json, the per-keyframe
step times (timing_and_fwd.npz under each run's output folder) and the driver's timing.tsv / status.tsv, rounds each
ONCE, and requires the exact cell string in ablation_numbers.md. Also recomputes the verdicts (P1, P2, P3, gate) and the
interpretation-table tests, requires the verdict strings, then runs check_step0.py and tools/check_numbers_frozen.py.
Exit 0 iff 0 mismatches. Usage: python3 docs/thesis/ablation/check_ablation.py
"""
import json, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
A = os.path.expanduser("~/thesis_data/ablation")
MD = open(os.path.join(HERE, "ablation_numbers.md")).read()
BAGS = [f"{d}_tex_r{i}" for d in ("fwdc", "fwdplainc") for i in (1, 2, 3)]
FOLD = {"r0": "r0_w0.25_lm2", "r1": "r1_kf1_lm1", "r2": "r2_kf1_lm2", "r3": "r3_kf1_lm100", "r4": "r4_w1_lm2",
        "r5": "r5_w2_lm2", "r6": "r6_w0.25_lm2_huber", "r7": "r7_kf1_lm100_huber"}
n_ok = n_bad = 0


def ok(c, what):
    global n_ok, n_bad
    if c:
        n_ok += 1
    else:
        n_bad += 1; print("MISMATCH:", what)


def has(s):
    ok(s in MD, f"ablation_numbers.md lacks {s!r}")


f3 = lambda x: f"{x:.3f}".replace("-", "−")
f2 = lambda x: f"{x:.2f}".replace("-", "−")
ST = {d: json.load(open(f"{REPO}/eval/results/phase4_{d}_arms.json")) for d in ("fwdc", "fwdplainc")}
sv = lambda t, k: ST[t.split("_")[0]][t][k]["evo"]["ate_a_cruise"]["+0.00"]
ekf = lambda t: ST[t.split("_")[0]][t]["EKF3"]["ate_a_cruise"]["+0.00"]
SC = lambda r, a: json.load(open(f"{A}/scores/{r}_{a}.json"))["trials"]
V = {}
for r in ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r6s"]:
    for a in ("heading", "baseline"):
        if r in ("r6", "r7", "r6s") and a == "baseline":
            continue
        s = SC(r, a)
        for t in BAGS:
            V[(r, t, a)] = s[t]["ate_a_cruise_m"]
            ok(s[t]["status"] == "OK", f"{r} {t} {a} score status {s[t]['status']}")
# score json roots are the right folders
for r in FOLD:
    for a in ("heading", "baseline"):
        if r in ("r6", "r7") and a == "baseline":
            continue
        j = json.load(open(f"{A}/scores/{r}_{a}.json"))
        ok(os.path.realpath(j["root"]) == f"{A}/{FOLD[r]}", f"{r}_{a} root {j['root']}")
        ok(j["sub"] == f"fgo_{a}" + ("_H1345" if r in ("r6", "r7") else ""), f"{r}_{a} sub {j['sub']}")
j = json.load(open(f"{A}/scores/r6s_heading.json"))
ok(j["sub"] == "fgo_heading_F1cauchy_2_385" and os.path.realpath(j["root"]) == os.path.expanduser("~/thesis_data/trials"), "r6s source")

# ---- gate ----
g = json.load(open(f"{A}/gate.json"))
ok(g["n_identical"] == 12 and g["verdict"] == "PASS", "gate.json")
eq = sum(V[("r0", t, a)] == sv(t, f"FGO_{a}") for t in BAGS for a in ("heading", "baseline"))
ok(eq == 12, f"r0 scores equal stored {eq}/12")
has("12/12 byte-identical"); has("12/12 equal")

# ---- driver records ----
tim = {}
for ln in open(f"{A}/timing.tsv"):
    p = ln.rstrip("\n").split("\t")
    if len(p) == 9:
        tim[p[0]] = p
st = {}
for ln in open(f"{A}/status.tsv"):
    p = ln.rstrip("\n").split("\t")
    if len(p) == 8:
        st[p[0]] = p
jobs = [f"{r}__{t}__{a}" for r in FOLD for a in (("heading",) if r in ("r6", "r7") else ("heading", "baseline")) for t in BAGS]
ok(len(jobs) == 84, "84 jobs")
n_comp = sum(tim.get(j, [""] * 9)[8] == "completed" for j in jobs)
n_okst = sum(st.get(j, [""] * 8)[7] == "OK" for j in jobs)
n_retry = sum(1 for ln in open(f"{A}/timing.tsv") if ln.rstrip("\n").split("\t")[-1] == "retry")
has(f"{n_comp}/84 completed"); has(f"{n_okst}/84 OK"); has(f"retries: {n_retry}")
kff = sum(int(st[j][2].split("=")[1]) for j in jobs if j in st)
has(f"keyframe failures: {kff}")
walls = {r: sum(float(tim[j][3]) for j in jobs if j.startswith(r + "__") and j in tim) for r in FOLD}
for r in FOLD:
    has(f"| {r} | {f'{walls[r]:.0f}'} |")
tw = sum(walls.values()); has(f"total {tw:.0f} s = {tw / 3600:.1f} h")

# ---- T1 heading ----
LAD = ["r1", "r2", "r3", "r4", "r5"]
for t in BAGS:
    has(f"| {t} | " + " | ".join(f3(V[(k, t, 'heading')]) for k in ["r0"] + LAD) + f" | {f3(sv(t, 'UKF_heading'))} | {f3(ekf(t))} |")
# ---- bands ----
band = {(d, a): (lambda v: max(v) - min(v))([sv(f"{d}_tex_r{i}", f"FGO_{a}") for i in (1, 2, 3)])
        for d in ("fwdc", "fwdplainc") for a in ("heading", "baseline")}
bd = lambda t, a: band[(t.split("_")[0], a)]
# ---- T2 R ----
R = {}
for t in BAGS:
    gap = sv(t, "UKF_heading") - sv(t, "FGO_heading")
    for k in ["r0"] + LAD + ["r6", "r7", "r6s"]:
        R[(k, t)] = (sv(t, "UKF_heading") - V[(k, t, "heading")]) / gap
    ok(R[("r0", t)] == 1.0, f"R(r0) {t}")
    has(f"| {t} | {f3(gap)} | {f2(1 - bd(t, 'heading') / gap)} | " + " | ".join(f2(R[(k, t)]) for k in LAD + ["r6", "r7"]) + " |")
# ---- T3 control ----
for t in BAGS:
    f0 = sv(t, "FGO_baseline")
    cells = [f"{f3(V[(k, t, 'baseline')])} ({f3(V[(k, t, 'baseline')] - f0)})" for k in LAD]
    has(f"| {t} | {f3(V[('r0', t, 'baseline')])} | " + " | ".join(cells) + f" | {f3(bd(t, 'baseline'))} | {f3(sv(t, 'UKF_baseline'))} |")
# ---- T4 robust ----
for t in BAGS:
    has(f"| {t} | {f3(V[('r0', t, 'heading')])} | {f3(V[('r6', t, 'heading')])} | {f3(V[('r6', t, 'heading')] - V[('r0', t, 'heading')])} | "
        f"{f3(V[('r3', t, 'heading')])} | {f3(V[('r7', t, 'heading')])} | {f3(V[('r7', t, 'heading')] - V[('r3', t, 'heading')])} | "
        f"{f3(V[('r6s', t, 'heading')])} | {f3(bd(t, 'heading'))} |")
# ---- T5 step times (from the npz, not the score json) ----
for a in ("heading", "baseline"):
    for t in BAGS:
        cells = []
        for k in FOLD:
            if k in ("r6", "r7") and a == "baseline":
                cells.append("—"); continue
            s = np.load(f"{A}/{FOLD[k]}/{t}/fgo_{a}" + ("_H1345" if k in ("r6", "r7") else "") + "/timing_and_fwd.npz")["t_keyframe_ns"] / 1e6
            cells.append(f"{np.median(s):.1f} / {np.percentile(s, 95):.1f}")
        has(f"| {t}, {a} | " + " | ".join(cells) + " |")
# ---- T6 headings ----
for t in BAGS:
    cells = []
    for k in FOLD:
        c = json.load(open(f"{A}/{FOLD[k]}/{t}/fgo_heading" + ("_H1345" if k in ("r6", "r7") else "") + "/fwd_stats.json"))["counts"]
        cells.append(f"{c['psi_fused']} / {c['psi_valid']}")
    has(f"| {t} | " + " | ".join(cells) + " |")

# ---- verdicts ----
OKR = lambda j: tim.get(j, [""] * 9)[8] == "completed" and st.get(j, [""] * 8)[7] == "OK"
p1 = {}
for k in LAD:
    n = sum(OKR(f"{k}__{t}__baseline") and abs(V[(k, t, "baseline")] - sv(t, "FGO_baseline")) <= bd(t, "baseline") for t in BAGS)
    p1[k] = n; has(f"| P1 {k} | {'PASS' if n == 6 else 'FAIL'} | {n}/6 |")
has(f"| P1 overall | {'PASS' if all(v == 6 for v in p1.values()) else 'FAIL'} |")
n2 = sum(OKR(f"r3__{t}__heading") and R[("r3", t)] >= 0.5 for t in BAGS[:3])
has(f"| P2 | {'PASS' if n2 == 3 else 'FAIL'} | {n2}/3 |")
n6 = sum(OKR(f"r6__{t}__heading") and abs(V[("r6", t, "heading")] - V[("r0", t, "heading")]) <= bd(t, "heading") for t in BAGS)
n7 = sum(OKR(f"r7__{t}__heading") and OKR(f"r3__{t}__heading") and abs(V[("r7", t, "heading")] - V[("r3", t, "heading")]) <= bd(t, "heading") for t in BAGS)
has(f"| P3 | {'PASS' if n6 == 6 and n7 == 6 else 'FAIL'} | r6 {n6}/6, r7 {n7}/6 |")
# interpretation tests (fwdc; D36, D44)
for t in BAGS[:3]:
    gap = sv(t, "UKF_heading") - sv(t, "FGO_heading"); bg = band[("fwdc", "heading")] / gap
    tag = lambda c: "yes" if c else "no"
    has(f"| {t} | {f2(R[('r3', t)])} | {f2(1 - bg)} | {tag(R[('r3', t)] >= 1 - bg)} | {tag(abs(R[('r4', t)] - 1) <= bg)} | "
        f"{tag(abs(R[('r5', t)] - 1) <= bg)} |")
    for a, b in (("r1", "r2"), ("r1", "r3"), ("r2", "r3")):
        d = V[(a, t, "heading")] - V[(b, t, "heading")]
        has(f"{t} {a}−{b} {f'{d:.6f}'.replace('-', '−')} m ({'>' if abs(d) > band[('fwdc', 'heading')] else '≤'} band)")

# ---- prose numbers ----
has(f"(r6 {V[('r6','fwdplainc_tex_r1','heading')]:.3f} / {V[('r6','fwdplainc_tex_r2','heading')]:.3f} m, r7 {V[('r7','fwdplainc_tex_r1','heading')]:.3f} / "
    f"{V[('r7','fwdplainc_tex_r2','heading')]:.3f} m, against r0 {V[('r0','fwdplainc_tex_r1','heading')]:.3f} / {V[('r0','fwdplainc_tex_r2','heading')]:.3f} m)")
fs = [json.load(open(f"{A}/r0_w0.25_lm2/{t}/fgo_heading/fwd_stats.json"))["counts"] for t in BAGS[3:]]
has(f"fused only {min(c['psi_fused'] for c in fs)}–{max(c['psi_fused'] for c in fs)} of the")
has(f"{min(c['psi_valid'] for c in fs)}–{max(c['psi_valid'] for c in fs)} valid plain-wall headings")
d7 = sorted(-(V[('r7', t, 'heading')] - V[('r3', t, 'heading')]) for t in BAGS[:2])
has(f"{d7[0]:.3f}–{d7[1]:.3f} m on two flights")
def meds(ks, arms):
    out = []
    for k in ks:
        for a in arms:
            if k in ("r6", "r7") and a == "baseline":
                continue
            for t in BAGS:
                out.append(np.median(np.load(f"{A}/{FOLD[k]}/{t}/fgo_{a}" + ("_H1345" if k in ("r6", "r7") else "") + "/timing_and_fwd.npz")["t_keyframe_ns"] / 1e6))
    return f"{min(out):.1f}–{max(out):.1f} ms"
HB = ("heading", "baseline")
has(f"one keyframe {meds(['r1','r2','r3','r7'], HB)} (r1–r3, r7)"); has(f"0.25 s {meds(['r0','r6'], HB)} (r0, r6)")
has(f"1 s {meds(['r4'], HB)}"); has(f"2 s {meds(['r5'], HB)}")
mx = max(abs(V[(a, t, "heading")] - V[(b, t, "heading")]) for t in BAGS[:3] for a, b in (("r1", "r2"), ("r1", "r3"), ("r2", "r3")))
has(f"differ by at most {mx:.6f} m on `fwdc`")
has("(" + " / ".join(f3(V[(k, 'fwdplainc_tex_r3', 'baseline')]) for k in ('r1', 'r2', 'r3')) + f" against {f3(sv('fwdplainc_tex_r3', 'FGO_baseline'))} m; Δ "
    + " / ".join(f3(V[(k, 'fwdplainc_tex_r3', 'baseline')] - sv('fwdplainc_tex_r3', 'FGO_baseline')) for k in ('r1', 'r2', 'r3')) + " m)")
has(f"(R = {', '.join(f2(R[('r3', t)]) for t in BAGS[:3])}, each above")
has(f"Δ {f3(V[('r4','fwdc_tex_r2','baseline')] - sv('fwdc_tex_r2','FGO_baseline'))} and {f3(V[('r5','fwdc_tex_r2','baseline')] - sv('fwdc_tex_r2','FGO_baseline'))} m")
has(f"(+{V[('r6','fwdplainc_tex_r1','heading')] - V[('r0','fwdplainc_tex_r1','heading')]:.3f}, +{V[('r6','fwdplainc_tex_r2','heading')] - V[('r0','fwdplainc_tex_r2','heading')]:.3f} m vs band 0.127)")
has(f"(+{V[('r7','fwdplainc_tex_r1','heading')] - V[('r3','fwdplainc_tex_r1','heading')]:.3f}, +{V[('r7','fwdplainc_tex_r2','heading')] - V[('r3','fwdplainc_tex_r2','heading')]:.3f} m)")
has(f"({f3(V[('r7','fwdc_tex_r1','heading')] - V[('r3','fwdc_tex_r1','heading')])}, {f3(V[('r7','fwdc_tex_r2','heading')] - V[('r3','fwdc_tex_r2','heading')])} m vs band 0.007)")
# ---- guard and code ----
for f in ("code_pre.json", "code_post.json"):
    ok(os.path.exists(f"{A}/{f}"), f)
cp, cq = json.load(open(f"{A}/code_pre.json")), json.load(open(f"{A}/code_post.json"))
ok(cp["sha256"] == cq["sha256"] and cq["status_src_eval_tracked"] == "", "run code changed")
has("run code identical")
gp = [f for f in os.listdir(f"{REPO}/docs/thesis/tier1") if "verify_ablation_post" in f]
ok(len(gp) == 1 and json.load(open(f"{REPO}/docs/thesis/tier1/{gp[0]}"))["verdict"] == "IDENTICAL", "guard post")
has("post-run guard verify: IDENTICAL")

# ---- other checks ----
for c in ("docs/thesis/ablation/check_step0.py", "tools/check_numbers_frozen.py"):
    rc = subprocess.run([sys.executable, f"{REPO}/{c}"], capture_output=True, text=True).returncode
    ok(rc == 0, f"{c} rc {rc}")
print(f"check_ablation: {n_ok} passed, {n_bad} mismatches")
sys.exit(0 if n_bad == 0 else 1)
