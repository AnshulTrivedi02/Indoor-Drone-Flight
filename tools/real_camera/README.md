# Real-camera test pipeline (real-flight plan, tooling item 3)

Test the FROZEN heading program on real images before any flight. Nothing here changes the method or its parameters.

1. **Calibrate the lens:** record 20–40 s of a printed chessboard (e.g. 9×6 inner corners, 25 mm squares), moved to
   fill the image at several tilts. Then
   `python3 tools/real_camera/calibrate.py chess.mp4 --cols 9 --rows 6 --square-mm 25 --out calib.json`
   (add `--fisheye` for wide lenses). Aim for an RMS below 0.5 px.
2. **Run the heading program on a recording:**
   `python3 tools/real_camera/run_heading_video.py corridor.mp4 --calib calib.json --overlay overlay.mp4 --out run.csv`.
   - Each frame is undistorted and resampled onto the frozen simulated camera (640×480, fx 554.38, a 60° horizontal
     FOV), so the program sees the geometry it was calibrated for.
   - The coverage printed is the share of the frozen view that real pixels fill.
3. **Known-angle (table) test:** rotate the camera through known yaw angles (a turntable, or a protractor-marked board),
   holding each angle for a few seconds. Note `t_start_s,t_end_s,yaw_deg` per hold in a CSV (yaw positive = nose LEFT),
   and pass it with `--truth holds.csv`.
   - It reports availability, the residual bias after one constant offset, robust noise and outliers.
   - These are compared, as a diagnostic, with Phase 3's validation bars.
4. **A real VALIDATION needs its own pre-registration** (real-flight plan, question 6).

**Self-tests (no camera):**
- `selftest_calibration.py`: synthetic distorted chessboards. It checks the recovered intrinsics and distortion, and
  that lines come out straight in the frozen frame. Passed: fx 0.15%, k1 0.0012, line deviation 0.024 px.
- The pipeline on a lossless PNG sequence of simulated frames (`fwdc_tex_r1`, frames 0–299, no `--calib`) reproduces
  Phase 3's frozen headings to 2.4 × 10⁻¹⁴°.
