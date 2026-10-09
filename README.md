# Log Sample

A tiny library that samples repetitive log lines while always keeping the first and last occurrence verbatim.

```python
from log_sample import LogSampler, SampledLine

lines = ["boot", "running", "running", "running", "done"]
sampler = LogSampler()
for line in lines:
    sampler.feed(line)

for entry in sampler.sampled():
    print(entry.text)
print(f"{sampler.middle_count} lines dropped; {sampler.total} lines seen")
```

`LogSampler` exposes `feed(line)`, `sampled()`, `total`, `middle_count`, `first`, and `last`. Each retained line is a `SampledLine(index, text)` where `index` is the zero-based position among all lines fed.

## Why

Repetitive logs waste space and attention. The first and last occurrences of a run carry the useful context — when it started and when it stopped — while the middle is identical noise. This sampler keeps those bookends and collapses the intervening run into a single count, so a thousand-line spam burst becomes three entries.

The trade-off is exact string comparison. Lines that differ only in a timestamp or request id are treated as distinct and are not collapsed. Normalizing those fields is the caller's job; doing it here would force the sampler to assume a log format, which it refuses to.

## Edge to know about

`middle_count` counts lines dropped because they repeated their *immediate predecessor*, not the total occurrences of any message across the whole stream. In an alternating `a, b, a, b, a` sequence every line after the first differs from its predecessor, so `middle_count` reflects the repeated `a` and `b` runs as committed each time the text changes — it is not a global deduplication count. See the docstring on `feed` for the exact accounting.

## Example output

The snippet above prints:

```
boot
... 2 repeated line(s) omitted ...
done
2 lines dropped; 5 lines seen
```

## Example with a list of lines

If you want to try it without opening a file:

```python
from log_sample import LogSampler, SampledLine

sampler = LogSampler()
lines = ["boot", "running", "running", "running", "done"]
for line in lines:
    sampler.feed(line)

for entry in sampler.sampled():
    print(entry.text)
print(f"{sampler.middle_count} lines dropped; {sampler.total} lines seen")
```

Output:

```
boot
... 2 repeated line(s) omitted ...
done
2 lines dropped; 5 lines seen
```

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

