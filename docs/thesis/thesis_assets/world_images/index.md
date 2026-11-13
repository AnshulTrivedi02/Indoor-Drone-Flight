# Simulation worlds: documentation images (2026-10-16)

This folder documents every Gazebo world used by a reported result, plus the superseded and record-only ones. It is documentation only: it changes no result, and nothing under `sim/worlds/`, `~/thesis_data` or `eval/results` was modified.

**Combined PDF:** `worlds_combined.pdf`. It has one page per world (24 pages). Each page carries the schematic, a top-down render, an angled render, the onboard frames (or a note that none exist) and a two-line caption.

| folder | what | generator |
|---|---|---|
| `renders/` | 165 headless Gazebo renders (JPEG q92), plus `shots.json` | `sim/tools/render_world_docs.py` |
| `schematics/` | top-down line drawings generated from the SDF (`.png` and `.pdf`) | `sim/tools/world_schematics.py` |
| `onboard/` | 10 onboard camera frames from stored bags, plus `frames.json` | `sim/tools/onboard_frames.py` (run with `~/venv-fwd/bin/python`) |
| `worlds_combined.pdf`, `shots_table.md` | the PDF and the per-shot camera table (the table is reproduced below) | `sim/tools/world_docs_pack.py` |

To reproduce, run the four scripts in the order of the table above. Only the render step simulates, so hold FLIGHT_LOCK for it, with nothing else running.

## 1. Inventory: every world and what used it

The world for each trial comes from the `world:` field of `~/thesis_data/trials/<t>/metadata.yaml`, or from the `sim/worlds/<w>.sdf` path in the trial's logs. This was cross-checked against `batches/*.conf`, `tools/run_*.sh`, `sim/tools/closed_loop_run.sh` and the figure indexes. The pack figure ids (F01–F15b) were checked against `final_results_pack_index.md`, and the numbers.md sections against that file's headings. "thesis Figure n.m / Table n.m / Table A.m" is the thesis numbering (by chapter) of `docs/thesis/thesis_vocabulary.md` §6, as printed in `docs/thesis/figures_thesis/index.md` (whose appendix mapping leads from each thesis number to the internal id and the output file; the tables are in `docs/thesis/tables/`). Experiment numbers and names follow the same vocabulary (§1).

