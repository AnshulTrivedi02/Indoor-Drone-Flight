#!/usr/bin/env python3
"""Mocap recorder (rung-1 item R7): logs every pose from a PoseSource to a raw CSV plus a JSON metadata sidecar.

The raw log keeps EVERYTHING the stream gave, in the mocap's own frame and clock: no frame conversion, no filtering
(a wrong up-axis guess or a filter choice can then be fixed later in export.py, never by re-flying).

Raw CSV columns (one row per accepted sample):
  frame_no, t_mocap, t_rx_mono, t_rx_wall, body_id, body_name, tracked, px, py, pz, qw, qx, qy, qz, segment
  t_mocap   the mocap clock (s), as sent;  t_rx_mono  receipt, this host's monotonic clock;  t_rx_wall  receipt, epoch s.
  tracked   1 / 0 (NOT tracked: the row is kept raw, export drops it) / -1 (the system gives no flag).

  segment   0 at the start; +1 at each RESTART of that body's stream (below).

Rejected (counted, not written): malformed packets; duplicates and out-of-order frames (frame_no <= the last one
written for that body); bodies other than --body-id / --body-name when one is given.

RESTARTS (2026-10-11 fix; before it, a forwarder or Motive restart reset the frame counter and every later frame was
dropped as a "duplicate", i.e. the rest of the flight was silently discarded). A new segment starts when:
  - frame_no jumps BACK by more than RESTART_JUMP_FRAMES (a counter reset): immediately, at that sample; or
  - RESTART_CONSEC consecutive would-be rejections have strictly increasing frame numbers among themselves (a reset to a
    number close below the last one): they are held, and written once the restart is declared, so no frame of the new
    segment is lost; a run that does not reach RESTART_CONSEC is counted as duplicates;
  - t_mocap steps backwards while frame_no increases (a mocap clock reset; also counted as a clock fault).
  Each restart is logged in the metadata (`restarts`: kind, frames and t_mocap / t_rx before and after) and that body's
  bookkeeping is reset (no spurious clock fault, time gap or frame gap across it). export.py then refuses a multi-segment
  log whose mocap clock is not continuous unless one segment is named.

Dropouts (written to the metadata, per body):
  - frame gaps: frame_no jumps by more than 1 (the number of missing frames is recorded);
  - time gaps: t_mocap step > GAP_FACTOR x the running median step;
  - silences: no packet at all for >= --silence-s (receive clock), with start and end;
  - clock faults: t_mocap not increasing while frame_no increases (a mocap clock reset: the time sync then fails, so
    it is flagged loudly).
The metadata is rewritten every few seconds, so a crash still leaves a usable sidecar.

Usage (any Python 3 with the standard library; numpy is not needed):
  python3 -m realflight.mocap.recorder --port 51001 --out-dir ~/thesis_data/mocap --name flight01 [--body-id 1]
  Stop with Ctrl+C (or --duration S). Then: python3 -m realflight.mocap.export ...
"""
import argparse, json, os, select, signal, socket, statistics, sys, time
from collections import deque
from datetime import datetime, timezone

from .source import PACKET, PoseSource, UdpPoseSource

COLUMNS = ["frame_no", "t_mocap", "t_rx_mono", "t_rx_wall", "body_id", "body_name", "tracked",
           "px", "py", "pz", "qw", "qx", "qy", "qz", "segment"]
GAP_FACTOR = 3.0
RESTART_JUMP_FRAMES = 100      # a backward frame jump larger than this is a counter reset (UDP reordering is << this)
RESTART_CONSEC = 10            # ... or this many consecutive, mutually increasing would-be rejections
META_EVERY_S = 5.0


class BodyState:
    def __init__(self):
        self.last_frame = None; self.last_t = None; self.dts = deque(maxlen=200)
        self.written = 0; self.dupes = 0; self.not_tracked = 0; self.missing_frames = 0
        self.frame_gaps = []; self.time_gaps = []; self.clock_faults = []
        self.first_t = None; self.first_rx = None
        self.segment = 0; self.restarts = []; self.pending = []     # pending: a run of would-be rejections (restart?)
        self.last_rx = None


