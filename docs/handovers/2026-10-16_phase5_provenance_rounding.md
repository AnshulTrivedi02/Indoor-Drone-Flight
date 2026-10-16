# Handover 2026-10-16: Phase 5 provenance record (item 6) and the rounding sweep

**Stage:** one stage. It applies METHODOLOGY "RULINGS (user, 2026-10-16): item 6 accepted with a provenance record;
rounding sweep". **Nothing was recomputed.** Only scripts, pipeline logs, job lists, file mtimes and the stored values were
read. METHODOLOGY.md, the result files and the frozen documents were not edited. The branch is `worktree-agent-a0cc5039e3ae685e2`,
reset to `fwd-camera` `842ca12` (the worktree had been created from the unrelated `main` root).

## Item 6: PASS on (1), (2) and (3); the record is a new section at the END of `numbers.md`

- **Placement: line-neutral, by design.** The record is the new last section, "Provenance record: the §6.3 Phase 5
  decomposition row", placed after Superseded. The row's own provenance cell gains a same-line pointer to it.
- **Why.** Thesis-facing docs cite `numbers.md` by line, for example `thesis_vocabulary.md:303` ("§6.4 (264-274) …") and
  `methodology_definitions_draft.md:64` (`numbers.md:467`). In-place insertion would have shifted every citation after
  line 263. The first commit (`98a3431`) inserted the record under the §6.3 table; the follow-up commit moved it.
- **Check.** The diff against `842ca12` changes line 263 in place and appends from line 1252 on. No cited line moves.

- **(1) PASS.** Phase 5 (`final_rerun2`, 2026-10-10 14:06:50–14:09:29) read 203 files:
  - 45 UKF `ukf_traj.tum` and 27 heading-arm UKF `timing_and_fwd.npz`, with mtimes 2026-10-09 20:52:24–21:18:53. These
    fall inside `final_rerun` phase4 (20:51:13–21:19:56).
  - 45 FGO TUMs and 27 FGO npz, with mtimes 2026-10-10 13:46:33–14:06:13. These fall inside `final_rerun2` phase4
    (13:44:22–14:06:50).
  - 4 phase4 JSONs, written 14:06:31–50 by `final_rerun2`'s phase4 eval. Their UKF leaves are proven unchanged by the hard
    UKF gate: "225 UKF leaves compared, 0 differences".
  - `fwd_calibration.json` (09-24) and 54 recorded-dataset files (09-29).
  - The UKF replays were skipped: the FGO-only filter kept 45 of 90 jobs, `final2_phase4/done` holds 0 `ukf__` markers,
    and `final_phase4/done` holds 45 + 45.
  - **The row's "126 inputs, all ≤ 14:06:13" is inaccurate.** The JSONs were written at 14:06:31–50, still before the
    stage began. The record says so; the row cell itself was not changed.
- **(2) PASS.** All of these commits are off by default or off the Phase 4 path, with the byte-identity proofs cited:
  - **UKF path, after `425e824`:** `df50ad9` and `5e0eba5` (ukf_replay knobs), `0ac0983` (`geom=None` in
    `measurement_models`, merged by `4608637`).
  - **FGO path, after `819caab`:** `0ac0983`, `eb629a6`, `4608637`, `b9da351` (events mode / `geom`), and `2610bdb`
    (fgo_cpp compile-time switch; not on the Python Phase 4 path).
  - **No `ATTRIB_` toggles exist.**
  - **Untouched since before `425e824`:** the job list, `phase4_eval.py`, `phase5_analysis.py`, `ukf_core.py`,
    `cruise_window.py`, `fgo_export.py` and `src/forward_camera/`.
  - **`df50ad9` is an ancestor of `819caab`**, so the FGO initial-yaw correction is in the FGO-only run.
- **(3)** The literal test fails only because the run ended with L (21:35:23). `phase5` comes before L, needs only
  `phase4`, and reads no L input or output.

## Rounding sweep

**Method.**
- **Instrumentation.** A temporary copy of `eval/figs_thesis.py`, with outputs redirected to the scratchpad (since
  deleted), logged every `rd()` call in a full build: 943 calls, 547 unique (value, precision) pairs. The cross-check
  again gave 128/128.
- **Candidate screen.** Each pair was tested for whether rounding first at 1–4 extra digits (half-up or half-even) and then
  to the printed precision, or a single half-even rounding, could give a different string. **31 candidates.**
- **Grep.** Each candidate's alternative string was grepped in its context across:
  - the hand-written thesis-facing docs: `headline_claims_before_after.md`, `limitations.md`, `thesis_vocabulary.md`,
    `methodology_definitions_draft.md`, `pending_items.md`, `world_images/index.md`;
  - `pdftotext` of both PDFs;
  - the tables and the index;
  - the hard-coded caption and note literals in the generator.
- **C FGO live (0.053504).** This is the one flag-8 value that no rounding rule reproduces, so its string "0.053" was
  grepped as well.

**Corrections (hand-written source; the generator was unchanged, so nothing was regenerated):**

| file:line | old → new | stored full-precision value |
|---|---|---|
| `docs/thesis/headline_claims_before_after.md:34` (claim 19) | H-O2 ratio 1.72–1.84 → **1.71–1.84** | min over flights of EKF3/min live = 1.4224755876/0.8296237187 = 1.7146033263374372 (`expO/O_r2.json`) |
| `docs/thesis/headline_claims_before_after.md:38` (claim 23) | nolc live **0.262–0.361** → **0.263–0.361** m | 0.262532619256968 (`expL/T_A_r2_t245.json` tracks["nolc live"].rmse_m) |

