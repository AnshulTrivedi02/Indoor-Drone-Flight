# Handover 2026-10-16: numbers.md single rounding, the full comparison, and the exact cross-check

**Stage:** one stage. It applies METHODOLOGY "RULING (user, 2026-10-16): numbers.md rounding, option (a); a full scan; an exact
cross-check". **Nothing was recomputed.** Stored values were read, and only displayed digits changed. METHODOLOGY, the result
files and the frozen pack (`final_results_pack*`, `eval/figs_final_pack.py`) were not touched. The branch is
`worktree-agent-a3276ca729b3e3253`; the worktree was created from the unrelated `main` root and was reset to `fwd-camera` `f9c12bb`.

## 1. numbers.md corrections (all in place; line-neutral for every cited line)

Each old row is kept verbatim in the new block "Superseded by the ruling of 2026-10-16 (numbers.md rounding): double rounding
corrected (ruling 2026-10-16)". It sits at the end of the Superseded section, just before the provenance record. Only that
record (cited by name, never by line) moved down 41 lines. No line at or before 1254 moved; the highest line any doc cites is
1017, and no doc cites a line inside the rewritten flag 8 (758–773). **No line citation needed an update.** One doc described
the old rule and was corrected in place (same line count):
- **`docs/thesis/methodology_definitions_draft.md`, lines 196–197 and 200–202.** "numbers.md keeps full precision … including the
  four double-rounded transcriptions" and "the cross-check records a last-digit match" now say: numbers.md shows the same single
  rounding, the old rows are in its Superseded section, and the cross-check is exact.
- **Not changed:** `pending_items.md` lines 16 and 32. They are the dated record of the item 3 ruling (history, not a description
  of the current rule).

| line | quantity | old → new | stored full-precision value (source) |
|---|---|---|---|
| 251 | §6.2 UKF baseline +60 s after loss, transition (n = 11) † | 129–139 → **128**–139 | 128.4931019883928 (`blank_behaviour.json` fwdc_trans_r2 ukf_baseline +60 s, hypot(along, cross)) |
| 305 | §6.6 FGO baseline NEES per bag, r3 | 2.6 → **2.5** | 2.5456255357111575 (`phase5b_consistency.json` consistency.fwdc_tex_r3.FGO_baseline.mean_nees) |
| 388 | §11 textured-half difference | +0.10 → **+0.09** px/s | 0.09460667204103856 (`ceiling_flow_effect.json` groups.tex_half.difference; the +0.10 was 136.08 − 135.98, the difference of the rounded METHODOLOGY means) |
| 526 | §16.1 A, FGO batch | 0.011 → **0.010** m | 0.010479623174296593 (`expT/t_aggregate.json`) |
| 528 | §16.1 C, FGO live | 0.053 → **0.054** m | 0.05350438641877409 (same) |
| 536 | §16.1 P-T3, D | 1.58 → **1.57** | 1.574656762869718 (same, "P-T3 live ratio max/min") |
| 537 | §16.1 P-T4, C | 2.07 → **2.06** | 2.0648622233420286 (same, "P-T4 hindsight ratio max/min") |
| 559 | §16.2 H-O2 lower bound | 1.72 → **1.71** | 1.7146033263374372 (min over O_r1/O_r2/O_r3b of max/min live `indoor_rmse_m`) |
| 560 | §16.2 P-O3 cap-free lower bound | 1.02 → **1.01** | 1.0148303286865021 (FGO batch / cap-free RTS-UKF, min over flights) |
| 574 | §16.3 no-LC live lower bound | 0.262 → **0.263** m | 0.262532619256968 (`expL/T_A_r2_t245.json` tracks["nolc live"].rmse_m) |
| 577 | §16.3 H-L bullet, "→ 0.262–0.361" | → **0.263**–0.361 m | same |

