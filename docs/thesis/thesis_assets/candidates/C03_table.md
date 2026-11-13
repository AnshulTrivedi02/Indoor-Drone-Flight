# C03. Extension E3: outcome of every run (table candidate)

| condition | runs diverged | error of the finished runs, lowest to highest (m) | collapsed (descriptive) | without loop closure (m), for reference |
|---|---|---|---|---|
| 1% wrong IDs, FGO as built (plain) | 6 of 9 | 3.7161 to 3.8960 | 3 of 9 | 0.2625 to 0.3608 |
| 1% wrong IDs, robust FGO | 0 of 9 | 0.0496 to 1.4769 | 0 of 9 | 0.2625 to 0.3608 |
| 5% wrong IDs, FGO as built (plain) | 0 of 9 | 4.0395 to 4.2231 | 9 of 9 | 0.2625 to 0.3608 |
| 5% wrong IDs, robust FGO | 0 of 9 | 0.9776 to 4.1849 | 1 of 9 | 0.2625 to 0.3608 |
| no wrong IDs, robust FGO | 0 of 3 | 0.0484 to 0.0760 | 0 of 3 | 0.2625 to 0.3608 |

collapsed (descriptive, not a registered measure): the run finished with a wrong tag map (plain runs: map shrunk, consistent with a least-squares compromise; the one robust run: map folded, a wrong basin). Source: docs/thesis/tier1/scores/E3_verdicts.json (runs, references). Same data as candidate C02.
