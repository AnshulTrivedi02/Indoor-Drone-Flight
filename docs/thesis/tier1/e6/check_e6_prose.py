#!/usr/bin/env python3
"""E6 Stage 2 exact cross-check (the stage2e/check_prose.py approach). Every hand-typed or generated number in
e6_results.md, e6_numbers.md §Results and the Stage 2 handover is recomputed here from its source json (independently of
e6_tables.py / e6_render.py), rounded ONCE by rd(), and the exact string must occur in the named document(s).
Also: every table row of e6_tables.py must occur verbatim in e6_results.md and e6_numbers.md, and the verdict jsons
must agree with the verdict words typed. Exit 1 on any mismatch. Read only."""
import glob, json, os, sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
T = os.path.join(R, "docs", "thesis", "tier1"); SC = os.path.join(T, "scores")
J = lambda p: json.load(open(p))
HO = sorted(glob.glob(os.path.join(R, "docs", "handovers", "2026-11-0*_e6_stage2.md")))
DOCS = {"res": open(os.path.join(T, "e6_results.md")).read(),
        "num": open(os.path.join(T, "e6_numbers.md")).read().split("## §Results")[1].split("## §Deviations")[0],
        "ho": open(HO[-1]).read() if HO else "",
        "numg": open(os.path.join(T, "e6_numbers.md")).read().split("## §Guard")[1].split("## §Gates")[0]}


def rd(x, nd=4):
    """Round once."""
    return f"{x:.{nd}f}"


def rng(v, nd=4, u=" m"):
    return f"{rd(min(v), nd)}–{rd(max(v), nd)}{u}"


S = {k: J(os.path.join(SC, f"e6_T_A_r{k}.json")) for k in (1, 2, 3)}; V = J(os.path.join(SC, "e6_verdicts.json"))
ARMS = ["(i) surveyed", "(ii) FGO map", "(iii) UKF map", "(iv) no map, LC online"]
t = lambda k, a, e, kind: S[k]["tracks"][f"{a} | {e} {kind}"]
L = lambda a, e, kind="live", lap1=False: [t(k, a, e, kind)["per_lap_rmse_m"][0] if lap1 else t(k, a, e, kind)["rmse_m"] for k in (1, 2, 3)]
checks = []
C = lambda label, s, docs=("res",): checks.append((label, s, docs))

# --- results-table rows (independent build) ---
for e in ("FGO", "UKF"):
    for a in ARMS:
        row = f"| {e} | {a} | " + " | ".join(rd(x) for x in L(a, e)) + " | " + " | ".join(rd(x) for x in L(a, e, lap1=True)) \
              + " | " + " | ".join(rd(x) for x in L(a, e, "hindsight")) + " |"
        C(f"main {e} {a}", row, ("res", "num"))
# --- map rows ---
for k in (1, 2, 3):
    me = J(os.path.expanduser(f"~/thesis_data/tier1/e6/maps/{V['pairs'][f'T_A_r{k}']}/map_errors.json"))["errors"]
    f, u = me["fgo"]["pos_rms_m"], me["ukf"]["pos_rms_m"]
    C(f"map T_A_r{k}", f"| T_A_r{k} | {V['pairs'][f'T_A_r{k}']} | {rd(f)} | {rd(u)} | {rd(u / f, 2)} |", ("res", "num"))
# --- verdict rows: per-flight booleans and verdict word recomputed from the scores ---
band = V["p2_bands_m"]
for e in ("FGO", "UKF"):
    st = [J(os.path.join(R, "eval", "results", "expT", f"T_A_r{k}.json"))["tracks"][f"{e} live"]["horiz_err_m"]["rmse"] for k in (1, 2, 3)]
    Rg = max(st) - min(st); lo, hi = min(st) - Rg, max(st) + Rg
    assert abs(lo - band[e]["lo"]) < 1e-15 and abs(hi - band[e]["hi"]) < 1e-15
    p2 = [lo <= x <= hi for x in L(ARMS[1], e)]
    p3 = [a < b for a, b in zip(L(ARMS[1], e), L(ARMS[2], e))]
    p4 = [a < b for a, b in zip(L(ARMS[1], e, lap1=True), L(ARMS[3], e, lap1=True))]
    for name, pf in (("P2", p2), ("P3", p3), ("P4", p4)):
        vd = "PASS" if all(pf) else "FAIL"; assert V["criteria"][f"{name} ({e})"]["verdict"] == vd
        C(f"verdict {name} {e}", f"| {', '.join('yes' if x else 'no' for x in pf)} | {sum(pf)}/3 | **{vd}** |", ("res", "num"))
