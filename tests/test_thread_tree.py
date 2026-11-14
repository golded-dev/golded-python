import unittest

from golded.logic.thread_tree import build_thread_rows, format_branch_prefix


class FakeMessage:
    def __init__(self, msgno, reply_to_msgno=None, from_name="") -> None:
        self.msgno = msgno
        self.reply_to_msgno = reply_to_msgno
        self.from_name = from_name


class ThreadTreeTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build_thread_rows([]), [])

    def test_single_message(self):
        rows = build_thread_rows([FakeMessage(1, from_name="Alice")])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].message.msgno, 1)
        self.assertEqual(rows[0].branch_path, [])
        self.assertFalse(rows[0].broken)
        self.assertEqual(format_branch_prefix(rows[0].branch_path), "")

    def test_alice_bob_clara_diana(self):
        # Alice
        # ├─ Bob
        # │  └─ Diana
        # └─ Clara
        messages = [
            FakeMessage(1, from_name="Alice"),
            FakeMessage(2, 1, "Bob"),
            FakeMessage(3, 1, "Clara"),
            FakeMessage(4, 2, "Diana"),
        ]
        rows = build_thread_rows(messages)
        names = [row.message.from_name for row in rows]
        self.assertEqual(names, ["Alice", "Bob", "Diana", "Clara"])
        self.assertEqual(rows[0].branch_path, [])
        self.assertEqual(rows[1].branch_path, [True])
        self.assertEqual(rows[2].branch_path, [True, False])
        self.assertEqual(rows[3].branch_path, [False])
        self.assertEqual(format_branch_prefix(rows[1].branch_path), "├─")
        self.assertEqual(format_branch_prefix(rows[2].branch_path), "│ └─")
        self.assertEqual(format_branch_prefix(rows[3].branch_path), "└─")

    def test_multiple_roots_keep_load_order(self):
        messages = [
            FakeMessage(1, from_name="A"),
            FakeMessage(2, from_name="B"),
            FakeMessage(3, 1, "A2"),
        ]
        rows = build_thread_rows(messages)
        names = [row.message.from_name for row in rows]
        self.assertEqual(names, ["A", "A2", "B"])

    def test_missing_parent_becomes_root(self):
        messages = [
            FakeMessage(2, 99, "Orphan"),
            FakeMessage(3, 2, "Child"),
        ]
        rows = build_thread_rows(messages)
        self.assertEqual(rows[0].message.from_name, "Orphan")
        self.assertEqual(rows[0].branch_path, [])
        self.assertFalse(rows[0].broken)
        self.assertEqual(rows[1].message.from_name, "Child")
        self.assertEqual(rows[1].branch_path, [False])

    def test_cycle_uses_temporary_root(self):
        messages = [
            FakeMessage(1, 2, "A"),
            FakeMessage(2, 1, "B"),
        ]
        rows = build_thread_rows(messages)
        self.assertEqual(len(rows), 2)
        msgnos = [row.message.msgno for row in rows]
        self.assertEqual(sorted(msgnos), [1, 2])
        self.assertTrue(rows[0].broken)
        self.assertEqual(rows[0].branch_path, [])

    def test_each_message_once_in_long_chain(self):
        messages = [FakeMessage(1)]
        for msgno in range(2, 8):
            messages.append(FakeMessage(msgno, msgno - 1))

        rows = build_thread_rows(messages)
        msgnos = [row.message.msgno for row in rows]
        self.assertEqual(msgnos, [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(len(set(msgnos)), 7)

    def test_self_reply_treated_as_root(self):
        rows = build_thread_rows([FakeMessage(1, 1, "Loop")])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].branch_path, [])


if __name__ == "__main__":
    unittest.main()