- **New beyond the brief:** P-T3 D (536), §6.2 +60 s (251) and §11 (388) were found by the full comparison.
- **Lines 3–4 (header):** "Every value is copied verbatim from its source. None has been recomputed or re-rounded." now reads
  "Values cited to M:/C:/P: are copied verbatim; values traced to a stored result file show it rounded once (flag 8). None has been
  recomputed." Both old lines are in the Superseded block.
- **Line 388 (§11):** the source cell is now "M:L2592 (METHODOLOGY prints +0.10, the difference of its rounded means);
  json:ceiling_flow_effect.json:groups.tex_half.difference", so the row no longer disagrees with its only cited source."
- **Flag 8 (lines 758–773):** rewritten in the same 16 lines. It records the correction and lists every changed value; its table
  now has "printed before" and "printed now" columns. The old text is in the new Superseded block.
- **Confirmatory d r5:** −0.489 is unchanged. It is the half-away-from-zero rounding of the 4-dp stored −0.4885.

## 2. Did the earlier scan compare every value? No: only near ties

The earlier scan (`2026-10-16_phase5_provenance_rounding.md`, "Method" and "Off-map values") did not compare values one by
one against their sources:
- **Generator values:** it screened `rd()` inputs only for whether double rounding *could* flip them (31 candidates).
- **numbers.md and other hand-typed values:** it screened only values ending in 5 at their stored precision.
- **Untraced values:** it flagged the "3.91–6.24°" yaw max as untraceable. This stage traced it to
  `sensitivity_yaw0_0p1/summary.json`; it matches.

That screen missed P-T3 D (1.5747 does not end in 5 at 4 dp) and the §6.2 and §11 cases. It also missed a generator **caption
literal**, "P-T3 … 1.58", in the F5 caption: the earlier handover's claim that no caption literal carries a double-rounded
form was wrong (§3).

**Full comparison, run now.**
- **Unit of count:** every numeric token in the current sections (lines 42–776), from `tokens.py` (in the scratchpad). The
  Superseded blocks are excluded, as they are verbatim by convention.
- **Method:** each token was traced to its stored file/key, and derived values (means, ranges, ratios, hypot) were computed from
  the full-precision leaves. Each was compared with `rd(stored, displayed precision)`.
- **Records (scratchpad):** `cmp_s1.tsv` to `cmp_s4.tsv`, with their scripts (`cmp_s1.py`, `cmp_s2.py`, `s3_cmp.py`, `s4_*.py`).

| | tokens |
|---|---|
| numeric tokens | 2107 |
| traced to a stored source and matching single rounding | 1233 |
| traced, mismatching (corrected above) | 14 (the 11 rows above plus the 3 flag-8 "printed here" cells) |
| traced, not reproduced, and not a rounding effect (reported, not changed) | 5 (3 items, below) |
| untraceable to a stored data file | 769 |
| not a value (section numbers, denominators, n, repeat indices, labels) | 86 |

**Untraceable values (769), by category.**

| category | count |
|---|---|
| METHODOLOGY / CLAUDE / PROGRESS text only (M:/C:/P: rows: §1–§5 setup and timing, §10, §12–§14, flags 1–7, VISO bounds, the 1.97 km C++ figure, …) | 328 |
| parameters and code constants (geometry, mounts, noise values, gates, thresholds, initial σ, software versions) | 166 |
| counts not stored as a value (pass tallies such as 3/3 or 20/20, 14 of 17, batch counts) | 98 |
| historical "was/before" values | 83 |
| bands and pre-registered settings | 60 |
| estimates (Part C) | 12 |
| other (time and origin labels, attribution shares from an uncited file, "~" approximations, a printed batch log, UKF OPEN) | 22 |

**Traced, but not reproduced by any rounding (NOT changed; for a ruling).**
- **l.522 "repeats agree within 8 mm" (§16.1):** the largest spread over the 3 repeats in `expT/T_*_r*.json` (horiz_err_m.rmse)
  is 18.6 mm (D, FGO live), and D EKF3 live is 16.9 mm.
