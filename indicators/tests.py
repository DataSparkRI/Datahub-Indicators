
from django.test import TestCase

class IndicatorTest(TestCase):
    def test_indicator_resolution(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)