p1 = []
for k in (1, 2, 3):
    me = J(os.path.expanduser(f"~/thesis_data/tier1/e6/maps/{V['pairs'][f'T_A_r{k}']}/map_errors.json"))["errors"]
    p1.append(me["fgo"]["pos_rms_m"] < me["ukf"]["pos_rms_m"])
assert V["criteria"]["P1"]["verdict"] == ("PASS" if all(p1) else "FAIL")
C("verdict P1", f"| P1 | FGO-map position RMS < UKF-map position RMS, 3/3 mapping flights | {', '.join('yes' if x else 'no' for x in p1)} | {sum(p1)}/3 | **{V['criteria']['P1']['verdict']}** |", ("res", "num"))
C("P1 headline", f"**P1: FAIL** ({sum(p1)}/3)", ("res", "ho"))
C("P2 bands", f"| FGO | [{rd(band['FGO']['lo'], 6)}, {rd(band['FGO']['hi'], 6)}] | {' / '.join(rd(x, 6) for x in L(ARMS[1], 'FGO'))} |", ("res", "num"))
C("P2 bands UKF", f"| UKF | [{rd(band['UKF']['lo'], 6)}, {rd(band['UKF']['hi'], 6)}] | {' / '.join(rd(x, 6) for x in L(ARMS[1], 'UKF'))} |", ("res", "num"))
# --- prose numbers ---
me1 = J(os.path.expanduser("~/thesis_data/tier1/e6/maps/E6M_fig8_r1b/map_errors.json"))["errors"]
C("p1 r1b", f"({rd(me1['fgo']['pos_rms_m'])} m against {rd(me1['ukf']['pos_rms_m'])} m)")
C("p2 ukf r1", f"({rd(L(ARMS[1], 'UKF')[0])} m against an upper edge of {rd(band['UKF']['hi'])} m)")
ratio = lambda e, a, b: [x / y for x, y in zip(L(a, e), L(b, e))]
C("p4o fgo", f"ratio {rng(ratio('FGO', ARMS[1], ARMS[3]), 2, '')} for the FGO")
C("p4o ukf", f"{rng(ratio('UKF', ARMS[1], ARMS[3]), 2, '')} for the UKF")
C("l1 fgo", f"lap-1 live errors of {rng(L(ARMS[1], 'FGO', lap1=True))} for the FGO", ("res", "ho"))
C("l1 fgo iv", f"against {rng(L(ARMS[3], 'FGO', lap1=True))} with no map", ("res", "ho"))
C("l1 ukf", f"For the UKF it gives {rng(L(ARMS[1], 'UKF', lap1=True))}, against {rng(L(ARMS[3], 'UKF', lap1=True))}", ("res",))
mf = [J(os.path.expanduser(f"~/thesis_data/tier1/e6/maps/{m}/map_errors.json"))["errors"] for m in ("E6M_fig8_r1b", "E6M_fig8_r2", "E6M_fig8_r3")]
C("map rng", f"off by {rng([x['fgo']['pos_rms_m'] for x in mf])} (FGO map) and\n  {rng([x['ukf']['pos_rms_m'] for x in mf])} (UKF map)")
C("r fgo", f"the live error is {rng(ratio('FGO', ARMS[1], ARMS[0]), 2, '')} times", ("res", "ho"))
C("ukf i", f"larger to begin with ({rng(L(ARMS[0], 'UKF'))})")
C("r ukf", f"{rng(ratio('UKF', ARMS[1], ARMS[0]), 2, '')} times that", ("res",))
C("hs fgo", f"reaches\n    {rng(L(ARMS[1], 'FGO', 'hindsight'))}, against {rng(L(ARMS[0], 'FGO', 'hindsight'))} on the surveyed map")
C("r1b diff", f"within\n  {rd(abs(me1['fgo']['pos_rms_m'] - me1['ukf']['pos_rms_m']))} m of each other")
bs = [J(p)["batch_s"] for p in glob.glob(os.path.expanduser("~/thesis_data/tier1/T_A_r*/room_fgo_e6_*/stats.json"))]
assert len(bs) == 6
C("batch", f"{rng(bs, 1, ' s')} per run", ("res",))
tm = [l.rstrip("\n").split("\t") for l in open(os.path.join(T, "e6", "stage2_timing.tsv")) if l.strip()]
wa = [float(x[2]) for x in tm if x[0].startswith("2a")]; wb = [float(x[2]) for x in tm if x[0].startswith("2b")]
assert len(wa) == 6 and len(wb) == 6 and all(x[3] == "0" for x in tm)
C("2a wall", f"{rd(min(wa), 1)}–{rd(max(wa), 1)} s", ("ho",)); C("2b wall", f"{rd(min(wb), 1)}–{rd(max(wb), 1)} s", ("ho",))
assert all(x["scorer_gate_S_E6"]["pass"] for x in S.values())
smax = max(c["abs_diff"] for x in S.values() for c in x["scorer_gate_S_E6"]["checks"])
C("S-E6 max", f"max |diff| ≤ {smax:.2e} m", ("res",))

