import unittest

from golded.logic.quote import (
    body_without_tearline,
    first_name,
    has_golded_tagline,
    quote_body,
    quote_initials,
    reply_intro,
    split_body_at_tagline,
)

class QuoteTests(unittest.TestCase):
    def test_initials_one_word(self):
        self.assertEqual(quote_initials("Odinn"), "O")

    def test_initials_first_and_last(self):
        self.assertEqual(quote_initials("Alice Bob"), "AB")

    def test_initials_skips_middle_name(self):
        self.assertEqual(quote_initials("Vasya S Pupkin"), "VP")

    def test_initials_empty(self):
        self.assertEqual(quote_initials(""), "")
        self.assertEqual(quote_initials("   "), "")

    def test_body_without_tearline(self):
        body = "Hello\n\n--- GoldED/Py\n * Origin: somewhere"
        self.assertEqual(body_without_tearline(body), "Hello\n")

    def test_body_without_tearline_keeps_user_dashes(self):
        body = "Før\n---- skillelinje\nEfter"
        self.assertEqual(body_without_tearline(body), body)

    def test_body_without_tearline_only_strips_trailing_footer(self):
        body = "Før\n---- midt\nEfter\n\n--- GoldED/Py\n * Origin: x"
        self.assertEqual(body_without_tearline(body), "Før\n---- midt\nEfter\n")

    def test_quote_multiline(self):
        quoted = quote_body("Alice Bob", "line one\nline two")
        self.assertEqual(quoted, "AB> line one\nAB> line two\n")

    def test_quote_blank_line(self):
        quoted = quote_body("Odinn", "hi\n\nthere")
        self.assertEqual(quoted, "O> hi\nO>\nO> there\n")

    def test_quote_stops_at_tearline(self):
        body = "Hello\n--- GoldED/Py\n * Origin: x"
        quoted = quote_body("Bob", body)
        self.assertEqual(quoted, "B> Hello\n")
        self.assertNotIn("GoldED", quoted)

    def test_quote_empty_name(self):
        quoted = quote_body("", "hello")
        self.assertEqual(quoted, "> hello\n")

    def test_quote_empty_body(self):
        self.assertEqual(quote_body("Alice", ""), "\n")

    def test_first_name(self):
        self.assertEqual(first_name("Alice Bob"), "Alice")
        self.assertEqual(first_name("Odinn"), "Odinn")
        self.assertEqual(first_name(""), "")

    def test_reply_intro(self):
        text = reply_intro("Alice Bob", "Hello")
        self.assertEqual(text, "Hello Alice\n\nAB> Hello\n")

    def test_split_body_at_tagline(self):
        body = "Hello\n\n--- GoldED/Py\n * Origin: x"
        main, tag = split_body_at_tagline(body)
        self.assertEqual(main, "Hello\n")
        self.assertEqual(tag, "--- GoldED/Py\n * Origin: x")

    def test_has_golded_tagline(self):
        self.assertTrue(has_golded_tagline("Hi\n--- GoldED/Py\n"))
        self.assertFalse(has_golded_tagline("Hi\n--- Other\n"))
        self.assertFalse(has_golded_tagline("Hi only"))

if __name__ == "__main__":
    unittest.main()
