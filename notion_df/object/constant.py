from __future__ import annotations

from typing import Literal, Union

from notion_df.util.collection import PlainStrEnum

TimestampName = Literal['created_time', 'last_edited_time']
Number = Union[int, float]


class BlockColor(PlainStrEnum):
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


class OptionColor(PlainStrEnum):
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


class NumberFormat(PlainStrEnum):
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


class RollupFunction(PlainStrEnum):
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


class CodeLanguage(PlainStrEnum):
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