| world | status | flown in it (trials/) | reported in |
|---|---|---|---|
| corridor_textured | CURRENT | `dsn_tex_r1–r10` (standard-sensor baseline); `ds_tex_r1–3` (compass on, reference); about 26 checks and passive-estimator runs | thesis Table 7.1 (Experiment 1A row), Table 4.1 (no-heading columns); pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18 |
| corridor_blank | CURRENT | `dsn_blank_r1–3`, `ds_blank_r1–3`, `corridor_blank_verify` | thesis Table 4.2, Table 7.2 (blank-floor validity), Table 7.1 blank-floor row; pack F06; numbers §6.2, §7 |
| corridor_transition | CURRENT | `dsn_trans_r1–3`, `ds_trans_r1–3`, `corridor_trans_verify` | numbers §1 (texture boundary y = 80 m by design, `sim/worlds/corridor_transition.sdf`: textured tile centred y = 70 m (l.175) and blank tile at y = 90 m (l.184), each 20 m), §6.2, §7, §11; no thesis figure or table |
| corridor_textured_fwdc | CURRENT (line-textured walls = upper bound) | `fwdc_tex_r1–3`, `p1c_fwdc_tex`, `f4_fwdc_tex_r1–6`, `tsx_off_tex`, real-time (RTF 1.0) closed loop `cl_*_tex`, `gt_heading_*`, `rgs_*`, `lfs_check_tex` | thesis Table 7.1 (Experiment 1B row, C1.a), Table 4.1, Table A.3; pack F01, F02, F04, F05, F07, F15a; numbers §6.3–§6.6, §8, §9, §15, §15.1, §15.2 |
| corridor_textured_fwdplainc | CURRENT (plain walls = featureless case) | `fwdplainc_tex_r1–3`, `p1c_fwdplainc_tex`, `f4_fwdplainc_tex_r1–6` | thesis Table 7.1 (Experiment 1B row), Table 4.1, Table A.3; pack F04, F07; numbers §6.4, §6.6, §8, §9, §15.1, §15.2 |
| corridor_transition_fwdc / _fwdplainc | CURRENT | `fwdc_trans_r1–3` and `fwdplainc_trans_r1–3`, each plus a `p1c_*_trans` | numbers §6.2 (transition +60 s), §8, §9, §11 (ceiling group); no thesis figure or table |
| corridor_blank_fwdc / _fwdplainc | CURRENT | `fwdc_blank_r1–3` and `fwdplainc_blank_r1–3`, each plus a `p1c_*_blank` | thesis Table 4.2 (11 blank flights = dsn 3 + p1c 2 + fwdc 3 + fwdplainc 3), Table 7.2, Table 7.1 blank-floor row (EKF3: 14 flights, + ds 3); numbers §6.2, §6.6, §8, §9 |
| corridor_textured_half_fwdc | CURRENT (every closed-loop result at half real-time, RTF 0.5; the simulator ran at half real time, the commanded flight speed was unchanged at 0.5 m/s) | 27 `cl_*_half` flights, plus FGO dev, shadow and ground-test runs and `gt_heading_half*` (44 in total) | thesis **Figure 4.1**, **Table 4.3**, Table 7.1 (Experiment 1C row), **Table A.1**; pack F08, F15a; numbers §15 |
| corridor_tson_fwdc | RECORD ONLY (time-sync A/B) | `tsx_on_tex` | numbers §6.5 note row |
| corridor_{textured,transition,blank}_fwd | SUPERSEDED (the forward camera sees the sky) | `fwd_*_r1–3`, `p1_fwd_*`, `p1diag_fwd_*` | numbers §1/§2 Phase-2 rows, §11 no-ceiling group, superseded block; not analysed |
| corridor_{textured,transition,blank}_fwdplain | SUPERSEDED; no dataset was flown | `p1plain_{tex,trans,blank}` | numbers §11 (`p1plain_trans`); METHODOLOGY only |
| room_tags | CURRENT (Experiments 2 and 3: known tags, loop closure) | `T_{A,B,C,D}_r1–3` (12 reported; Experiment 3 replays `T_A_r1–3` and is not a separate flight set), `tagchar_h15/20/25/30`, `tag_check*`, `room_check` | thesis **Figure 5.1** (Experiment 2), **Figure 5.2** (Experiment 3), Table 5.2 (Experiment 2 rows), Table 7.1 (Experiment 2 and 3 rows), Table A.3; pack F09, F10, F12, F13; numbers §16.1, §16.3 |
| room_wall_tag | CURRENT results; no new flights (`closed_loop_run.sh` refuses this world) | `H_s0a`, `H_s0b`, `H_s1_r1–3`, `H_gt_*`, `H_wtest_*` | thesis **Table 6.1** (EKF3-flying hold set, near spawn), Table A.2; pack F14, F15b; numbers §17 |
| room_wall_tag_far | CURRENT (Experiment 5 re-flies: far-spawn EKF3, UKF- and FGO-flying hold sets; 5S safety tests) | `H_s1far_r1/r2/r3b`, `H_s2(_v2)_r1–3`, `H_s3(_v2)_r1–3`, `H_gt_*_far`, about 21 `H_safety_*` | thesis Table 6.1, Table 7.2 (5S safety tests), Table A.2, Table 7.1 Experiment 5 row; pack F14, F15b; numbers §15 safety rows, §17, §17.1, §17.2 |
| room_wall_tag_far_occ | RECORD ONLY (in-flight-anchor check) | `H_ifa_ekf3` (FAIL: room-box breach; the UKF and FGO runs were skipped by ruling) | METHODOLOGY only |
| outdoor_indoor | CURRENT (Experiment 4, outdoor–indoor) | `O_r1`, `O_r2`, `O_r3b` reported; `O_r3_IMUGAP` excluded; `o_check1` | thesis **Figure 5.3**, **Table 5.1**, Table 7.2 (return jump), Table 5.2 (Experiment 4 rows), Table 7.1 Experiment 4 row; pack F11; numbers §16.2, §18 |
| iris_textured | RECORD ONLY | 13: Stage B/C, `smoke_test`, `ekf3_diag_60s`, `imu_rate_verify`, `imu_verify2`, `nomag_test_long`, `sweep_v*`; also the watcher SITL bench (`~/thesis_data/wbench`) | numbers §2 IMU-rate rows and remaining flag 2; the Stage B/C ATE is VOID |
| iris_runway | RECORD ONLY | `stage_c_blank` | the Stage C blank ATE is VOID; no current row |

**24 SDFs in total:**
- 16 have current results or their underlying data: the 3 dsn corridors, 6 fwdc/fwdplainc, the half real-time (RTF 0.5) world, room_tags, room_wall_tag, room_wall_tag_far, outdoor_indoor, and iris_textured for two numbers.md rows.
- 3 are record-only: tson, far_occ and iris_runway.
- 6 are superseded: `_fwd` and `_fwdplain`.

