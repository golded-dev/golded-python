import unittest

from logic.subject import reply_subject, subject_without_re, thread_subject

class SubjectTests(unittest.TestCase):
    def test_subject_without_re(self):
        self.assertEqual(subject_without_re("Re: Hello"), "Hello")
        self.assertEqual(subject_without_re("re: re: Hello"), "Hello")
        self.assertEqual(subject_without_re("Hello"), "Hello")

    def test_thread_subject(self):
        self.assertEqual(thread_subject("Re: Hello"), "hello")

    def test_reply_subject(self):
        self.assertEqual(reply_subject("Hello"), "Re: Hello")
        self.assertEqual(reply_subject("re: re: Hello"), "Re: Hello")

if __name__ == "__main__":
    unittest.main()
