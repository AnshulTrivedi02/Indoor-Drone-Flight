# B08. Experiment 5S: outcome of each safety check, the final run of each test

| what was done in flight | attitude | 'position lost' declared in time | landed safely | overall |
|---|---|---|---|---|
| UKF: forced to report its output invalid | PASS | PASS (0.00 s; limit 0.10 s) | PASS | PASS |
| UKF: all its position inputs cut off | PASS | FAIL (5.69 s; limit 5.50 s) | PASS | FAIL (as worded) |
| FGO: program stopped | PASS | PASS (0.60 s; limit 0.75 s) | PASS | PASS |
| FGO: program stopped, safety monitor watching it | PASS | PASS (0.62 s; limit 0.75 s) | PASS | PASS |

Experiment 5S (safety tests: the flying estimator is deliberately broken mid-flight): the final build's run of each test (the final UKF port's re-test, the FGO corrected-priors node's re-test). Attitude within 3 degrees (roll/pitch) and 5 degrees (yaw); 'position lost' declared within the limit shown, seconds; landing within 1.5 m of where the failure happened with no safety-watcher breach. The UKF forced-invalid test's limit is shown as the registered 0.10 s, not the 0.75 s its own score file records (a scorer artefact: that file was re-run with the FGO bound; both final-port delays are 0.00 s, so the outcome is the same either way, Table 7.2/T7 footnote). EKF3 (ArduPilot's standard filter) has no such breakage path, so it is not in this table (it is reference-only in Table 7.2/T7).

Verdicts: Table A.4, rows S-A (UKF forced-invalid test, final UKF port, re-test); S-A (UKF node-kill test, final UKF port, re-test); S-A (FGO forced-invalid test, corrected-priors node, re-test); S-A (FGO node-kill test, corrected-priors node, re-test).
