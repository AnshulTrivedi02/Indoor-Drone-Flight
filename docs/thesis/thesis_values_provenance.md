# Thesis-facing values with no stored-result trace in numbers.md: their written sources (2026-10-16)

*Ruling: METHODOLOGY "RULINGS (user, 2026-10-16): the three mismatched numbers.md rows; thesis-facing untraceable values;
numbers.md CONTENT-FROZEN", second bullet. Nothing was recomputed. Stored files were read, and some historical values
were read from a stored file at an earlier commit (`git show <commit>:<path>`).*

## Scope and method

- **Starting set: the 769 untraceable tokens.** These are the numeric tokens in the current sections of
  `docs/thesis/numbers.md` (lines 42–776 at `8e5d116`) that the full comparison of 2026-10-16 could not trace to a stored
  data file (class U; `docs/handovers/2026-10-16_numbers_rounding_exact.md` §2; scratch records `cmp_s1–s4.tsv`).
- **Thesis-facing material:**
  - `docs/thesis/figures_thesis/index.md` (captions and checks), which is also the text of the combined PDF;
  - `docs/thesis/tables/T1–T8.md` (the `.tex` versions carry the same cells);
  - the claims table `headline_claims_before_after.md`;
  - `thesis_vocabulary.md`, `methodology_definitions_draft.md`, `limitations.md` and `pending_items.md`;
  - `docs/thesis/world_images/index.md` and `shots_table.md` (the world-images captions).
- **Step 1, candidates.** Every numeral in that material was extracted. Values that the generator builds with `rd()` are
  traced by construction. Each numeral was paired with any U token that has the same digit string, scored by the
  overlap of the words around the two. That gave 220 strong and about 200 weak but distinctive candidates
  (scratch: `tf2.py`, `tf2_strong.txt`, `weak_c.txt`).
- **Step 2, review by hand, by QUANTITY, not by digits.**
  - A candidate was kept only when the thesis text states the same quantity as the numbers.md row.
  - Most candidates were coincidences and were dropped: repeat indices ("flights 1 / 2 / 3"), run numbers, section
    and figure numbers, and table cells built by `rd()` that happen to share digits with a parameter.
- **Step 3, a written source for each kept quantity.** "Written source" means one of the ruled types:
  - **R**: a results file and key (at `8e5d116` unless a commit is given);
  - **M**: a `METHODOLOGY.md` line at `8e5d116`. This is not the `M:L` snapshot of numbers.md, which predates T, O and H;
  - **PR**: a pre-registration line, also in `METHODOLOGY.md`;
  - **P**: a parameter, world or code file and line.

  Two further classes are kept apart for a ruling:
  - **C**: the only written source is `CLAUDE.md`, which is none of the four ruled types;
  - **N**: no written source was found outside numbers.md itself.
- **Limits.**
  - The pairing works on digit strings, so a thesis value whose numbers.md form uses different digits (another unit or
    another rounding) could be missed.
  - Thesis-facing numerals that match no numbers.md token at all are not chased (ruled scope: the 769 only). They are
    mostly criterion bounds in the vocabulary's criterion table, such as the B3 1.0° / 2.0°, the gyro-rms bounds and the
    S-A attitude 3° / 5°. Their pre-registrations are in METHODOLOGY (for example B3 and B4 at `METHODOLOGY.md:5096`
    and `:4874`).

## Result

**43 quantities appear in thesis-facing material** (one quantity can span several of the 769 tokens; the token count per quantity was not tallied). **Each has a written source:**

| class | quantities |
|---|---|
| R, M, PR or P | 41 |
| C only (`CLAUDE.md`) | 1 |
| N, none found | 0 |

- **One quantity carries a caution** (row 42): its written source says the thesis-facing wording is inaccurate.
- **Three historical values rest on a results file at an earlier commit**, not on the current file: rows 26, 35 and 37.
  This is noted in their rows.

