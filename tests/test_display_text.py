import unittest

from golded.logic.display_text import for_display


class DisplayTextTests(unittest.TestCase):
    def test_off_returns_same_text(self) -> None:
        text = "MLJ> svµre med bonsai kommer f°rst"
        self.assertEqual(for_display(text, False), text)

    def test_on_repairs_quoted_danish(self) -> None:
        damaged = "MLJ> svµre med bonsai kommer f°rst"
        repaired = for_display(damaged, True)
        self.assertIn("svære", repaired)
        self.assertIn("først", repaired)
        self.assertNotIn("µ", repaired)

    def test_on_repairs_trailing_mu_subject(self) -> None:
        self.assertEqual(for_display("Kastanjetrµ", True), "Kastanjetræ")
