from dataclasses import dataclass
from typing import ClassVar, Type, Dict, TypeVar

T = TypeVar("T", bound="TaggedUnion")

class TaggedUnion:
    _registry: ClassVar[Dict[str, Type[T]]] = {}

    @classmethod
    def register(cls, tag: str):
        def wrapper(subcls: Type[T]):
            cls._registry[tag] = subcls
            return subcls
        return wrapper

    @classmethod
    def dispatch(cls, data: dict) -> Type[T]:
        tag = data["type"]
        return cls._registry.get(tag, DynamicTaggedNode)

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        impl = cls.dispatch(data)
        return impl._from_payload(data)

    @classmethod
    def _from_payload(cls: Type[T], data: dict) -> T:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError


@dataclass
class DynamicTaggedNode(TaggedUnion):
    data: dict

    @classmethod
    def _from_payload(cls, data: dict) -> "DynamicTaggedNode":
        return cls(data)

    def to_dict(self) -> dict:
        return self.data


# icon.py
from dataclasses import dataclass
from typing import ClassVar

# Base TaggedUnion class comes from tagged_union.py

class Icon(TaggedUnion):
    _registry: ClassVar[dict[str, type]] = {}


@Icon.register("emoji")
@dataclass
class EmojiIcon(Icon):
    type: ClassVar[str] = "emoji"
    emoji: str

    @classmethod
    def _from_payload(cls, data: dict) -> "EmojiIcon":
        return cls(emoji=data["emoji"])

    def to_dict(self) -> dict:
        return {"type": self.type, "emoji": self.emoji}


@Icon.register("file")
@dataclass
class FileIcon(Icon):
    type: ClassVar[str] = "file"
    file: dict  # Will delegate inside to FileType

    @classmethod
    def _from_payload(cls, data: dict) -> "FileIcon":
        file_data = FileType.from_dict(data["file"])
        return cls(file=file_data.to_dict())

    def to_dict(self) -> dict:
        return {"type": self.type, "file": self.file}


# file.py
class FileType(TaggedUnion):
    _registry: ClassVar[dict[str, type]] = {}

@FileType.register("external")
@dataclass
class ExternalFile(FileType):
    type: ClassVar[str] = "external"
    url: str

    @classmethod
    def _from_payload(cls, data: dict) -> "ExternalFile":
        return cls(url=data["url"])

    def to_dict(self) -> dict:
        return {"type": self.type, "url": self.url}


@FileType.register("internal")
@dataclass
class InternalFile(FileType):
    type: ClassVar[str] = "internal"
    file_id: str

    @classmethod
    def _from_payload(cls, data: dict) -> "InternalFile":
        return cls(file_id=data["file_id"])

    def to_dict(self) -> dict:
        return {"type": self.type, "file_id": self.file_id}
