"""Selected area, current message and draft."""

from golded_ftn import FtnAddress, OutgoingMessage, ParsedMessage

from golded.data.area import Area
from golded.data.store import MessageStore
from golded.logic.quote import reply_intro
from golded.logic.subject import reply_subject, thread_subject
from golded.logic.tear_origin import with_tear_origin
from golded.logic.thread_tree import ThreadRow, build_thread_rows
from golded.logic.user_config import UserConfig


class Session:
    def __init__(
        self,
        store: MessageStore,
        user_config: UserConfig | None = None,
    ) -> None:
        self.__store = store
        self.__user = UserConfig() if user_config is None else user_config
        self.__selected_area: str | None = None
        self.__current_message_index: int | None = None
        self.__draft_message: OutgoingMessage | None = None
        self.__draft_area: str | None = None
        self.__threaded_list = self.__user.threaded_list
        self.__message_rows_cache: list[ThreadRow] | None = None
        self.__cache_area: str | None = None
        self.__cache_threaded: bool | None = None

    def __clear_message_cache(self) -> None:
        self.__message_rows_cache = None

    def areas(self) -> tuple[Area, ...]:
        return self.__store.areas()

    def selected_area(self) -> str | None:
        return self.__selected_area

    def current_message_index(self) -> int | None:
        return self.__current_message_index

    def message_count(self, area: str) -> int:
        return len(self.__store.messages(area))

    def draft_message(self) -> OutgoingMessage | None:
        return self.__draft_message

    def draft_area(self) -> str | None:
        return self.__draft_area

    def threaded_list(self) -> bool:
        return self.__threaded_list

    def toggle_threaded_list(self) -> bool:
        current = self.current_message()
        msgno = None
        if current is not None:
            msgno = current.msgno

        self.__threaded_list = not self.__threaded_list

        if msgno is not None:
            self.select_message(msgno)

        return self.__threaded_list

    def select_area(self, area: str) -> None:
        self.__selected_area = area
        self.__current_message_index = None
        self.__clear_message_cache()

    def message_rows(self) -> list[ThreadRow]:
        if self.__selected_area is None:
            return []

        if (
            self.__message_rows_cache is not None
            and self.__cache_area == self.__selected_area
            and self.__cache_threaded == self.__threaded_list
        ):
            return self.__message_rows_cache

        messages = self.__store.messages(self.__selected_area)

        if self.__threaded_list:
            rows = build_thread_rows(messages)
        else:
            rows = []
            for message in messages:
                rows.append(ThreadRow(message, []))

        self.__cache_area = self.__selected_area
        self.__cache_threaded = self.__threaded_list
        self.__message_rows_cache = rows

        return rows

    def messages(self) -> tuple[ParsedMessage, ...]:
        rows = self.message_rows()
        result = []
        for row in rows:
            result.append(row.message)

        return tuple(result)

    def select_message(self, msgno: int) -> None:
        messages = self.messages()

        for index, message in enumerate(messages):
            if message.msgno == msgno:
                self.__current_message_index = index
                return

        self.__current_message_index = None

    def current_message(self) -> ParsedMessage | None:
        if self.__current_message_index is None:
            return None

        messages = self.messages()
        if self.__current_message_index >= len(messages):
            return None

        return messages[self.__current_message_index]

    def next_message(self) -> None:
        if self.__current_message_index is None:
            return

        messages = self.messages()

        if self.__current_message_index + 1 < len(messages):
            self.__current_message_index = self.__current_message_index + 1

    def previous_message(self) -> None:
        if self.__current_message_index is None:
            return

        if self.__current_message_index > 0:
            self.__current_message_index = self.__current_message_index - 1

    def next_subject_message(self) -> None:
        if self.__current_message_index is None:
            return

        messages = self.messages()

        current = messages[self.__current_message_index]
        subject = thread_subject(current.subject)

        for index, message in enumerate(messages):
            if index <= self.__current_message_index:
                continue
            if thread_subject(message.subject) == subject:
                self.__current_message_index = index
                return

    def previous_subject_message(self) -> None:
        if self.__current_message_index is None:
            return

        messages = self.messages()

        current = messages[self.__current_message_index]
        subject = thread_subject(current.subject)

        for index, message in reversed(list(enumerate(messages))):
            if index >= self.__current_message_index:
                continue
            if thread_subject(message.subject) == subject:
                self.__current_message_index = index
                return

    def area_name(self, area: str) -> str:
        for item in self.__store.areas():
            if item.code == area:
                return item.name

        return area

    def area_kind(self, area: str) -> str:
        for item in self.__store.areas():
            if item.code == area:
                return item.kind

        return "echomail"

    def start_draft_message(self) -> None:
        if self.__selected_area is None:
            return

        to_name = ""
        if self.area_kind(self.__selected_area) == "echomail":
            to_name = "All"

        self.__draft_area = self.__selected_area

        self.__draft_message = OutgoingMessage(
            from_name=self.__user.from_name,
            to_name=to_name,
            subject="",
            body_text=with_tear_origin(
                "",
                self.__user.origin,
                self.__user.from_address,
            ),
            from_address=self.__user.from_address,
        )

    def start_reply_draft(
        self,
        body_for_quote: str,
        subject_for_reply: str | None = None,
    ) -> None:
        if self.__selected_area is None:
            return

        message = self.current_message()
        if message is None:
            return

        if subject_for_reply is None:
            subject_for_reply = message.subject

        body = reply_intro(message.from_name, body_for_quote)

        self.__draft_area = self.__selected_area

        # The reader returns addresses as text; the writer stores str(FtnAddress),
        # so parsing it back gives the same address.
        to_address = None
        if message.from_address is not None:
            to_address = FtnAddress.from_string(message.from_address)

        self.__draft_message = OutgoingMessage(
            from_name=self.__user.from_name,
            to_name=message.from_name,
            subject=reply_subject(subject_for_reply),
            body_text=with_tear_origin(
                body,
                self.__user.origin,
                self.__user.from_address,
            ),
            reply_to_msgno=message.msgno,
            from_address=self.__user.from_address,
            to_address=to_address,
        )

    def set_draft_message(self, message: OutgoingMessage) -> None:
        if self.__draft_area is None:
            return

        self.__draft_message = message

    def discard_draft_message(self) -> None:
        self.__draft_message = None
        self.__draft_area = None

    def save_draft_message(self) -> int | None:
        if self.__draft_message is None or self.__draft_area is None:
            return None

        if self.__draft_message.from_name.strip() == "":
            raise ValueError("from name is required")

        if self.__draft_message.to_name.strip() == "":
            raise ValueError("to name is required")

        if self.__draft_message.subject.strip() == "":
            raise ValueError("subject is required")

        if (
            self.area_kind(self.__draft_area) == "netmail"
            and self.__draft_message.to_address is None
        ):
            raise ValueError("netmail requires a destination address")

        draft = self.__draft_message

        message = OutgoingMessage(
            from_name=draft.from_name,
            to_name=draft.to_name,
            subject=draft.subject,
            body_text=with_tear_origin(
                draft.body_text,
                self.__user.origin,
                draft.from_address,
            ),
            reply_to_msgno=draft.reply_to_msgno,
            from_address=draft.from_address,
            to_address=draft.to_address,
        )

        msgno = self.__store.append(self.__draft_area, message)

        self.__draft_message = None
        self.__draft_area = None
        self.__clear_message_cache()

        return msgno
