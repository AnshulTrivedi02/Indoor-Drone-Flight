#!/usr/bin/env python3
"""Stage 2f (E4): exact cross-check. Every value is recomputed INDEPENDENTLY from the raw sources (run stats.json,
fgo_live.tum, scores/E4_*.json from tag_score.py, stored eval/results/expT, stage2f/timing.tsv, stage2a/timing.tsv), NOT
from E4_verdicts.json. It is rounded ONCE (m 4 dp, ms 2 dp, s 1 dp, fractions 2 dp, differences m 7 dp), and the exact
string must appear in the named document(s). The verdicts and counts in E4_verdicts.json are also re-derived and compared.
The PROSE section checks every hand-typed number in e4_results.md and the final handover. Exit 1 on any mismatch."""
import glob, json, math, statistics as stt, sys
import numpy as np
R = "/home/makerspace/thesis_ws"; SC = f"{R}/docs/thesis/tier1/scores"; T1 = "/home/makerspace/thesis_data/tier1"
S = f"{T1}/stage2f"
DOCS = {"res": open(f"{R}/docs/thesis/tier1/e4_results.md").read(), "num": open(f"{R}/docs/thesis/tier1/numbers_tier1.md").read()}
HO = sorted(glob.glob(f"{R}/docs/handovers/*tier1_stage2f*.md"))
if HO:
    DOCS["ho"] = open(HO[-1]).read()
J = lambda p: json.load(open(p)); V = J(f"{SC}/E4_verdicts.json")
FL = [f"T_{c}_r{r}" for c in "ABCD" for r in (1, 2, 3)]; WS = ["0.25", "0.5", "1", "2", "5"]
f4 = lambda x: f"{x:.4f}"; f2 = lambda x: f"{x:.2f}"; f1 = lambda x: f"{x:.1f}"; f7 = lambda x: f"{x:+.7f}"
bad = []; n = 0


def C(label, s, where=("res",)):
    global n
    for d in where:
        n += 1
        if d not in DOCS:
            bad.append((label, s, d + " (doc missing)")); continue
        if s not in DOCS[d]:
            bad.append((label, s, d))


def EQ(label, a, b):
    global n
    n += 1
    if a != b:
        bad.append((label, f"{a!r} != {b!r}", "verdicts json"))


rd_ = lambda t, w, lm="": f"{T1}/{t}/room_fgo_w{w}{lm}"
st = lambda t, w, lm="": J(f"{rd_(t, w, lm)}/stats.json")
sc = lambda t, w, lm="": J(f"{SC}/E4_{t}_w{w}{lm}.json")["tracks"]["FGO live"]["horiz_err_m"]["rmse"]
B = {t: J(f"{R}/eval/results/expT/{t}.json")["tracks"]["FGO hindsight (whole-flight batch)"]["horiz_err_m"]["rmse"] for t in FL}
# ---- status, independently ----
for t in FL + ["T_A_r1", "T_D_r1"]:
    for w in WS:
        for lm in (("", "_lm10") if t in ("T_A_r1", "T_D_r1") else ("",)):
            s_ = st(t, w, lm); x = np.loadtxt(f"{rd_(t, w, lm)}/fgo_live.tum", ndmin=2)
            EQ(f"{t} w{w}{lm} status OK", s_["keyframe_failures"] == 0 and bool(np.isfinite(x).all()), True)
            EQ(f"{t} w{w}{lm} window/lm", (s_["window_s"], s_["lm_iters"]), (float(w), 10 if lm else 2))
            EQ(f"{t} w{w}{lm} commit", (s_["tier1"]["commit"][:7] if w != "0.25" or lm else "a09230a", s_["tier1"]["src_dirty"]),
               ("2eb6852" if w != "0.25" or lm else "a09230a", ""))
# ---- per-run values ----
LIVE = {(t, w): sc(t, w) for t in FL for w in WS}
for t in FL:
    for w in WS:
        C(f"{t} live w{w}", f"| {t} FGO live RMSE, W = {w} s | {f4(LIVE[(t, w)])} | m |", ("num",))
        s_ = st(t, w)
        C(f"{t} steps w{w}", f"| {t} step median after anchor / all keyframes, W = {w} s | {f2(s_['tier1']['step_median_ms_after_anchor'])} / {f2(s_['step_median_ms'])} | ms |", ("num",))
    C(f"{t} res live row", f"| {t} | " + " | ".join(f4(LIVE[(t, w)]) for w in WS) + f" | {f4(B[t])} |")
    C(f"{t} res step row", f"| {t} | " + " | ".join(f"{f2(st(t, w)['tier1']['step_median_ms_after_anchor'])} / {f2(st(t, w)['tier1']['step_p95_ms_after_anchor'])}" for w in WS) + " |")
    C(f"{t} res all-kf row", f"| {t} | " + " | ".join(f2(st(t, w)["step_median_ms"]) for w in WS) + " |")
    C(f"{t} H diff", f"({f7(LIVE[(t, '5')] - LIVE[(t, '0.25')])} m)")
