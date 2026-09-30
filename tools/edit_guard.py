#!/usr/bin/env python3
"""HARD edit guard (user ruling 2026-10-01, after two edits to files a running batch used): a Claude Code
PreToolUse hook for Edit, Write and Bash. Before any edit it lists the running jobs and the files they use, and
REFUSES the edit (exit 2) if the target overlaps.

Running jobs: processes whose command line references a guarded repository or is a simulation/replay process
(arducopter, gz sim, Replay, ros2 bag, run_trial.sh, run_jobs_resumable.sh, fgo_node.py, *_replay.py, ...),
excluding this hook and Claude's own tool shells.
Files a job uses: CONSERVATIVELY, every existing source file (.py .sh .parm .sdf .cpp .h .hpp .c .jobs .conf .msg)
in any guarded repository the job references (a Python job imports from its whole tree; a simulation reads the
harness, parameter files and worlds). Documentation (.md), results (eval/results/, thesis_data) and NEW files
are never blocked.
Edit targets: Edit/Write file_path; for Bash, the files a command would modify: `sed -i`, Python
open(<path>|<var>, 'w'/'a'), shell redirection `>`/`>>`, `tee`, and `cp`/`mv` destinations.
Manual use: tools/edit_guard.py --check FILE...  (prints the running jobs and the verdict)."""
import json, os, re, shlex, subprocess, sys

HOME = os.path.expanduser("~")
REPOS = [os.path.join(HOME, r) for r in ("thesis_ws", "ardupilot_ukf", "ardupilot_diag", "ardupilot", "ardupilot_gazebo")]
SRC_EXT = (".py", ".sh", ".parm", ".sdf", ".cpp", ".h", ".hpp", ".c", ".jobs", ".conf", ".msg", ".yaml", ".config")
JOB_PAT = re.compile(r"(arducopter|gz sim|/Replay\b|ros2 bag|run_trial\.sh|closed_loop_run\.sh|run_jobs_resumable\.sh|"
                     r"run_resumable_batch\.sh|fgo_node\.py|_replay\.py|heading_bridge|flow_tracker|fly_trial\.py|"
                     r"_pipeline\.sh|run_set_eval\.sh|thesis_ws|ardupilot_ukf|ardupilot_diag)")


def running_jobs():
    out = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, text=True).stdout.splitlines()
    me = os.getpid(); jobs = []
    for line in out:
        line = line.strip()
        if not line:
            continue
        pid, _, args = line.partition(" ")
        if int(pid) in (me, os.getppid()):
            continue
        if "edit_guard.py" in args or "shell-snapshots" in args or "claude" in args.split(" ")[0]:
            continue
        if JOB_PAT.search(args):
            jobs.append((int(pid), args[:200]))
    return jobs


def repo_of(path):
    p = os.path.realpath(path)
    for r in REPOS:
        if p == r or p.startswith(r + os.sep):
            return r
    return None


def guarded(path):
    p = os.path.realpath(path)
    if not os.path.exists(p) or not p.endswith(SRC_EXT):
        return False
    if "/eval/results/" in p or "/thesis_data/" in p or p.endswith(".md"):
        return False
    return repo_of(p) is not None


def job_repos(jobs):
    rs = set()
    for _, args in jobs:
        for r in REPOS:
            if r in args or r.replace(HOME, "~") in args:
                rs.add(r)
        if re.search(r"arducopter|/Replay\b", args) and not any(r in args for r in REPOS):
            rs.update(REPOS[:2])
        if re.search(r"run_trial|closed_loop_run|gz sim|ros2 bag|fly_trial|heading_bridge|flow_tracker", args):
            rs.add(REPOS[0])
    return rs


def bash_targets(cmd, cwd):
    t = set()
    for m in re.finditer(r"sed\s+-i\S*\s+(?:-e\s+)?('[^']*'|\"[^\"]*\"|\S+)\s+([^;&|]+)", cmd):
        for tok in m.group(2).split():
            if not tok.startswith("-"):
                t.add(tok)
    for m in re.finditer(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wa]", cmd):
        t.add(m.group(1))
    names = {m.group(1) for m in re.finditer(r"open\(\s*([A-Za-z_]\w*)\s*,\s*['\"][wa]", cmd)}
    for n in names:
        for m in re.finditer(rf"\b{n}\s*=\s*['\"]([^'\"]+)['\"]", cmd):
            t.add(m.group(1))
    for m in re.finditer(r"(?<![0-9&<>])>>?\s*([^\s;&|<>]+)", cmd):
        tok = m.group(1)
        if tok not in ("/dev/null", "&1", "&2") and not tok.startswith("&"):
            t.add(tok)
    for m in re.finditer(r"\btee\s+(?:-a\s+)?([^\s;&|]+)", cmd):
        t.add(m.group(1))
    for m in re.finditer(r"\b(?:cp|mv)\s+(?:-\S+\s+)*\S+\s+([^\s;&|]+)", cmd):
        t.add(m.group(1))
    res = set()
    for x in t:
        x = x.strip("'\"")
        x = os.path.expanduser(x.replace("$HOME", HOME))
        res.add(x if os.path.isabs(x) else os.path.join(cwd, x))
    return res


def verdict(targets):
    jobs = running_jobs()
    hit = [p for p in targets if guarded(p)]
    if not jobs or not hit:
        return 0, jobs, []
    rs = job_repos(jobs)
    blocked = [p for p in hit if repo_of(p) in rs]
    return (2 if blocked else 0), jobs, blocked


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        code, jobs, blocked = verdict({os.path.abspath(f) for f in sys.argv[2:]})
        print("running jobs:"); [print(f"  {p} {a}") for p, a in jobs]
        print("BLOCKED:" if blocked else "allowed", *blocked)
        sys.exit(code)
    data = json.load(sys.stdin)
    tool, ti, cwd = data.get("tool_name", ""), data.get("tool_input", {}), data.get("cwd", os.getcwd())
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        targets = {ti.get("file_path") or ti.get("notebook_path") or ""}
    elif tool == "Bash":
        targets = bash_targets(ti.get("command", ""), cwd)
    else:
        sys.exit(0)
    code, jobs, blocked = verdict({t for t in targets if t})
    if code:
        sys.stderr.write("EDIT GUARD: refused - a running job uses this repository's sources.\n"
                         f"  target(s): {', '.join(blocked)}\n  running jobs:\n" +
                         "".join(f"    {p} {a}\n" for p, a in jobs[:12]) +
                         "  Wait for the jobs to finish (or hold the change as a patch).\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
