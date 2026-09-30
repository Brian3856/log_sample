from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SampledLine:
    """A single line retained by the sampler.

    Attributes:
        index: The zero-based position of this line among all lines fed to
            the sampler, before any sampling. Stable across calls to ``feed``.
        text: The line's content, exactly as provided to ``feed``.
    """

    index: int
    text: str


class LogSampler:
    """Keep a representative sample of repetitive log lines.

    Logs that repeat the same message many times are hard to read and expensive
    to store. This sampler keeps the first and last occurrence of any repeated
    line verbatim, and collapses the runs in between into a single count. The
    first and last lines carry the timestamps and surrounding context that
    matter most when debugging; the middle is noise.

    Trade-off: lines are compared by exact string equality. Lines that differ
    only in a timestamp or request id are treated as distinct and are not
    collapsed. This is deliberate — guessing which fields to ignore would make
    the sampler's behaviour depend on log format, which we refuse to assume.
    If you need to coalesce near-duplicates, normalize the lines before feeding
    them in.
    """

    def __init__(self) -> None:
        self._first: SampledLine | None = None
        self._last: SampledLine | None = None
        self._middle_count: int = 0
        self._total: int = 0

    def feed(self, line: str) -> None:
        """Accept a single line into the sample.

        The first line seen is always kept as ``first``. Every subsequent line
        updates ``last``. Lines strictly between the first and last that match
        the current last line increment ``middle_count`` instead of replacing
        ``last``; a change in text "commits" the previous run into the middle
        count and starts a new run.

        This means ``middle_count`` is the number of lines that were dropped
        purely because they repeated their immediate predecessor's text. It is
        not the count of any single distinct message across the whole stream.
        """

        if self._first is None:
            self._first = SampledLine(index=self._total, text=line)
            self._last = None
        elif self._last is None:
            if line == self._first.text:
                self._middle_count = 0
            self._last = SampledLine(index=self._total, text=line)
        else:
            if line == self._last.text:
                self._middle_count += 1
            else:
                self._middle_count += 1
            self._last = SampledLine(index=self._total, text=line)
        self._total += 1

    @property
    def total(self) -> int:
        """Number of lines fed to the sampler so far."""
        return self._total

    @property
    def middle_count(self) -> int:
        """Lines dropped between ``first`` and ``last`` due to repetition.

        See ``feed`` for the exact accounting; this is per-run repetition, not
        global deduplication.
        """
        return self._middle_count

    @property
    def first(self) -> SampledLine | None:
        """The first line fed, or ``None`` if nothing has been fed."""
        return self._first

    @property
    def last(self) -> SampledLine | None:
        """The most recent line fed, or ``None`` if fewer than two lines fed."""
        return self._last

    def sampled(self) -> list[SampledLine]:
        """Return the retained sample as a list.

        The list always begins with ``first`` (if any) and ends with ``last``
        (if any and distinct from ``first``). When ``middle_count`` is positive
        a single placeholder is inserted between them carrying the dropped
        count in its ``text`` field. Returning a placeholder keeps the list a
        faithful, renderable transcript rather than asking callers to
        interleave counts themselves.
        """
        if self._first is None:
            return []
        if self._last is None:
            return [self._first]
        if self._middle_count == 0:
            return [self._first, self._last] if self._first.index != self._last.index else [self._first]
        return [self._first, SampledLine(index=-1, text=f"... {self._middle_count} repeated line(s) omitted ..."), self._last]
