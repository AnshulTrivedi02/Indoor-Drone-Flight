# Handover: Raw corridor errors, Stage 1 (D106/D107) — 2026-11-02

**Branch:** `raw-corridor`, created from `fwd-camera` at base commit `f09d56b`.
**Commits:** `393b794` (initial build), `19294e9` (advisor-review fixes — positional
citation checks, cross-source consistency, completeness, header-count checks).
**Scope:** documentation and offline re-scoring only. No flights, no estimator replays, no
simulation. All inputs read-only (stored TUM trajectory files under `~/thesis_data/trials/`
and stored result JSONs under `eval/results/`); no bags were read.

## What this did

Per the user's ruling (2026-11-02) and decisions D106/D107: for every offline Experiment 1
flight in scope, compute the raw (world-frame, **nothing fitted** — no rotation, translation
or scale alignment) 3D position error over the registered cruise window, next to the
already-registered evo -a (cruise) value, labelled DESCRIPTIVE. Registered fitted metrics and
verdicts are completely unchanged.

**Files added (all new; nothing existing was edited):**
- `eval/raw_corridor_errors.py` — computes everything, writes `eval/results/raw_corridor_errors.json`.
- `eval/gen_raw_corridor_numbers.py` — renders `docs/thesis/raw_corridor/raw_corridor_numbers.md`.
- `docs/thesis/raw_corridor/raw_corridor_numbers.md` — the numbers file (D107).
- `docs/thesis/raw_corridor/check_raw_corridor.py` — stdlib-only exact cross-check.
- `eval/results/raw_corridor_errors.json` — full-precision results + provenance.

`numbers.md`, `numbers_tier1.md`, every figure/table generator, `METHODOLOGY.md` and the
fact sheets are untouched (`git status` on `raw-corridor` shows only the five new files).

## Scope (D106), 154 cells

- `dsn_tex` r1–r10 × {EKF3, UKF, FGO} (r10 EKF3 only, IMU-gap rule) = 28 cells, from
  `rerun_dsn_evo.json` (r1–r3, blank, trans) + `dsn_extra_evo.json` (r4–r10).
- `dsn_blank` r1–r3, `dsn_trans` r1–r3 × {EKF3, UKF, FGO} = 18 cells, same two files.
- `fwdc` tex/trans/blank r1–r3 × {EKF3 baseline, UKF/FGO × baseline/heading/heading_yawrate}
  = 9 × 7 = 63 cells, from `phase4_fwdc_arms.json`.
- `fwdplainc` tex/trans/blank r1–r3 × {EKF3 baseline, UKF/FGO × baseline/heading}
  = 9 × 5 = 45 cells, from `phase4_fwdplainc_arms.json`.
- Total 28 + 18 + 63 + 45 = **154**, enumerated programmatically from the four stored JSONs
  (never from a directory listing — this is what excludes the many `F3*`/`regress*`/
  `PATnocap`/`.preD27` sensitivity-variant directories that also exist under some trials).

## Frame

Re-derived (not imported) from `docs/thesis/figures_thesis/index_drift.md` / Figure 4.1c,
generalised beyond its single flight:
- EKF3 traj + truth (N, E, D) → (N, E, U) = (col1, col2, −col3).
- UKF/FGO truth, ENU (E, N, U) → (N, E, U) = (col2, col1, col3).
- UKF/FGO estimate, own frame (x = take-off heading/North, y = West, z = up) →
  (N, E, U) = (col1, −col2, col3).
- `yaw0 = 0.0` confirmed for every cell in scope: `ukf_core.py:318` (unconditional),
  `fgo_core.py:120` + `fgo_replay.py:134` (`F_YAW0_DEG` only set by the plain-wall
  initial-yaw sensitivity trace runs in `eval/diag/plainwall_trace/*.sh`, which are outside
  this scope — different output directories, never read by this script).
- Verified numerically before trusting it for the whole scope: the mapped height of
  `dsn_tex_r1`'s UKF estimate and its own ENU truth file agree (~2.31 m) at a mid-cruise
  sample.
- **External reproduction check:** re-ran this script's own `frame_check()` on
  `dsn_tex_r3` (EKF3/UKF/FGO baseline) and compared to `index_drift.md`'s already-published
  frame-check table — **3/3 OK to 3 dp** (`index_drift_reproduction` in the json).

## GATE and frame-check results

