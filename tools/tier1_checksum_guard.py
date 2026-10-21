#!/usr/bin/env python3
"""Tier-1 checksum guard (user ruling 2026-10-21; docs/thesis/tier1/preregistration.md "Checksum guard").

  tier1_checksum_guard.py snapshot [--repo DIR] [--out FILE] [--docs none|pack|all] [--paths P ...]
  tier1_checksum_guard.py verify MANIFEST [--report FILE]

snapshot: sha256 + size of every regular file (symlinks recorded by target, never followed) under every covered
          path, written to docs/thesis/tier1/frozen_manifest_<YYYYmmddTHHMMSS>.json (or --out). Taken IMMEDIATELY
          BEFORE the first tier-1 run (Stage 2, step 1), never earlier.
verify:   re-expands the SAME path specs stored in the manifest, re-hashes, and compares. Any changed, missing or added
          file (or an unreadable one) is a difference: the report is printed (and written to --report) and the exit
          status is 1 = STOP AND REPORT. Exit 0 only when every covered file is byte-identical.

Default coverage = RESULT DATA, documents EXCLUDED (user sign-off 2026-10-22: "checksum guard scope = result data
(trial outputs, eval/results, all folders behind existing numbers); docs excluded"). --paths overrides it (used only
for the tool's own test on a temporary copy):
  trials_T        ~/thesis_data/trials/T_*            every file of every T (Experiment 2/3) trial dir (bags, imu_gaps.json,
                                                      metadata.yaml, logs/, lc_fgo_*, room_fgo*, room_ukf*, the
                                                      *_IMUGAP / *_ABORTED dirs): the replay inputs and every
                                                      frozen T/L output a mis-pathed replay or scorer could touch
  trials_lc_other ~/thesis_data/trials/*/lc_fgo_* outside T_*, and dsn_tex_r1/fgo_baseline (the V-L pair)
  batches         ~/thesis_data/batches/{final2_L,final_L,final_rerun2,final2_room_T,final_room_T}: job lists and
                  logs cited at numbers.md §16.3 (cost) and the T replay timing; a batch-name collision would append
  results         <repo>/eval/results/expL, <repo>/eval/results/expT (numbers.md §16.1, §16.3 sources; Experiment 2
                  results E4/E5 compare against), <repo>/batches/final_rerun/room_T.jobs (the Experiment 2 job list)
  run_code        (retained: code, not result data or documents) the code the tier-1 replays and scorer execute (must not change between the snapshot and the last
                  run): src/estimators/fgo/{lc_fgo_replay,tier1_paths,fgo_core,factors}.py,
                  src/estimators/{measurement_models,imu_timing}.py, src/tags/tag_measure.py, eval/l_score.py,
                  sim/worlds/room_tags_map.json, tools/tier1_checksum_guard.py, and for E4/E5:
                  src/estimators/fgo/{room_fgo_replay,fgo_export}.py, src/estimators/{room_ukf_replay,ukf_core,apin}.py,
                  eval/tag_score.py; the runners eval/run_jobs_resumable.sh, src/estimators/fgo_cpp/tools/heavy.py.
                  NEW E5 modules are not covered (they do not exist yet); E5 must not edit any covered file.
Documents (frozen_docs) are NOT covered by default (--docs none). Optional, not used for the tier-1 snapshot:
  --docs all  adds frozen_docs: <repo>/docs/thesis/numbers.md, final_results_pack.pdf, final_results_pack_index.md,
              final_results_pack_corrections.md, headline_claims_before_after.md, docs/thesis/figures_thesis/,
              docs/thesis/tables/, plots/final_results_pack/, plots/supervisor_2026-10-08/ (numbers.md §16 figures)
  --docs pack adds only final_results_pack.{pdf,_index.md,_corrections.md}, plots/final_results_pack/ and
              plots/supervisor_2026-10-08/.
NOT covered (stated): every document (numbers.md, the frozen pack, headline_claims, figures_thesis/, tables/, the
  plots above, METHODOLOGY.md) unless --docs says otherwise; docs/thesis/tier1/ and ~/thesis_data/tier1/ (the tier-1
  outputs themselves). Default (decided 2026-10-22): all result data: every T_* trial in full,
  every other trial's outputs (not its input bag/), all batch folders and all of eval/results; code only with --code."""
