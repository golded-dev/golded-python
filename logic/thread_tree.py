"""Build a flat message list in depth-first thread order."""

class ThreadRow:
    def __init__(self, message, branch_path: list[bool], broken: bool = False) -> None:
        self.message = message
        self.branch_path = branch_path
        self.broken = broken

def format_branch_prefix(branch_path: list[bool]) -> str:
    if len(branch_path) == 0:
        return ""

    parts = []
    last = len(branch_path) - 1

    for index in range(len(branch_path)):
        more = branch_path[index]
        if index < last:
            if more:
                parts.append("│ ")
            else:
                parts.append("  ")
        else:
            if more:
                parts.append("├─")
            else:
                parts.append("└─")

    return "".join(parts)

def build_thread_rows(messages: list) -> list[ThreadRow]:
    by_msgno = {}
    for message in messages:
        by_msgno[message.msgno] = message

    roots = []
    replies_by_msgno = {}

    for message in messages:
        parent = message.reply_to_msgno
        if parent is None or parent == message.msgno or parent not in by_msgno:
            roots.append(message)
            continue

        if parent not in replies_by_msgno:
            replies_by_msgno[parent] = []

        replies_by_msgno[parent].append(message)

    rows = []
    visited = set()

    for root in roots:
        _walk_thread(root, [], replies_by_msgno, rows, visited, False)

    for message in messages:
        if message.msgno in visited:
            continue

        _walk_thread(message, [], replies_by_msgno, rows, visited, True)

    return rows

def _walk_thread(
    root,
    start_path: list[bool],
    replies_by_msgno: dict[int, list],
    rows: list[ThreadRow],
    visited: set[int],
    broken: bool,
) -> None:
    stack = [(root, start_path, broken)]

    while len(stack) > 0:
        message, branch_path, is_broken = stack.pop()

        if message.msgno in visited:
            continue

        visited.add(message.msgno)
        rows.append(ThreadRow(message, branch_path, is_broken))

        replies = []
        if message.msgno in replies_by_msgno:
            replies = replies_by_msgno[message.msgno]

        for index in range(len(replies) - 1, -1, -1):
            has_more = index < len(replies) - 1
            new_path = list(branch_path)
            new_path.append(has_more)
            stack.append((replies[index], new_path, False))