- **GATE (evo -a cruise reproduction, 6 dp, in each cell's own un-relabelled frame):
  154/154 PASS.** No STOPs from the gate at all.
- **Frame check (take-off origin + first-5m heading, same convention as index_drift.md):
  85/154 PASS, 69 STOP** (raw values withheld for those 69; everything else is reported).
  By floor: 45 blank, 14 textured, 10 transition. Every EKF3 textured/transition cell
  passes (41/41) — the STOPs track the *estimator's own* early yaw, not the frame map.
  20/34 flights (trials) have at least one STOP cell.

## Cross-checks

- `docs/thesis/raw_corridor/check_raw_corridor.py`: **154/154 rows, 1411/1411 checks OK.**
  Covers: aligned value == `rd(json, 2)`; json `stored_ate_a_cruise` == the value at the
  *original* source file+key (independently re-derived, not read back from the json's own
  "source" string); numbers.md citations checked **positionally** (rank-exact against the
  r1/r2/r3 row), not by substring; raw values == `rd(json, 2)` for every non-STOP row;
  STOP rows have no `raw` entry and a failing gate or frame_check; `rd()` SHA matches;
  header counts (n_cells, gate/frame OK, STOP-by-floor, flights-with-stop, tolerances) all
  appear in the md; every json cell appears exactly once in the md and vice versa
  (completeness, both directions).
- `tools/check_numbers_frozen.py`: **PASS.**
- Tier-1 checksum guard (`frozen_manifest_20261022T002851.json`): **IDENTICAL before and
  after** (13253 files both times) — but see RC-4, this needs a coordinator decision before
  merge.

## RC decisions (not written to `decisions_log.md`, per instruction)

- **RC-1 — no pre-existing stored raw values reused.** Searched for already-computed raw
  (unaligned) cruise errors before computing anything. None exist for this scope beyond the
  single R5 figure flight (`dsn_tex_r3`, `index_drift.md`), which this script reproduces as
  its own external check rather than reusing (it only ever covered one flight). Two
  candidates were checked and ruled out as a different quantity, not reused:
  `blank_behaviour.json`'s `+10s/+30s/.../end` values have their origin at the point of flow
  *loss*, not take-off, and are along/cross-track components, not a 3D/horizontal error
  from truth; `phase5_analysis.json`'s `xtrack_head_m` is one component of the
  heading-driven error only. All 154 cells were computed fresh.
- **RC-2 — fwdc/fwdplainc baseline+EKF3 source.** Primary source is
  `phase4_{fwdc,fwdplainc}_arms.json` (has EKF3 + every arm uniformly). Cross-cited and
  verified against `rerun_fwdc_evo.json`/`rerun_fwdplainc_evo.json` (numbers.md §6.4's own
  cited source) and `phase4_*_evo.json`: **0 mismatches across 54 checks** (window_s +
  ate_a_cruise, all three files, every baseline/EKF3 cell of both datasets), independently
  recomputed again inside `check_raw_corridor.py`. Also independently confirmed by TUM-file
  md5 identity (`ukf`≡`ukf_baseline`, `fgo`≡`fgo_baseline`) across all 18 trials by hand
  before writing any code.
- **RC-3 — rounding.** 2 dp for every value (raw and aligned), matching numbers.md
  §6.1/§6.4/§6.6's own precision for cruise ATE, and `units.md`'s choice of metres for
  position error. `rd()` is parsed via `ast` from `eval/figs_thesis.py` at runtime in all
  three scripts, never hand-copied; its SHA-256 is recorded in the json and checked.
- **RC-4 — checksum-guard scope (coordinator decision needed before merge).** The guard's
  `results` spec is a fixed absolute path, `/home/makerspace/thesis_ws/eval/results` —
  the **main checkout**, not this `raw-corridor` worktree's own (separate) directory. Both
  "before" and "after" runs are genuinely IDENTICAL for everything the guard actually
  covers, and nothing in the main checkout was touched. **But** once `raw-corridor` is
  merged into the main checkout, `eval/results/raw_corridor_errors.json` will exist there
  too, and a future `verify` will report `ADDED eval/results/raw_corridor_errors.json` →
  `DIFFERENT: STOP AND REPORT`, breaking the "guard IDENTICAL after merge" pattern used by
  earlier merges. Two options, left to the coordinator (the brief names this exact path, so
  it was not moved unilaterally):
  1. Move `raw_corridor_errors.json` under `docs/thesis/raw_corridor/` (outside the guard's
     `results` spec, since that spec only covers `eval/results/`) — breaks D107's exact
     named path and would need a one-line doc-string update to the generators.
  2. Take a fresh checksum-guard snapshot after merging, accepting the addition as expected
     (it is new descriptive output, not a change to any frozen file).
- **RC-5 — STOP granularity.** The brief says "a failure is a STOP for that flight"; this
  is read as **per CELL** (estimator+arm), because different arms of the same trial
  (baseline vs. heading-corrected) can have materially different early headings, and the
  frame check is inherently about the *estimate's* early heading, not the trial's. The
  stricter "whole flight" reading is also reported for transparency: 20/34 trials have at
  least one STOP cell (vs. 69/154 cells). If the coordinator wants the stricter reading
  applied (withhold every arm of a trial once any one of its cells fails), that is a
  one-line change in `raw_corridor_errors.py`'s STOP logic — not done here, since D106/D107
  don't specify which reading, and withholding more data by default without being asked
  seemed the wrong default to pick unilaterally.
- **RC-6 — numbers.md citation coverage.** Only the literal `r1 / r2 / r3` rows in
  numbers.md §6.1/§6.4/§6.6 are individually printed (confirmed by grep, bounded to the
  CURRENT section 6, i.e. before the first superseded duplicate "## 6. Baseline results"
  heading later in the file): `dsn_tex` r1–r3 baseline; `fwdc`/`fwdplainc` **textured**
  baseline and heading rows. Everything else — all blank/transition individual values,
  `dsn_tex` r4–r10, the `heading_yawrate` arm, and every blank/transition heading-arm row —
  is cited against the JSON only, exactly as `index_drift.md` already does for its own
  blank/transition rows. This is a coverage fact, not a gap: numbers.md genuinely never
  prints those individual numbers (only aggregate ranges/medians).
- **RC-7 — EKF3 on the transition floor.** 9 rows (`{dsn,fwdc,fwdplainc}_trans_r{1,2,3}`,
  EKF3) are computed and reported exactly as specified, but their window includes ~140 s
  (of ~300 s) where EKF3's output is pinned near the origin after losing flow aiding at the
  textured/blank boundary — numbers.md §6.2 calls this period "not scored" by its own
  evaluation rule. Reported as computed per the brief (nothing dropped silently); footnoted
  `[a]` in the table with the exact numbers.md citation.

## Coverage table (flights × estimators)

| dataset | cells in scope | GATE OK | frame OK (raw reported) | STOP |
|---|---|---|---|---|
| `dsn_tex` (r1–r10) | 28 | 28 | 24 | 4 |
| `dsn_blank` (r1–r3) | 9 | 9 | 0 | 9 |
| `dsn_trans` (r1–r3) | 9 | 9 | 9 | 0 |
| `fwdc` (tex/trans/blank r1–r3, all arms) | 63 | 63 | 38 | 25 |
| `fwdplainc` (tex/trans/blank r1–r3, all arms) | 45 | 45 | 14 | 31 |
| **total** | **154** | **154** | **85** | **69** |

## Raw vs. aligned ranges per dataset (numbers only, no interpretation)

Aligned = stored `ate_a_cruise` (registered, all 154 cells). Raw = this script's raw 3D
RMS / end-of-cruise (only the 85 cells that passed the frame check; n given per row).

| dataset | n (aligned) | aligned range (m) | n (raw) | raw RMS range (m) | raw end-of-cruise range (m) |
|---|---|---|---|---|---|
| `dsn_tex` | 28 | 1.17 – 5.85 | 24 | 7.84 – 25.16 | 22.54 – 60.26 |
| `dsn_blank` | 9 | 43.37 – 11332.74 | 0 | — | — |
| `dsn_trans` | 9 | 41.48 – 595.48 | 9 | 79.60 – 730.67 | 150.92 – 2871.32 |
| `fwdc` | 63 | 0.06 – 12135.15 | 38 | 0.16 – 772.18 | 0.22 – 3132.74 |
| `fwdplainc` | 45 | 0.09 – 11694.64 | 14 | 14.43 – 816.42 | 37.01 – 3404.94 |

(`dsn_blank` has zero frame-check passes — see RC-5/coverage table — so no raw range
exists for it; its aligned values are all still reported in the md and json.)

## Anything the coordinator must rule on

1. **RC-4** — checksum-guard path vs. scope (move the json, or re-snapshot after merge).
2. **RC-5** — per-cell vs. per-flight STOP granularity (current: per-cell; both counts given).
3. Whether the stricter per-flight STOP reading should actually be applied before this is
   used downstream (table integration is explicitly out of scope for this stage).

No other STOPs, mismatches or open questions. Every gate passed; every cross-check passed;
nothing fitted, interpreted, compared or ordered anywhere in the new files.
