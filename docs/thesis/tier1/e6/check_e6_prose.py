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
        "ho": open(HO[-1]).read() if HO else ""}


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

bad = 0
for label, s, docs in checks:
    for d in docs:
        if not DOCS[d] or s not in DOCS[d]:
            bad += 1; print(f"MISSING [{d}] {label}: {s!r}")
print(f"{len(checks)} checks, {sum(len(c[2]) for c in checks)} (string, document) pairs, {bad} mismatches")
sys.exit(1 if bad else 0)