No other world appears in any trial metadata. Two configurations were never flown: `batches/phase2b_fwdplain.conf` and `tools/run_p1c_img.sh` (`p1c_img`).

**What differs between related worlds** (checked by diffing the SDFs):
- `corridor_textured_half_fwdc` differs from `corridor_textured_fwdc` only in its world name and `<real_time_factor>` (0.5 against 1.0).
- `corridor_tson_fwdc` differs from it only in the drone model, `iris_fwd_ts`.
- `room_wall_tag_far` differs from `room_wall_tag` only in the spawn, (0, 1.1) against (0, 3.5).
- `room_wall_tag_far_occ` differs from `room_wall_tag_far` only in the occluder's start height: z = 1.5 m, in front of the tag, against z = −5 m, parked.

So the renders of each pair are visually identical apart from those details.

**Vendoring caveat.** Trials before 2026-07-29 ran the un-vendored copies in `~/ardupilot_gazebo/worlds`. That covers iris_textured, iris_runway (Stage A–C, the sweep) and the earliest corridor checks. The renders and schematics here show the vendored SDFs in `sim/worlds/`.

## 2. Renders (`renders/`)

**Method.**
- `render_world_docs.py` writes a copy of each world SDF to a scratch directory and adds temporary static camera models, one per shot.
- It runs the copy server-only with `gz sim -s -r`, the way `run_trial.sh` runs flights, under FLIGHT_LOCK and with one gz instance at a time.
- It takes each camera's 4th frame (sim t = 2 s) from its gz-transport topic. This needs an in-process subscriber, because a camera with no subscriber is never rendered.
- The world's own `<scene>` and directional sun are untouched, so the lighting is the flights' lighting.
- Nothing in `sim/worlds/` is modified. The scratch copies were deleted afterwards.

**Shots per world.**
- `top`: the whole world from above.
- `angled`: a three-quarter overview.
- `spawn`: the drone at its spawn.
- Close-ups:
  - corridors: `interior` (flight height, looking +y);
  - transition: `boundary` (the y = 80 m texture boundary);
  - forward-camera worlds: `wall` (the wall surface, line-textured or plain) and `endwall` (the end wall at y = 165 m);
  - ceiling worlds: `ceiling` (looking up at the slab);
  - rooms: `top_room`, `tags`, and `tag2` (floor tag 2);
  - tag-hold worlds (Experiment 5): `walltag` (wall tag id 10, with the occluder in front of it in `_far_occ`);
  - outdoor_indoor (Experiment 4): `entrance` and `indoor`;
  - iris_runway: `top_wide`.

**Cutaways.** In ceiling worlds the plain ceiling slab covers the whole corridor, so `top` and `angled_cutaway` are rendered from a second copy with the visual-only `corridor_ceiling` removed. `top_roof` and `angled` show the world as built. In outdoor_indoor, `top` is as built (roof on) and `top_cutaway` has `bldg_roof` removed. Every cutaway is marked in the table below. Both the ceiling and the roof are visual-only and cast no shadow, so removing them does not change the floor lighting.

**Projection outcome: orthographic is NOT available; the top views are high-altitude, narrow-FOV perspective (near-orthographic).** This was checked two ways:
1. sdformat 14.9 parses `<projection_type>orthographic</projection_type>`, but `libgz-sensors8-camera.so.8.2.2` (gz-sensors 8.2.2) references no `sdf::Camera::ProjectionType` symbol.
2. A tested render settled it. In `room_tags`, two cameras with the same pose, one plain and one with `<projection_type>orthographic</projection_type>`, gave images whose mean absolute pixel difference was **0.0**. The element is silently ignored.

SDF also requires `horizontal_fov ≥ 0.1 rad`, so the top views use the lowest altitude that keeps HFOV ≥ 0.12 rad:
- 600 m for the corridors;
- 500 m for outdoor_indoor;
- 92–150 m for the rooms;
- 300 m and 3000 m for the iris worlds.

The residual parallax is the worst-case horizontal shift of the tallest object's top edge, h·r/altitude, and is given per shot. For example, the 5 m corridor walls at the far end shift by 0.80 m at 600 m. Because these altitudes exceed the directional light's shadow distance, the corridor and outdoor_indoor top views show no cast shadows; the room top views (≤ 150 m) do. The angled and close-up views show the flights' shadows.

**Render failures: none.** Every world and every shot rendered: 24 worlds, 33 server launches (9 cutaway copies), 165 shots. Each launch took 7–28 s.

## 3. Schematics (`schematics/`)

