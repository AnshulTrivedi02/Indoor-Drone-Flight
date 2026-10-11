#!/usr/bin/env python3
"""board-h743 (2a): route AP_NavUKF.cpp's Replay-only stdio through ukf_fopen/ukf_fprintf/ukf_fflush (no-ops on a board)."""
import re, sys
p = sys.argv[1]
s = open(p).read()
n0 = s.count('fprintf(') + s.count('fopen(') + s.count('fflush(')
helpers = '''#if AP_NAVUKF_REPLAY_IO_ENABLED
#include <stdio.h>
#include <stdarg.h>
// Replay-only files (CSV, input dump, geometry and derotation reports): stdio, exactly as before
static void *ukf_fopen(const char *path) { return (void *)fopen(path, "w"); }
static void ukf_fprintf(void *f, const char *fmt, ...) FMT_PRINTF(2, 3);
static void ukf_fprintf(void *f, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vfprintf((FILE *)f, fmt, ap);
    va_end(ap);
}
static void ukf_fflush(void *f) { fflush((FILE *)f); }
#else
// board build (board-h743, 2026-10-11): the Replay-only files are never opened (the set_*() calls leave the pointers
// nullptr) and no file I/O is linked into flight code
static inline void *ukf_fopen(const char *) { return nullptr; }
static inline void ukf_fprintf(void *, const char *, ...) {}
static inline void ukf_fflush(void *) {}
#endif'''
assert s.count('#include <stdio.h>\n') == 1
s = s.replace('fprintf((FILE *)', 'ukf_fprintf(')
s = re.sub(r'fflush\(\(FILE \*\)(\w+)\)', r'ukf_fflush(\1)', s)
s = s.replace('FILE *f = fopen(path, "w");', 'void *f = ukf_fopen(path);')
s = s.replace('        fprintf(f, "TimeUS', '        ukf_fprintf(f, "TimeUS')
s = re.sub(r'= fopen\(path, "w"\);', '= ukf_fopen(path);', s)
left = [l for l in s.splitlines() if re.search(r'(?<![_a-z])(fprintf|fopen|fflush|FILE)\b', l)]
s = s.replace('#include <stdio.h>\n', helpers + '\n', 1)
print('remaining raw stdio lines after the helper block:', left)
open(p, 'w').write(s)
print('ukf_fprintf calls:', s.count('ukf_fprintf('), 'ukf_fflush:', s.count('ukf_fflush('), 'ukf_fopen:', s.count('ukf_fopen('))
