#!/usr/bin/env python3
"""Safety check for parameter files meant for a REAL flight controller (R6, rung 1; written 2026-10-10).

  python3 realflight/params/check_parm.py [--final] [--names FILE] FILE.parm [FILE.parm ...]
  python3 realflight/params/check_parm.py --selftest

The files are checked as ONE set, in load order (later files override earlier ones, as on the FC).

ALWAYS REFUSED (exit 1), in any mode:
  - AHRS_EKF_TYPE 10 anywhere (EKFType::SIM: the simulator's perfect state; it does not exist on a real FC);
  - any SIM_* parameter (simulation-only; e.g. consolidated_rerun.parm, sim_noise.parm);
  - ARMING_SKIPCHK other than 0 (arming checks are never skipped for rung 1), and the stale name ARMING_CHECK (not a
    parameter at the pinned commit; it would be silently ignored);
  - a value that is neither a number nor the placeholder TODO_SUPERVISOR; a line that does not parse;
  - with --names: a parameter name not in the names list (default list: pinned_param_names.txt next to this script,
    the PARM dump of a SITL build of 7bac20cbcc; a board build can add board-only names, so pass --names to override).

REQUIRED VALUES (checked on the merged set; a wrong value is always an error, a MISSING one is an error with --final):
  AHRS_EKF_TYPE 3, EK3_SRC1_POSXY 0, EK3_SRC1_VELXY 5, EK3_SRC1_POSZ 2, EK3_SRC1_VELZ 0, EK3_FLOW_USE 1, GPS1_TYPE 0,
  LOG_REPLAY 1, LOG_DISARMED 1, ARMING_SKIPCHK 0, FENCE_ENABLE 1; and EK3_SRC1_YAW set by EXACTLY ONE file (the
  compass variant), to 0 (nomag) or 1 (compass).

--final additionally refuses any TODO_SUPERVISOR left in the set (the file is then ready to load).
"""
import argparse, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NAMES = os.path.join(HERE, "pinned_param_names.txt")
PLACEHOLDER = "TODO_SUPERVISOR"
REQUIRED = {"AHRS_EKF_TYPE": 3, "EK3_SRC1_POSXY": 0, "EK3_SRC1_VELXY": 5, "EK3_SRC1_POSZ": 2, "EK3_SRC1_VELZ": 0,
            "EK3_FLOW_USE": 1, "GPS1_TYPE": 0, "LOG_REPLAY": 1, "LOG_DISARMED": 1, "ARMING_SKIPCHK": 0,
            "FENCE_ENABLE": 1}
LINE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*[,\s]\s*(\S+)\s*$")


def parse(path):
    """[(lineno, name, raw_value)], errors"""
    out, err = [], []
    for i, raw in enumerate(open(path), 1):
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        m = LINE.match(s)
        if not m:
            err.append(f"{path}:{i}: cannot parse '{s}'")
            continue
        out.append((i, m.group(1).upper(), m.group(2)))
    return out, err


def num(v):
    try:
        return float(v)
    except ValueError:
        return None


def check(files, final=False, names_file=None):
    errors, warnings, merged, yaw_files = [], [], {}, []
    names = None
    if names_file:
        names = {l.split()[0] for l in open(names_file) if l.strip() and not l.startswith("#")}
    for f in files:
        rows, perr = parse(f)
        errors += perr
        seen_here = set()
        for ln, name, val in rows:
            where = f"{f}:{ln}"
            if name in seen_here:
                errors.append(f"{where}: {name} set twice in one file")
            seen_here.add(name)
            x = num(val)
            if val != PLACEHOLDER and x is None:
                errors.append(f"{where}: {name} value '{val}' is not a number")
            if name.startswith("SIM_"):
                errors.append(f"{where}: {name}: SIM_* parameters are simulation-only and must never reach a real FC")
            if name == "AHRS_EKF_TYPE" and x is not None and int(round(x)) == 10:
                errors.append(f"{where}: AHRS_EKF_TYPE 10 (the SIMULATOR'S state) - REFUSED. Real flights use 3 (EKF3)")
            if name == "ARMING_CHECK":
                errors.append(f"{where}: ARMING_CHECK is not a parameter at the pinned commit (it is ARMING_SKIPCHK)")
            if name == "ARMING_SKIPCHK" and x is not None and x != 0:
                errors.append(f"{where}: ARMING_SKIPCHK {val}: arming checks must not be skipped (0)")
            if final and val == PLACEHOLDER:
                errors.append(f"{where}: {name} is still {PLACEHOLDER}")
            if names is not None and name not in names:
                errors.append(f"{where}: {name} is not a parameter of the pinned build (names list {names_file})")
            if name == "EK3_SRC1_YAW":
                yaw_files.append(f)
            merged[name] = (val, where)
    for name, want in REQUIRED.items():
        if name not in merged:
            (errors if final else warnings).append(f"{name} missing (required = {want})")
            continue
        val, where = merged[name]
        if val == PLACEHOLDER:
            continue
        if num(val) is not None and num(val) != want:
            errors.append(f"{where}: {name} {val}, required {want}")
    if len(yaw_files) == 0:
        (errors if final else warnings).append("EK3_SRC1_YAW not set: append exactly one compass variant file")
    elif len(yaw_files) > 1:
        errors.append(f"EK3_SRC1_YAW set by more than one file ({', '.join(yaw_files)}): load exactly ONE variant")
    else:
        v = num(merged["EK3_SRC1_YAW"][0])
        if v not in (0.0, 1.0):
            errors.append(f"EK3_SRC1_YAW {merged['EK3_SRC1_YAW'][0]}: expected 0 (nomag) or 1 (compass)")
    n_todo = sum(1 for v, _ in merged.values() if v == PLACEHOLDER)
    return errors, warnings, n_todo