# --- hindsight bullet (descriptive) ---
hfm = L(ARMS[1], "FGO", "hindsight") + L(ARMS[2], "FGO", "hindsight")
nh = sum(a < min(b, c) for a, b, c in zip(L(ARMS[3], "FGO", "hindsight"), L(ARMS[1], "FGO", "hindsight"), L(ARMS[2], "FGO", "hindsight")))
C("hs fgo iv", f"hindsight, {rng(L(ARMS[3], 'FGO', 'hindsight'))}) beat the FGO whole-flight batch on either fixed estimated map ({rng(hfm)}) on\n  {nh}/3 flights")
C("hs ukf", f"arm (iv) RTS gives {rng(L(ARMS[3], 'UKF', 'hindsight'))}, against {rng(L(ARMS[1], 'UKF', 'hindsight'))} on the FGO")
# --- counts and run facts (registered phrases) ---
FG = [J(p) for p in glob.glob(os.path.expanduser("~/thesis_data/tier1/T_A_r*/room_fgo_e6_*/stats.json"))]
UK = glob.glob(os.path.expanduser("~/thesis_data/tier1/T_A_r*/room_ukf_e6_*/stats.json"))
it = {x["batch_iterations"] for x in FG}; kf = {x["keyframe_failures"] for x in FG}; assert len(it) == 1 and kf == {0}
C("runs", f"{len(UK)} runs each. All {len(tm)} exited {tm[0][3]}. 2b had {kf.pop()} keyframe\n  failures, and every FGO whole-flight batch converged in {it.pop()} iterations")
C("num all exit", f"all {len(tm)} exit 0", ("num",))
C("ho runs", f"{len(UK)} runs", ("ho",))
C("ho 2a", f"| all exit {tm[0][3]}, wall {rd(min(wa), 1)}–{rd(max(wa), 1)} s", ("ho",))
C("ho 2b", f"| all exit {tm[0][3]}, wall {rd(min(wb), 1)}–{rd(max(wb), 1)} s, {min(x['keyframe_failures'] for x in FG)} keyframe failures, batch converged in {FG[0]['batch_iterations']} iterations", ("ho",))
C("ho scoring", f"× {len(S)}, S-E6 PASS {sum(x['scorer_gate_S_E6']['pass'] for x in S.values())}/3", ("ho",))
pre = open(os.path.join(T, "e6_preregistration.md")).read(); assert "≤ 155 + 2,961 s" in pre
C("prereg batch bound", "upper\n  bound of 2,961 s, which was a 6-parallel figure")
G = [J(p) for p in glob.glob(os.path.join(T, "frozen_manifest_20261022T002851_verify_e6_stage2*.json"))]
assert len(G) == 6 and all(g["verdict"] == "IDENTICAL" for g in G); nf = {g["n_files_checked"] for g in G}; assert len(nf) == 1
nf = nf.pop(); C("guard files", f"**IDENTICAL**, {nf:,} files"); C("guard heading", f"(`frozen_manifest_20261022T002851.json`, {nf:,} files)")
for g in G:
    C(f"guard time {g['verified_local']}", f"{g['verified_local'][:10]} {g['verified_local'][11:16]} AEDT", ("res", "numg"))
C("S-E6 tol", f"tolerance {S[1]['scorer_gate_S_E6']['tolerance_m']:.0e} m".replace("e-09", "e-9"))
# D96 row in the decisions log
DL = open(os.path.join(T, "decisions_log.md")).read(); d85 = [l for l in DL.split("\n") if l.startswith("| D96 |")][0]
for e, lab in (("FGO", "the FGO"), ("UKF", "the UKF")):
    if f"{rng(ratio(e, ARMS[1], ARMS[0]), 2, '')} for {lab}" not in d85:
        checks.append((f"D96 {e}", "MISSING-IN-D96", ("res",)))

bad = 0
for label, s, docs in checks:
    for d in docs:
        if not DOCS[d] or s not in DOCS[d]:
            bad += 1; print(f"MISSING [{d}] {label}: {s!r}")

