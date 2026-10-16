# Handover 2026-10-16: world documentation images

**Stage:** documentation images of every simulation world (renders, schematics, onboard frames, combined PDF). This is documentation only. No result, world SDF, METHODOLOGY, numbers.md, `eval/` file or stored trial was changed.

**Deliverables** (`docs/thesis/world_images/`):
- **`index.md`** holds:
  - the inventory of the 24 SDFs, with status, the trials flown in each, and the figure, pack and numbers.md mapping;
  - the method;
  - the projection outcome;
  - the onboard coverage;
  - the per-shot camera record (pose, rpy, HFOV, resolution, projection, cutaway, top-view parallax).
- **`worlds_combined.pdf`**: 24 pages, one per world.
- **`renders/`**: 165 JPEGs plus `shots.json`.
- **`schematics/`**: 24 PNG/PDF pairs.
- **`onboard/`**: 10 PNGs plus `frames.json`.

**Generators** (`sim/tools/`), run in this order:
1. `render_world_docs.py`: needs FLIGHT_LOCK and nothing else simulating; about 5 minutes.
2. `world_schematics.py`.
3. `onboard_frames.py`: run with `~/venv-fwd/bin/python`. It decompresses bag copies to a scratch directory and deletes them afterwards.
4. `world_docs_pack.py`: writes the PDF and `shots_table.md`. `index.md` is the hand-written sections 1–5 with `shots_table.md` appended. If the shots change, re-append it.

**Key findings**
- **Orthographic is unavailable in this stack.** gz-sensors 8.2.2 ignores `<projection_type>`. A test render with and without it differed by 0.0 mean absolute pixels. The top views are therefore high-altitude narrow-FOV perspective, with the parallax stated per shot; it is 0.80 m worst case on the corridors. The corridor and O top views show no cast shadows, because the shadow distance is exceeded at 500–600 m.
- **Every world rendered**: 33 launches, 0 failures.
- **Downward camera images exist only in 6 room_tags bags.** No stored downward frames exist over a blank floor, the corridor checker, iris_textured or the runway. `p1c_img` was never flown.
- **The frozen per-frame VP output** is `<trial>/fwd_meas/meas_frozen.npz`, with keys t, u, v, psi, support, ...; row k is the k-th forward image.
  - The `fwdplainc_tex_r1` frame at y = 40 m shows the documented plain-wall-over-checker failure: it passes support but reads +5.62° against a GT yaw of +0.03°.
  - The y = 150 m frames are correctly "no measurement".
- **The inventory mapping** was compiled by a research subagent. The pack F-ids and numbers.md sections were spot-checked against the source files.

**Not done / possible follow-ups**
- Onboard frames were not extracted for the `fwdplainc_trans` bags, the closed-loop `cl_*` sets or the H bags. All of these have forward images.
- The no-ceiling `_fwd` worlds are rendered but have no onboard frames.

**State at hand-off:** no gz or SITL process is running, FLIGHT_LOCK has been released, and my scratch copies have been removed. Other sessions' files in the shared scratchpad were left alone. The work is committed on the worktree branch and not merged.
