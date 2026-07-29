# Simulation assets (vendored)

The thesis-custom Gazebo environment, version-controlled here so a single
`thesis_ws` commit pins the sim configuration used for a trial (`git_commit` in
each trial's `metadata.yaml`). All files are text/small (~200 KB).

## Contents

- `worlds/` — the five worlds the harness flies: `corridor_{textured,blank,transition}.sdf`
  (the degraded-sensing dataset), `iris_runway.sdf`, `iris_textured.sdf`.
- `models/` — the self-contained custom models the worlds include:
  `textured_ground_visual`, `blank_ground_visual`, `ground_collision`,
  `corridor_wall`, and `textured_ground` (holds the 70 KB `checker.png`).
- `reference/iris_with_standoffs.model.{sdf,config}` — the thesis iris sensor
  config (downward camera + gpu_lidar + standoffs), tracked for the record /
  diff. **Not on the resource path** — the running iris comes from
  `~/ardupilot_gazebo` because it carries 22 MB of upstream meshes (see below).

## How it is wired

`run_trial.sh` and `start_sim.sh` set:

    GZ_SIM_RESOURCE_PATH = $HOME/thesis_ws/sim/models   # vendored — wins
                           : $HOME/ardupilot_gazebo/models
                           : $HOME/ardupilot_gazebo/worlds

and load the world by absolute path from `sim/worlds/`. So the vendored worlds
and floor/wall models are what actually run; `model://iris_with_ardupilot` (→
`iris_with_standoffs`, meshes) and `model://runway` resolve from
`~/ardupilot_gazebo`.

## The upstream dependency (meshes, plugin)

`~/ardupilot_gazebo` is a clone of `https://github.com/ArduPilot/ardupilot_gazebo`.
It supplies the iris/runway meshes and the ArduPilotPlugin (`build/`). The
thesis changes committed there are: `d1eaad3` (iris downward gpu_lidar/camera),
`e0359c2` (corridor worlds), `81e6b10` (visual-only floor tiles + ground
collision) — the world/model parts are mirrored here; the iris part is in
`reference/`.

**To reproduce on a fresh machine:** clone `ardupilot_gazebo`, apply the iris
sensor config from `reference/iris_with_standoffs.model.sdf`, build its plugin.
The vendored worlds/models here then override the corridor environment.