# ---- verdicts, independently ----
p1 = sum(all(a < b for a, b in zip(m, m[1:])) for m in ([st(t, w)["tier1"]["step_median_ms_after_anchor"] for w in WS] for t in FL))
EQ("P-E4.1 count", V["P-E4.1"]["count"], f"{p1}/12"); EQ("P-E4.1 verdict", V["P-E4.1"]["verdict"], "PASS" if p1 == 12 else "FAIL")
cnt = {}
for w in ("0.25", "1", "2", "5"):
    cnt[w] = sum(((s_["step_median_ms"] <= 33 and s_["tier1"]["step_median_ms_after_anchor"] <= 33) if w == "0.25" else
                  (s_["step_median_ms"] > 33 and s_["tier1"]["step_median_ms_after_anchor"] > 33)) for s_ in (st(t, w) for t in FL))
    EQ(f"P-E4.2 {w}", V["P-E4.2"]["counts"][w], f"{cnt[w]}/12")
EQ("P-E4.2 verdict", V["P-E4.2"]["verdict"], "PASS" if all(v == 12 for v in cnt.values()) else "FAIL")
c05 = sum(st(t, "0.5")["step_median_ms"] <= 33 and st(t, "0.5")["tier1"]["step_median_ms_after_anchor"] <= 33 for t in FL)
C("P-E4.2 0.5 desc", f"0.5 s (DESCRIPTIVE, on the budget): {c05}/12 ≤ 33 ms")
h3 = [t for t in FL if LIVE[(t, "5")] < LIVE[(t, "0.25")]]
EQ("H-E4.3 count", V["H-E4.3"]["count"], f"{len(h3)}/12"); EQ("H-E4.3 verdict", V["H-E4.3"]["verdict"], "PASS" if len(h3) >= 10 else "FAIL")
C("H-E4.3 res", f"**FAIL, {len(h3)}/12.**"); C("H-E4.3 num", f"| **FAIL** (null result) | {len(h3)}/12 |", ("num",))
C("H-E4.3 sum", f"**H-E4.3 FAIL {len(h3)}/12**"); C("P-E4.1 res", f"**PASS, {p1}/12.**")
# ---- gain fractions ----
Fp = {}
for w in WS[1:]:
    num = {t: LIVE[(t, "0.25")] - LIVE[(t, w)] for t in FL}; den = {t: LIVE[(t, "0.25")] - B[t] for t in FL}
    F = sum(num.values()) / sum(den.values()); Fp[w] = F; fi = [num[t] / den[t] for t in FL]
    Fc = [sum(num[t] for t in FL if t[2] == c) / sum(den[t] for t in FL if t[2] == c) for c in "ABCD"]
    C(f"F row {w}", f"| {w} | {f2(F)} | " + " | ".join(f2(x) for x in Fc) + f" | {f2(stt.median(fi))} | {f2(min(fi))}–{f2(max(fi))} | 12 |")
    C(f"F num {w}", f"| F({w} s) pooled / median f_i | {f2(F)} / {f2(stt.median(fi))} | fraction |", ("num",))
C("F prose", "F(W) pooled is " + " / ".join(f2(Fp[w]) for w in WS[1:]) + " at W = 0.5 / 1 / 2 / 5 s")
for t in ("T_A_r1", "T_D_r1"):
    C(f"lm10 f {t}", f"{t} " + ", ".join(f"W {w}: {f2((LIVE[(t, '0.25')] - sc(t, w, '_lm10')) / (LIVE[(t, '0.25')] - B[t]))}" for w in WS))
# ---- convergence, independently ----
mx = 0.0
for t in ("T_A_r1", "T_D_r1"):
    win = J(f"{SC}/E4_{t}_w0.25.json")["window_s"]
    for w in WS:
        a = np.loadtxt(f"{rd_(t, w)}/fgo_live.tum", ndmin=2); b = np.loadtxt(f"{rd_(t, w, '_lm10')}/fgo_live.tum", ndmin=2)
        EQ(f"conv {t} w{w} rows", (len(a), np.array_equal(a[:, 0], b[:, 0])), (len(b), True))
        d = a[:, 1:4] - b[:, 1:4]; inw = (a[:, 0] >= win[0]) & (a[:, 0] <= win[1])
        h, d3 = np.hypot(d[:, 0], d[:, 1]), np.linalg.norm(d, axis=1)
        rms = lambda x: float(np.sqrt(np.mean(x ** 2)))
        rr = [rms(h), rms(d3), rms(h[inw]), rms(d3[inw])]; mx = max(mx, max(rr))
        C(f"conv {t} {w}", f"| {t}, {w} | {len(a)} (0) | {f4(rr[0])} / {f4(h.max())} | {f4(rr[1])} / {f4(d3.max())} | {f4(rr[2])} | {f4(rr[3])} | "
          f"{f4(LIVE[(t, w)])} / {f4(sc(t, w, '_lm10'))} |")
        EQ(f"conv flag {t} {w}", V["convergence"]["per_run"][f"{t} w{w}"]["NOT_CONVERGED"], max(rr) > 0.029)