class Recorder:
    """I/O-light core: accept(samples) writes rows and updates the bookkeeping; testable without sockets."""

    def __init__(self, csv_path, meta_path, meta_static, body_id=None, body_name=None, silence_s=0.5):
        self.csv_path, self.meta_path = csv_path, meta_path
        self.f = open(csv_path, "w", buffering=1 << 16)
        self.f.write(",".join(COLUMNS) + "\n")
        self.meta_static = meta_static
        self.body_id, self.body_name, self.silence_s = body_id, body_name, silence_s
        self.bodies = {}; self.other_body = 0; self.received = 0
        self.silences = []; self.last_rx = None; self.in_silence_since = None
        self.t_start_wall = time.time(); self.t_start_mono = time.monotonic()
        self.status = "recording"
        self.write_meta()

    def _wanted(self, s):
        if self.body_id is not None and s.body_id != self.body_id:
            return False
        if self.body_name is not None and s.body_name != self.body_name:
            return False
        return True

    def accept(self, samples):
        for s in samples:
            self.received += 1
            if not self._wanted(s):
                self.other_body += 1
                continue
            if self.last_rx is not None and s.t_rx - self.last_rx >= self.silence_s:
                self.silences.append({"from_rx_mono": self.last_rx, "to_rx_mono": s.t_rx, "length_s": s.t_rx - self.last_rx})
            self.last_rx = s.t_rx
            b = self.bodies.setdefault(f"{s.body_id}:{s.body_name}", BodyState())
            if b.last_frame is not None and s.frame_no <= b.last_frame:
                if b.last_frame - s.frame_no > RESTART_JUMP_FRAMES:
                    b.dupes += len(b.pending); b.pending = []
                    self._restart(b, s, "frame_counter_reset")
                    self._write(b, s)
                    continue
                if b.pending and s.frame_no > b.pending[-1].frame_no:
                    b.pending.append(s)
                else:
                    b.dupes += len(b.pending); b.pending = [s]
                if len(b.pending) >= RESTART_CONSEC:
                    held, b.pending = b.pending, []
                    self._restart(b, held[0], "frame_counter_reset")
                    for h in held:
                        self._write(b, h)
                continue
            b.dupes += len(b.pending); b.pending = []          # a held run that did not continue: duplicates after all
            self._write(b, s)

    def _restart(self, b, s, kind):
        b.restarts.append({"kind": kind, "new_segment": b.segment + 1, "last_frame_before": b.last_frame,
                           "last_t_mocap_before": b.last_t, "last_t_rx_before": b.last_rx,
                           "first_frame_after": s.frame_no, "first_t_mocap_after": s.t_mocap, "first_t_rx_after": s.t_rx})
        b.segment += 1; b.last_frame = None; b.last_t = None; b.dts.clear()

    def _write(self, b, s):
        if b.last_frame is not None:
            dt = s.t_mocap - b.last_t
            if dt <= 0:                                    # a mocap clock reset: flagged, and a new segment
                b.clock_faults.append({"frame_no": s.frame_no, "t_mocap": s.t_mocap, "previous_t_mocap": b.last_t})
                self._restart(b, s, "mocap_clock_reset")
            else:
                if s.frame_no - b.last_frame > 1:
                    n = s.frame_no - b.last_frame - 1; b.missing_frames += n
                    b.frame_gaps.append({"after_frame": b.last_frame, "missing": n, "t_mocap_before": b.last_t,
                                         "t_mocap_after": s.t_mocap})
                if len(b.dts) >= 20 and dt > GAP_FACTOR * statistics.median(b.dts):
                    b.time_gaps.append({"t_mocap_before": b.last_t, "t_mocap_after": s.t_mocap, "length_s": dt})
                b.dts.append(dt)
        if b.first_t is None:
            b.first_t, b.first_rx = s.t_mocap, s.t_rx
        b.last_frame, b.last_t, b.last_rx = s.frame_no, s.t_mocap, s.t_rx
        if s.tracked == 0:
            b.not_tracked += 1
        b.written += 1
        name = s.body_name.replace(",", "_")
        self.f.write(f"{s.frame_no},{s.t_mocap:.9f},{s.t_rx:.9f},{s.t_rx_wall:.6f},{s.body_id},{name},"
                     f"{s.tracked},{s.pos[0]:.6f},{s.pos[1]:.6f},{s.pos[2]:.6f},"
                     f"{s.quat[0]:.9f},{s.quat[1]:.9f},{s.quat[2]:.9f},{s.quat[3]:.9f},{b.segment}\n")

    def check_silence(self, now_mono):
        """Called from the loop: an ongoing silence is reported in the metadata even if no packet ever returns."""
        if self.last_rx is not None and now_mono - self.last_rx >= self.silence_s:
            self.in_silence_since = self.last_rx
        else:
            self.in_silence_since = None

    def summary(self, bad=0):
        bodies = {}
        for k, b in self.bodies.items():
            med = statistics.median(b.dts) if b.dts else None
            longest = max([g["length_s"] for g in b.time_gaps] + [0.0])
            bodies[k] = {"written": b.written, "duplicates_or_out_of_order": b.dupes + len(b.pending),
                         "not_tracked_rows": b.not_tracked, "segments": b.segment + 1, "restarts": b.restarts[:100],
                         "missing_frames": b.missing_frames, "n_frame_gaps": len(b.frame_gaps),
                         "n_time_gaps": len(b.time_gaps), "longest_time_gap_s": longest,
                         "median_step_s": med, "rate_hz": (1.0 / med) if med else None,
                         "first_t_mocap": b.first_t, "last_t_mocap": b.last_t,
                         "clock_faults": b.clock_faults[:50], "n_clock_faults": len(b.clock_faults),
                         "frame_gaps": b.frame_gaps[:500], "time_gaps": b.time_gaps[:500]}
        return {"received": self.received, "malformed": bad, "other_body_ignored": self.other_body, "bodies": bodies,
                "silences": self.silences[:500],
                "ongoing_silence_since_rx_mono": self.in_silence_since,
                "longest_silence_s": max([x["length_s"] for x in self.silences] + [0.0])}

    def write_meta(self, bad=0):
        meta = {**self.meta_static, "status": self.status,
                "start_utc": datetime.fromtimestamp(self.t_start_wall, timezone.utc).isoformat(),
                "start_rx_mono": self.t_start_mono, "updated_utc": datetime.now(timezone.utc).isoformat(),
                "csv": os.path.basename(self.csv_path), "columns": COLUMNS, **self.summary(bad)}
        tmp = self.meta_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(meta, f, indent=1)
        os.replace(tmp, self.meta_path)

    def close(self, bad=0):
        self.f.flush(); self.f.close()
        self.status = "complete"
        self.write_meta(bad)