- **l.565 "EKF3 switched source set at OFF + 4.3 s and ON + 4.4 s" (§16.2):** `expO` `ekf3.source_set_changes` against
  `markers_bag_s` gives OFF +4.37/+4.37/+4.34 and ON +4.32/+4.32/+4.28 s. Rounded once, that is OFF 4.4/4.4/4.3 and ON 4.3, so
  the two look swapped or differently defined.
- **l.647 S3 "EKF3 shadow 10–20" mm (§17.1):** `expH/s3_r*.json` EKF3 `drift_end_m` spans 6.3–20.1 and the effective drift
  5.1–18.9, so the lower bound of 10 is not reproduced.

**Soft notes (not mismatches).**
- **l.482 "no excursion above 0.7°":** the largest value is 0.682.
- **l.500 "max within 0.03°":** the largest value is 0.024, so the bound holds but is not that value rounded.
- **l.299 "0.06 vs 0.13 m":** r3 UKF is 0.137 → 0.14, so 0.13 is the minimum, not all three.
- **Uncited sources:** some traced values (the old P4 bands, the l.326 IMU-gap counts) come from untracked `results_pre_final*/`
  or per-trial files that the row does not cite.

## 3. Exact cross-check in `eval/figs_thesis.py`

- **`check()`:** it now compares strings exactly. The tolerance branch, the `exact=` parameter, `ROUNDING` and `NUM` are removed.
  The index shows "yes"/"**NO**" and lists every failure ("not forced") instead of "last-digit rounding matches".
- **Rounding:** every computed string is built with `rd()`. A grep found no `:.Nf`, `round(` or `%` formatting in any check.
- **Run with the old expected strings:** 118/128, failing on exactly the 10 former "last-digit" matches.
- **Expected literals updated to the corrected numbers.md strings:**
  - `0.010–0.028`;
  - `1.71–1.84; True` (twice);
  - `0.263–0.361` (twice);
  - `exp10` A and C;
  - P-T4 `2.06`;
  - FGO batch `0.010 / …`;
  - cap-free `1.01–1.05`.
- **F5 caption literal replaced.** The hard-coded "P-T3 FAILS (live max/min 1.97 / 2.36 / 1.42 / 1.58)" was a double-rounded
  literal that went through no `rd()`. It is now computed with `rd()` from `t_aggregate.json`, and a new check against numbers.md
  §16.1 P-T3 was added.
- **Other caption literals checked against the stored values, all correct:**
  - F5: 2–4 / 8–13 cm, 8.3, 9.6 cm, 1.31–3.89;
  - F2: 0.39 m;
  - F6 and T6: 4.1 m, 0.8–1.4, 0.58–0.60;
  - T8: 1.3–3.9×;
  - A1: 0.246.
- **Result: 129/129 exact, 0 failures.** That is the old 128 plus the new P-T3 check. Every check against numbers.md now matches
  numbers.md character for character, including the checks that compare against METHODOLOGY.
- **Regenerated.** The tables (`docs/thesis/tables/*.md`, `.tex`) differ from the pre-stage snapshot only in the
  "generated … (commit …)" line. **The one displayed change is the F5 caption, "1.58" → "1.57"** (P-T3 D), which appears in
  `index.md` and in the F5 page of the combined PDF. Every other displayed value is unchanged, because the generator already
  printed single roundings.

## Left as they are
- **`docs/thesis/final_restatement_draft.md`** (a 2026-10-10 restatement record) still shows 1.31 / 2.14 / 2.07 / 3.89, 1.72–1.84
  and 129–139. It is a dated record, not a thesis display, and was not changed. Flag it if it is to be cited.
- **The frozen pack and the earlier handovers:** unchanged.

## For the user
- A ruling on the three "not reproduced" items in §2 (l.522, l.565, l.647).
