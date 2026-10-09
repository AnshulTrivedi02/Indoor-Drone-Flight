#!/usr/bin/env python3
"""Checks for the FINAL consolidated offline re-run (eval/final_rerun_pipeline.sh; user rulings 2026-10-09, METHODOLOGY
"RULING (user, 2026-10-09): FGO noise-model correction ... consolidated re-run plan" and "MODEL AUDIT RESULT ... RULINGS").
Light (no replays, no ROS), standard-library only, so it runs under any python3.

  final_rerun_checks.py provenance             git SHA + md5 of every estimator source the re-run depends on (stdout)
  final_rerun_checks.py corrections            exit 1 unless ALL FOUR ruled corrections are present in the tree:
        (1) FGO noise model: setBiasAccOmegaInit is ZERO in both cores (fgo_core.py, fgo_cpp/src/fgo_core.cpp) and no
            other setBiasAccOmegaInit call exists;
        (2) FGO yaw cap VARIANCE-GATED: ATT_VAR_GATE defined and used as the firing condition in both cores;
        (3) UKF sigma-point jitter ONLY on Cholesky failure: CHOL_JITTER_LADDER starts at 0.0 and the first attempt adds
            no jitter; no unconditional "+ 1e-12*np.eye" in ukf_core.py;
        (4) UKF bias-corrected flow derotation is the DEFAULT (ruling 2026-10-08 item 3), in every offline UKF harness
            (ukf_replay.py, room_ukf_replay.py): accepted if EITHER the harness subtracts the UKF's own gyro-bias
            estimate (x[...BG_SLICE...]) from the derotation rate in an assignment that is NOT inside an `if` whose test
            mentions APIN / "biascorr" (i.e. not only the diagnostic variant), OR ukf_core.update_flow / measurement
            models h_flow themselves reference BG_SLICE (the subtraction moved into the core). Written so that it FAILS
            on the tree as of 2026-10-09 (diagnostic-only `if APIN == "biascorr"`) and PASSES once the parallel
            derotation change lands as the default.
  final_rerun_checks.py ekf3-gate OLD NEW [OLD NEW ...]
        exit 1 if any JSON leaf whose key path contains an EKF3 key ("EKF3", "ekf3", "EKF3 live", ...) differs between
        OLD and NEW (exact equality after JSON load), or if an EKF3 leaf exists on one side only. Prints every difference.
"""
import ast, hashlib, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EST = os.path.join(REPO, "src", "estimators")
SOURCES = ["src/estimators/ukf_core.py", "src/estimators/measurement_models.py", "src/estimators/imu_timing.py",
           "src/estimators/ukf_replay.py", "src/estimators/room_ukf_replay.py", "src/estimators/apin.py",
           "src/estimators/fgo/fgo_core.py", "src/estimators/fgo/factors.py", "src/estimators/fgo/fgo_replay.py",
           "src/estimators/fgo/room_fgo_replay.py", "src/estimators/fgo/lc_fgo_replay.py",
           "src/estimators/fgo_cpp/src/fgo_core.cpp", "src/estimators/fgo_cpp/include/fgo_cpp/fgo_core.h"]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def provenance():
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                           text=True).stdout.strip()
    print(f"thesis_ws HEAD {sha}{' (TRACKED FILES MODIFIED)' if dirty else ''}")
    if dirty:
        print(dirty)
    for s in SOURCES:
        p = os.path.join(REPO, s)
        print(f"md5 {md5(p) if os.path.exists(p) else 'MISSING':32s}  {s}")
    for b in ("fgo_cpp_replay", "fgo_cpp_node"):     # installed C++ binaries (only used if a stage calls them)
        p = os.path.expanduser(f"~/opt/fgo_cpp/bin/{b}")
        if os.path.exists(p):
            print(f"md5 {md5(p)}  {p}")
    return 0 if not dirty else 0      # a dirty tree is reported, not fatal (the pipeline dies on it separately)


def _src(rel):
    return open(os.path.join(REPO, rel)).read()