**Method.**
- `world_schematics.py` parses the world SDF and every included model. It resolves models from `sim/models` first, then `~/ardupilot_gazebo/models`, the same order as `GZ_SIM_RESOURCE_PATH`.
- It places each `<visual>` (box, plane, or the bounding box of a COLLADA mesh) in 3-D through the full pose chain and projects it onto the floor.
- **No dimension is typed in.** That covers the walls, floor tiles and their texture (checker or blank, from the albedo map), the ceiling and roof, the tags with their ids (from the model name) and yaw, the wall tag, the occluder and the spawn.
- The checker square size, 0.3125 m, is computed from `checker.png`: 64 squares across a 20 m tile.

**Routes come from the mission and profile files, not from flown data:**
- **Corridor cruise:** each world's line in `batches/*.conf`, as velocity × duration north from the spawn (0.5 m/s × 300 s = 150 m at 2 m). The half real-time (RTF 0.5) world's route comes from `closed_loop_run.sh`. The measured travel is 151 m (numbers §1).
- **Experiments 2 and 3 (known tags, loop closure):** `LAPS=5,6,0.5` and the conf line in `tools/run_expT.sh`: 5 laps of a 6 m square, N–E–S–W from the spawn over tag 0, at 2.0 m.
- **Tag check flights (`tagchar_*`):** `batches/tagchar.conf`.
- **Experiment 4 (outdoor–indoor):** `OUTBACK=15,1.5,50,0.5,20` in `tools/run_expO.sh`, with the GNSS gate at N = 20 m.
- **Experiment 5 (tag hold):** `batches/expH/*.json`, converted from the tag frame W to world coordinates with N_W = world y − 4.998 and E_W = world x. The 4.998 is `WALL_P` in `tag_bridge_fwd.py`. `s0a` and `s0b` are flown in the world frame.
- **Experiment 5 safety-watcher room box:** the `--box` in `closed_loop_run.sh`.
- **iris worlds:** no mission file exists, so only the spawn is drawn.

**Drawing offsets (not geometry).** The outdoor_indoor out and back legs are drawn 0.6 m either side of x = 0, and the tag-check-flight line (`tagchar_*`) 0.25 m west of the lap line, so the overlapping legs stay visible. They were all flown at the spawn's x.

**Colours (Okabe–Ito).** The estimator colours, EKF3 #0072B2, UKF #009E73 and FGO #D55E00, are deliberately not used because they carry fixed meanings in the thesis figures.

| colour | used for |
|---|---|
| #E69F00 orange | planned route |
| #CC79A7 reddish purple | AprilTags (floor and wall) |
| #56B4E9 sky blue, dashed | ceiling and roof slab outline |
| #999999 grey | references: the transition boundary, the GNSS gate, the watcher room box, the occluder (the thesis's truth/reference grey) |
| #5e5e5e | walls; hatched means a textured wall (the thesis figures' wall grey) |
| #111111 | spawn |
| light grey with a `++` hatch | checker floor |
| white | blank floor |

## 4. Onboard views (`onboard/`): from existing bags only

**Method.**
- `onboard_frames.py` decompresses a COPY of each packed bag (`bag_0.db3.zst`) to scratch, reads it with rosbags, and deletes the copy afterwards.
- It reads nothing from `~/thesis_data` except the bags, `fwd_meas/meas_frozen.npz` and `fwd_meas/gt_eval_only.npz`. It writes nothing there.
- Each frame's trial, time, ground truth and VP values are in `frames.json`.

