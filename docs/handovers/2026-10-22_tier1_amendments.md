# Handover: extension experiments E2–E5, sign-off amendments written in (2026-10-22)

**One stage: documents only.** Nothing was run: no replay, no estimator, no simulation, and nothing involving
`arducopter` or `gz sim`.
- Stored results were only read to derive figures. The files read were `eval/results/expT/T_*.json`,
  `~/thesis_data/trials/T_A_r*/lc_fgo_{lc,nolc}_t245/stats.json` (`t_anchor`, landmark counts and the final L(0)), and
  the row count and timestamps of `T_A_r1`/`T_D_r1` `room_ukf/{ukf_live,ukf_rts}.tum`.
- The only execution was the checksum guard's temp-copy self-test (below).
- **Branch:** `worktree-agent-a82413da50b039739` (reset to the Stage 1 branch `worktree-agent-adb3f27ee84b408d1` at
  `9be1333`, then committed on top). Not merged.
- **Sign-off source:** `METHODOLOGY.md` on `fwd-camera` (`dcc81f7`), heading "SIGN-OFF (user, 2026-10-22): extension
  experiments Stage 1 accepted with amendments; Stage 2 authorised". It was read, not edited.

## What changed

| file | change |
|---|---|
| `docs/thesis/tier1/preregistration.md` | Status: SIGNED OFF 2026-10-22, with the 5 amendments and the decisions listed in the header. Amendments 1–4 applied (details below). §0.5: run status (completed / crashed / NOT RUN) and the criterion verdicts (PASS / FAIL / NOT MET / NOT RUN; no early decisions); every judgement band labelled "judgement, not derived from data" with a reason. §2.1: the E3 error model is DECIDED, and effective overall rates are reported. §6: guard scope = result data, documents excluded; `run_code` retained; open item on coverage. §7: why G0-L, G-E4 and G0-UKF stay byte-identical; report after the gates. §8: one job at a time; lock semantics. §10: every former flag with its outcome. |
| `docs/thesis/tier1/e5_design.md` | Status: signed off. §5 rewritten (amendment 5a, the FGO anchor; §5.3 invariants). §6.1 new (amendment 5b, the no-LC drop). §7 and §9: corrected, the smoother gain is solved on the diagonally scaled matrix as `ukf_core.rts_smooth` does (the draft said plain Cholesky). §8 rewritten (amendment 2, the tolerance against the stored tracks). §10: DECIDED. |
| `docs/thesis/tier1/numbers_tier1.md` | Template wording only: the label, NOT RUN semantics, the gate rows, the new criteria (H-E4.3, P-E3b.1 "no worse", S-E5.5/6). |
| `tools/tier1_checksum_guard.py` | The default `--docs` is now `none`: there is no `frozen_docs` group, so documents are excluded. `pack` and `all` remain. Docstring updated. No other code change. |

## Key figures

- **E5 known-map tolerance (amendment 2).**
  - **Compared directly with the stored files:** `~/thesis_data/trials/T_{A,B,C,D}_r{1,2,3}/room_ukf/ukf_live.tum` and
    `ukf_rts.tum`, plus `stats.json` (`t_anchor`, `n_tag_fused`). The comparison is never chained through another V-E5
    run.
  - **Per flight, live and RTS separately, 12/12:**
    - rows match 1:1, with identical 6-dp timestamps and no interpolation;
    - **RMS horizontal difference ≤ 1.0 mm** over the `tag_score` lap window;
    - max ≤ 2.0 mm;
    - accept counts equal to V-E5a's. A flip whose two test ratios both lie within 1e-9 of the gate counts as
      round-off, and the trajectory bounds decide.
  - **Reason:**
    - Floor: 6-dp storage gives 0.29 µm RMS, and float64 reordering in the re-implemented variable-n code adds far
      less than 1 µm.
    - Ceiling: |ΔRMSE| ≤ RMS(Δ) (Minkowski). The smallest stored per-flight gap between a UKF track and another
      estimator's (EKF3 live, FGO live, FGO batch) is **2.16 mm** (RTS-UKF 0.01280 against FGO batch 0.01064 m,
      T_A_r1). The next is 2.45 mm (UKF live against EKF3 live, T_A_r2), and UKF live against FGO live is
      ≥ 14.2 mm.
    - The smallest stored Experiment 3 per-lap value is 0.0149 m (LC hindsight, lap 5, T_A_r3).
    - 1.0 mm is the reporting precision, less than half the ceiling, and about 3,400× the floor. The choice within
      that range is labelled judgement.
- **E4 (amendment 3).**
  - **H-E4.3:** L_i(5) < L_i(0.25) on ≥ 10/12 flights. The judgement band is the smallest one-sided sign-test count
    significant at 5% (p = 0.019; 9/12 gives 0.073).
  - **Gain fraction:** per flight, f_i(W) = (L_i(0.25) − L_i(W)) / (L_i(0.25) − B_i). Pooled,
    F(W) = Σ(L(0.25) − L(W)) / Σ(L(0.25) − B), over 12 flights and per condition, with the median f_i beside it.
    - L is the `tag_score` "FGO live" RMSE.
    - B is the stored `json:expT` "FGO hindsight (whole-flight batch)" (N:526-529).
    - The denominators are 8.9–65.9 mm; Σ = 330.3 mm.
