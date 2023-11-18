from enum import Enum
from typing import NamedTuple


class Tag(NamedTuple):
    name: str


class Translator(NamedTuple):
    name: str


class Status(Enum):
    UNDEFINED = 0
    CONTINUES = 1
    COMPLETED = 2


class Manga(NamedTuple):
    url: str
    title: str
    author: str
    tags: list[Tag]
    translators: list[Translator]
    manga_status: Status
    translate_status: Status
    volumes: int
    chapters: int