**Forward camera (640×480 mono8).**
- Each frame is the one nearest the requested ground-truth y.
- The vanishing point drawn on it is the **frozen heading-measurement output (Experiment 1B) for that exact frame**: row k of `meas_frozen.npz` is the k-th forward image, and the script asserts that the header stamp matches. Nothing is recomputed.
- A filled orange marker (#E69F00) is a valid heading measurement (support ≥ `s_min` = 200, from `eval/results/fwd_calibration.json` "frozen").
- A hollow sky-blue marker (#56B4E9) is "no measurement".

| frame | world / walls / floor | frozen VP |
|---|---|---|
| `fwdc_tex_r1__fwd_y040.png` | fwdc, line-textured walls, checker | valid: u 327.0 px, support 1609, heading +0.72° (GT yaw +0.03°) |
| `fwdc_tex_r1__fwd_y150.png` | fwdc, near the end wall | **no measurement** (support 166 < 200): the intended "no measurement near the end wall" behaviour |
| `fwdplainc_tex_r1__fwd_y040.png` | fwdplainc, plain walls, checker | passes support (492) but heading **+5.62° against GT +0.03°**: the documented heading-measurement validation (H1.2) failure for plain walls over a checker floor (the overlay shows the frozen output, which is wrong here) |
| `fwdplainc_tex_r1__fwd_y150.png` | fwdplainc, near the end wall | **no measurement** (support 137 < 200), intended |
| `fwdc_trans_r1__fwd_y080.png` | fwdc, at the transition boundary | valid: heading +0.02°, support 1814 |
| `fwdc_blank_r1__fwd_y040.png` | fwdc, line-textured walls, blank floor | valid: heading −0.01°, support 2140 |
| `fwdplainc_blank_r1__fwd_y040.png` | fwdplainc, plain walls, blank floor | valid: heading −0.01°, support 975 (validated case) |

**Downward camera (640×480 rgb8).** Only **6** stored bags carry `/downward_camera/image`, and all of them are `room_tags` flights: `tagchar_h15/20/25/30`, `room_check` and `tag_check2img` (verified from every bag's metadata). The frames here are chosen by ground truth in the same bag:
- hover: airborne with horizontal speed < 0.05 m/s;
- cruise: 0.5 ± 0.05 m/s.

| frame | floor | state |
|---|---|---|
| `tagchar_h20__down_hover.png` | checker + floor tag (room_tags) | hover, z 2.26 m (base_link) |
| `tagchar_h20__down_cruise.png` | checker + tag 0 | cruise 0.50 m/s, z 2.26 m |
| `tagchar_h30__down_cruise.png` | checker + tag 0 | cruise 0.50 m/s, z 3.28 m |

**Onboard coverage, stated explicitly.**
- **Checker floor, downward: available,** but only in the room (`room_tags`, which uses the same `checker.png` texture and the same 20 m tile as the corridors).
- **Blank floor, downward: NO stored frames.** No bag over any blank floor recorded the downward camera.
- **Corridor checker floor, downward: NO stored frames.** The dsn, fwdc and fwdplainc bags record flow, not images.
- **iris_textured and iris_runway, downward: NO stored frames.**
- **Not used:** the `p1c_img` calibration flights that would have provided these were PARKED and never flown (`tools/run_p1c_img.sh`; no `p1c_img_*` trial exists).
- **Not used:** the downward sheets in `plots/fwd_camera/ceiling_render_check/` are static live renders (`sim/tools/grab_frames.py`), not bag frames. They are excluded here.
- **Line-textured walls, forward:** available (fwdc tex, trans and blank).
- **Plain walls, forward:** available (fwdplainc tex and blank).
- **Near the end wall, forward:** available for both wall types (y = 150 m).
- **Bags exist but no frames were extracted:** `fwdplainc_trans_*`, the half real-time (RTF 0.5) and real-time (RTF 1.0) closed-loop `cl_*` sets, and the Experiment 5 flights (`H_*` bags carry `/forward_camera/image`).
- **Superseded no-ceiling worlds:** no frames extracted.

## 5. Per-shot camera record (generated: `shots_table.md`)

Camera pose convention: SDF `<pose>` x y z roll pitch yaw. The camera looks along its +x axis, and positive pitch looks down. Top views use pitch = π/2: yaw π/2 puts world +x to the right and +y up (the rooms and iris worlds); yaw π puts world +y to the right and +x down (the corridors and O). Near/far clip 0.05 m / (altitude + 50 m) for top views, 4000 m otherwise. Image format R8G8B8, saved as JPEG q92.

| world | shot | what | eye (x, y, z) m | rpy (rad) | HFOV deg | px | projection | cutaway | top-view parallax |
|---|---|---|---|---|---|---|---|---|---|
| corridor_textured | `corridor_textured__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_textured | `corridor_textured__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured | `corridor_textured__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured | `corridor_textured__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank | `corridor_blank__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_blank | `corridor_blank__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank | `corridor_blank__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank | `corridor_blank__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition | `corridor_transition__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_transition | `corridor_transition__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition | `corridor_transition__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition | `corridor_transition__boundary.jpg` | the textured/blank floor boundary at y = 80 m | -7.0, 70.0, 4.5 | 0.000, 0.313, 1.043 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition | `corridor_transition__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_fwdc | `corridor_textured_fwdc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdc | `corridor_textured_fwdc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_fwdc | `corridor_textured_fwdc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_fwdplainc | `corridor_textured_fwdplainc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_transition_fwdc | `corridor_transition_fwdc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__boundary.jpg` | the textured/blank floor boundary at y = 80 m | -7.0, 70.0, 4.5 | 0.000, 0.313, 1.043 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdc | `corridor_transition_fwdc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_transition_fwdc | `corridor_transition_fwdc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__boundary.jpg` | the textured/blank floor boundary at y = 80 m | -7.0, 70.0, 4.5 | 0.000, 0.313, 1.043 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_transition_fwdplainc | `corridor_transition_fwdplainc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_blank_fwdc | `corridor_blank_fwdc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdc | `corridor_blank_fwdc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_blank_fwdc | `corridor_blank_fwdc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_blank_fwdplainc | `corridor_blank_fwdplainc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_textured_half_fwdc | `corridor_textured_half_fwdc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__top_roof.jpg` | whole world from above, as built (the ceiling slab covers the corridor) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_tson_fwdc | `corridor_tson_fwdc__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__ceiling.jpg` | looking up at the ceiling slab (underside z = 5.0 m) from 1 m | -8.0, 30.0, 1.0 | 0.000, -0.218, 0.983 | 80.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_tson_fwdc | `corridor_tson_fwdc__top.jpg` | whole world from above (ceiling removed: cutaway) | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | yes | 0.81 m (h 5.1 m at r 96 m, alt 600 m) |
| corridor_tson_fwdc | `corridor_tson_fwdc__angled_cutaway.jpg` | three-quarter overview with the ceiling removed (cutaway) | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | yes |  |
| corridor_textured_fwd | `corridor_textured_fwd__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_textured_fwd | `corridor_textured_fwd__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwd | `corridor_textured_fwd__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwd | `corridor_textured_fwd__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwd | `corridor_textured_fwd__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwd | `corridor_textured_fwd__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_transition_fwd | `corridor_transition_fwd__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__boundary.jpg` | the textured/blank floor boundary at y = 80 m | -7.0, 70.0, 4.5 | 0.000, 0.313, 1.043 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwd | `corridor_transition_fwd__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwd | `corridor_blank_fwd__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_blank_fwd | `corridor_blank_fwd__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwd | `corridor_blank_fwd__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwd | `corridor_blank_fwd__wall.jpg` | close-up of the east wall surface (line-textured) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwd | `corridor_blank_fwd__endwall.jpg` | approaching the end wall at y = 165 m (textured) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwd | `corridor_blank_fwd__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_textured_fwdplain | `corridor_textured_fwdplain__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__boundary.jpg` | the textured/blank floor boundary at y = 80 m | -7.0, 70.0, 4.5 | 0.000, 0.313, 1.043 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_transition_fwdplain | `corridor_transition_fwdplain__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__top.jpg` | whole world from above | 0.0, 72.5, 600.0 | 0.000, 1.571, 3.142 | 17.99 | 3200x400 | persp. (near-ortho) | no | 0.80 m (h 5.0 m at r 96 m, alt 600 m) |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__angled.jpg` | three-quarter overview from the south-west, above the spawn end | -30.0, -32.0, 24.0 | 0.000, 0.283, 1.199 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__interior.jpg` | inside the corridor at flight height (2 m) looking down the flight direction (+y) | 0.0, 2.0, 2.0 | 0.000, -0.000, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__wall.jpg` | close-up of the east wall surface (plain) | 3.0, 40.0, 2.0 | 0.000, -0.033, 0.709 | 70.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__endwall.jpg` | approaching the end wall at y = 165 m (plain) | 0.0, 140.0, 2.0 | 0.000, -0.000, 1.571 | 60.00 | 1600x900 | perspective | no |  |
| corridor_blank_fwdplain | `corridor_blank_fwdplain__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| room_tags | `room_tags__top.jpg` | whole world from above (the 20 x 20 m floor tile; room walls at |x|, |y| = 5.1 m) | 0.0, 0.0, 150.0 | 0.000, 1.571, 1.571 | 8.01 | 1600x1600 | persp. (near-ortho) | no | 0.30 m (h 3.0 m at r 15 m, alt 150 m) |
| room_tags | `room_tags__top_room.jpg` | the 10 x 10 m room from above (tags readable) | 0.0, 0.0, 91.6 | 0.000, 1.571, 1.571 | 6.88 | 1600x1600 | persp. (near-ortho) | no | 0.25 m (h 3.0 m at r 8 m, alt 92 m) |
| room_tags | `room_tags__angled.jpg` | three-quarter overview from the south-west | -8.5, -10.5, 11.0 | 0.000, 0.669, 0.913 | 60.00 | 1600x900 | perspective | no |  |
| room_tags | `room_tags__tags.jpg` | inside the room from above the south wall (5 m), all eight floor tags | 0.0, -4.9, 5.0 | 0.000, 0.738, 1.571 | 85.00 | 1600x900 | perspective | no |  |
| room_tags | `room_tags__tag2.jpg` | close-up of floor tag 2 at (3, 3), yaw -45 deg (0.5 m tile, 0.4 m black square) | 2.2, 1.6, 1.6 | 0.000, 0.782, 1.052 | 50.00 | 1600x900 | perspective | no |  |
| room_tags | `room_tags__spawn.jpg` | the drone at the spawn (-3, -3) over tag 0 | -4.6, -5.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag | `room_wall_tag__top.jpg` | whole world from above (the 20 x 20 m floor tile; room walls at |x|, |y| = 5.1 m) | 0.0, 0.0, 150.0 | 0.000, 1.571, 1.571 | 8.01 | 1600x1600 | persp. (near-ortho) | no | 0.30 m (h 3.0 m at r 15 m, alt 150 m) |
| room_wall_tag | `room_wall_tag__top_room.jpg` | the 10 x 10 m room from above (tags readable) | 0.0, 0.0, 91.6 | 0.000, 1.571, 1.571 | 6.88 | 1600x1600 | persp. (near-ortho) | no | 0.25 m (h 3.0 m at r 8 m, alt 92 m) |
| room_wall_tag | `room_wall_tag__angled.jpg` | three-quarter overview from the south-west | -8.5, -10.5, 11.0 | 0.000, 0.669, 0.913 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag | `room_wall_tag__tags.jpg` | inside the room from above the south wall (5 m), all eight floor tags | 0.0, -4.9, 5.0 | 0.000, 0.738, 1.571 | 85.00 | 1600x900 | perspective | no |  |
| room_wall_tag | `room_wall_tag__tag2.jpg` | close-up of floor tag 2 at (3, 3), yaw -45 deg (0.5 m tile, 0.4 m black square) | 2.2, 1.6, 1.6 | 0.000, 0.782, 1.052 | 50.00 | 1600x900 | perspective | no |  |
| room_wall_tag | `room_wall_tag__walltag.jpg` | wall tag id 10 on the north wall (0, 5.0, 1.5) seen from beside the spawn | 0.9, 2.9, 1.7 | 0.000, 0.087, 1.976 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag | `room_wall_tag__spawn.jpg` | the forward-camera drone at the spawn (0, 3.5), facing the wall tag | -1.6, 1.1, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far | `room_wall_tag_far__top.jpg` | whole world from above (the 20 x 20 m floor tile; room walls at |x|, |y| = 5.1 m) | 0.0, 0.0, 150.0 | 0.000, 1.571, 1.571 | 8.01 | 1600x1600 | persp. (near-ortho) | no | 0.30 m (h 3.0 m at r 15 m, alt 150 m) |
| room_wall_tag_far | `room_wall_tag_far__top_room.jpg` | the 10 x 10 m room from above (tags readable) | 0.0, 0.0, 91.6 | 0.000, 1.571, 1.571 | 6.88 | 1600x1600 | persp. (near-ortho) | no | 0.25 m (h 3.0 m at r 8 m, alt 92 m) |
| room_wall_tag_far | `room_wall_tag_far__angled.jpg` | three-quarter overview from the south-west | -8.5, -10.5, 11.0 | 0.000, 0.669, 0.913 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far | `room_wall_tag_far__tags.jpg` | inside the room from above the south wall (5 m), all eight floor tags | 0.0, -4.9, 5.0 | 0.000, 0.738, 1.571 | 85.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far | `room_wall_tag_far__tag2.jpg` | close-up of floor tag 2 at (3, 3), yaw -45 deg (0.5 m tile, 0.4 m black square) | 2.2, 1.6, 1.6 | 0.000, 0.782, 1.052 | 50.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far | `room_wall_tag_far__walltag.jpg` | wall tag id 10 on the north wall (0, 5.0, 1.5) seen from beside the spawn | 0.9, 0.5, 1.7 | 0.000, 0.044, 1.768 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far | `room_wall_tag_far__spawn.jpg` | the forward-camera drone at the spawn (0, 1.1), facing the wall tag | -1.6, -1.3, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__top.jpg` | whole world from above (the 20 x 20 m floor tile; room walls at |x|, |y| = 5.1 m) | 0.0, 0.0, 150.0 | 0.000, 1.571, 1.571 | 8.01 | 1600x1600 | persp. (near-ortho) | no | 0.30 m (h 3.0 m at r 15 m, alt 150 m) |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__top_room.jpg` | the 10 x 10 m room from above (tags readable) | 0.0, 0.0, 91.6 | 0.000, 1.571, 1.571 | 6.88 | 1600x1600 | persp. (near-ortho) | no | 0.25 m (h 3.0 m at r 8 m, alt 92 m) |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__angled.jpg` | three-quarter overview from the south-west | -8.5, -10.5, 11.0 | 0.000, 0.669, 0.913 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__tags.jpg` | inside the room from above the south wall (5 m), all eight floor tags | 0.0, -4.9, 5.0 | 0.000, 0.738, 1.571 | 85.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__tag2.jpg` | close-up of floor tag 2 at (3, 3), yaw -45 deg (0.5 m tile, 0.4 m black square) | 2.2, 1.6, 1.6 | 0.000, 0.782, 1.052 | 50.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__walltag.jpg` | wall tag id 10 on the north wall (0, 5.0, 1.5) seen from beside the spawn (occluder in front of it) | 0.9, 0.5, 1.7 | 0.000, 0.044, 1.768 | 60.00 | 1600x900 | perspective | no |  |
| room_wall_tag_far_occ | `room_wall_tag_far_occ__spawn.jpg` | the forward-camera drone at the spawn (0, 1.1), facing the wall tag | -1.6, -1.3, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| outdoor_indoor | `outdoor_indoor__top.jpg` | whole world from above, as built (roof on) | 0.0, 30.0, 500.0 | 0.000, 1.571, 3.142 | 11.87 | 2400x500 | persp. (near-ortho) | no | 0.33 m (h 3.1 m at r 53 m, alt 500 m) |
| outdoor_indoor | `outdoor_indoor__angled.jpg` | three-quarter overview from the south-west | -26.0, -32.0, 18.0 | 0.000, 0.262, 1.174 | 60.00 | 1600x900 | perspective | no |  |
| outdoor_indoor | `outdoor_indoor__entrance.jpg` | the 3 m entrance in the south wall (y = 20 m) seen from outside at flight height | 0.0, 9.0, 2.0 | 0.000, 0.045, 1.571 | 70.00 | 1600x900 | perspective | no |  |
| outdoor_indoor | `outdoor_indoor__indoor.jpg` | inside the building at flight height looking north (+y) | 0.0, 22.0, 2.0 | 0.000, 0.013, 1.571 | 80.00 | 1600x900 | perspective | no |  |
| outdoor_indoor | `outdoor_indoor__spawn.jpg` | the drone at the spawn (0, -15), facing +y | -1.6, -17.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| outdoor_indoor | `outdoor_indoor__top_cutaway.jpg` | whole world from above with the building roof removed (cutaway) | 0.0, 30.0, 500.0 | 0.000, 1.571, 3.142 | 11.87 | 2400x500 | persp. (near-ortho) | yes | 0.33 m (h 3.1 m at r 53 m, alt 500 m) |
| iris_textured | `iris_textured__top.jpg` | the area around the spawn from above (60 m across) | 0.0, 0.0, 300.0 | 0.000, 1.571, 1.571 | 11.42 | 1600x1600 | persp. (near-ortho) | no | 0.00 m (h 0.0 m at r 42 m, alt 300 m) |
| iris_textured | `iris_textured__angled.jpg` | three-quarter overview from the south-west | -15.0, -18.0, 10.0 | 0.000, 0.381, 0.927 | 65.00 | 1600x900 | perspective | no |  |
| iris_textured | `iris_textured__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
| iris_runway | `iris_runway__top.jpg` | the area around the spawn from above (60 m across) | 0.0, 0.0, 300.0 | 0.000, 1.571, 1.571 | 11.42 | 1600x1600 | persp. (near-ortho) | no | 0.00 m (h 0.0 m at r 42 m, alt 300 m) |
| iris_runway | `iris_runway__top_wide.jpg` | the whole runway from above (1600 m along y, left to right) | -29.0, 545.0, 3000.0 | 0.000, 1.571, 3.142 | 29.86 | 2400x600 | persp. (near-ortho) | no | 0.00 m (h 0.0 m at r 825 m, alt 3000 m) |
| iris_runway | `iris_runway__angled.jpg` | three-quarter overview from the south-west | -15.0, -18.0, 10.0 | 0.000, 0.381, 0.927 | 65.00 | 1600x900 | perspective | no |  |
| iris_runway | `iris_runway__spawn.jpg` | the drone at the spawn (0, 0, 0.195), facing +y | -1.6, -2.4, 1.4 | 0.000, 0.379, 0.983 | 60.00 | 1600x900 | perspective | no |  |
