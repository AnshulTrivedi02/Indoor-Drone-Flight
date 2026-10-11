# Handover: final results pack, the four flags (2026-10-11)

**Stage:** analysis and documentation only. No replays, no flights, no heavy jobs. METHODOLOGY.md and src/ were not edited.
**Branch:** `worktree-agent-adab9f4f4ce48265d` (reset to `fwd-camera` `fb926d4` at the start; it had been cut from `main`). Commits:
- `4f91ac6`: numbers.md, the pack script and `eval/h_comparative.py`;
- `344030f`: the pack outputs regenerated at `4f91ac6`;
- `c9cc39a` added this handover; a follow-up commit corrects the branch name and two wordings.

Not merged.

## What changed in `docs/thesis/numbers.md`
1. **Flag 1, §16.3 cost bullets.** Restated from the FGO-only re-run outputs (`~/thesis_data/trials/T_A_r*/lc_fgo_*_t245/stats.json`
   and `~/thesis_data/batches/final2_L/logs/`):
   - LC: median 35–41 ms; p99 80–94 ms; wall 299–519 s.
   - no-LC: median 50–61 ms; p99 1.1–1.7 s; wall 7,276–9,583 s.
   - The wall time breaks away from about keyframe 4,000–6,000 (this was 3,000–4,000 in the old bullet).
   - The old bullets are kept verbatim in "Superseded by the FGO-only re-run".
2. **Flag 2, §15.**
   - Builds legend: old UKF (jitter), jitter-corrected UKF, original FGO, "FGO noise fix only (yaw cap ungated)" (the ABLATION), and the
     final FGO. Every FGO flight used the OLD priors.
   - Rows: the UKF v2 contact (+165.9 s); the FGO v2 contact (+169.6 s); the UKF v2 heading set 3/3 (the original r3 failed B4, 0.296 m/s);
     the FGO v2 and v3 heading sets 3/3 (v3 r3 B4 0.246 m/s, a near miss); per-flight B1/B2/B4 and B3 for all three re-flown sets.
   - Two safety-test rows: the final runs, then the history and the ablation. UKF (b) fails S-A2 as worded; all other final runs PASS.
   - The replaced rows are kept verbatim in a new block at the end: "Superseded by the closed-loop re-flight restatement (2026-10-11)".
   - ⚑ **Window.** The closed-loop scorer's contact key is EKF3's [+155, +215], and METHODOLOGY quotes the UKF v2 contact against that
     window, while the UKF's registered window is [+146, +218]. +165.9 s is inside both, so the verdict does not depend on which applies.
     This is flagged in the row, not resolved.
3. **Flag 3: new §17.1 and §17.2.**
   - §17.1 has rows for the S2v2, S2, S3v2 and S3 (ablation) sets.
   - §17.2 is "H comparative criteria — computed 2026-10-11 on the re-flown sets, PENDING user ruling".
   - The existing adjudicated H rows were not changed.
4. **Flag 4, "Flags: remaining" item 8.** It lists the four values, each with three readings: the full-precision file value, the 4-dp
   intermediate, and the printed value. None was changed.
   - Three of them are double rounding through the 4-dp table in `final2_old_vs_new.md`: 0.01048 → 0.011, 0.053504 → 0.053, and
     0.262533 → 0.262.
   - d r5 (stored as −0.4885) is a true tie.
   - The values stay as printed (numbers.md copies verbatim). A tidy rule (round the full-precision value once, half away from
     zero) is PROPOSED, pending a user ruling.

## Flag 3 result (computed only, NOT adopted)
- **Method.** `eval/h_comparative.py` reduces the stored `eval/h_score.py` outputs. h_score was not re-run; it is unchanged since `55edd75`,
  and the score-file key sets are identical.
  - It reproduces the adjudicated S2/S3 table exactly. The r2 UKF 5 s value of 6 mm is the effective-jump reading; as scored it is 7 mm.
  - Output: `eval/results/expH/h_comparative_2026-10-11.json`.
- **Re-flown values** (UKF = S2v2, FGO = S3v2, EKF3 = S1 far re-fly, paired by run):
  - hold error: UKF 6.4–7.1 mm, FGO 8.3–8.6 mm, EKF3 7.8–7.9 mm;
  - gyro activity relative to EKF3: UKF 2.40–2.58×, FGO 2.10–2.37×;
  - 15 s jump: EKF3 5 / 5 / 7 mm, UKF 20–30 mm, FGO 7–30 mm;
  - 5 s jump: EKF3 4–5 mm, UKF 7–16 mm, FGO 11–34 mm.
- **Verdicts.** H-H2 FAIL, P-H3 FAIL, H-H4 FAIL on both the 15 s and 5 s parts. These are **the same verdicts as the earlier sets**, under
  both jump readings.
- **Wording changes only:**
  - the FGO's hold error is now the highest, where before it tied with EKF3;
  - EKF3's 15 s jump is now strictly the smallest, where before it was "smallest or tied".

## Pack
- `eval/figs_final_pack.py` was updated: the F13 expected values, the FGO v2 pass check, two new F14 checks (the §17.2 verdicts and the hold
  ranges), the F08, F13, F14, F15a and F15b captions and sources, and the index FLAG text.
- Regenerated at `4f91ac6`: **17/17 figures CURRENT** (F05 against its JSON only), T1 and T2 CURRENT, and every check matches.
  - Only the F15a and F15b images changed.
  - The F13 and F14 changes are in the PDF captions and the index.

## Open / for the user
- **A ruling on §17.2.** Either adopt the re-flown-set computation (same verdicts) or keep the S2/S3 adjudication as the stated one.
- **The window ⚑** in §15 (cosmetic, since the verdict is unaffected).
- **Not covered here:** the S1-far shadows still have no numbers.md rows.