def _check_binit():
    errs = []
    py, cpp = _src("src/estimators/fgo/fgo_core.py"), _src("src/estimators/fgo_cpp/src/fgo_core.cpp")
    py_calls = re.findall(r"setBiasAccOmegaInit\(([^\n]*)\)", py)
    cpp_calls = re.findall(r"setBiasAccOmegaInit\(([^\n;]*)\)", cpp)
    if py_calls != ["np.zeros((6, 6))"]:
        errs.append(f"fgo_core.py setBiasAccOmegaInit calls {py_calls!r} (expected exactly ['np.zeros((6, 6))'])")
    if cpp_calls != ["gtsam::Matrix6::Zero()"]:
        errs.append(f"fgo_core.cpp setBiasAccOmegaInit calls {cpp_calls!r} (expected exactly ['gtsam::Matrix6::Zero()'])")
    return errs


def _check_yawgate():
    errs = []
    py = _src("src/estimators/fgo/fgo_core.py")
    if not re.search(r"^ATT_VAR_GATE\s*=\s*0\.04\b", py, re.M):
        errs.append("fgo_core.py: ATT_VAR_GATE = 0.04 not defined")
    if not re.search(r"fire\s*=\s*bool\(\s*tr\s*>\s*ATT_VAR_GATE\s*\)", py):
        errs.append("fgo_core.py: yaw-cap firing condition 'tr > ATT_VAR_GATE' not found")
    h = _src("src/estimators/fgo_cpp/include/fgo_cpp/fgo_core.h"); cpp = _src("src/estimators/fgo_cpp/src/fgo_core.cpp")
    if not re.search(r"constexpr\s+double\s+ATT_VAR_GATE\s*=\s*0\.04\s*;", h):
        errs.append("fgo_core.h: constexpr ATT_VAR_GATE = 0.04 not defined")
    if not re.search(r"fire\s*=\s*tr\s*>\s*ATT_VAR_GATE", cpp):
        errs.append("fgo_core.cpp: yaw-cap firing condition 'tr > ATT_VAR_GATE' not found")
    return errs


def _check_jitter():
    errs = []
    u = _src("src/estimators/ukf_core.py")
    m = re.search(r"^CHOL_JITTER_LADDER\s*=\s*\(([^)]*)\)", u, re.M)
    if not m or not m.group(1).strip().startswith("0.0"):
        errs.append("ukf_core.py: CHOL_JITTER_LADDER missing or does not start with 0.0 (no jitter on the first attempt)")
    if re.search(r"\+\s*1e-12\s*\*\s*np\.eye", u):
        errs.append("ukf_core.py: an unconditional '+ 1e-12*np.eye' is present (jitter on every call)")
    if "if jit else" not in u:
        errs.append("ukf_core.py: first Cholesky attempt is not jitter-free ('... if jit else c * Psym' not found)")
    return errs


def _mentions_diag(node):
    s = ast.unparse(node)
    return "APIN" in s or "biascorr" in s


def _refs_bias(node):
    return "BG_SLICE" in ast.unparse(node)


def _harness_biascorr_default(rel):
    """True iff some assignment to omega_flow subtracts a BG_SLICE term outside any APIN/biascorr-conditioned `if`."""
    tree = ast.parse(_src(rel))
    hits = []
    # the derotation-rate variable = the 4th positional argument of every update_flow(...) call in the harness
    rate_vars = {ast.unparse(c.args[3]) for c in ast.walk(tree) if isinstance(c, ast.Call)
                 and ast.unparse(c.func).endswith("update_flow") and len(c.args) >= 4}

    def walk(node, diag):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.If) and _mentions_diag(ch.test):
                for b in ch.body:     # the body is conditioned on the diagnostic; orelse is the non-diagnostic path
                    walk_one(b, True)
                for b in ch.orelse:
                    walk_one(b, diag)
                continue
            walk_one(ch, diag)

    def walk_one(ch, diag):
        if isinstance(ch, (ast.Assign, ast.AugAssign)):
            tgts = ch.targets if isinstance(ch, ast.Assign) else [ch.target]
            if any(ast.unparse(t) in rate_vars for t in tgts) and _refs_bias(ch.value):
                hits.append((ch.lineno, diag))
        walk(ch, diag)

    walk(tree, False)
    return [ln for ln, diag in hits if not diag], [ln for ln, diag in hits if diag]