def report(files, final, names_file):
    errors, warnings, n_todo = check(files, final, names_file)
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    status = "REFUSED" if errors else ("OK (final)" if final else f"OK (draft; {n_todo} {PLACEHOLDER} left)")
    print(f"{status}: {' + '.join(files)}")
    return 1 if errors else 0


def selftest():
    ok = True

    def expect(label, files, final, want_refused, must_contain=None):
        nonlocal ok
        errors, _, _ = check(files, final, DEFAULT_NAMES if os.path.exists(DEFAULT_NAMES) else None)
        refused = bool(errors)
        good = refused == want_refused and (must_contain is None or any(must_contain in e for e in errors))
        print(("PASS " if good else "FAIL ") + label + ("" if good else f"  errors={errors}"))
        ok &= good

    ws = os.path.abspath(os.path.join(HERE, "..", ".."))
    tpl = os.path.join(HERE, "rung1_template.parm")
    nomag, comp = os.path.join(HERE, "rung1_variant_nomag.parm"), os.path.join(HERE, "rung1_variant_compass.parm")
    expect("consolidated_rerun.parm is refused (AHRS_EKF_TYPE 10)", [os.path.join(ws, "consolidated_rerun.parm")],
           False, True, "AHRS_EKF_TYPE 10")
    expect("gnss_denied.parm is refused (SIM_GPS1_ENABLE)", [os.path.join(ws, "gnss_denied.parm")], False, True, "SIM_")
    expect("template + nomag passes in draft mode", [tpl, nomag], False, False)
    expect("template + compass passes in draft mode", [tpl, comp], False, False)
    expect("template + nomag is refused in --final (placeholders)", [tpl, nomag], True, True, PLACEHOLDER)
    expect("template + both variants is refused", [tpl, nomag, comp], False, True, "more than one file")
    with tempfile.TemporaryDirectory() as d:
        bad = os.path.join(d, "bad.parm")
        open(bad, "w").write("AHRS_EKF_TYPE,10.0\nARMING_CHECK 1\n")
        expect("comma form AHRS_EKF_TYPE,10.0 is refused", [bad], False, True, "AHRS_EKF_TYPE 10")
        expect("ARMING_CHECK is refused", [bad], False, True, "ARMING_CHECK")
        sk = os.path.join(d, "skip.parm")
        open(sk, "w").write("ARMING_SKIPCHK -1\n")
        expect("ARMING_SKIPCHK -1 is refused", [sk], False, True, "must not be skipped")
        typo = os.path.join(d, "typo.parm")
        open(typo, "w").write("RNGFND1_GNDCLEAR 0.1\n")
        if os.path.exists(DEFAULT_NAMES):
            expect("unknown name RNGFND1_GNDCLEAR is refused", [typo], False, True, "not a parameter")
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--final", action="store_true", help="also refuse leftover TODO_SUPERVISOR values")
    ap.add_argument("--names", default=DEFAULT_NAMES if os.path.exists(DEFAULT_NAMES) else None,
                    help="parameter names list (one per line); default pinned_param_names.txt")
    ap.add_argument("--no-names", action="store_true", help="skip the name check")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.files:
        ap.error("give one or more .parm files")
    return report(a.files, a.final, None if a.no_names else a.names)


if __name__ == "__main__":
    sys.exit(main())
