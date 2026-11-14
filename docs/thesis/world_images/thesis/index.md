# Thesis world figures and onboard frames (reader-facing set)

This folder holds the reader-facing replacement for the earlier, larger per-world figure set
(`docs/thesis/world_images/schematics/` and `docs/thesis/world_images/onboard/`, which stay where they are as
source material and are not deleted). It changes no world file, trial data or result: everything here is drawn from
already-existing files, read only.

Style: 160 mm wide, vector PDF plus PNG, the same colour palette and fonts as the rest of the thesis figure set
(`eval/thesis_style.py`). No figure carries an in-figure title; each has a one-line caption file in
`captions/<file>.md`.

## Schematics (`sim/tools/thesis_world_figs.py`)

Four drawings, each built directly from the geometry in the relevant world file and flight profile (not retyped by
hand), with every drawn number checked in the generator against an independent reading of its source before the
figure is produced.

| file | shows |
|---|---|
| `corridor_family.png` / `.pdf` | The 20 m by 160 m corridor: the textured and blank floor conditions and the boundary between them, the two wall finishes, the roof (present in one version only), the spawn point and the planned straight flight line. One drawing stands in for all of the corridor variants; the key explains which parts vary. |
| `room_tags_lap.png` / `.pdf` | The room used for the known-tag flights: its 8 floor tags with their ids, the 6 m square lap path with direction arrows, the spawn point, and a scale bar. |
| `room_tags_wall_tag.png` / `.pdf` | The same room with a wall tag added and the hold point in front of it marked, including the small side-to-side steps flown there. The occluder panel and the safety-monitor boundary used in some flights are left out for clarity. |
| `outdoor_to_indoor.png` / `.pdf` | The outdoor-to-indoor flight: the building entrance, the point where satellite positioning switches off and on (the GNSS gate, which coincides with the entrance), the out and back legs, and a scale bar. |

## Onboard frames (`sim/tools/thesis_frames.py`, `sim/tools/thesis_frames_panel.py`)

Read from the stored flight recordings only, through the project's one-bag-at-a-time read tool. Frames carry no
added text at all. A separate vanishing-point variant exists for each forward camera frame, with only the marker
drawn (no text); see `frames.json` for the exact frame each one came from and the measurement values drawn on it.
The marker is the already-computed heading measurement for that exact frame, taken from the stored measurement
output and matched to the frame by its timestamp; it is not recomputed here.

| file | shows |
|---|---|
| `forward_camera_panel.png` / `.pdf` | Three forward camera frames at the same position along the corridor, one figure with panels (a) to (c): line-textured walls, plain walls over a checkerboard floor, and plain walls over a blank floor. |
| `forward_line_walls_raw.png`, `forward_plain_walls_checker_raw.png`, `forward_plain_walls_blank_raw.png` | The same three frames on their own, exactly as read from the camera. |
| `forward_line_walls_vp.png`, `forward_plain_walls_checker_vp.png`, `forward_plain_walls_blank_vp.png` | The matching vanishing-point variant for each of the three frames above. |
| `downward_checker_tag.png` | Downward camera view over the checkerboard floor with a floor tag in view, during level flight, read directly from the camera. |

These cover the frames the brief asked for (the three-panel forward comparison and one downward frame); the fuller
set of camera positions in the earlier `onboard/` folder (the end of the corridor, the texture transition, a hover
frame) was not regenerated here, to keep this pass inside its time box - say if any of those should be added in
the same no-overlay style.

**No frame over a blank floor exists for the downward camera, in any stored flight.** Only six recorded flights carry
a downward camera image at all, and all six are over the checkerboard floor (names and exact durations in the
accompanying report, so a reader can ask for a different one of the six if the checkerboard frame already used is
not the preferred choice; none of the six is over a blank floor, so picking a different one would not add that
case):

| role | approximate duration |
|---|---|
| a general check flight over the room | 44 s |
| a tag-characterisation flight, 1.5 m altitude | 47 s |
| a tag-characterisation flight, 2.0 m altitude (the one used here) | 47 s |
| a tag-characterisation flight, 2.5 m altitude | 47 s |
| a tag-characterisation flight, 3.0 m altitude | 50 s |
| a second general check flight over the room | 77 s |

## Checks

- Every drawn coordinate in the four schematics is checked in `sim/tools/thesis_world_figs.py` against a second,
  independent reading of its source file (the world file's own wall, floor-tile, tag and building geometry, a
  profile file, or a flight script's own constant) before the figure is produced (54 checks, all passing). This
  includes deriving the textured/blank floor boundary from each tile's own texture reference rather than its
  position in the list, the room's wall positions and tag size from the room's own wall and tag models rather than
  a typed-in figure, the hold point from the same navigation-frame constant the flight code itself uses, and the
  entrance position from the building's own two south-wall pieces, which is then checked against the flight
  script's separate GNSS-gate constant (the two agree, which is the real content of the "entrance and gate
  coincide" claim).
- A few numbers remain declared display choices, not independent values to check: the corridor wall is drawn
  thicker than true scale so it is visible at this width, and the outdoor flight's out and back legs are drawn a
  little apart so both are visible; both are stated in the relevant caption.
- Each forward camera frame's header timestamp is checked against the stored measurement row it is paired with
  before either image is written.
- Every PDF in this folder is exactly 453.6 pt (160 mm) wide.
- `tools/check_numbers_frozen.py` passes unchanged; nothing under `docs/thesis/numbers.md`,
  `docs/thesis/summary/`, candidates, or any result file was touched.
