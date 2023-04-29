from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, NewType, Literal, final

from typing_extensions import Self

from notion_df.objects.core import DualSerializable, deserialize_datetime, serialize_datetime
from notion_df.utils.collection import StrEnum

UUID = NewType('UUID', str)
TimestampType = Literal['created_time', 'last_edited_time']


class BlockColor(StrEnum):
    DEFAULT = 'default'
    GRAY = 'gray'
    BROWN = 'brown'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    PINK = 'pink'
    RED = 'red'
    GRAY_BACKGROUND = 'gray_background'
    BROWN_BACKGROUND = 'brown_background'
    ORANGE_BACKGROUND = 'orange_background'
    YELLOW_BACKGROUND = 'yellow_background'
    GREEN_BACKGROUND = 'green_background'
    BLUE_BACKGROUND = 'blue_background'
    PURPLE_BACKGROUND = 'purple_background'
    PINK_BACKGROUND = 'pink_background'
    RED_BACKGROUND = 'red_background'


class OptionColor(StrEnum):
    DEFAULT = 'default'
    GRAY = 'gray'
    BROWN = 'brown'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    PINK = 'pink'
    RED = 'red'


class NumberFormat(StrEnum):
    NUMBER = 'number'
    NUMBER_WITH_COMMAS = 'number_with_commas'
    PERCENT = 'percent'
    DOLLAR = 'dollar'
    CANADIAN_DOLLAR = 'canadian_dollar'
    EURO = 'euro'
    POUND = 'pound'
    YEN = 'yen'
    RUBLE = 'ruble'
    RUPEE = 'rupee'
    WON = 'won'
    YUAN = 'yuan'
    REAL = 'real'
    LIRA = 'lira'
    RUPIAH = 'rupiah'
    FRANC = 'franc'
    HONG_KONG_DOLLAR = 'hong_kong_dollar'
    NEW_ZEALAND_DOLLAR = 'new_zealand_dollar'
    KRONA = 'krona'
    NORWEGIAN_KRONE = 'norwegian_krone'
    MEXICAN_PESO = 'mexican_peso'
    RAND = 'rand'
    NEW_TAIWAN_DOLLAR = 'new_taiwan_dollar'
    DANISH_KRONE = 'danish_krone'
    ZLOTY = 'zloty'
    BAHT = 'baht'
    FORINT = 'forint'
    KORUNA = 'koruna'
    SHEKEL = 'shekel'
    CHILEAN_PESO = 'chilean_peso'
    PHILIPPINE_PESO = 'philippine_peso'
    DIRHAM = 'dirham'
    COLOMBIAN_PESO = 'colombian_peso'
    RIYAL = 'riyal'
    RINGGIT = 'ringgit'
    LEU = 'leu'
    ARGENTINE_PESO = 'argentine_peso'
    URUGUAYAN_PESO = 'uruguayan_peso'
    SINGAPORE_DOLLAR = 'singapore_dollar'


class RollupFunction(StrEnum):
    AVERAGE = 'average'
    CHECKED = 'checked'
    COUNT = 'count'
    COUNT_PER_GROUP = 'count_per_group'
    COUNT_VALUES = 'count_values'
    DATE_RANGE = 'date_range'
    EARLIEST_DATE = 'earliest_date'
    EMPTY = 'empty'
    LATEST_DATE = 'latest_date'
    MAX = 'max'
    MEDIAN = 'median'
    MIN = 'min'
    NOT_EMPTY = 'not_empty'
    PERCENT_CHECKED = 'percent_checked'
    PERCENT_EMPTY = 'percent_empty'
    PERCENT_NOT_EMPTY = 'percent_not_empty'
    PERCENT_PER_GROUP = 'percent_per_group'
    PERCENT_UNCHECKED = 'percent_unchecked'
    RANGE = 'range'
    SHOW_ORIGINAL = 'show_original'
    SHOW_UNIQUE = 'show_unique'
    SUM = 'sum'
    UNCHECKED = 'unchecked'
    UNIQUE = 'unique'


class CodeLanguage(StrEnum):
    ABAP = "abap"
    ARDUINO = "arduino"
    BASH = "bash"
    BASIC = "basic"
    C = "c"
    CLOJURE = "clojure"
    COFFEESCRIPT = "coffeescript"
    CPP = "c++"
    C_SHARP = "c#"
    CSS = "css"
    DART = "dart"
    DIFF = "diff"
    DOCKER = "docker"
    ELIXIR = "elixir"
    ELM = "elm"
    ERLANG = "erlang"
    FLOW = "flow"
    FORTRAN = "fortran"
    F_SHARP = "f#"
    GHERKIN = "gherkin"
    GLSL = "glsl"
    GO = "go"
    GRAPHQL = "graphql"
    GROOVY = "groovy"
    HASKELL = "haskell"
    HTML = "html"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    JSON = "json"
    JULIA = "julia"
    KOTLIN = "kotlin"
    LATEX = "latex"
    LESS = "less"
    LISP = "lisp"
    LIVESCRIPT = "livescript"
    LUA = "lua"
    MAKEFILE = "makefile"
    MARKDOWN = "markdown"
    MARKUP = "markup"
    MATLAB = "matlab"
    MERMAID = "mermaid"
    NIX = "nix"
    OBJECTIVE_C = "objective-c"
    OCAML = "ocaml"
    PASCAL = "pascal"
    PERL = "perl"
    PHP = "php"
    PLAIN_TEXT = "plain text"
    POWERSHELL = "powershell"
    PROLOG = "prolog"
    PROTOBUF = "protobuf"
    PYTHON = "python"
    R = "r"
    REASON = "reason"
    RUBY = "ruby"
    RUST = "rust"
    SASS = "sass"
    SCALA = "scala"
    SCHEME = "scheme"
    SCSS = "scss"
    SHELL = "shell"
    SQL = "sql"
    SWIFT = "swift"
    TYPESCRIPT = "typescript"
    VB_NET = "vb.net"
    VERILOG = "verilog"
    VHDL = "vhdl"
    VISUAL_BASIC = "visual basic"
    WEBASSEMBLY = "webassembly"
    XML = "xml"
    YAML = "yaml"
    JAVA_C_CPP_C_SHARP = "java/c/c++/c#"


@dataclass
class Annotations(DualSerializable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: BlockColor = BlockColor.DEFAULT

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)


icon_subclass_registry: dict[str, type[Icon]] = {}


class Icon(DualSerializable, metaclass=ABCMeta):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        icon_subclass_registry[cls.get_type()] = cls

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        pass

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != Icon:
            return cls._deserialize_this(serialized)
        subclass = icon_subclass_registry[cls.get_type()]
        return subclass._deserialize_this(serialized)


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    emoji: str

    @classmethod
    def get_type(cls) -> str:
        return 'emoji'

    def serialize(self):
        return {
            "type": "emoji",
            "emoji": self.emoji
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['emoji'])


@dataclass
class DateRange(DualSerializable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def serialize(self):
        return {
            'start': serialize_datetime(self.start),
            'end': serialize_datetime(self.end),
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls(deserialize_datetime(serialized['start']), deserialize_datetime(serialized['end']))


@dataclass
class SelectOption(DualSerializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False)

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)


@dataclass
class StatusGroups(DualSerializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False)
    option_ids: list[str] = field()
    """Sorted list of ids of all options that belong to a group."""

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)
