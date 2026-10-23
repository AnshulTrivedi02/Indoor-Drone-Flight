# Tier-1 extension experiments: decisions log

These decisions were taken under the user's **standing decision rules (2026-10-23)**, numbered 1–8 below. The user reviews
this log and may reverse any decision marked reversible. Open questions are in `open_questions.md`.

The rules in brief:
1. Take the Recommended option when it is consistent with rules 2–8.
2. Pre-registration integrity: score verdicts as worded, and read any ambiguity against the hypothesis.
3. A genuine failure counts against the criterion. A harness bug is fixed without changing the error model. The
   counterfactual test is used only when a verdict depends on it.
4. Spend no machine time on checks that no verdict depends on.
5. Diagnose (at most 5 h) only when a result is more than 10× off AND will become a thesis claim.
6. Experiments with a timing hypothesis run one job at a time; the others run up to 4 in parallel.
7. Never modify frozen material. Run the guard before and after every experiment.
8. No claim may be stronger than its verdict.

**STOP conditions:**
- a frozen result or existing output would change;
- data would be deleted;
- a registered error model or the meaning of a hypothesis would change;
- the lock (2026-11-04 23:59 AEDT) would be missed;
- a guard or gate fails with no safe default.

| # | time (AEDT) | question | options | choice | rule | reversible |
|---|---|---|---|---|---|---|
| D1 | 2026-10-23 10:35 | E4 scheduling: serial or up to 4 in parallel? | serial / parallel ≤ 4 | **serial, one job at a time.** E4 has timing hypotheses (P-E4.1 step time increases with W; P-E4.2 the 33 ms budget, preregistration §3) | 6 | yes |
| D2 | 2026-10-23 10:35 | Order after the E3 map-collapse diagnosis (running) | E4 next / other | **E4 next**, as pre-registered (E2 → E3 → E4; E5 already done) | 6 | yes |
| D3 | 2026-10-23 10:35 | The E3 map-collapse diagnosis started before these rules: does it satisfy rule 5? | continue / stop | **continue.** 51–85× clean against a pre-registered ~+20% is more than 10× off. It will feed claims_update.md. It is bounded at ≤ 5 h machine time | 5 | yes |
| D4 | 2026-10-23 10:35 | The four new E3 divergences (T_A_r2/T_A_r3 1% s1, s2) | cf2 test / triage label | **triage label** "classified by triage, not counterfactual-tested". No verdict depends on the classification | 3, 4 | yes |
| D5 | 2026-10-23 10:25 (decided before the standing rules arrived; logged afterwards) | E3 collapse diagnosis: counterfactual (i) (first-sighting mislabels kept true, 17 wrong ids remain) DIVERGED (onset 60.632 s), not the later collapse predicted in `stage2e/diag_collapse/predictions.md`. Stop, or continue? | stop and report / continue with (ii) | **continue with (ii)**; record (i) as a failed prediction. The pre-written "contradicts Part 1" test (ends near clean with a true-size map) did not fire, and divergence is not a STOP condition | 3, 5 | yes |
| D6 | 2026-10-23 10:25 (decided before the standing rules arrived; logged afterwards) | Add a third counterfactual (also keep 59.995/60.127) to see whether (i) then collapses? | run (iii) / no | **no.** Whether collapse needs first-sighting mislabels is already answered by the existing cf2_s1/cf2_s2 outputs (0 first-sighting mislabels, collapsed maps), scored read-only (seconds); the ruling allows 1–2 runs | 4, 5 | yes |
| D7 | 2026-10-23 | Units pass: should the Experiment 5 hold error, tag-loss drift and re-lock jump be in mm or m? | mm / m at 4 dp | **mm** (values 1–31 mm; m would read 0.0049–0.0090). This matches the user's Q1 example "drift in mm, position error in m". It reverses the 2026-10-22 plain-m change on A.2, summary pages 10–11 and walkthrough pages 24–26. All other position errors are in m, compute times in ms, timeline times in s. Pre-registered wording is quoted in its registered units | Q1 ruling, 1 | yes |
| D8 | 2026-10-23 | Two existing column overlaps on Table A.3 (p1 "NOT met (lockout tie)", p2 "Experiment 5 hold, window means") | fix / leave | **fix** after the units merge: widen the column, then regenerate. CPU-light, no machine-time job | 1 | yes |
| D7 | 2026-10-23 11:40 | Checksum guard: no verify was run immediately before the two diagnosis replays (rule 7) | rerun the replays / record and verify now | **record and verify now**: post-run verify at 11:20 IDENTICAL (13,253 files); the last verify before was stage 2e's (06:57); the replays wrote only under `~/thesis_data/tier1/stage2e/diag_collapse/` | 7 | yes |

*(The user's own rulings before 2026-10-23 10:30 are recorded in preregistration.md and METHODOLOGY.md, not here.)*