def run(source: PoseSource, rec: Recorder, duration=None, stop=lambda: False):
    t0 = time.monotonic(); next_meta = t0 + META_EVERY_S
    while not stop():
        now = time.monotonic()
        if duration is not None and now - t0 >= duration:
            break
        r, _, _ = select.select([source], [], [], 0.1)
        if r:
            rec.accept(source.poll())
        rec.check_silence(time.monotonic())
        if time.monotonic() >= next_meta:
            rec.f.flush(); rec.write_meta(source.bad); next_meta += META_EVERY_S
    rec.accept(source.poll())


def main(argv=None):
    ap = argparse.ArgumentParser(description="mocap recorder (MCP1 UDP)")
    ap.add_argument("--host", default="0.0.0.0"); ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out-dir", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--body-id", type=int); ap.add_argument("--body-name")
    ap.add_argument("--duration", type=float); ap.add_argument("--silence-s", type=float, default=0.5)
    ap.add_argument("--up-axis", choices=["z", "y"], help="the mocap world's up axis, if known (recorded only; "
                    "applied by export)")
    ap.add_argument("--notes", default="")
    a = ap.parse_args(argv)
    os.makedirs(os.path.expanduser(a.out_dir), exist_ok=True)
    base = os.path.join(os.path.expanduser(a.out_dir), a.name)
    if os.path.exists(base + ".csv"):
        sys.exit(f"{base}.csv exists: refusing to overwrite a recording")
    src = UdpPoseSource(a.host, a.port)
    meta = {"recorder": "realflight.mocap.recorder", "adapter": "UdpPoseSource (MCP1)", "packet_struct": PACKET.format,
            "host": socket.gethostname(), "listen": [a.host, src.port], "body_id_filter": a.body_id,
            "body_name_filter": a.body_name, "up_axis_declared": a.up_axis, "notes": a.notes,
            "quaternion_order_in_csv": "w,x,y,z (scalar first, as sent)", "frame": "the mocap world frame, unconverted"}
    rec = Recorder(base + ".csv", base + ".meta.json", meta, a.body_id, a.body_name, a.silence_s)
    flag = {"stop": False}
    def _stop(*_):
        flag["stop"] = True
    signal.signal(signal.SIGINT, _stop); signal.signal(signal.SIGTERM, _stop)
    print(f"[mocap recorder] listening on {a.host}:{src.port} -> {base}.csv", flush=True)
    try:
        run(src, rec, a.duration, lambda: flag["stop"])
    finally:
        rec.close(src.bad); src.close()
    s = rec.summary(src.bad)
    print(f"[mocap recorder] received {s['received']}, malformed {s['malformed']}, bodies "
          + ", ".join(f"{k}: {v['written']} rows, {v['missing_frames']} missing frames, longest gap "
                      f"{v['longest_time_gap_s']:.3f} s" for k, v in s["bodies"].items()), flush=True)


if __name__ == "__main__":
    main()
