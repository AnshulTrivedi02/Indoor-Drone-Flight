"""UKF safety (b) relay-drain figure, as in the H_safety_ukf_b_v2 entry: the kill instant (fly_trial.log 'KILL ... t_sim='),
the last OF row with quality > 0 received by the FC after it, and the 'position lost' text relative to both.
Usage (venv-ardupilot): python3 ukf_b_drain.py TRIAL"""
import os, re, sys
from pymavlink import mavutil
T = sys.argv[1]
D = os.path.expanduser(f"~/thesis_data/trials/{T}")
CL = os.path.expanduser(f"~/thesis_data/closed_loop/{T}")
t_kill = None
for p in (f"{D}/logs/fly_trial.log",):
    if os.path.exists(p):
        for line in open(p):
            m = re.search(r"KILL .*?t_sim=([\d.]+)", line)
            if m:
                t_kill = float(m.group(1)); break
    if t_kill is not None:
        break
assert t_kill is not None, "no KILL line"
mlog = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
last_of = None; t_text = None
while True:
    m = mlog.recv_match(type=["OF", "MSG"])
    if m is None:
        break
    t = m.TimeUS * 1e-6
    if m.get_type() == "OF" and t >= t_kill and m.Qual > 0:
        last_of = t
    if m.get_type() == "MSG" and t >= t_kill and t_text is None and "position lost" in m.Message:
        t_text = t
print(f"{T}: kill {t_kill:.3f} s; last OF (qual>0) {last_of:.3f} s (drain {last_of - t_kill:+.2f} s); "
      f"'position lost' {t_text:.3f} s = kill {t_text - t_kill:+.2f} s = last OF {t_text - last_of:+.2f} s")
