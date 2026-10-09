# Handover, 2026-10-10: final restatement applied (rulings 2–11), headline table written

**Stage:** analysis and editing only. No replays, no heavy jobs, no estimator edits, METHODOLOGY NOT edited. The
plain-wall trace and the attribution study (rulings 1, 5, 12) were run by other agents and are NOT reflected here
beyond "trace / attribution pending" placeholders.

## 1. Ruling 10: `eval/rerun_compare.py` fixed and the comparison regenerated
- **Mapping fix.** Sections 6.4, 7 and 8 now read the same `rerun_*` files on both sides (`rerun_fwdc_evo`,
  `rerun_fwdplainc_evo`, `rerun_p1c_evo`, `rerun_*_score.json`). The old P4 bands come from
  `OLD/rerun_p4_bands.json`; the hard-coded pre-re-fly `ob` dict is gone.
- **Self-test, beyond ruling 10's wording (disclosed):**
  - At HEAD (`ef7a0a5`), `--selftest eval/results` already FAILED. It passed only on `results_pre_final`, for two
    data-dependent reasons:
    - the O mutation ("FGO batch × 3") no longer flips the sign, because the corrected FGO batch is already above
      the RTS-UKF;
    - `s1far_r3b` is now present in the results directory, so it is not new-only.
  - Fixed:
    - the O mutation now puts the batch on the opposite side of the RTS-UKF;
    - if `s1far_r3b` exists, the mutation's OLD side is a scratch copy without it.
  - Extended: the OLD = NEW identity check now also covers 6.4, 7 and 8, which are identities after the fix.
  - `--selftest` passes on both `eval/results` and `~/thesis_ws/eval/results_pre_final`.
- **Regenerated** with the exact command from the brief (OLD = `~/thesis_ws/eval/results_pre_final`, read by absolute
  path, untracked in the main checkout; no symlink).
- **Flags: 95 → 91** (1279 rows). **82 DIRECTION + 9 VERDICT** (was 86 + 9). The arithmetic is 95 − 7 + 3:
  - **removed, the 7 artefacts:**
    - the four 6.4 transition displacement ratios (fwdc FGO/UKF, fwdplainc FGO/UKF);
    - the three section-8 per-trial verdicts (`fwdc_tex_r2`, `fwdc_trans_r1`, `p1c_fwdplainc_trans`).
  - **added, 3 real per-trial verdict flips** (FAIL → PASS): `fwdc_blank_r1`, `fwdc_blank_r2`, `fwdplainc_blank_r2`.
    These are the per-trial cause of the two hidden count changes.
- **Count rows** now show **fwdc 6/9 → 8/9** and **fwdplainc 8/9 → 9/9** (p1c 6/6 → 6/6). They carry no flag, because
  the script never flags aggregate count rows; the three per-trial rows above carry the flag. Section 7's old
  bands now read e.g. FGO tex [4.189, 5.117] → [−0.614, 7.017].

## 2. `docs/thesis/numbers.md` (rulings 2–9 and 11)
- **71 rows replaced in place**, each copied verbatim into a new block at the end, "Superseded by the final
  consolidated re-run (2026-10-10)". A header note states the re-run, the rulings, and that attribution is pending.
- **Sections touched:**
  - §2 and §5: sensitivity rows from `*_final.json`, marked not like-for-like;
  - §6.1: FGO and UKF values, noise floor, D15 wording, drift, take-off kick ≤ 0.82°, a new FGO drift row, a new
    textured-standing row;
  - §6.2: blank and transition values, plus a transition ratio row;
  - §6.4 and §6.5;
  - §6.6: the plain-wall divergence row ("trace pending"), the C0 row, `fwdc` UKF ≈ FGO, NEES rows;
  - §7: P4 FGO band [−0.614, 7.017] with the "too wide to be informative" caveat;
  - §8: 8/9 and 9/9;
  - §15: the `_v3` contact; the post-hoc contact-consistency row naming the missing `fgo_shadow_half_a` and the
    live XFGO; per-heading weight FGO ≈ 1.3–1.4 %, UKF OPEN, no ratio;
  - §15.1: 2(a) 7/12 and 5/12; robust FGO lower yaw max 8/10;
  - **new §15.2 F tests:**
    - F1 "NOT met (lockout tie)";
    - F2 MET;
    - F3 NOT met, with the reason changed;
    - F3b unchanged;
    - F3c (b) FALSE;
  - §16.1 T: new table; D descriptive only (n = 3);
  - §16.2 O: P-O3 PASS; "FGO batch ~2× better" WITHDRAWN; batch worsening "attribution PENDING";
  - §16.3 L: new values, V-L not re-scorable, the slowdown;
  - §17 H: new shadow values; "no gap between shadow and flying estimators";
  - Flags: FGO noise-floor SD 1.23.