def _core_biascorr():
    """True iff the core flow update itself applies the gyro-bias estimate."""
    tree = ast.parse(_src("src/estimators/ukf_core.py"))
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "update_flow" and _refs_bias(n):
            return "ukf_core.update_flow references BG_SLICE"
    tree = ast.parse(_src("src/estimators/measurement_models.py"))
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "h_flow" and _refs_bias(n):
            return "measurement_models.h_flow references BG_SLICE"
    return None


def _check_derotation():
    core = _core_biascorr()
    if core:
        return [], [f"derotation: {core} (core-level)"]
    errs, notes = [], []
    for rel in ("src/estimators/ukf_replay.py", "src/estimators/room_ukf_replay.py"):
        default, diag_only = _harness_biascorr_default(rel)
        if default:
            notes.append(f"derotation: {rel} default-path bias subtraction at line(s) {default}")
        else:
            errs.append(f"derotation: {rel} has NO default-path bias-corrected derotation "
                        f"(only the diagnostic UKF_APIN=biascorr variant at line(s) {diag_only})")
    return errs, notes


def corrections():
    errs = _check_binit() + _check_yawgate() + _check_jitter()
    e4, notes = _check_derotation(); errs += e4
    for n in notes:
        print("ok  ", n)
    for name, f in (("(1) FGO setBiasAccOmegaInit = 0", _check_binit), ("(2) FGO yaw cap variance-gated", _check_yawgate),
                    ("(3) UKF jitter only on Cholesky failure", _check_jitter)):
        print(("ok  " if not f() else "FAIL"), name)
    print(("ok  " if not e4 else "FAIL"), "(4) UKF bias-corrected derotation is the default")
    for e in errs:
        print("  -", e)
    return 1 if errs else 0


EKF3_KEY = re.compile(r"ekf3", re.I)


def _leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _leaves(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, path + (f"[{i}]",))
    else:
        yield path, o


def ekf3_gate(pairs):
    bad = 0; n = 0
    for old, new in pairs:
        if not os.path.exists(old):
            print(f"FAIL {old}: snapshot file missing"); bad += 1; continue
        if not os.path.exists(new):
            print(f"FAIL {new}: new file missing"); bad += 1; continue
        a = {p: v for p, v in _leaves(json.load(open(old))) if any(EKF3_KEY.search(x) for x in p)}
        b = {p: v for p, v in _leaves(json.load(open(new))) if any(EKF3_KEY.search(x) for x in p)}
        for p in sorted(set(a) | set(b)):
            n += 1
            if p not in a or p not in b:
                print(f"FAIL {os.path.basename(new)}: EKF3 leaf only in {'new' if p in b else 'old'}: {'/'.join(p)}"); bad += 1
            elif json.dumps(a[p]) != json.dumps(b[p]):
                print(f"FAIL {os.path.basename(new)}: {'/'.join(p)}: {a[p]!r} -> {b[p]!r}"); bad += 1
        if not a:
            print(f"WARN {os.path.basename(new)}: no EKF3 leaves found (nothing gated in this file)")
    print(f"ekf3-gate: {n} EKF3 leaves compared, {bad} differences")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "provenance":
        sys.exit(provenance())
    if cmd == "corrections":
        sys.exit(corrections())
    if cmd == "ekf3-gate":
        r = sys.argv[2:]
        if not r or len(r) % 2:
            sys.exit("ekf3-gate needs OLD NEW pairs")
        sys.exit(ekf3_gate(list(zip(r[::2], r[1::2]))))
    sys.exit(__doc__)
