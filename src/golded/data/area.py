"""One message area in the store."""


class Area:
    def __init__(self, code: str, name: str, kind: str = "echomail") -> None:
        self.code = code
        self.name = name
        self.kind = kind
