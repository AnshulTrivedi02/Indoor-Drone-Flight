#!/usr/bin/env python3
"""Run ONE CPU-heavy step (a single make, a single replay) under the flight/build lock protocol (ruling 2026-10-08).

  heavy.py [--wait-s N] [--keep-threads] "<description>" -- <command> [args...]

1. Before starting: ~/thesis_data/FLIGHT_LOCK must not exist and no `[a]rducopter` / `[g]z sim` process may run.
   Otherwise poll every 60 s until clear, up to --wait-s (default 6 h), then give up (exit 75) without running.
2. While running: ~/thesis_data/BUILD_LOCK holds this PID and the description; it is removed when the step ends,
   on success, failure, Ctrl-C or SIGTERM. The command runs at nice 19.
3. One invocation = one bounded step, so the lock is released between steps.
"""
import os, signal, subprocess, sys, time

LOCK_DIR = os.path.expanduser("~/thesis_data")
FLIGHT_LOCK, BUILD_LOCK = os.path.join(LOCK_DIR, "FLIGHT_LOCK"), os.path.join(LOCK_DIR, "BUILD_LOCK")


def flying():
    if os.path.exists(FLIGHT_LOCK):
        return "FLIGHT_LOCK present"
    for pat in ("[a]rducopter", "[g]z sim"):
        if subprocess.run(["pgrep", "-f", pat], capture_output=True).returncode == 0:
            return f"process matching {pat} running"
    return None


def other_lock():
    """Another job's BUILD_LOCK. Held (wait) while it exists: a stale one is reported, never removed."""
    if not os.path.exists(BUILD_LOCK):
        return None
    try:
        txt = open(BUILD_LOCK).read().strip()
    except OSError:
        return None
    pid = next((int(t) for t in txt.replace("pid", " ").split() if t.isdigit()), None)
    alive = pid is not None and os.path.exists(f"/proc/{pid}")
    return f"BUILD_LOCK held by another job ({'running' if alive else 'STALE?'}): {txt}"


def main():
    a = sys.argv[1:]
    wait_s = 6 * 3600; keep_threads = False
    while a[:1] in (["--wait-s"], ["--keep-threads"]):
        if a[0] == "--wait-s":
            wait_s = float(a[1]); a = a[2:]
        else:
            keep_threads = True; a = a[1:]     # diagnostic only: leave BLAS/OpenMP thread counts at their defaults
    desc, sep, cmd = a[0], a[1], a[2:]
    assert sep == "--" and cmd, __doc__
    t0 = time.time()
    while True:
        why = flying() or other_lock()
        if why is None:
            try:   # O_EXCL: never overwrite another job's BUILD_LOCK (2026-10-08 fix: an earlier version did)
                fd = os.open(BUILD_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o664)
                os.write(fd, f"pid {os.getpid()} started {time.strftime('%Y-%m-%dT%H:%M:%S')} : {desc}\n".encode())
                os.close(fd)
                break
            except FileExistsError:
                why = "BUILD_LOCK appeared"
        if time.time() - t0 > wait_s:
            print(f"[heavy] still blocked after {wait_s:.0f} s ({why}); not running: {desc}", flush=True)
            sys.exit(75)
        print(f"[heavy] waiting: {why}", flush=True)
        time.sleep(60)

    def cleanup(*_):
        try:
            if os.path.exists(BUILD_LOCK) and f"pid {os.getpid()} " in open(BUILD_LOCK).read():
                os.remove(BUILD_LOCK)
        except OSError:
            pass
    signal.signal(signal.SIGTERM, lambda *_: (cleanup(), sys.exit(143)))
    rc = 1
    try:
        env = dict(os.environ) if keep_threads else dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
        rc = subprocess.run(cmd, env=env, preexec_fn=lambda: os.nice(19)).returncode
    finally:
        cleanup()
    if flying():
        print("[heavy] note: a flight lock appeared during this step; start no further step", flush=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
