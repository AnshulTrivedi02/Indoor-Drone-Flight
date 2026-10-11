# Band C with the gate decisions forced: RESULT against PREREG.md (committed `b3ec6f4` before any forced run)

**Verdict: PASS on every pre-registered condition.** Forced build: `2610bdb` source, `-DFGO_CPP_FORCED_GATE=ON
-DFGO_CPP_BUILD_ROS=OFF` (scratch; replay `e0e5915d…`, front end `a3d13e78…`; never installed). Logs: `logs/forced_*.log`.

| bag | max / p99 \|Δp\| (mm), forced replay vs forced front end | max \|Δyaw\| (°) | count | factor-flag mismatches | construction check (replay / front end) | decisions overridden (replay / fe) | switch validity (forced replay kf ≡ unforced 2d) |
|---|---|---|---|---|---|---|---|
| dsn_tex_r1 baseline | **0.111** / 0.0106 | 3.6e-5 | 10197 = | 0 | PASS / PASS (2039 checks, 63 fired) | 0 / **1** | byte-identical |
| fwdc_tex_r1 heading | 8.9e-5 / 8.0e-5 | 1.9e-10 | 10118 = | 0 | PASS / PASS (2023, 0 fired) | 0 / 0 | byte-identical |
| T_A_r1 | 2.6e-7 / 1.1e-7 (batch 2.2e-9) | 2.9e-10 | 8015 = | 0 | PASS / PASS (48, 8 fired) | 0 / 0 | byte-identical (and batch) |
| T_D_r1 | 5.1e-4 / 4.6e-4 (batch 4.0e-8) | 7.6e-6 | 8017 = | 0 | PASS / PASS (52, 9 fired) | 0 / 0 | byte-identical (and batch) |

- **dsn_tex:** the forcing overrode exactly ONE front-end decision (the 241.1 s threshold tie, where the front end's
  trace sat just below 0.04). With it forced, the 16 paired mismatches of the 2d run vanish and |Δp| drops from 1.95 mm
  to 0.111 mm. The onset (first |Δp| > 1e-9 m at row 905, t 38.98 s) is unchanged: it is the front end's last-bit
  `t_init` difference, as in 2d.
- fwdc, T_A, T_D: no decision was overridden, so their numbers equal the 2d band C values (8.9e-5, 2.6e-7, 5.1e-4 mm).
- Room bags, batch: "key ids identical: False" is the key timestamps' last bits (as in the 2d logs); positions agree
  to ≤ 4e-8 mm, BAND PASS.
- Switch-OFF byte-identity (before the forced run): `ident_switch_off.txt`, `md5_builds.txt`.
