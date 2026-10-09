#!/bin/bash
# emit driver END/SKIP/DONE lines; exit when the driver is gone or after $1 s
L=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2/driver.log
end=$(( $(date +%s) + ${1:-1790} )); n=${2:-0}
while [ $(date +%s) -lt $end ]; do
  c=$(wc -l < $L)
  if [ $c -gt $n ]; then sed -n "$((n+1)),${c}p" $L | grep -E "END|SKIP|fail|DONE"; n=$c; fi
  pgrep -f "yawgate2/driver.sh" >/dev/null || { echo "driver not alive (lines $n)"; exit 0; }
  sleep 15
done
echo "watch timeout at line $n"
