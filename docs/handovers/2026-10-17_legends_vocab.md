# Handover 2026-10-17: schematic legends in thesis vocabulary; two vocabulary additions; blank-floor pooling noted

*One stage, text only. **No number changed.** Not edited: `numbers.md` (CONTENT-FROZEN; `tools/check_numbers_frozen.py` PASS),
METHODOLOGY, results, the frozen pack. Follows `docs/handovers/2026-10-17_vocab_applied.md` (its residual "raster schematic
legends" row is now closed).*

## 1. Schematic legends (`sim/tools/world_schematics.py`)

**Policy:** the old codes are replaced with vocabulary names, and **the provenance file paths are taken out of the image text**
(`tools/run_expT.sh`, `run_expO.sh OUTBACK=…`, `batches/tagchar.conf`, `s0a_sweep.json`, `s1_profile.json`,
`s1_far_profile.json`, `safety2_fgo_profile.json`, `ifanchor_profile.json`, `closed_loop_run.sh --box`,
`tag_bridge_fwd.py WALL_P`, and the `batches/*.conf (trial)` suffix on every corridor cruise). They carried the
codes in their file names. Vocabulary §8.2 keeps file names out of captions, and every source is still listed in the method lines
of `docs/thesis/world_images/index.md` (lines ~104–114). In its two hand-written tagchar lines the "tagchar" label became "Tag check flights (`tagchar_*`)" / "the tag-check-flight line (`tagchar_*`)", so the image wording leads to the source. Nothing else in that file changed.

Re-run from the SDF (no Gazebo, no camera rendering): `python3 sim/tools/world_schematics.py --out docs/thesis/world_images/schematics`,
then `python3 sim/tools/world_docs_pack.py` (worlds_combined.pdf, 24 pages as before. p.20, `room_wall_tag_far`, was viewed and embeds the new schematic).

**Legend entries after the change.** They were checked mechanically (pdftotext on each schematic's vector PDF, with a grep for the old codes: none) and by viewing
all 24 PNGs with the Read tool. **The schematic titles keep the world file names** (e.g. `corridor_transition_fwdc: top-down schematic from the SDF`), by design (vocabulary §8.2 row 18: world names stay in the world table and pack). The "no old code" claim covers the legend and annotation text. Every schematic also has its floor/wall/ceiling patches and "spawn <model> (x, y), yaw 90 deg".

| schematic | route / annotation entries |
|---|---|
| all 17 `corridor_*` | "planned cruise: 0.5 m/s x 300 s = 150 m at 2.0 m" (+ "textured \| blank boundary y = 80 m" on the transition worlds) |
| `room_tags` | "Experiments 2 and 3: laps: 5 x 6 m square N-E-S-W at 0.5 m/s, 2.0 m"; "tag check flights: 0.5 m/s north for 12 s at 1.5/2.0/2.5/3.0 m" (was "T/L laps …", "tagchar: …") |
| `outdoor_indoor` | "Experiment 4: align: 15 m at 1.5 m/s (GNSS on)"; "Experiment 4: out: 50 m at 0.5 m/s"; "Experiment 4: back: reverse, same heading"; GNSS gate text. The duplicate "tools/run_expO.sh OUTBACK=…" header note was removed |
| `room_wall_tag` | "Experiment 5 characterisation: grid sweep (world frame)"; "Experiment 5 EKF3-flying hold set: hold W(-1.5, 0.0), E steps of 0.5 m"; "Experiment 5 safety-watcher room box" (was "H S0a …", "H S1: …", "watcher room box") |
| `room_wall_tag_far` | "Experiment 5 hold sets, far spawn (EKF3-, UKF- and FGO-flying): anchor at W(-3.9, 0.0), move to the hold W(-1.5, 0.0)"; "then E steps of 0.5 m at the hold"; "5S safety tests (FGO): hold W(-2.6, 0.0)"; safety-watcher room box (was "H S1far / S2 / S3 …", "safety2_* hold …") |
| `room_wall_tag_far_occ` | "Experiment 5 in-flight-anchor check: move 1.5 m north in EKF3's own pre-anchor frame, drawn from the spawn"; safety-watcher room box (was "H_ifa: …") |
| `iris_textured`, `iris_runway` | header note "no mission file: the early pipeline-check and speed-sweep flights flew a few metres north (record only)" (was "Stage A-C / sweep flights … by fly_forward/fly_trial") |

**Choices to review:**
- "tag check flights" (`tagchar_*`, room_tags). These are check flights (§8.2 row 20), not the Experiment 5 characterisation.
- "5S safety tests (FGO)". This is deliberately neutral, because "re-test" means only the final corrected-priors run in Tables 7.2/A.2. `safety2_fgo_profile.json` is used by `tools/run_h_safety.sh` (the second FGO run) and the `_v3`/`_v4` runs (`tools/run_fgo_refly.sh`); the first FGO runs used `safety_fgo_profile.json`, which is not drawn.
- The far-spawn hold sets are named without a build qualifier.

**Numeric tokens in the schematic PDFs:** lost or gained only label numerals: "Experiments 2 and 3", "Experiment 4/5", and the removed `dsn_tex_r1`-style trial suffix,
`s0a`/`s1` file names and the duplicate OUTBACK list (its values are still printed in the Experiment 4 legend entries). No geometry
or route value changed.

## 2. `docs/thesis/thesis_vocabulary.md`

- **Added** under H1.3 (§5, a "(analysis, H1.3)" row): **heading-error decomposition of sideways drift**. The lateral-velocity error is split into a heading-driven part, speed × (sin ψ_est − sin ψ_true), and a residual. Sources: method M:3400-3404, the Phase 5 test M:1336-1338, and the values numbers.md §6.3.
- **"thesis-nav" appears in thesis-facing text**: the Table 7.2 EKF3 cell ("EKF3 has no thesis-nav position-lost path") and the Table A.2 note on `A2_H_and_safety_p2` ("no thesis-nav text"; present in that page's PDF text, absent from the combined-PDF text). So it was **defined, not replaced**. The new §8.3 gives **thesis-nav position-lost path** (descriptive): the Copter `thesis_nav_check` landing trigger. Source M:11264-11265; fork `ekf_check.cpp:337-358` (glossary.md:2964); status text glossary_flags.md:915.
- Both are in §9. A dated note under the preamble says that neither is counted in the §0 vocabulary-term count (47 rows unchanged) and that no row was renumbered.

## 3. Generated outputs (`eval/figs_thesis.py`)

- **Table 4.1 (T2):**
  - The caption and the decomposition note now use "heading-error decomposition of sideways drift".
  - The note says it is the analysis that H1.3 is judged on.
- **Index mapping:**
  - The H1.3 row no longer says "has no thesis name".
  - There are two new generated rows: the decomposition (used in Table 4.1) and thesis-nav (Table 7.2, Table A.2).
- **Blank floor:**
  - Table 7.1 row: "Experiment 1: blank floor (no flow; 1A and 1B flights pooled)". The T1 caption gains a sentence: the row pools the 1A standard-sensor flights with the 1B forward-camera flights (the camera calibration flights and both camera datasets).
  - Table 4.2 (T3): the caption adds "The blank-floor flights pool Experiment 1A (standard sensors) and 1B (forward camera)". The note gives the per-dataset split. The flight counts (EKF3 14, UKF/FGO 11) are unchanged and are not restated in the new text.
  - As a side effect, the generated "used in" cells for 1A, 1B and the camera calibration flights now also list Table 4.2 and Table 7.1.

## 4. Verification

- **Cross-check 129/129 exact**, and the per-item counts are unchanged. The freeze check passes, for both numbers.md and the frozen commit 669f099.
- **Numeric-token diff**, using the previous stage's `numdiff.py`, adjusted to strip the new labels and commit hashes:
  - 69 units (table .md/.tex, the per-figure and appendix PDFs, the combined PDF per item and its cover, the worlds PDF per page, the world index and the shots table): **0 units with a numeric difference**.
  - Figure index, 15 items (caption, computed and expected): **0**.
  - The only non-label change in all outputs is the embedded generator commit, `6bb231b` → `a8ef120`.
- The T1 and T3 PNGs were viewed after the change. The cells wrap cleanly.

## State

- Branch `worktree-agent-ad5fb8fddc2826a8c`, based on `fwd-camera` at `a8ef120`. Two commits: the main pass, then the neutral 5S label, the tagchar index bridge and this note. **Not merged.**
- Still open from the earlier handover:
  - safety *run* labels (item 4);
  - hold-set stage-code parentheses (item 6);
  - the provisional chapter plan (item 7);
  - "pre-registered"/"CLOSED" definitions (item 9).
