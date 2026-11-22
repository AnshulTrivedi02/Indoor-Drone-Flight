#!/usr/bin/env python3
"""IPLS stage 2 report generator (docs/thesis/iterated_smoother/preregistration.md + AMENDMENT 1, EXPLORATORY).

Read-only: reads eval/results/iterated_smoother/ipls_scores.json (written by eval/ipls_score.py). Writes:
  - docs/thesis/iterated_smoother/numbers_ipls.md  (every number used in results.md, each tagged with its json
    key, rounded ONCE with rd()/rd_si() of eval/figs_thesis.py, loaded through the AST -- the same pattern
    eval/cl_heading_perflight.py uses -- plus the raw unrounded value for traceability);
  - docs/thesis/iterated_smoother/results.md (the EXPLORATORY results write-up: per-condition table of UKF live /
    RTS-UKF / IPLS-UKF / FGO batch, per-flight RMSE, E-1..E-3 verdicts as worded in the pre-registration,
    convergence table, the Experiment 4 (O) check).

Every number placed into results.md comes from the SAME formatted-string dict (NUM) that numbers_ipls.md is built
from -- so results.md cannot contain a number that disagrees with numbers_ipls.md by construction. --check
re-reads ipls_scores.json, rebuilds NUM, re-renders both files, and asserts the freshly rendered text is
byte-identical to what is on disk (i.e. nothing in either file was hand-edited after generation) -- the "exact
cross-check that every number in results.md equals the numbers file".

This script does not score anything and does not touch eval/results/expT/, numbers.md, or any stored trial output.

Usage: python3 eval/ipls_report.py [--check]"""
import ast, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCORES = os.path.join(HERE, "results", "iterated_smoother", "ipls_scores.json")
DOCDIR = os.path.join(ROOT, "docs", "thesis", "iterated_smoother")
NUMBERS_OUT = os.path.join(DOCDIR, "numbers_ipls.md")
RESULTS_OUT = os.path.join(DOCDIR, "results.md")
IPLS_NAME = "IPLS-UKF (hindsight, exploratory)"
TRACK_ORDER = ["UKF live", "RTS-UKF (hindsight)", IPLS_NAME, "FGO hindsight (whole-flight batch)"]
TRACK_SHORT = {"UKF live": "UKF live", "RTS-UKF (hindsight)": "RTS-UKF", IPLS_NAME: "IPLS-UKF",
               "FGO hindsight (whole-flight batch)": "FGO batch"}


def _load_from_figs_thesis(*names):
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py")).read())
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    return tuple(ns[n] for n in names)


rd, rd_si = _load_from_figs_thesis("rd", "rd_si")


class Numbers:
    """Accumulates (key, formatted, raw) triples in insertion order; `get` is the only way a formatted value
    reaches the rendered markdown, so results.md and numbers_ipls.md are always built from the same table."""

    def __init__(self):
        self.rows = []
        self._by_key = {}

    def add(self, key, raw, n=3, si=None):
        if si is None:
            s = rd(raw, n)
        else:
            s = rd_si(raw, n, k=si)
        if key in self._by_key:
            assert self._by_key[key] == (s, raw), f"duplicate key with different value: {key}"
        else:
            self.rows.append((key, s, raw))
            self._by_key[key] = (s, raw)
        return s

    def get(self, key):
        return self._by_key[key][0]


def build(data):
    N = Numbers()
    trials = data["trials"]
    scored = set(data["scored_trials"])

    for t in trials:
        for tr in TRACK_ORDER:
            if tr in data["rmse_m"][t]:
                N.add(f"rmse_m.{t}.{tr}", data["rmse_m"][t][tr], 3)
        conv = data["convergence"][t]
        if conv is not None:
            N.add(f"convergence.{t}.iterations_run", conv["iterations_run"], 0)
            N.add(f"convergence.{t}.run_time_s_total", conv["run_time_s_total"], 1)
            N.add(f"convergence.{t}.run_time_s_forward_pass", conv["run_time_s_forward_pass"], 1)
            N.add(f"convergence.{t}.run_time_s_ipls", conv["run_time_s_ipls"], 1)
            for h in conv["history"]:
                N.add(f"convergence.{t}.history.{h['iter']}.cost", h["cost"], 2)
                if h["max_change_m"] is not None:
                    N.add(f"convergence.{t}.history.{h['iter']}.max_change_mm", h["max_change_m"], 2, si=3)

    for c in "ABCD":
        row = data["conditions"][c]
        for tr in TRACK_ORDER:
            if tr in row["mean_rmse_m"]:
                N.add(f"conditions.{c}.mean_rmse_m.{tr}", row["mean_rmse_m"][tr], 3)

    N.add("E-1.n_pass", data["E-1"]["n_pass"], 0)
    N.add("E-1.n_total", data["E-1"]["n_total"], 0)

    for c in "ABCD":
        if c in data["E-2"]["by_condition"]:
            e2 = data["E-2"]["by_condition"][c]
            N.add(f"E-2.by_condition.{c}.ratio", e2["ratio"], 2)
    N.add("E-2.n_pass", data["E-2"]["n_pass"], 0)
    N.add("E-2.n_total", data["E-2"]["n_total"], 0)

    for c in "ABCD":
        if data["E-3"]["condition_medians_m"][c] is not None:
            N.add(f"E-3.condition_medians_m.{c}", data["E-3"]["condition_medians_m"][c], 3)
    N.add("E-3.n_gaps", data["E-3"]["n_gaps"], 0)

    return N


