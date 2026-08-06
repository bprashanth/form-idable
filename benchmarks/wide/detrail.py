#!/usr/bin/env python3
"""FAILED APPROACH — kept as a record so it is not retried. Do not use.

Measured on 31 structure-diverse forms:
  novelty + arithmetic signals : mean numF1 0.375 -> 0.358 (recall 0.80 -> 0.68)
  arithmetic signal alone      : mean numF1 0.375 -> 0.289 (recall 0.80 -> 0.56)

Both signals are CONFOUNDED with legitimate form structure:
  * novelty    — ecology tables are legitimately repetitive; a column of
                 `N N N N N` or `L L L L` is low-novelty BY DESIGN.
  * arithmetic — a serial-number column (1,2,3,4,…) IS an arithmetic
                 progression, so the detector cuts at the START of every
                 well-formed table. It destroyed near-perfect results
                 (nrcs_rangeland 0.977 -> 0.280, agrra_benthos 0.821 -> 0.129).

What DOES work: bounding output length by the number of ruled rows detected on
the PAGE (golden-sized cap simulated at 0.388 -> 0.530). Measure the document,
do not pattern-match the model's output. And the real fix is training data with
sparse fill — see FINDINGS.

Original description follows.

Trim the degenerate tail off a transcription.

Measured failure of the LoRA-tuned small model: it reads the page correctly and
then keeps going, emitting invented rows — often a literal arithmetic
progression (`37.7,6.4 / 37.8,6.4 / 37.9,6.4 …`). Recall stays 0.9+ while
precision collapses to 0.06. The good content comes FIRST, so cutting the tail
recovers most of the loss.

Unlike a length cap this needs no knowledge of the expected output size, so it
works at inference time with nothing but the model's own output.

Two signals, both scale-free:
  * novelty  — a line whose tokens are all already-seen adds nothing
  * monotone — a run of lines whose leading number steps by a near-constant
               delta is a counting sequence, not transcription

Usage: python3 detrail.py <in.txt> [out.txt]      (also importable: trim())
"""
import re, sys
from pathlib import Path

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _toks(line):
    return [t for t in re.split(r"[\s,;/|]+", line.strip().lower()) if t]


def _lead_num(line):
    m = _NUM.search(line)
    return float(m.group()) if m else None


def trim(text, novelty_window=12, novelty_floor=0.12, run_len=6, delta_tol=0.35):
    """Return text with the degenerate tail removed."""
    lines = text.splitlines()
    if len(lines) < 20:
        return text

    seen = set()
    novelty = []
    for ln in lines:
        ts = _toks(ln)
        if not ts:
            novelty.append(1.0); continue
        new = sum(1 for t in ts if t not in seen)
        novelty.append(new / len(ts))
        seen.update(ts)

    cut = len(lines)

    # 1) sustained low novelty -> the model is recycling tokens
    for i in range(len(lines) - novelty_window):
        w = novelty[i:i + novelty_window]
        if sum(w) / len(w) < novelty_floor:
            cut = min(cut, i)
            break

    # 2) an arithmetic run in the leading number -> a counting sequence
    nums = [_lead_num(l) for l in lines]
    i = 0
    while i < len(nums) - run_len:
        seq = nums[i:i + run_len]
        if all(v is not None for v in seq):
            ds = [seq[k + 1] - seq[k] for k in range(len(seq) - 1)]
            if ds[0] != 0 and all(abs(d - ds[0]) <= delta_tol * max(abs(ds[0]), 1e-6)
                                  for d in ds):
                cut = min(cut, i)
                break
        i += 1

    # never cut away a page marker's content wholesale: keep at least the first
    # third of what was produced
    cut = max(cut, len(lines) // 3)
    return "\n".join(lines[:cut])


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = trim(src.read_text())
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(out)
    else:
        sys.stdout.write(out)
