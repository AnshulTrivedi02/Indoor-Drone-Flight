# C04. Extension E3: every registered verdict (table candidate)

| registered test | what it checks | runs passing | verdict | note |
|---|---|---|---|---|
| H-E3.1 (primary) | 1%: live error below the stored no-loop-closure error | 0 of 9 | FAIL |  |
| H-E3.2 | 1%: the same for the hindsight error | 0 of 9 | FAIL |  |
| H-E3.3 | 1%: lap-5 live error at most 1.5 × lap 1 | 3 of 9 | FAIL |  |
| P-E3.4 | 1%: live error at most 2 × the clean live error | 0 of 9 | FAIL |  |
| P-E3.5a | 5%: as H-E3.1 | 0 of 9 | FAIL |  |
| P-E3.5b | 5%: as H-E3.2 | 0 of 9 | FAIL |  |
| P-E3.5c | 5%: as H-E3.3 | 9 of 9 | PASS |  |
| P-E3.6 | per flight: error does not fall as the rate rises | 0 of 3 | FAIL |  |
| P-E3b.1 (1%, robust) | 1%: robust error at most 1.10 × the plain FGO's | 9 of 9 | PASS | 6 of 9 are SATISFIED, flagged: the matched arm (a) run diverged, so no ratio exists |
| P-E3b.1 (5%, robust) | 5%: robust error at most 1.10 × the plain FGO's | 9 of 9 | PASS |  |
| P-E3b.2 (robust) | no wrong IDs: robust within ±10% of the clean error | 3 of 3 | PASS |  |

Pass or fail of each test, counted over the runs (flights for P-E3.6); 1% / 5% = share of tag sightings given a wrong ID; a diverged run counts as not met. Source: docs/thesis/tier1/scores/E3_verdicts.json (criteria_a, criteria_b). Primary: H-E3.1. This table reproduces the same rows as the Extension E3 section of the appendix verdict register (docs/thesis/tables/TA_verdicts.md), already in docs/thesis/figures_thesis/; it is included here because the brief names it explicitly as its own candidate -- flagged for the coordinator to rule on whether it duplicates that register or stands as a focused Extension-E3-only companion.