- **E3 (b) (amendment 4):**
  - P-E3b.1 is robust ≤ 1.10 × arm (a), per run (flight, rate, seed), 9/9 per rate. The +10% is labelled judgement.
  - The `wall_s` ratio is descriptive.
- **E5 primary (amendment 1):** H-E5.1, LC live lap-5 / lap-1 ≤ 1.5 on 3/3 T_A flights, with H-E2.1's derivation.
  - The secondary criteria are S-E5.5 (live) and S-E5.6 (hindsight): the registered direction is UKF > FGO, with the
    ratios descriptive.
  - "Batch" maps to the FGO's iSAM2 + 5-update hindsight, and this is stated wherever it is reported.

## Amendment 5 in brief

- **Anchor:**
  - The FGO re-anchors X(0) to the measured pose under a loose prior (yaw 0.5 rad, x and y 1 m; diagonal), adds the
    anchoring detection once as a factor against L(0), and holds L(0) with a 1e-4 prior. The effective anchor is
    0.04994 m and 4.93°.
  - The landmark UKF re-anchors to the same detection with variances 0.05 m and 5° (diag(JPJᵀ)) and holds tag 0
    exact.
  - Evidence: the stored FGO L(0) stayed within 4e-10 of the origin in all 6 runs.
  - Invariants: `t_anchor` and the landmark counts (8 / 41) match the FGO, with the pass rule on the FGO's keyframe
    time base.
- **No-LC drop:**
  - A finished-pass landmark is never observed again. Its information is already in the vehicle marginal, so
    marginalising it changes nothing live (exactly so in the linear-Gaussian case). The FGO's retained landmark only
    helps through relinearisation of past poses: the filter-versus-graph difference E5 measures.
  - Stated approximation: the UT's dependence on n (second-order exact; α = 1e-3), and the RTS over the forward
    linearisation.

## Guard self-test (temp copy only; `scratchpad/guard_selftest.py`)

- **The Stage 1 test, re-run:** `snapshot --paths` over a scratchpad copy (`T_A_r1/lc_fgo_lc_t245`, `room_fgo`, the expL
  json). `verify` gave IDENTICAL (exit 0). After an append, an added file and a deletion, it reported CHANGED, MISSING
  and ADDED (exit 1).
- **Default-scope check:** run with HOME and `--repo` pointed at scratch directories and `--out` in the scratchpad,
  with no real data hashed.
  - `--docs none` (the default): no `frozen_docs` group, and `numbers.md` absent.
  - `pack`: `frozen_docs` present, `numbers.md` absent.
  - `all`: `numbers.md` present.
- No manifest was written into the repository.

## Still open (needs a decision)

1. **Guard coverage against the ruling's wording.** The ruling names "eval/results, all folders behind existing
   numbers". The default covers only the result data the tier-1 runs read or could touch: T_*, the V-L pair,
   `eval/results/expL` and `expT`, and the §16 batches. It does not cover the rest of `eval/results/` or the other
   trial sets. Widening it is one line per path; it needs a ruling before the snapshot.
2. **`run_code` retained in the guard.** It is code, not result data or documents, and was kept so that the gates
   prove reproduction for the snapshotted code. Confirm or drop.
3. **Former flags 7 and 8** (E4 against the stored batch; LM-10 on two flights only) were not ruled separately. They
   are recorded as "accepted as drafted under the general Stage 1 sign-off".
4. **E5 further criteria.** H-E5.2, H-E5.3 and P-E5.4 (LC against no-LC within the UKF) were kept beside amendment 1's
   primary (H-E5.1) and secondary (S-E5.5/6). The amendment names only those two roles, so the user should confirm
   that the further criteria stay.

## Corrections made after the first commit (`294eca6`), same day

- The E5 tolerance ceiling now names every track compared: the EKF3 live gaps (2.45 mm and up) had been left out. The
  2.16 mm minimum and the 1.0 mm / 2.0 mm figures are unchanged.
- The smallest Experiment 3 lap value is 0.0149 m (LC hindsight), not 0.026 m (which is the smallest LC live lap-5
  value).
- `e5_design.md` §5.2: tag 0 is held exact on equivalence grounds. The draft's conditioning argument contradicted §7
  (bias variances of about 1e-14) and V-E5c (1e-10).

## Next (Stage 2, per the sign-off)

- Merge this branch with the user's go-ahead.
- Run the idle check, then the snapshot, from the main checkout.
- Run G0-L, then G0-UKF, then **report**. Stop before the main runs if any gate fails.
- One job at a time throughout.
