f = '/home/makerspace/thesis_ws/.claude/worktrees/agent-aa29cfc08768a86c5/docs/handovers/2026-10-09_fgo_yawcap_gate.md'
s = open(f).read()
forced = '''| bag | Python forced to the emulate-gemv build's decisions, vs that build | Python forced to the default build's decisions, vs that build |
|---|---|---|
| dsn_tex_r1 | **bit-identical** (whole kf export, `cmp`) | max / p99 \\|Δp\\| 0.151 / 0.012 mm, yaw 1.1e-4 °: **within the band** |
| dsn_blank_r1 | **bit-identical** | 6.0e6 mm: outside the band, as under binit0 (gemv round-off on a divergent run) |
| dsn_trans_r1 | **bit-identical** | 9.8e5 mm: outside the band, as under binit0 |

- **Once the decisions agree, the cores are identical:**
  - emulate-gemv: bit-identical;
  - default build: the binit0 picture (tex passes, while blank and trans differ only through the known gemv rounding
    on a diverging trajectory).
- **So the only new source of difference is the gate decision itself.**'''
s = s.replace("__FORCED__", forced)
s = s.replace("__ACCEPT__", "**ACCEPT replay** and **ACCEPT live (node path)**, with `sha256sum -c` OK on all 7 files (`accept.sh`, run through\n  `heavy.py`; log `logs/accept.log`).")
assert "__" not in s
open(f, 'w').write(s)