import argparse, glob, hashlib, json, os, socket, subprocess, sys, time

HOME = os.path.expanduser("~")


def default_specs(repo):
    T = f"{HOME}/thesis_data/trials"; B = f"{HOME}/thesis_data/batches"; r = lambda p: os.path.join(repo, p)
    return {
        # Ruling 2026-10-22 ("result data (trial outputs, eval/results, all folders behind existing numbers)"): every trial's
        # outputs (every entry of every trial folder except its recorded input bag; the T bags, which the tier-1 replays read,
        # are covered in full), every batch folder, and all of eval/results.
        "trials_T": [f"{T}/T_*"],
        "trials_outputs": sorted(p for p in glob.glob(f"{T}/*/*")
                                 if os.path.basename(p) != "bag" and not os.path.basename(os.path.dirname(p)).startswith("T_")),
        "batches": [f"{B}", r("batches")],
        "results": [r("eval/results")],
        "frozen_docs": [r("docs/thesis/numbers.md"), r("docs/thesis/final_results_pack.pdf"),
                        r("docs/thesis/final_results_pack_index.md"), r("docs/thesis/final_results_pack_corrections.md"),
                        r("docs/thesis/headline_claims_before_after.md"), r("docs/thesis/figures_thesis"),
                        r("docs/thesis/tables"), r("plots/final_results_pack"), r("plots/supervisor_2026-10-08")],
        "run_code": [r(p) for p in ("src/estimators/fgo/lc_fgo_replay.py", "src/estimators/fgo/tier1_paths.py",
                                    "src/estimators/fgo/fgo_core.py", "src/estimators/fgo/factors.py",
                                    "src/estimators/measurement_models.py", "src/estimators/imu_timing.py",
                                    "src/tags/tag_measure.py", "eval/l_score.py", "sim/worlds/room_tags_map.json",
                                    "tools/tier1_checksum_guard.py", "src/estimators/fgo/room_fgo_replay.py",
                                    "src/estimators/fgo/fgo_export.py", "src/estimators/room_ukf_replay.py",
                                    "src/estimators/ukf_core.py", "src/estimators/apin.py", "eval/tag_score.py",
                                    "eval/run_jobs_resumable.sh", "src/estimators/fgo_cpp/tools/heavy.py")],
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def expand(specs):
    """{group: {abs path: entry}}; entry = {sha256, size} | {symlink: target} | {error: msg}; plus unmatched specs."""
    out, unmatched = {}, []
    for grp, pats in specs.items():
        files = {}
        for pat in pats:
            hits = sorted(glob.glob(pat))
            if not hits:
                unmatched.append(pat)
            for h in hits:
                walk = [h] if not os.path.isdir(h) or os.path.islink(h) else \
                    [os.path.join(dp, f) for dp, dns, fs in os.walk(h) for f in fs + [d for d in dns if os.path.islink(os.path.join(dp, d))]]
                for p in walk:
                    p = os.path.abspath(p)
                    try:
                        files[p] = {"symlink": os.readlink(p)} if os.path.islink(p) else {"sha256": sha256(p), "size": os.path.getsize(p)}
                    except OSError as e:
                        files[p] = {"error": f"{type(e).__name__}: {e}"}
        out[grp] = files
    return out, unmatched


def git(repo, *c):
    return subprocess.run(["git", "-C", repo, *c], capture_output=True, text=True).stdout.strip()


def snapshot(a):
    repo = os.path.abspath(a.repo)
    specs = {"custom": [os.path.abspath(p) for p in a.paths]} if a.paths else default_specs(repo)
    if not a.paths and a.docs == "none":   # default (sign-off 2026-10-22): result data only, documents excluded
        del specs["frozen_docs"]
    if not a.paths and not a.code:         # result data only (ruling 2026-10-22); code is checked by the reproduction gates
        del specs["run_code"]
    if not a.paths and a.docs == "pack":   # optional: only the frozen pack files and plots
        keep = ("final_results_pack.pdf", "final_results_pack_index.md", "final_results_pack_corrections.md",
                "plots/final_results_pack", "plots/supervisor_2026-10-08")
        specs["frozen_docs"] = [x for x in specs["frozen_docs"] if x.endswith(keep)]
    t0 = time.time(); groups, unmatched = expand(specs)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out = a.out or os.path.join(repo, "docs", "thesis", "tier1", f"frozen_manifest_{stamp}.json")
    if os.path.exists(out):
        sys.exit(f"refusing to overwrite {out}")
    errors = [p for g in groups.values() for p, e in g.items() if "error" in e]
    man = {"kind": "tier1 frozen-results manifest", "created_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "host": socket.gethostname(), "repo": repo, "repo_commit": git(repo, "rev-parse", "HEAD"),
           "specs": specs, "unmatched_specs": unmatched, "hash_seconds": round(time.time() - t0, 1),
           "counts": {g: len(f) for g, f in groups.items()},
           "bytes": {g: sum(e.get("size", 0) for e in f.values()) for g, f in groups.items()}, "groups": groups}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(man, open(out, "w"), indent=1, sort_keys=True)
    print(f"snapshot: {sum(man['counts'].values())} files in {len(groups)} groups ({man['counts']}), "
          f"{sum(man['bytes'].values()) / 1e6:.1f} MB, {man['hash_seconds']} s -> {out}")
    if unmatched:
        print(f"WARNING: specs that matched nothing: {unmatched}")
    if errors:
        print(f"WARNING: {len(errors)} unreadable files recorded as errors (verify will flag them): {errors[:5]}")
    return 0


def verify(a):
    man = json.load(open(a.manifest))
    groups, unmatched = expand(man["specs"])
    rep = {"manifest": os.path.abspath(a.manifest), "verified_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "changed": [], "missing": [], "added": [], "errors": [], "unmatched_specs_now": unmatched}
    for g, old in man["groups"].items():
        new = groups.get(g, {})
        for p, e in old.items():
            if p not in new:
                rep["missing"].append(p)
            elif new[p] != e:
                (rep["errors"] if "error" in new[p] or "error" in e else rep["changed"]).append({"path": p, "was": e, "now": new[p]})
        rep["added"] += [p for p in new if p not in old]
    n_diff = sum(len(rep[k]) for k in ("changed", "missing", "added", "errors"))
    rep["n_files_checked"] = sum(len(g) for g in man["groups"].values())
    rep["verdict"] = "IDENTICAL" if n_diff == 0 else "DIFFERENT: STOP AND REPORT"
    if a.report:
        json.dump(rep, open(a.report, "w"), indent=1)
    print(f"verify: {rep['n_files_checked']} files against {a.manifest}: {rep['verdict']}")
    for k in ("changed", "missing", "added", "errors"):
        for x in rep[k][:50]:
            print(f"  {k.upper():8s} {x if isinstance(x, str) else x['path']}"
                  + ("" if isinstance(x, str) else f"  was {x['was']} now {x['now']}"))
        if len(rep[k]) > 50:
            print(f"  ... {len(rep[k]) - 50} more {k}")
    return 0 if n_diff == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("snapshot"); s.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    s.add_argument("--out"); s.add_argument("--paths", nargs="+", help="TEST ONLY: cover these paths instead of the default")
    s.add_argument("--docs", choices=["none", "pack", "all"], default="none",
                   help="document coverage: none (default; sign-off 2026-10-22: result data only, documents excluded), "
                        "pack = only the frozen pack files and plots, all = every frozen document")
    s.add_argument("--code", action="store_true", help="also cover the code the replays run (not in the default: the ruling "
                   "limits the guard to result data; the reproduction gates check the code)")
    v = sp.add_parser("verify"); v.add_argument("manifest"); v.add_argument("--report")
    a = ap.parse_args()
    sys.exit(snapshot(a) if a.cmd == "snapshot" else verify(a))


if __name__ == "__main__":
    main()
