# Group C candidate thesis figures (decision D124): Extension E2, Extension E3 (including the tag maps) and Extension E5

Built by eval/figs_cand_c.py at commit `d37f63b`, run with /home/makerspace/venv-evo/bin/python. The E3 tag maps (C05, C06) also need eval/figs_cand_c_extract.py, run once under heavy.py to cache /ground_truth/pose from the stored bags to ~/thesis_data/cand_c_cache (deleted once this script finishes). Stored outputs only throughout: no flight, estimator replay or simulation. Rules: 160 mm (6.30 in) wide, Okabe-Ito EKF3/UKF/FGO + grey truth, filled = live / open = hindsight, no titles, no verdict words, no badges or explanatory notes inside axes, no bold in axes, side-by-side panels only on a shared scale, every number in an exact cross-check (parsed rd(), SHA-pinned).

**Checks: 81/81 (exact string equality).**

| id | proposed title | source chart(s) | data files | checks | verdict pointer |
|---|---|---|---|---|---|
| C01 | Loop closure with fewer tags: the FGO's error on lap 5 | walkthrough extra/ex_E2_fewer_tags.png (p15); summary page 13 (same data, one candidate) | tier1/scores/E2_verdicts.json, E2_T_{B,C,D}_r{1,2,3}.json; eval/results/expL/T_A_r{1,2,3}_t245.json | 14/14 | H-E2.1; P-E2.5 (graded) |
| C02 | Wrong tag IDs: outcome of every run (chart) | walkthrough extra/ex_E3_table.png (p16, really a table -> see C03); summary page 14 (chart; same underlying data) | tier1/scores/E3_verdicts.json | 14/14 (shared with C03) | H-E3.1; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |
| C03 | Wrong tag IDs: outcome of every run (table) | walkthrough extra/ex_E3_table.png (p16) | tier1/scores/E3_verdicts.json | shared with C02 | H-E3.1; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |
| C04 | Wrong tag IDs: every registered verdict (table) | summary page 15 = walkthrough page A1 (table drawn as a figure) | tier1/scores/E3_verdicts.json | 18/18 | H-E3.1; H-E3.2; H-E3.3; P-E3.4; P-E3.5a; P-E3.5b; P-E3.5c; P-E3.6; P-E3b.1 (1%); P-E3b.1 (5%); P-E3b.2 |
| C05 | Wrong tag IDs: tag maps, clean reference + main collapse example | flights/fl_E3_maps.png (walkthrough wt_16m_E3_maps.png) | bags T_A_r1 (ground truth); tier1 run dirs; tier1/scores/E3a_T_A_r1_0.01_s0.json | 6/6 | none (descriptive: one run per panel, not the 9-run H-E3.1 population) |
| C06 | Wrong tag IDs: tag maps, appendix (two more runs) | flights/fl_E3_maps_app.png (walkthrough wt_A2_E3_maps_app.png) | bags T_A_r2, T_A_r3 (ground truth); tier1 run dirs; tier1/scores/E3a_T_A_r3_0.05_s0.json, E3b_T_A_r2_0.05_s1.json | 6/6 | none (descriptive, as C05) |
| C07 | A UKF with landmark states against the FGO | walkthrough extra/ex_E5_ukf_landmarks.png (p18); summary page 18 (same data) | tier1/scores/e5_verdicts.json, e5_T_A_r{1,2,3}.json | 23/23 | H-E5.1; S-E5.5; S-E5.6 |

Notes for the coordinator:
- C02 and C03 share one dataset (the per-run outcome of Extension E3); C02 is the chart, C03 the table candidate, as the brief asks for both.
- C04 reproduces the same rows as Table A.4's Extension E3 section (already in docs/thesis/figures_thesis/ as part of TA_verdicts), but is built anyway because the brief names "the registered verdicts (summary page 15 / walkthrough A1)" as its own candidate; flagged in case the coordinator judges it redundant with Table A.4.
- C03 and C04 are markdown table candidates, not charts (per the brief, "verdicts belong in tables, not on figures"): C03_table.md and C04_table.md sit beside this index; C04_table.md legitimately carries PASS/FAIL words (same convention as Table A.4/A1-A3), but its caption file (captions/C04.md) stays banned-word-clean per D113, describing the table rather than restating its verdicts.
- C05/C06 need the cache from eval/figs_cand_c_extract.py (run once under heavy.py, deleted at the end of this run); regenerating these two candidates from scratch means re-running that extraction step first.
