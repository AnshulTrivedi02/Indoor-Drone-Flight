"""Tier-1 extension experiments, pre-registered (E2-E5, docs/thesis/tier1/preregistration.md): output-path guard, tag-id filter
and mislabel injector for lc_fgo_replay.py. No gtsam import, so it can be checked statically (python3 -m py_compile,
`python3 tier1_paths.py --selftest`) without a replay.

Rules (user ruling 2026-10-21):
  * any tier-1 run writes under TIER1_DATA_ROOT (~/thesis_data/tier1), never under ~/thesis_data/trials;
  * the new flags (--tag-ids, --mislabel-*, --tag-robust) are refused without --out-root;
  * an existing NON-EMPTY output directory is refused (no overwrite, including inside the tier-1 root);
  * the gauge tag must be in --tag-ids; the gauge tag is never mislabelled and never used as a replacement.
The default lc_fgo_replay.py path (no --out-root, no new flags) never calls into this module's guard or injector."""
import os
import sys
import numpy as np

TIER1_DATA_ROOT = os.path.expanduser("~/thesis_data/tier1")
TRIALS_ROOT = os.path.expanduser("~/thesis_data/trials")


def refuse(msg):
    sys.exit(f"[tier1] REFUSED: {msg}")


def _under(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def parse_tag_ids(s, gauge):
    """'0,1,2,3' -> sorted tuple of ints; the gauge tag must be included (it defines the frame)."""
    try:
        ids = tuple(sorted({int(x) for x in s.split(",") if x.strip() != ""}))
    except ValueError:
        refuse(f"--tag-ids {s!r} is not a comma-separated list of integers")
    if not ids:
        refuse("--tag-ids is empty")
    if gauge not in ids:
        refuse(f"--tag-ids {s!r} omits the gauge tag {gauge}: the frame would be undefined")
    return ids


def run_suffix(tag_ids, mislabel_rate, mislabel_seed, tag_robust):
    """Directory suffix after lc_fgo_<mode>[_tN]; empty for the default configuration."""
    s = ""
    if tag_ids is not None:
        s += "_tags" + "-".join(str(i) for i in tag_ids)
    if mislabel_rate is not None:
        s += f"_mis{mislabel_rate:g}_s{mislabel_seed}"
    if tag_robust is not None:
        s += "_rob" + tag_robust.replace(":", "")
    return s


def resolve_out(trial, base_name, out_root):
    """<out_root>/<trial>/<base_name>, after the guard. Creates the directory. Refuses (exit) on any rule breach."""
    if not _under(out_root, TIER1_DATA_ROOT):
        refuse(f"--out-root {out_root!r} (real path {os.path.realpath(out_root)!r}) is not under {TIER1_DATA_ROOT}")
    out = os.path.join(out_root, trial, base_name)
    if _under(out, TRIALS_ROOT):
        refuse(f"output {out!r} resolves under {TRIALS_ROOT} (frozen trial outputs)")
    if os.path.lexists(out) and (not os.path.isdir(out) or os.listdir(out)):
        refuse(f"output {out!r} already exists and is not an empty directory; move it aside first")
    os.makedirs(out, exist_ok=True)
    if not _under(out, TIER1_DATA_ROOT):         # a symlink inside the root pointing out of it
        refuse(f"output {out!r} resolves outside {TIER1_DATA_ROOT}")
    return out


class MisDet(tuple):
    """A tag detection (tid, x, y, yaw) whose id was injected wrong; behaves exactly as the plain tuple."""


class Mislabeller:
    """E3 wrong-re-identification injector (pre-registered).

    Called once per central detection that passed the tag-id filter, in bag order. EVERY call draws two uniforms from
    numpy.random.default_rng(seed) (PCG64): u (mislabel?) and r (which replacement), whether or not the detection is
    mislabelled. The stream therefore depends only on the bag, and for one seed the 1% set is nested in the 5% set
    with the same replacement ids. A detection of tag i != gauge is mislabelled iff u < rate; the replacement is
    choices[floor(r * len(choices))], choices = sorted(valid_ids - {gauge, i}) (uniform over the OTHER non-gauge ids).
    The gauge tag is never mislabelled and never a replacement."""

    def __init__(self, rate, seed, valid_ids, gauge):
        if not (0.0 <= rate < 1.0):
            refuse(f"--mislabel-rate {rate} not in [0, 1)")
        if len([i for i in valid_ids if i != gauge]) < 2:
            refuse("mislabelling needs at least two non-gauge tag ids in --tag-ids")
        self.rate, self.seed, self.gauge = float(rate), int(seed), gauge
        self.valid = tuple(sorted(valid_ids))
        self.rng = np.random.default_rng(self.seed)
        self.n_calls = self.n_eligible = self.n_mislabelled = 0
        self.events = []                          # (t, true id, reported id)

    def __call__(self, t, tid):
        u, r = self.rng.random(), self.rng.random()
        self.n_calls += 1
        if tid == self.gauge:
            return tid, False
        self.n_eligible += 1
        if u >= self.rate:
            return tid, False
        choices = [i for i in self.valid if i != self.gauge and i != tid]
        new = choices[min(int(r * len(choices)), len(choices) - 1)]
        self.n_mislabelled += 1
        self.events.append((float(t), int(tid), int(new)))
        return new, True


def _selftest():
    import tempfile
    ids = parse_tag_ids("3,0,1,2", 0)
    assert ids == (0, 1, 2, 3)
    assert run_suffix(None, None, None, None) == ""
    assert run_suffix(ids, None, None, None) == "_tags0-1-2-3"
    assert run_suffix((0, 1, 2, 3, 4, 5, 6, 7), 0.01, 0, None) == "_tags0-1-2-3-4-5-6-7_mis0.01_s0"
    assert run_suffix((0, 1), None, None, "cauchy:2.385") == "_tags0-1_robcauchy2.385"
    # nesting and gauge rules
    valid = tuple(range(8)); tids = [i % 8 for i in range(20000)]
    m1, m5 = Mislabeller(0.01, 0, valid, 0), Mislabeller(0.05, 0, valid, 0)
    o1 = [m1(k, t) for k, t in enumerate(tids)]; o5 = [m5(k, t) for k, t in enumerate(tids)]
    s1 = {k for k, (_, f) in enumerate(o1) if f}; s5 = {k for k, (_, f) in enumerate(o5) if f}
    assert s1 <= s5, "1% set not nested in 5% set"
    assert all(o1[k][0] == o5[k][0] for k in s1), "replacement differs between rates"
    assert all(tids[k] != 0 for k in s5) and all(o5[k][0] not in (0, tids[k]) for k in s5)
    assert all(o5[k][0] == 0 for k, t in enumerate(tids) if t == 0)
    print(f"selftest: rate 0.01 -> {m1.n_mislabelled}/{m1.n_eligible}, 0.05 -> {m5.n_mislabelled}/{m5.n_eligible} "
          f"eligible; nested OK; gauge never touched OK")
    m0 = Mislabeller(0.0, 0, valid, 0)
    assert not any(m0(k, t)[1] for k, t in enumerate(tids))
    # path guard (in a temp dir: the guard must refuse it as not under the tier-1 root)
    with tempfile.TemporaryDirectory() as td:
        try:
            resolve_out("T_X", "lc_fgo_lc_t245", td); raise AssertionError("temp dir accepted")
        except SystemExit as e:
            assert "not under" in str(e)
    try:
        resolve_out("T_A_r1", "lc_fgo_lc_t245", TRIALS_ROOT); raise AssertionError("trials root accepted")
    except SystemExit as e:
        assert "REFUSED" in str(e)
    try:
        parse_tag_ids("1,2", 0); raise AssertionError("gauge-less tag set accepted")
    except SystemExit:
        pass
    print("selftest: path guard refuses a non-tier1 root and the trials root; gauge-less --tag-ids refused. ALL OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
    else:
        print(__doc__)
