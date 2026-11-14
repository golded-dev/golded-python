import unittest
from importlib.metadata import version

from golded.logic.version import VERSION


class TestVersion(unittest.TestCase):
    def test_constant_matches_distribution(self) -> None:
        self.assertEqual(VERSION, version("golded"))