# --- verdict counts typed in prose (from e6_verdicts.json per_flight; S-E6 passes from the score jsons) ---
cnt = lambda c: sum(1 for x in V["criteria"][c]["per_flight"] if x)
vw = lambda c: V["criteria"][c]["verdict"]
nS = sum(x["scorer_gate_S_E6"]["pass"] for x in S.values())
C("S-E6 res", f"scoring call, PASS {nS}/3", ("res",)); C("S-E6 num", f"PASS {nS}/3 inside every call", ("num",))
assert vw("P2 (FGO)") == vw("P2 (UKF)") == "FAIL" and vw("P3 (FGO)") == vw("P3 (UKF)") == "FAIL" and vw("P4 (FGO)") == vw("P4 (UKF)") == "PASS"
assert cnt("P3 (FGO)") == cnt("P3 (UKF)") and cnt("P4 (FGO)") == cnt("P4 (UKF)")
C("P2 head", f"**P2: FAIL (both).** FGO {cnt('P2 (FGO)')}/3:", ("res", "ho"))
C("P2 head ukf", f"UKF {cnt('P2 (UKF)')}/3:", ("res", "ho"))
C("P3 head res", f"**P3: FAIL (both)**, {cnt('P3 (FGO)')}/3 for each estimator", ("res",))
C("P4 head res", f"**P4: PASS (both)**, {cnt('P4 (FGO)')}/3 for each estimator", ("res",))
C("P3 head ho", f"**P3: FAIL (both)**, {cnt('P3 (FGO)')}/3 each", ("ho",))
C("P4 head ho", f"**P4: PASS (both)**, {cnt('P4 (FGO)')}/3 each", ("ho",))
p4o = {e: sum(t(k, ARMS[1], e, "live")["rmse_m"] < t(k, ARMS[3], e, "live")["rmse_m"] for k in (1, 2, 3)) for e in ("FGO", "UKF")}
assert p4o["FGO"] == p4o["UKF"]
C("P4o count", f"lower than arm (iv)'s on {p4o['FGO']}/3 flights")
C("P2 fgo reading", f"(P2 FAIL, {cnt('P2 (FGO)')}/3)"); C("P2 ukf reading", f"(P2 FAIL, {cnt('P2 (UKF)')}/3)")
C("P1 reading", f"(P1 FAIL, {sum(p1)}/3)")

# --- COMPLETENESS: every numeric token left after removing registered strings and identifiers ---
import re
IDENT = [r"`[^`]*`", r"[\w./-]*(tier1|e6_|sha256|iSAM2)[\w./-]*", r"T_A_r\d", r"E6[MV]_fig8_\w+", r"\bD\d+\b", r"\bP\d\b", r"§\s?\d+(\.\d+)*", r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?",
         r"\b\d{1,2}:\d{2}\b", r"\br\d+b?\b", r"\b[0-9a-f]{7}\b", r"\bk = 1, 2, 3\b", r"\b(lap|laps|Lap)[- ]\d( ÷ lap-\d)?\b", r"lap-\d", r"\b[1-5]–[1-5]\b",
         r"\b2[abcde]\b", r"\b1[bcde]\b", r"Stage \d[a-e]?", r"Experiment \d", r"\bE\d\b", r"[0-9]+ dp", r"\b(tags?|tag) \d( and \d)?", r"0\.25 s",
         r"\b3 circuits\b", r"\b7 tags?\b", r"the other 7 tags", r"\b7 non-gauge", r"5 extra updates", r"iSAM2 \+ 5 updates", r"\+ 5 updates", r"\bn = 3\b",
         r"\bstep \d\b", r"\(\d\)", r"^\s*\d\.\s", r"^#+ \d+\.", r"mapping flights E6M", r"thread variables at 1", r"rule \d", r"rules [\d, ]+",
         r"\d+ checks", r"0 mismatches", r"\b4 Nov\b", r"2026", r"12:00", r"23:59", r"three", r"r\{\{?1,2,3\}?\}"]
TABLE = lambda txt: "\n".join(l for l in txt.split("\n") if not l.startswith("|"))
left = []
for d, txt in DOCS.items():
    if d == "numg":
        continue
    x = txt
    for _, st, docs in sorted(checks, key=lambda c: -len(c[1])):
        if d in docs:
            x = x.replace(st, " ")
    x = TABLE(x) if d != "ho" else x
    for pat in IDENT:
        x = re.sub(pat, " ", x, flags=re.M)
    for m in re.finditer(r"\d[\d,.]*", x):
        left.append((d, m.group(), x[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")))
for l in left:
    print("UNREGISTERED", l)

bad += len(left)
print(f"{len(checks)} checks, {sum(len(c[2]) for c in checks)} (string, document) pairs, {bad} mismatches")
sys.exit(1 if bad else 0)