- **WITHDRAWN in place:**
  - the "EKF3 vs FGO (claim wording)" row;
  - a new row holding the old confirmatory verdict, labelled "computed with the mis-specified FGO noise model".
- **The new confirmatory row** reads "no ordering claimed" and REPLACES the old verdict.
- **Not restated (no new values in the re-run):** §14 timing; the fwdplainc/p1c take-off kick magnitudes; §16.1's
  "repeats agree within 8 mm".

## 3. "EKF3 beats the FGO on standard sensors": where it appears
- **numbers.md:** rows 214 and 215 (old numbering). Both are now WITHDRAWN.
- **docs/thesis/\*:** no other occurrence. Searched recursively, including the `export_*` snapshots, which predate the
  confirmatory test.
- **METHODOLOGY (NOT edited; for the user to annotate):**
  - **5515–5516:** "DIRECTION — textured `dsn` ordering … −0.53 m (EKF3 now better)".
  - **5554:** "Substantive: EKF3 beats FGO on `dsn_tex` by 0.53 m".
  - **5624–5625:** interim "EKF3 lower on all three repeats".
  - **6247:** RESULT heading "EKF3 lower than the FGO on the textured floor".
  - **6265:** verdict.
  - **6269–6271:** "Claim wording now permitted".
  - **6393–6395:** "Established claim". Line 6395 also carries the stale FGO SD 0.13 m.
  - **7207–7210:** "The confirmatory EKF3-vs-FGO test HOLDS … Verdict 'EKF3 lower'".
  - **9635–9637:** "UNAFFECTED … 'EKF3 lower', byte-identical".
  - **6759 and 7118:** "the EKF3-vs-FGO result held despite it".
  - **11364:** "The main EKF3-vs-FGO result is affected by at most ~0.25 m".
  - **Context only, not claims:**
    - 5638, 5644 and 5649 are the pre-registered hypothesis and rule;
    - 8163, 8190 and 8239 are references to the test.
- **Outside the named scope (listed, not edited):**
  - `PROGRESS.md:156` ("Confirmatory `dsn_tex_r4..r10`: EKF3 lower than the FGO");
  - `docs/handovers/2026-10-09_final_rerun_pipeline.md:223`.

## 4. `docs/thesis/headline_claims_before_after.md`
- One page, 35 claims: **HOLDS 14 · CHANGED 16 · WITHDRAWN 3 · PENDING 2**. The counts were taken from the status
  column.
- **Withdrawn:**
  - EKF3 beats the FGO;
  - FGO batch ~2× better than the RTS-UKF;
  - V-L PASS.
- **Pending:**
  - the plain-wall hard-gated FGO mechanism;
  - the O batch worsening.
- **The UKF's textured standing** (from `rerun_dsn_evo.json`):
  - **on the mean of r1–r3: FGO 3.49 < UKF 3.59 < EKF3 4.00, so the UKF is NOT last.** On the same statistic it was
    not last before either (UKF 3.91 < EKF3 4.00 < FGO 4.64).
  - **By the r1–r9 median** (the basis of the old "UKF above both" wording): UKF 5.13 > FGO 4.45 > EKF3 4.10, so the
    UKF is still highest, and highest on 6/9 flights.
  - The statement is descriptive; no ordering is claimed.
- **L: unchanged.** H-L1, H-L2, H-L3 and P-L4 all PASS 3/3, old and new; only the magnitudes moved.

## State
- The worktree branch was reset to `fwd-camera` `ef7a0a5` at the start, because it had been created from the
  unrelated root.
- No flight was running at commit: `pgrep -fa '[a]rducopter'` was empty and there was no `~/thesis_data/FLIGHT_LOCK`.
- Committed on the worktree branch; not merged. Scratch scripts are in this session's scratchpad and are not
  committed.

## Open / next
- When the trace and the attribution study report, replace the "trace pending" and "attribution PENDING" cells:
  numbers.md §6.6, §16.2 and the F1/2(a) notes, plus headline rows 8 and 22.
- The METHODOLOGY annotations at the locations in §3 are the user's call.
