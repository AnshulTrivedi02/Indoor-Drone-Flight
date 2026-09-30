# Plan to the freezes (written Wed 30 Sep 2026, evening)

Deadlines (user ruling): **FGO closed-loop flights done by Fri 9 Oct**; simulation freeze **Fri 16 Oct**;
experiment freeze **Fri 23 Oct**.

## Critical path: the FGO closed-loop flights (by Fri 9 Oct)

| when | work | output |
|---|---|---|
| Thu 1 Oct | Half-speed world copies (`real_time_factor` 0.5 only). **`VISO_DELAY_MS` re-measured at half speed** by the original rule: ground test run 1 with the placeholder delay, then run 2 to verify. The FGO backend starts: A1 (`EKFType::FGO`, `AP_AHRS_FGO`, switch arms). | the new `VISO_DELAY_MS`; the A1 build |
| Fri 2 Oct | A2: the FGO state input route (its own, not `ODOMETRY`), logged for Replay. A3: the in-ArduPilot output predictor. **Evening/overnight: re-fly EKF3 and UKF at half speed** (a ×1 and b ×3 each = 8 flights, ~13 min each wall), unattended, with the stop rules. | half-speed EKF3/UKF sets |
| Sat 3 – Sun 4 Oct | A4: validity and health. **FGO heading input in the node** (new, see risk R1). Pre-register the FGO gates and bands. | FGO backend complete |
| Mon 5 Oct | FGO gates: backend equivalence to the offline FGO (pre-registered bands); validity signal; predictor check (Replay/logged input). | gate results |
| Tue 6 Oct | FGO shadow run (half speed, EKF3 flying); ground test; written predictions. | shadow + ground test |
| Wed 7 Oct | **FGO no-heading ×1**; FGO with-heading ×3 (can run overnight). | FGO sets |
| Thu 8 – Fri 9 Oct | Buffer for one failed gate or re-fly; scoring and write-up. | FGO closed loop DONE |

## In parallel: offline tests (existing recordings only, modest CPU, pre-registered first)

| when | test |
|---|---|
| Thu 1 Oct | Pre-register all four. The FGO-vs-UKF with-heading comparison on post-D15 data: the values already exist from the D15 re-run (Phase 4 heading arms), so report and tabulate them. |
| Fri 2 – Tue 6 Oct | **F3** (large initial yaw error): first the EKF3-in-Replay feasibility check, then 4 errors × arms × fwdc tex r1–r3. **F2** (intermittent heading): mask pattern, 3 arms (UKF, live FGO, long-window/batch FGO). |
| Wed 7 – Mon 12 Oct | **F1** (robust heading weighting): Huber/Cauchy chosen on `p1c_*` only, then the test worlds. |
| by Wed 14 Oct | All F-tests reported. |

Offline runs use `nice -n 15`, at most 2 parallel jobs while flights are running, and none at all during
the timing-sensitive heading-delay measurement.

## Risks, flagged now

- **R1 (new work, threatens 9 Oct by ~1 day).** The live FGO node has **no camera-heading input**; only
  ArduPilot receives the heading (`ODOMETRY`). For the with-heading FGO set, the node must receive the
  same headings, pass the same quality gate (`VISO_QUAL_MIN` 50) and clamp, and apply them at the same
  trust (5°, 3σ gate, the D17 principle). Estimate 0.5–1 day. It is not in the 4.5–5 day D12 estimate.
  - The FGO fuses each heading at its capture stamp (its factor-graph design), while EKF3/UKF use
    TS − `VISO_DELAY_MS`. **Proposed:** keep the capture stamp as the FGO's design and state it.
- **R2.** The D15 node core's take-off step time has not been measured live. If half speed does not
  remove the backlog, the shadow run shows it before any FGO flight. The fallback is decided then (a
  ruling).
- **R3.** 20+ half-speed flights at ~13 min wall each is ~5 h of flight time before the 16 Oct freeze.
  That is fine if run unattended overnight.
- **R4.** If an FGO gate fails, 9 Oct has only ~1.5 days of buffer. Any failure is flagged the same day.
