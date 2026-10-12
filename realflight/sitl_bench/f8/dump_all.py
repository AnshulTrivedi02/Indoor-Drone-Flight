"""F8: dump every wbench/wbench2 session's dataflash (read-only) to <out_dir>/<session>__<bin>.pkl."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dump_df  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for b in sorted(glob.glob(os.path.expanduser("~/thesis_data/wbench/wbench*/dataflash/*.BIN"))):
    sess = b.split("/")[-3]
    p = os.path.join(out, f"{sess}__{os.path.basename(b)[:-4]}.pkl")
    if os.path.exists(p):
        continue
    print(p, flush=True)
    dump_df.main(b, p)
