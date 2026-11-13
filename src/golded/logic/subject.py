"""Subject line helpers for threads and replies."""

def subject_without_re(subject: str) -> str:
    text = subject.strip()

    while True:
        lower = text.lower()
        if lower.startswith("re:"):
            text = text[3:].lstrip()
        else:
            break

    return text

def thread_subject(subject: str) -> str:
    return subject_without_re(subject).lower()

def reply_subject(subject: str) -> str:
    return "Re: " + subject_without_re(subject)