| # | quantity (numbers.md line at 8e5d116) | thesis-facing places | written source | class |
|---|---|---|---|---|
| 1 | Transition texture boundary y = 80 m (L49) | world_images/index.md:73 | `sim/worlds/corridor_transition.sdf:12, 180` ("BOUNDARY IS EXACTLY y = 80 m") | P |
| 2 | Measured boundary crossing y = 80.01 m (L50) | world_images/index.md:24 | `CLAUDE.md:1827` only; not in METHODOLOGY or any results file found | **C** |
| 3 | Spawn pose (0, 0, 0.195) (L51) | world_images/index.md shot rows (e.g. :184, :188, :193, :200); shots_table.md | `sim/worlds/corridor_textured.sdf:218` (`<pose degrees="true">0 0 0.195 0 0 90</pose>`) | P |
| 4 | Flight profile 0.5 m/s, 2.0 m, 300 s (L56) | world_images/index.md:29, :106; "the commanded flight speed was unchanged at 0.5 m/s" in figures_thesis/index.md:35, T1:20, T4:11, thesis_vocabulary.md:119, methodology_definitions_draft.md:209, pending_items.md:36 | `METHODOLOGY.md:138`, `:1846`, `:2206` | M |
| 5 | True travel per trial 151 m (L58) | world_images/index.md:106 | `METHODOLOGY.md:560` | M |
| 6 | Forward camera 640 × 480 (L64) | world_images/index.md:136 | `METHODOLOGY.md:1367` | M |
| 7 | Half real-time RTF 0.5 / real-time RTF 1.0 (L464, L466) | figures_thesis/index.md:20, :35, :152; T1:18, :20; T4:1, :11; thesis_vocabulary.md:119, :341, :446, :476; methodology_definitions_draft.md:206–211; pending_items.md:36; world_images/index.md:25, :29, :42, :49, :106, :172 | `sim/worlds/corridor_textured_half_fwdc.sdf:44` (`<real_time_factor>0.5`); `sim/worlds/corridor_textured_fwdc.sdf:44` (`1.0`) | P |
| 8 | Heading validity S_MIN = 200 px (L338, L372) | world_images/index.md:139, :145, :147 | `METHODOLOGY.md:2674`, `:2694` (pre-registered grid); frozen value in `eval/results/fwd_calibration*.json` (row L338's source) | PR |
| 9 | EKF3 contact window [+155, +215] s (L470) | T4:7, :11; thesis_vocabulary.md:89 | `METHODOLOGY.md:4861`, `:4948` | PR |
| 10 | UKF contact window [+146, +218] s (L471) | T4:8, :11; thesis_vocabulary.md:89 | `METHODOLOGY.md:7513` (U3) | PR |
| 11 | FGO contact window [+145, +196] s (L473) | T4:9, :11; thesis_vocabulary.md:89 | `METHODOLOGY.md:8995` (U3) | PR |
| 12 | No contact before +100 s (L471, L473) | thesis_vocabulary.md:90 | `METHODOLOGY.md:4948`, `:8022` | PR |
| 13 | B4 band ≤ 0.25 m/s (L480) | T4:11; thesis_vocabulary.md:95 | `METHODOLOGY.md:4874`, `:5096` | PR |
| 14 | Wall contact \|x\| ≥ 9.58 m (L428) | thesis_vocabulary.md:92 | `METHODOLOGY.md:3106`, `:3953` | M |
| 15 | FGO initial priors: OLD yaw σ 1e-3 rad, roll/pitch 2°; NEW 1°, 5° (L296, L464, L700) | headline_claims_before_after.md:4, :12, :24, :30; thesis_vocabulary.md:118; T4:11; the PRIORS caption sentence in figures_thesis/index.md, T4 and T7 | `src/estimators/fgo/fgo_core.py:40–48` (`YAW0_SIGMA = np.radians(1)`, `ROLLPITCH0_SIGMA = np.radians(5)`, with the old values in the comments); `METHODOLOGY.md:12836`; `docs/handovers/2026-10-10_initial_sigma_audit.md` | P |
| 16 | 0.1 rad initial-yaw sensitivity check (L302, L701) | headline_claims_before_after.md:21, :23, :60, :63 | `eval/results/sensitivity_yaw0_0p1/summary.json`; `METHODOLOGY.md:12836` (EKF3's 0.1 rad) | R |
| 17 | P-H5 drift bands: EKF3 and FGO ≤ 50 / 100 / 200 / 150 mm, UKF 2× (L626) | T5:7–10 (band column), :14 | `METHODOLOGY.md:10689–10691` | PR |
| 18 | Safety tests at the 2 m-clearance hold (L490, L491) | thesis_vocabulary.md:47; T7:9 | `METHODOLOGY.md:11850`, `:11872` | PR |
| 19 | S-A3 safe landing, ≤ 1.5 m drift to touchdown (L490) | thesis_vocabulary.md:104; T7:11 | `METHODOLOGY.md:11825`, `:11884` (the pre-registered 1.5 m drift bound) | PR |
| 20 | S-A2 position-lost bound 0.75 s; 0.10 s in run 1 (L490, L491) | T7:8, :11, :15 | `METHODOLOGY.md:11298` (0.75 s); run 1's 0.10 s is in its score file `eval/results/expH/safety_ukf_a.json` (as T7:15 says) | PR / R |
| 21 | UKF 5 s flow timeout (L491) | T7:11 | `METHODOLOGY.md:5396` ("the 5 s timeout") | M |
| 22 | EKF3 reference drift 1.40 m against a ≤ 0.5 m prediction (L491) | T7:7 | `METHODOLOGY.md:11886`, `:11898`, `:11489`; `eval/results/expH/safety_ekf3_ref.json` | R / PR |
| 23 | Former UKF take-off kick bound ≤ 0.79° (L234) | headline_claims_before_after.md:29 | `METHODOLOGY.md:9645` | M |
| 24 | Transition displacement ratio before the final re-run, UKF 45.9 / FGO 50.0 (L253) | headline_claims_before_after.md:27 | `eval/results/final_old_vs_new.md:36, 38` ("old" column) | R |
| 25 | Old NEES: FGO baseline 57.1 (~57×) (L305); UKF plain-wall 6.11 (L304); FGO +heading 24.8 in the first re-run (L306) | headline_claims_before_after.md:25 | `eval/results/final_old_vs_new.md:641` (57.11), `:700` (6.11), `:702` (24.83); `final2_old_vs_new.md:702` | R |
| 26 | First-re-run plain-wall FGO divergence: yaw RMS 838–1,014°, evo 43 m (L296, L299) | headline_claims_before_after.md:24 (also :23, "FGO 43 m") | `json:phase4_fwdplainc_arms.json` at `425e824` (`yaw_err_rms_deg` 838.10 … 1013.77, read this stage); the 43 m is from the C0 row's `json:phase4_*` at `425e824` (not re-read); verbatim copies in numbers.md Superseded l.1160–1161 | R (earlier commit) |
| 27 | "~1% under-scale" of the UKF with heading (L284) | headline_claims_before_after.md:28 | `METHODOLOGY.md:5530` ("UKF+heading 0.99") | M |
| 28 | "UKF about 2× lower yaw error than the FGO" (L297) | headline_claims_before_after.md:22 | `METHODOLOGY.md:12807` | M |
| 29 | First-re-run band counts fwdc 8/9, fwdplainc 9/9 (L328) | headline_claims_before_after.md:49 | `METHODOLOGY.md:12831` | M |
| 30 | 2(a) FGO_hard lockout total 23 → 61 (L500) | headline_claims_before_after.md:47 | `METHODOLOGY.md:13374` | M |
| 31 | 2(a) former "UKF lower yaw max 10/10" (L500, L501) | headline_claims_before_after.md:48 | `METHODOLOGY.md:12808` | M |
| 32 | H-O2 ratio "was ~2.2" (L559) | headline_claims_before_after.md:34 | `METHODOLOGY.md:10424` ("2.2–2.3×") | M |
| 33 | O "FGO batch ~2× better" (withdrawn), 0.33 vs 0.60–0.64 m (L561) | headline_claims_before_after.md:36; methodology_definitions_draft.md:163; T8:17 | `METHODOLOGY.md:10446` | M |
| 34 | V-L old result 4.63 vs 4.59 m (L576) | headline_claims_before_after.md:39 | `METHODOLOGY.md:10554` | M |
| 35 | L without loop closure before the FGO-only re-run: live 0.281–0.362 m, lap ratio 3.0–5.0 (L577) | headline_claims_before_after.md:38 | `eval/results/final2_old_vs_new.md:1004` (T_A_r2 0.2810); `json:expL/T_A_r{1,2,3}_t245.json` at `425e824` (`tracks["nolc live"].rmse_m` 0.3505 / 0.2810 / 0.3616, read this stage; the lap ratio comes from `per_lap_rmse_m` in the same files, not re-derived) | R (earlier commit) |
| 36 | EKF3 speed ratio 0.935 (withdrawn) (L285) | methodology_definitions_draft.md:170 | `METHODOLOGY.md:4697` | M |
| 37 | FGO noise-floor SD 1.23 m in the first re-run (L737) | headline_claims_before_after.md:19 | `json:dsn_paired_test.json` at `425e824` (`noise_floor_n10.FGO.sd` 1.2297, read this stage); verbatim copy in numbers.md Superseded l.1147 | R (earlier commit) |
| 38 | O FGO batch moved < 0.001 m by the initial-yaw correction (L695) | headline_claims_before_after.md:37 | `eval/results/final2_old_vs_new.md:906, 924` (indoor RMSE 0.589 → 0.589, 0.590 → 0.590; Δ 0.000) | R |
| 39 | Confirmatory test counts: old "EKF3 lower 6/7", now 5/7 (L227) | headline_claims_before_after.md:18 | old: `METHODOLOGY.md:6393` (result; criterion "at least 6 of 7" pre-registered at `:5650`); now: `eval/results/dsn_paired_test.json` (per-flight d, r4–r10) | M / R |
| 40 | UKF highest on 6/9 textured flights (L236) | headline_claims_before_after.md:17 | `eval/results/rerun_dsn_evo.json` + `dsn_extra_evo.json` (per-flight evo, the claim row's own source; count not stored) | R |
| 41 | EKF3 residual along-track scale 0.97–0.98 (L732) | limitations.md:9; headline_claims_before_after.md:28 | `METHODOLOGY.md:5530`, `:14183` | M |
| 42 | Phase 5 provenance: "126 inputs" (L263) | pending_items.md:17 | numbers.md provenance record; **caution:** `docs/handovers/2026-10-16_phase5_provenance_rounding.md:27` records that the row's "126 inputs, all ≤ 14:06:13" is inaccurate (the JSONs were written at 14:06:31–50). `pending_items.md:17` still carries the "all 126 inputs written ≤ …" wording | M-equivalent (handover), **flagged** |
| 43 | F1 robust-weighting constant k = 2.385 (L509) | thesis_vocabulary.md:393 | `METHODOLOGY.md:7907` (pre-registered grid), `:8281` (chosen on the calibration bags) | PR |

## Reported for a ruling

- **No written source (class N): none.** Every U quantity found in thesis-facing material has a written source.
- **Only `CLAUDE.md` (class C): one.** Row 2, the measured transition crossing y = 80.01 m in
  `world_images/index.md:24`. It is not a ruled source type. The options are:
  - cite it as "CLAUDE.md:1827, verification trial 2026-07-23";
  - replace it with the design value y = 80 m (row 1, a world file).
- **Wording contradicted by its own source: one.** Row 42, `pending_items.md:17`, "all 126 inputs written ≤ …". The
  provenance handover found that timing inaccurate. pending_items is a dated record, so it was not edited here.
- **Earlier-commit sources: three.** Rows 26, 35 and 37 are historical values read from a results file at the
  first-final-re-run commit `425e824`. The current file holds the restated value. That is the expected state for a
  "was/before" value, and it is stated rather than assumed.
