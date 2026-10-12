"""Raw scan of a dataflash log: FMT table, then a strict walk (header A3 95 + type, length from FMT); counts per type,
lists undeclared types and their byte offsets. Independent of pymavlink's resync behaviour."""
import sys, struct, collections
for p in sys.argv[1:]:
    d = open(p, "rb").read(); n = len(d)
    fmt = {}                         # type -> (name, length)
    # FMT = type 128, length 89: A3 95 80 | type(B) length(B) name(4s) format(16s) labels(64s)
    i = 0; cnt = collections.Counter(); undeclared = collections.Counter(); first_bad = {}
    while i + 3 <= n:
        if d[i] != 0xA3 or d[i + 1] != 0x95:
            # lost sync: search forward for the next header with a known type
            j = d.find(b"\xa3\x95", i + 1)
            if j < 0:
                break
            i = j; continue
        t = d[i + 2]
        if t == 0x80:
            ty, ln = d[i + 3], d[i + 4]; name = d[i + 5:i + 9].rstrip(b"\0").decode(errors="replace")
            fmt[ty] = (name, ln); cnt["FMT"] += 1; i += 89; continue
        if t not in fmt:
            undeclared[t] += 1; first_bad.setdefault(t, i)
            j = d.find(b"\xa3\x95", i + 3)
            if j < 0:
                break
            i = j; continue
        name, ln = fmt[t]
        cnt[name] += 1; i += ln
    want = ["XKF1", "XUKF", "XUKO", "XUKS", "RFRH", "RISI"]
    print(p)
    print("   counts:", {k: cnt[k] for k in want}, " total typed:", sum(cnt.values()))
    print("   undeclared types (no FMT):", dict(undeclared), "first offsets:", first_bad)
    print("   XU FMTs:", sorted(v[0] for v in fmt.values() if v[0].startswith("XU")))
