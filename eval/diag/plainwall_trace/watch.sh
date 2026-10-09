#!/bin/bash
# Wait loop: reports each job exit; stops on BOTHDONE, on both.sh dying, or after ~29 min.
L=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw
seen=""
for i in $(seq 1 174); do
  for f in $L/logs/*.log; do
    [ -e "$f" ] || continue
    if grep -q "^exit" "$f" && ! echo "$seen" | grep -q "$f"; then echo "$(basename $f): $(grep '^exit' $f)"; seen="$seen $f"; fi
  done
  if grep -q BOTHDONE $L/heavy1.log 2>/dev/null; then echo BOTHDONE; exit 0; fi
  if ! pgrep -f "[b]oth.sh" >/dev/null; then echo "both.sh not alive"; exit 1; fi
  sleep 10
done
echo TIMEOUT