def render_results(data, N):
    trials = data["trials"]
    scored = set(data["scored_trials"])
    not_scored = data["not_scored_trials"]

    L = []
    L.append("# Iterated UKF smoother (IPLS) for Experiment 2: results")
    L.append("")
    L.append("**STATUS: EXPLORATORY.** Added after the Experiment 2 results (`docs/thesis/numbers.md` section 16.1). "
             "Nothing in `numbers.md`, the frozen pack, `eval/results/expT/`, or any stored `room_ukf/`/`room_fgo/` "
             "output is touched. P-T2 and P-T4 stay FAIL as scored in `numbers.md`; this document does not change "
             "that. Pre-registration: `docs/thesis/iterated_smoother/preregistration.md`, including AMENDMENT 1 "
             "(D153, the cost definition and the G3(b) cost check). Scored by `eval/ipls_score.py`, generated by "
             "`eval/ipls_report.py`. Rounding: `rd()`/`rd_si()` of `eval/figs_thesis.py`, loaded through the AST, "
             "applied once; every number here is tagged with its json key in "
             "`docs/thesis/iterated_smoother/numbers_ipls.md`.")
    L.append("")

    L.append("## Reproduction check (precondition for scoring)")
    L.append("")
    L.append(f"`eval/ipls_score.py` recomputes \"UKF live\", \"RTS-UKF (hindsight)\" and \"FGO hindsight "
             f"(whole-flight batch)\" for all {len(trials)} flights from the bag and the same stored `room_ukf/` / "
             f"`room_fgo/` tum files `eval/tag_score.py` reads, using functions copied verbatim from `tag_score.py` "
             f"(`tum`, `err`, `st`, the lap-window/clock-map logic) and from `t_aggregate.py` (`gains`). Before any "
             f"IPLS number is read, it asserts, by float equality, that every one of those tracks' `horiz_err_m` "
             f"statistics AND every stored gap's `t0`/`t1`/track `mean`/`max` reproduce "
             f"`eval/results/expT/<trial>.json` exactly. Result: **{data['reproduction_check']}** for all "
             f"{len(trials)} flights.")
    L.append("")

    L.append("## Gates (per run)")
    L.append("")
    L.append("G1: the forward pass reproduces the stored `room_ukf/ukf_live.tum` (max horizontal difference "
             "<= 1e-6 m). G2: iteration 0 reproduces the stored `room_ukf/ukf_rts.tum` (same tolerance). A run "
             "failing either gate is reported, not scored (pre-registration section 4).")
    L.append("")
    L.append("| flight | G1/G2 | scored |")
    L.append("|---|---|---|")
    for t in trials:
        g = data["gates"][t]
        L.append(f"| `{t}` | {'PASS' if g['PASS'] else 'FAIL'} | {'yes' if t in scored else 'NO'} |")
    L.append("")
    if not_scored:
        L.append(f"Not scored: {', '.join('`' + t + '`' for t in not_scored)} (see gate column above).")
    else:
        L.append("All 12 flights passed G1/G2 and are scored below.")
    L.append("")

    L.append("## Convergence (per run)")
    L.append("")
    L.append("Stopping rule: largest smoothed-position change between successive iterations < 1 mm, or 10 "
             "iterations, whichever first (pre-registration section 2). Label (AMENDMENT 1): \"converged\" iff the "
             "1 mm rule was met within 10 iterations AND no cost increase (strict `cost[i] > cost[i-1]`, no "
             "epsilon) appears anywhere in the iterations actually taken; otherwise \"non-converged\", with that "
             "stopping-rule trajectory scored anyway.")
    L.append("")
    L.append("| flight | iterations | label | cost trace | max |Δposition| trace (mm) | run time, total / forward pass / IPLS (s) |")
    L.append("|---|---|---|---|---|---|")
    for t in trials:
        conv = data["convergence"][t]
        if conv is None:
            L.append(f"| `{t}` | — | no output | — | — | — |")
            continue
        costs = " → ".join(N.get(f"convergence.{t}.history.{h['iter']}.cost") for h in conv["history"])
        chgs = " → ".join(N.get(f"convergence.{t}.history.{h['iter']}.max_change_mm")
                                for h in conv["history"] if h["max_change_m"] is not None)
        L.append(f"| `{t}` | {N.get(f'convergence.{t}.iterations_run')} | {conv['final_label']} | {costs} | {chgs} "
                 f"| {N.get(f'convergence.{t}.run_time_s_total')} / {N.get(f'convergence.{t}.run_time_s_forward_pass')} / "
                 f"{N.get(f'convergence.{t}.run_time_s_ipls')} |")
    L.append("")
    n_nonconv = sum(1 for t in trials if data["convergence"][t] and data["convergence"][t]["final_label"] == "non-converged")
    L.append(f"{len(trials) - n_nonconv}/{len(trials)} converged by this label; {n_nonconv} non-converged.")
    L.append("")

    L.append("## Per-condition RMSE (horizontal, lap window, mean of 3 repeats)")
    L.append("")
    L.append("| condition | UKF live | RTS-UKF (hindsight) | IPLS-UKF (hindsight, exploratory) | FGO batch (hindsight) |")
    L.append("|---|---|---|---|---|")
    for c in "ABCD":
        row = data["conditions"][c]
        cells = []
        for tr in TRACK_ORDER:
            cells.append(f"{N.get(f'conditions.{c}.mean_rmse_m.{tr}')} m" if tr in row["mean_rmse_m"] else "—")
        L.append(f"| {c} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    L.append("")

    L.append("## Per-flight RMSE (horizontal, lap window)")
    L.append("")
    L.append("| flight | UKF live | RTS-UKF (hindsight) | IPLS-UKF (hindsight, exploratory) | FGO batch (hindsight) |")
    L.append("|---|---|---|---|---|")
    for t in trials:
        cells = []
        for tr in TRACK_ORDER:
            cells.append(f"{N.get(f'rmse_m.{t}.{tr}')} m" if tr in data["rmse_m"][t] else "—")
        L.append(f"| `{t}` | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    L.append("")

    L.append("## Predictions")
    L.append("")
    e1 = data["E-1"]
    L.append(f"**E-1 (re-linearisation helps over long gaps):** IPLS-UKF RMSE < RTS-UKF RMSE on every flight in "
             f"conditions B, C, D. **{'PASS' if e1['PASS'] else 'FAIL'}** ({N.get('E-1.n_pass')}/{N.get('E-1.n_total')}).")
    for t in sorted(e1["per_flight"]):
        v = e1["per_flight"][t]
        L.append(f"  - `{t}`: {'holds' if v else 'does NOT hold'} (IPLS-UKF {N.get(f'rmse_m.{t}.{IPLS_NAME}')} m vs "
                 f"RTS-UKF {N.get(f'rmse_m.{t}.RTS-UKF (hindsight)')} m)")
    L.append("")
    e2 = data["E-2"]
    L.append(f"**E-2 (the filter-side fair comparison, P-T4's rule applied to the new track):** in every condition, "
             f"the larger of IPLS-UKF and FGO-batch mean-of-3 RMSE is <= 1.5x the smaller. "
             f"**{'PASS' if e2['PASS'] else 'FAIL'}** ({N.get('E-2.n_pass')}/{N.get('E-2.n_total')}).")
    for c in "ABCD":
        if c in e2["by_condition"]:
            r = e2["by_condition"][c]
            L.append(f"  - {c}: ratio {N.get(f'E-2.by_condition.{c}.ratio')} ({'<=' if r['PASS'] else '>'} 1.5)")
    L.append("")
    e3 = data["E-3"]
    L.append(f"**E-3 (H-T1's rule applied to the new track):** the IPLS-UKF per-gap hindsight gain (UKF live minus "
             f"IPLS-UKF) has condition medians strictly increasing A to D. **{'PASS' if e3['PASS'] else 'FAIL'}** "
             f"(n = {N.get('E-3.n_gaps')} gaps).")
    med_cells = " / ".join(N.get(f"E-3.condition_medians_m.{c}") + " m" for c in "ABCD"
                           if data["E-3"]["condition_medians_m"][c] is not None)
    L.append(f"  - condition medians (A/B/C/D): {med_cells}")
    L.append("")

    L.append("## Reading (pre-registered, section 5)")
    L.append("")
    if e2["PASS"]:
        L.append("E-2 holds: the FGO batch's hindsight advantage over the RTS-UKF is attributed to re-linearising "
                 "over the whole trajectory rather than to the factor-graph formulation.")
    elif e1["PASS"]:
        L.append("E-2 fails while E-1 holds: re-linearisation narrows but does not close the gap.")
    else:
        L.append("Neither of the pre-registered readings applies as worded (E-1 did not hold on every B/C/D "
                 "flight); no reading is inferred beyond the verdicts above.")
    L.append("")
    L.append("These are exploratory statements; no registered Experiment 2 verdict changes.")
    L.append("")

    o = data.get("experiment4_O")
    L.append("## Experiment 4 (O) check")
    L.append("")
    if o is None:
        L.append("**SKIPPED.** `src/estimators/room_ukf_ipls_replay.py` lists `--gnss` in its `REFUSED_FLAGS` and "
                 "exits before doing anything else if it is passed. Its `read_events()` has no `\"gnss\"` event "
                 "kind (it only emits `imu`/`rng`/`flow`/`att`/`tag`), and `ukf_ipls.py` has no GNSS measurement "
                 "model or op type. Supporting `--gnss` would require a new event kind, a new recorded op "
                 "(`U.update_gnss`'s linearisation in `ukf_ipls.py`), and the GNSS-mode branch of "
                 "`room_ukf_replay.py`'s anchoring logic (`O_r*` use `--gnss`, not tags) to be duplicated into the "
                 "IPLS replay -- that is new estimator code, not a flag pass-through, so per the task's own "
                 "instruction this was not done and O is not run.")
    else:
        L.append("(run; see numbers_ipls.md)")
    L.append("")

    L.append("---")
    L.append("")
    L.append(f"*Generated by `eval/ipls_report.py` from `eval/results/iterated_smoother/ipls_scores.json`. "
             f"Every number above is tagged with its json key in `docs/thesis/iterated_smoother/numbers_ipls.md`; "
             f"`--check` asserts they match exactly.*")
    L.append("")
    return "\n".join(L)


def render_numbers(N, data):
    L = ["# IPLS stage 2: numbers", "", "EXPLORATORY. Generated by `eval/ipls_report.py` from "
         "`eval/results/iterated_smoother/ipls_scores.json`. Every number used in "
         "`docs/thesis/iterated_smoother/results.md` is listed here with its json key, rounded ONCE with "
         "`rd()`/`rd_si()` of `eval/figs_thesis.py` (metres to 3 dp, mm to 2 dp, seconds to 1 dp, counts exact), "
         "plus the raw unrounded value.", "", "| json key | rounded | raw |", "|---|---|---|"]
    for key, s, raw in N.rows:
        L.append(f"| `{key}` | {s} | {raw!r} |")
    L.append("")
    return "\n".join(L)


def main():
    check = "--check" in sys.argv
    data = json.load(open(SCORES))
    N = build(data)
    results_text = render_results(data, N)
    numbers_text = render_numbers(N, data)

    if check:
        ok = True
        if os.path.exists(RESULTS_OUT):
            on_disk = open(RESULTS_OUT).read()
            if on_disk != results_text:
                ok = False
                print("CHECK FAIL: results.md on disk differs from a fresh render")
        else:
            ok = False
            print("CHECK FAIL: results.md missing")
        if os.path.exists(NUMBERS_OUT):
            on_disk_n = open(NUMBERS_OUT).read()
            if on_disk_n != numbers_text:
                ok = False
                print("CHECK FAIL: numbers_ipls.md on disk differs from a fresh render")
        else:
            ok = False
            print("CHECK FAIL: numbers_ipls.md missing")
        # cross-check: every "{N.get(key)}" value actually appears verbatim in results_text
        missing = [key for key, s, _ in N.rows if s not in results_text]
        if missing:
            ok = False
            print(f"CHECK FAIL: {len(missing)} numbers_ipls.md values do not appear in results.md: {missing[:10]}")
        print("CHECK " + ("PASS" if ok else "FAIL"))
        sys.exit(0 if ok else 1)

    os.makedirs(DOCDIR, exist_ok=True)
    open(RESULTS_OUT, "w").write(results_text)
    open(NUMBERS_OUT, "w").write(numbers_text)
    print(f"wrote {RESULTS_OUT}")
    print(f"wrote {NUMBERS_OUT}")


if __name__ == "__main__":
    main()
