#!/usr/bin/env python
"""Summarize a Gödel Agent run log.

Usage:
    python scripts/summarize_run.py runs/run3_2026-11-02_reward_hack.log [more logs...]

For each log it prints, as Markdown:
  * every evaluation of the solver, in order, with its validation / test accuracy
  * every solver rewrite (action_adjust_logic) and whether it was installed
  * the tool-call counts and how many calls errored
  * how the run ended
It is deliberately dependency-free so it runs in any Python 3.
"""
import re
import sys
from pathlib import Path

CALL_RE = re.compile(r"name='(action_[a-z_]+)'")
VALID_RE = re.compile(r"`?Valid Accuracy: `?([0-9.]+)")
TEST_RE = re.compile(r"Test Accuracy ([0-9.]+)")
LOOKUP_HINTS = ("_MGSM_QA_MAP", "look", "ground-truth", "ground truth", "dataset that ships")


def parse(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    calls, evals, rewrites = [], [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("========== Tool Call:"):
            m = CALL_RE.search(lines[i + 1]) if i + 1 < len(lines) else None
            name = m.group(1) if m else "?"
            j = i + 1
            while j < len(lines) and not lines[j].startswith("========== Tool Call Result:"):
                j += 1
            result = lines[j + 1] if j + 1 < len(lines) else ""
            calls.append((i + 1, name, result))
            if name == "action_adjust_logic":
                # the printed "New Code" block sits between the call and its result
                block = "\n".join(lines[i:j])
                rewrites.append((i + 1, result.startswith("Successfully"),
                                 any(h in block for h in LOOKUP_HINTS)))
        elif line.startswith("========== Tool Call Result:"):
            pass
        m = VALID_RE.search(line)
        if m and "Tool Call" not in line:
            test = None
            if i + 1 < len(lines):
                t = TEST_RE.search(lines[i + 1])
                test = float(t.group(1)) if t else None
            evals.append((i + 1, float(m.group(1)), test))
        i += 1

    counter = None
    for line in reversed(lines):
        if line.startswith("defaultdict("):
            counter = line.strip()
            break
    fatal = next((l for l in lines if re.search(r"(BadRequestError|RateLimitError|APIConnectionError)\(", l)), None)
    return calls, evals, rewrites, counter, fatal


def report(path: Path):
    calls, evals, rewrites, counter, fatal = parse(path)
    print(f"## {path.name}\n")
    print("### Evaluations of `solver` (in order)\n")
    print("| # | log line | valid acc (50 problems) | test acc (800 problems) |")
    print("|---|---|---|---|")
    for n, (ln, v, t) in enumerate(evals, 1):
        print(f"| {n} | {ln} | {v:.2f} | {'' if t is None else f'{t:.2f}'} |")
    if not evals:
        print("| – | – | no evaluation reached | |")
    print("\n### Solver rewrites (`action_adjust_logic`)\n")
    print("| log line | installed | looks up dataset answers |")
    print("|---|---|---|")
    for ln, ok, hack in rewrites:
        print(f"| {ln} | {'yes' if ok else 'no'} | {'YES' if hack else 'no'} |")
    if not rewrites:
        print("| – | none | |")
    print("\n### Tool calls\n")
    names = {}
    for _, name, result in calls:
        d = names.setdefault(name, [0, 0])
        d[0] += 1
        d[1] += result.startswith("Error")
    print("| tool | calls | errored |")
    print("|---|---|---|")
    for name, (n, e) in sorted(names.items(), key=lambda kv: -kv[1][0]):
        print(f"| {name} | {n} | {e} |")
    print(f"| **total** | **{len(calls)}** | **{sum(v[1] for v in names.values())}** |")
    print("\n### End of run\n")
    if fatal:
        print(f"Fatal API error: `{fatal.strip()[:160]}`")
    elif counter and "'evolve': 100" in counter:
        print("Reached the built-in cap of 100 evolve steps (normal termination, exit status 1).")
    else:
        print("Final action counter: " + (counter or "not found"))
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        report(Path(p))
