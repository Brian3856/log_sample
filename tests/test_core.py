import unittest

from log_sample import LogSampler, SampledLine


class TestLogSampler(unittest.TestCase):
    def test_empty_sampler(self):
        s = LogSampler()
        self.assertEqual(s.total, 0)
        self.assertEqual(s.middle_count, 0)
        self.assertIsNone(s.first)
        self.assertIsNone(s.last)
        self.assertEqual(s.sampled(), [])

    def test_single_line(self):
        s = LogSampler()
        s.feed("hello")
        self.assertEqual(s.total, 1)
        self.assertEqual(s.middle_count, 0)
        self.assertEqual(s.first, SampledLine(index=0, text="hello"))
        self.assertIsNone(s.last)
        self.assertEqual(s.sampled(), [SampledLine(index=0, text="hello")])

    def test_two_distinct_lines(self):
        s = LogSampler()
        s.feed("a")
        s.feed("b")
        self.assertEqual(s.total, 2)
        self.assertEqual(s.middle_count, 0)
        self.assertEqual(s.first, SampledLine(index=0, text="a"))
        self.assertEqual(s.last, SampledLine(index=1, text="b"))
        self.assertEqual(s.sampled(), [SampledLine(index=0, text="a"), SampledLine(index=1, text="b")])

    def test_two_identical_lines(self):
        s = LogSampler()
        s.feed("x")
        s.feed("x")
        self.assertEqual(s.total, 2)
        self.assertEqual(s.middle_count, 0)
        self.assertEqual(s.first, SampledLine(index=0, text="x"))
        self.assertEqual(s.last, SampledLine(index=1, text="x"))
        result = s.sampled()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], SampledLine(index=0, text="x"))
        self.assertEqual(result[1], SampledLine(index=1, text="x"))

    def test_three_identical_lines(self):
        s = LogSampler()
        s.feed("y")
        s.feed("y")
        s.feed("y")
        self.assertEqual(s.total, 3)
        self.assertEqual(s.middle_count, 1)
        self.assertEqual(s.first, SampledLine(index=0, text="y"))
        self.assertEqual(s.last, SampledLine(index=2, text="y"))
        result = s.sampled()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], SampledLine(index=0, text="y"))
        self.assertEqual(result[2], SampledLine(index=2, text="y"))
        self.assertIn("1", result[1].text)
        self.assertEqual(result[1].index, -1)

    def test_repeating_run_then_change(self):
        s = LogSampler()
        s.feed("a")
        s.feed("b")
        s.feed("b")
        s.feed("b")
        s.feed("c")
        self.assertEqual(s.total, 5)
        self.assertEqual(s.middle_count, 3)
        self.assertEqual(s.first, SampledLine(index=0, text="a"))
        self.assertEqual(s.last, SampledLine(index=4, text="c"))
        result = s.sampled()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text, "a")
        self.assertIn("3", result[1].text)
        self.assertEqual(result[2].text, "c")

    def test_alternating_lines(self):
        s = LogSampler()
        for line in ["a", "b", "a", "b", "a"]:
            s.feed(line)
        self.assertEqual(s.total, 5)
        self.assertEqual(s.middle_count, 3)
        self.assertEqual(s.first, SampledLine(index=0, text="a"))
        self.assertEqual(s.last, SampledLine(index=4, text="a"))
        result = s.sampled()
        self.assertEqual(len(result), 3)

    def test_indices_are_global(self):
        s = LogSampler()
        s.feed("p")
        s.feed("q")
        s.feed("r")
        self.assertEqual(s.first.index, 0)
        self.assertEqual(s.last.index, 2)

    def test_feed_empty_string(self):
        s = LogSampler()
        s.feed("")
        self.assertEqual(s.first, SampledLine(index=0, text=""))
        self.assertIsNone(s.last)
        self.assertEqual(s.sampled(), [SampledLine(index=0, text="")])

    def test_multiple_batches(self):
        s = LogSampler()
        s.feed("a")
        s.feed("a")
        self.assertEqual(s.middle_count, 0)
        s.feed("a")
        self.assertEqual(s.middle_count, 1)
        s.feed("b")
        self.assertEqual(s.middle_count, 2)
        self.assertEqual(s.last, SampledLine(index=3, text="b"))


if __name__ == "__main__":
    unittest.main()