C("conv max", f"The largest RMS reading is {f4(mx)} m")
# ---- wall times ----
wall = {}
for ln in open(f"{S}/timing.tsv"):
    f = ln.rstrip("\n").split("\t")
    if len(f) >= 9 and f[8] == "completed":
        wall[f[0]] = float(f[3])
for ln in open(f"{T1}/stage2a/timing.tsv"):
    f = ln.split("\t")
    if f[0].startswith("ge4_"):
        wall[f"e4_{f[0][4:]}_w0.25"] = float(f[3])
EQ("58 completed", len([k for k in wall if not (k.endswith("_w0.25") and "lm10" not in k)]), 58)
for lm, fls in (("", FL), ("_lm10", ["T_A_r1", "T_D_r1"])):
    for w in WS:
        ws_ = [wall[f"e4_{t}_w{w}{lm}"] for t in fls]
        C(f"wall {w}{lm}", f"| {w} | {10 if lm else 2} | {len(fls)}/{len(fls)} | {len(fls)} / 0 | {f1(min(ws_))}–{f1(max(ws_))} | {f1(stt.mean(ws_))} |")
# ---- PROSE (hand-typed numbers) ----
rng = lambda xs, f: f"{f(min(xs))}–{f(max(xs))}"
med_aa = lambda w: [st(t, w)["tier1"]["step_median_ms_after_anchor"] for t in FL]
C("prose 0.25 range", f"{rng(med_aa('0.25'), f2)} ms at 0.25 s", ("res", "ho"))
C("prose 5 range", f"{rng(med_aa('5'), f2)} ms at 5 s", ("res", "ho"))
C("prose 0.5 range", f"it measured {rng(med_aa('0.5'), f2)} ms after the anchor")
fd = [LIVE[(t, "5")] - LIVE[(t, "0.25")] for t in FL if t not in h3]
C("prose fail diffs", f"{f7(min(fd))} to {f7(max(fd))} m", ("res", "ho"))
C("prose fail flights", "(" + ", ".join(t for t in FL if t not in h3) + ")")
C("prose D diffs", "(by " + ", ".join(f"{abs(LIVE[(t, '5')] - LIVE[(t, '0.25')]):.7f}" for t in ("T_D_r1", "T_D_r2", "T_D_r3")).replace(", 0.0006", " and 0.0006") + " m)")
C("prose T_D_r2", f"T_D_r2 is worse at 1 s ({f4(LIVE[('T_D_r2', '1')])} m) and better at 5 s ({f4(LIVE[('T_D_r2', '5')])} m)")
C("prose 5s mean wall", f"measured mean of {stt.mean(wall[f'e4_{t}_w5'] for t in FL):,.1f} s")
C("prose times", "2026-10-23 11:28:45 AEDT to 2026-10-24 04:33:39 AEDT")
C("prose guard", "13,253 files", ("res", "ho"))
EQ("timing start", open(f"{S}/timing.tsv").readline().split("\t")[1], "2026-10-23T11:28:45+11:00")
EQ("timing end", [l for l in open(f"{S}/timing.tsv") if l.startswith("ALLDONE")][0].strip(), "ALLDONE 2026-10-24T04:33:39+11:00")
for g in glob.glob(f"{R}/docs/thesis/tier1/frozen_manifest_20261022T002851_verify_stage2f_*.json"):
    r_ = J(g); EQ(f"guard {g[-30:]}", (r_["verdict"], r_["n_files_checked"], sum(len(r_[k]) if isinstance(r_[k], list) else r_[k] for k in ("changed", "missing", "added", "errors"))), ("IDENTICAL", 13253, 0))
C("ho wall 5", f"{stt.mean(wall[f'e4_{t}_w5'] for t in FL):,.1f} s at cap 2 and {stt.mean(wall[f'e4_{t}_w5_lm10'] for t in ('T_A_r1', 'T_D_r1')):,.1f} s at cap 10", ("ho",))
C("ho F", "pooled F = " + " / ".join(f2(Fp[w]) for w in WS[1:]) + " at W = 0.5 / 1 / 2 / 5 s", ("ho",))
C("ho conv max", f"The largest RMS reading is {f4(mx)} m", ("ho",))
_pj = [l for l in open(f"{S}/projection.log") if "done 4/58" in l][0]
C("ho projection", "about " + _pj.split("projected end ")[1][:16].replace("T", " ") + " AEDT", ("ho",))
C("ho fail count", f"| **FAIL** (null result) | {len(h3)}/12 |", ("ho",))
print(f"{n} checks, {len(bad)} mismatches")
for b in bad:
    print("MISMATCH", b)
sys.exit(1 if bad else 0)