- **Generated outputs are correct by construction.** Every displayed number goes through `rd()`, and no caption literal
  carries a double-rounded form. "within 0.39 m" in F2 is 0.39229 rounded once.
- **The two hits are the only ones.** The other hits are different quantities or are historical "before" values: −0.040
  (first re-run d), 0.33 (old O batch), 8.4 deg/min, "all ≤ 0.013 m" (sensitivity, not on the map), 0.281–0.362 (old L,
  file 0.28096/0.36160, correct), and EKF3 "3–11 mm" (S1 near 30 s, 3.355/11.382, correct).

**Left as they are:**
- **`pending_items.md:16, 32`.** These lines narrate the old 1.1/26.2 → 1.0/26.3 change. They are history, not displays.
- **`figures_thesis/index.md`, the "expected" column and the "last-digit rounding matches" line.** These quote the
  numbers.md strings by design (the cross-check record). Changing the generator's expected strings would break the
  comparison with numbers.md.
- **Frozen documents** (`final_results_pack*`, Superseded blocks, METHODOLOGY): not changed. Their hits are listed below.

**`numbers.md` rows that DISPLAY a value differing from the single rounding, for a ruling (not changed):**
- §16.1 table: A FGO batch 0.011 (file 0.0104796) and C FGO live 0.053 (file 0.0535044, single 0.054).
- §16.1 P-T4: C 2.07 (file 2.0648622; single 2.06; 2.0649 → 2.065 → 2.07 is double rounding).
- §16.2 H-O2 bullet: 1.72–1.84 (file min 1.7146033; single 1.71).
- §16.2 P-O3 cap-free: 1.02–1.05 (file min 1.0148303; single 1.01).
- §16.3: nolc live 0.262–0.361 (file 0.2625326; single 0.263).

- §6.6 (line 305), FGO baseline cross-track NEES per bag "(2.4 / 0.2 / 2.6)": the r3 file value is 2.5456255
  (`phase5b_consistency.json` consistency.fwdc_tex_r3.FGO_baseline.mean_nees), and its single rounding is **2.5**
  (2.5456 → 2.55 → 2.6 is double rounding). The mean, 1.70, is correct, and the per-bag values appear in no
  thesis-facing file.

**Flag 8 (numbers.md, "four last-digit transcriptions") undercounts.** P-T4 C, the H-O2 lower bound and the P-O3 cap-free
lower bound are three more. The generator already displays the single roundings: T6 1.71–1.84, T8 2.06, the T8 caption
1.01–1.05.

**Off-map values (hand-typed, not printed by the generator).**
- **Screen.** I listed every value ending in 5 at its stored precision in `final2_old_vs_new.md`,
  `final_old_vs_new.md` and `numbers.md`. Only such a value can flip under double rounding. For each, I grepped its two
  one-digit-shorter forms in the hand-written thesis-facing docs.
- **Same-quantity hits.** Each was checked against the full-precision file value:
  - dsn r1–r3 means 4.00 / 3.59 / 3.44;
  - paired d −0.021, CI [−0.989, +0.947];
  - noise-floor SDs: FGO 1.30 [0.88, 2.49], EKF3 0.31 [0.22, 0.57];
  - F2 live yaw 0.32–0.36° (both lives, as `f23_eval.py` tests);
  - NEES 1.70 / 13.41 / 13.95;
  - kick ≤ 0.82°;
  - sensitivity ≤ 0.013 m (clock max 0.01311, threshold 0.00956);
  - 0.1 rad check 0.75 / 0.73, 0.25 / 0.22 → 5.70 / 5.70;
  - yaw RMS 0.07–0.08°, 3.08–3.39 / 3.07–3.41°;
  - yaw max 4.59–5.03° (`f1_test.json`);
  - fused 647–778 / 3,582–5,911; bias −7.6 … −8.4;
  - transition ratios 6.8 / 17.7 (18.0 / 18.1 / 17.0);
  - scale 0.996–0.997 / 0.998–0.999 / 0.97–0.98;
  - contact median +163.2 s, west +154 … +198;
  - shadows 4–9 / 1–8 mm, EKF3 3–11 mm;
  - O attribution 0.22–0.30, +0.03.
- **Result: all correct; no off-map hits.** The only corrections are the two above.
- **Not traceable to a stored field:** "3.91–6.24° trans" yaw max (numbers.md §6.6 l.296; the plain-wall trace). Not
  checked. "Before" values and METHODOLOGY quotations were not checked, as history.

**Frozen documents: searched, hits left frozen** (the known double-rounded forms 0.011, 0.053, 0.262, 26.2, 2.07, 1.72,
1.02):
- `final_results_pack.pdf` (`pdftotext` lines):
  - 112: P-T4 "1.31 / 2.14 / 2.07 / 3.89";
  - 119: "H-O2 … 1.72–1.84×", "cap-free 1.02–1.05";
  - 128: L "0.262–0.361 m";
  - 234: claim 19 "1.72–1.84";
  - 244 and 422: "0.281–0.362 → 0.262–0.361 m".
- `final_results_pack_index.md`:
  - 302: 2.07;
  - 309: 1.72–1.84; cap-free 1.02–1.05;
  - 316: 0.262–0.361;
  - check-table expected strings at 35, 126, 128, 150.
- `final_results_pack_corrections.md:45`: L "0.281–0.362 → 0.262–0.361 m".
- `numbers.md` Superseded l.1105: old-run T table "**0.011 m**". This is a pre-re-run value, a different stored value,
  and was not checked.

## Cross-check

**128/128**, unchanged. It was confirmed by the instrumented build into the scratchpad; the committed outputs were not
regenerated, since the generator was not changed.

## Not done / for the user

- **A ruling on the numbers.md rows above,** and on whether flag 8 should list the three extra values.
