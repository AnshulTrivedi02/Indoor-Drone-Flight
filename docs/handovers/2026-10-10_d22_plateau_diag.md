# Handover, 2026-10-10: D22 climb-plateau mechanism (image expansion + off-centre median)

## 0. D22 decay-test criterion, written down BEFORE the D22 prediction was computed (12:01 +11:00)

- **Model (one free parameter).** While the tracker keeps its feature set, the median feature's image x-offset u
  (px, from the principal point) evolves as
  du/dt = −(ż/h)·u + F·(c_rot·ω_x + c_lat·v_left/h), and the published flow is
  flow_x = [−(ż/h)·u]/F + c_rot·ω_x + c_lat·v_left/h.
  - h = GT z − 0.25 (camera height; confirmed by the analogue's fitted scale rate, §2), ż from GT,
    ω_x = `/attitude/angular_rates` x (FRD roll rate), v_left = −v_East from GT (vehicle heading north).
  - **Coefficients from an independent source, not fitted on D22:** c_lat = +1.004 and c_rot = +1.0
    (METHODOLOGY "FINDING — lateral optical-flow sign": flow_x = +1.004·v_left/h, and ArduPilot's convention
    raw_x = v_left/h + p). c_rot = 1.5 (the 17 Hz-tone value from the same finding) is reported as a sensitivity.
  - u0 is set from the FIRST plateau frame only (where ω_x ≈ 0 and v_East ≈ 0): u0 = −flow_x·F/(ż/h).
- **Window:** the climb plateau frames listed in real_flights_plan §7.1a (valid, GT z 1.07–1.6 m), starting at the
  re-detection frame, ending before the next feature-set jump (count drop of ≥ 5).
- **Pass:** residual RMS (observed − predicted) over the window, excluding the u0 frame, ≤ 0.10 rad/s on BOTH
  flights, AND at least 3× smaller than the null model (u ≡ 0: rotation + lateral terms only).
- A pass makes D22 *consistent with* the mechanism; it cannot *confirm* it (no downward images were recorded).

(Results follow below.)
