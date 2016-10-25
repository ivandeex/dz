import random
from django.test import TestCase, tag
from dz.ranges import merge_ranges, split_ranges


@tag('ranges')
class RangesTests(TestCase):
    MAX_LENGTH = 1000
    LOOPS_PER_SAMPLE = 10

    def test_ranges(self):
        full_sample = list(range(self.MAX_LENGTH))
        for sample_len in range(self.MAX_LENGTH):
            for loops in range(self.LOOPS_PER_SAMPLE):
                sample = set(random.sample(full_sample, sample_len))
                result = split_ranges(merge_ranges(sample))
                self.assertEquals(sample, result)
