#!/usr/bin/env python3
"""E6 Stage 2: the results tables, built from the score jsons ONLY, each value rounded ONCE by rd().

Read only. Prints Markdown tables to stdout; e6_results.md / e6_numbers.md carry them verbatim, and
check_e6_prose.py re-builds every row and requires string equality in the documents.
Inputs: docs/thesis/tier1/scores/e6_T_A_r{1,2,3}.json (eval/e6_score.py), docs/thesis/tier1/scores/e6_verdicts.json
(eval/e6_verdicts.py), ~/thesis_data/tier1/e6/maps/<m>/map_errors.json, docs/thesis/tier1/e6/stage2_timing.tsv."""
import json, os

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SC = os.path.join(R, "docs", "thesis", "tier1", "scores")
MAPS = os.path.expanduser("~/thesis_data/tier1/e6/maps")
J = lambda p: json.load(open(p))
V = J(os.path.join(SC, "e6_verdicts.json"))
S = {k: J(os.path.join(SC, f"e6_T_A_r{k}.json")) for k in (1, 2, 3)}
PAIR = {int(t[-1]): m for t, m in V["pairs"].items()}
ARMS = ["(i) surveyed", "(ii) FGO map", "(iii) UKF map", "(iv) no map, LC online"]


def rd(x, nd=4):
    """Round once."""
    return f"{x:.{nd}f}"


def tr(k, arm, est, kind):
    return S[k]["tracks"][f"{arm} | {est} {kind}"]


def table_main():
    """Results table: per estimator, per arm, per flight: live overall, live lap 1, hindsight overall (m)."""
    rows = ["| estimator | arm | T_A_r1 live | T_A_r2 live | T_A_r3 live | T_A_r1 lap-1 live | T_A_r2 lap-1 live | "
            "T_A_r3 lap-1 live | T_A_r1 hindsight | T_A_r2 hindsight | T_A_r3 hindsight |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for est in ("FGO", "UKF"):
        for arm in ARMS:
            L = [tr(k, arm, est, "live") for k in (1, 2, 3)]; H = [tr(k, arm, est, "hindsight") for k in (1, 2, 3)]
            rows.append(f"| {est} | {arm} | " + " | ".join(rd(t["rmse_m"]) for t in L) + " | "
                        + " | ".join(rd(t["per_lap_rmse_m"][0]) for t in L) + " | "
                        + " | ".join(rd(t["rmse_m"]) for t in H) + " |")
    return rows


def table_maps():
    rows = ["| test flight | mapping flight | FGO-map position RMS (m) | UKF-map position RMS (m) | UKF ÷ FGO |", "|---|---|---|---|---|"]
    for k in (1, 2, 3):
        m = V["flights"][f"T_A_r{k}"]["map"]
        rows.append(f"| T_A_r{k} | {m['mapping_trial']} | {rd(m['fgo_map_pos_rms_m'])} | {rd(m['ukf_map_pos_rms_m'])} | {rd(m['ukf_over_fgo'], 2)} |")
    return rows


def table_verdicts():
    rows = ["| prediction | criterion (as pre-registered) | per flight (r1, r2, r3) | count | verdict |", "|---|---|---|---|---|"]
    for c, v in V["criteria"].items():
        pf = ", ".join("—" if x is None else ("yes" if x else "no") for x in v["per_flight"])
        n = sum(1 for x in v["per_flight"] if x)
        rows.append(f"| {c} | {v['criterion']} | {pf} | {n}/3 | **{v['verdict']}** |")
    return rows


def table_ratios():
    rows = ["| estimator | flight | FGO map ÷ surveyed (live) | UKF map ÷ surveyed (live) | FGO map ÷ UKF map (live) | "
            "FGO map ÷ no map (live, overall; P4-overall) | FGO map ÷ surveyed (hindsight) | UKF map ÷ surveyed (hindsight) |",
            "|---|---|---|---|---|---|---|---|"]
    for est in ("FGO", "UKF"):
        for k in (1, 2, 3):
            g = lambda arm, kind: tr(k, arm, est, kind)["rmse_m"]
            rows.append(f"| {est} | T_A_r{k} | {rd(g(ARMS[1], 'live') / g(ARMS[0], 'live'), 2)} | {rd(g(ARMS[2], 'live') / g(ARMS[0], 'live'), 2)} | "
                        f"{rd(g(ARMS[1], 'live') / g(ARMS[2], 'live'), 2)} | {rd(g(ARMS[1], 'live') / g(ARMS[3], 'live'), 2)} | "
                        f"{rd(g(ARMS[1], 'hindsight') / g(ARMS[0], 'hindsight'), 2)} | {rd(g(ARMS[2], 'hindsight') / g(ARMS[0], 'hindsight'), 2)} |")
    return rows


def table_p2():
    rows = ["| estimator | surveyed band (m) | FGO-map live T_A_r1 / r2 / r3 (m) | inside |", "|---|---|---|---|"]
    for est in ("FGO", "UKF"):
        b = V["p2_bands_m"][est]; L = [tr(k, ARMS[1], est, "live")["rmse_m"] for k in (1, 2, 3)]
        ins = ", ".join("yes" if b["lo"] <= x <= b["hi"] else ("below" if x < b["lo"] else "above") for x in L)
        rows.append(f"| {est} | [{rd(b['lo'], 6)}, {rd(b['hi'], 6)}] | {' / '.join(rd(x, 6) for x in L)} | {ins} |")
    return rows


def table_timing():
    T = [l.rstrip("\n").split("\t") for l in open(os.path.join(R, "docs", "thesis", "tier1", "e6", "stage2_timing.tsv")) if l.strip()]
    rows = ["| run | start (AEDT) | wall (s) | exit |", "|---|---|---|---|"]
    for n, s, w, rc in T:
        rows.append(f"| {n} | {s[:16].replace('T', ' ')} | {w} | {rc} |")
    return rows


TABLES = {"main": table_main, "maps": table_maps, "verdicts": table_verdicts, "ratios": table_ratios, "p2": table_p2,
          "timing": table_timing}

if __name__ == "__main__":
    for name, f in TABLES.items():
        print(f"<!-- table {name} -->"); print("\n".join(f())); print()
