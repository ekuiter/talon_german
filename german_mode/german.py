import unicodedata

from talon import Context, Module, actions, settings, speech_system
from talon.grammar import Phrase

from .clipscanner import ClipScanner

mod = Module()

ctx = Context()
ctx.matches = """
mode: user.german
language: de_DE
"""

mod.setting("german_use_spacy",
            type=int,
            default=0,
            desc="Use spaCy for grammar correction")

mod.setting("german_python_spacy",
            type=str,
            default="/usr/bin/python",
            desc="Python interpreter with the spaCy package installed")

mod.setting("german_unicode",
            type=int,
            default=1,
            desc="Enable proper unicode punctuation")

letters = {
    "alt": "a",
    "bett": "b",
    "kap": "c",
    "kapp": "c",
    "cap": "c",
    "cup": "c",
    "drum": "d",
    "echt": "e",
    "fein": "f",
    "feind": "f",
    "gast": "g",
    "hab": "h",
    "hat": "h",
    "hart": "h",
    "ich": "i",
    "j": "j",
    "kennt": "k",
    "kent": "k",
    "kind": "k",
    "look": "l",
    "luck": "l",
    "met": "m",
    "mit": "m",
    "not": "n",
    "oft": "o",
    "pitt": "p",
    "kuh": "q",
    "rad": "r",
    "rat": "r",
    "rate": "r",
    "raten": "r",
    "sinn": "s",
    "tipp": "t",
    "ulf": "u",
    "von": "v",
    "wall": "w",
    "plex": "x",
    "chunky": "y",
    "junkie": "y",
    "tanki": "y",
    "z": "z",
    "ähnlich": "ä",
    "öl": "ö",
    "übel": "ü",
    "üben": "ü",
    "s z": "ß",
}
letters.update({v: v for v in letters.values()})

ctx.lists["user.letter"] = letters

ctx.lists["user.number_key"] = {
    "null": "0",
    "eins": "1",
    "zwei": "2",
    "drei": "3",
    "vier": "4",
    "fünf": "5",
    "sechs": "6",
    "sieben": "7",
    "acht": "8",
    "neun": "9",
    "komma": ",",
    "punkt": ".",
}

ctx.lists["user.punctuation"] = {
    "leerzeichen": "␣",  # will become spaces after all substitutions
    "blank": "␣",
    "beistrich": ",",  # komma is often confused with komme
    "punkt": ".",
    "ellipse": "...",
    "semikolon": ";",
    "doppelpunkt": ":",
    "schrägstrich": "/",
    "fragezeichen": "?",
    "ausrufezeichen": "!",
    "sternchen": "*",
    "bindestrich": "-",
    "gedankenstrich": "–",
    "unterstrich": "_",
    "raute": "#",
    "prozent": "%",
    "at zeichen": "@",
    "klammeraffe": "@",
    "und zeichen": "&",

    "dollar zeichen": "$",
    "pfund zeichen": "£",
    "euro zeichen": "€",
}

ctx.lists["user.symbol_key"] = {
    "leerzeichen": "␣",  # will become spaces after all substitutions
    "blank": "␣",
    "beistrich": ",",  # komma is often confused with komme
    "punkt": ".",
    "fangt": ".",
    "semikolon": ";",
    "doppelpunkt": ":",
    "schrägstrich": "/",
    "fragezeichen": "?",
    "ausrufezeichen": "!",
    "sternchen": "*",
    "bindestrich": "-",
    "gedankenstrich": "–",
    "unterstrich": "_",
    "raute": "#",
    "hashtag": "#",
    "prozent": "%",
    "at zeichen": "@",
    "klammeraffe": "@",
    "und zeichen": "&",

    "dollar zeichen": "$",
    "pfund zeichen": "£",
    "euro zeichen": "€",

    "backslash": "\\",
    "senkrecht strich": "|",
    "zitat": '„',
    "zitat ende": '“',
    "halbes zitat": '‚',
    "halbes zitat ende": '‘',
    "apostroph": "’",
    "klammer auf": "(",
    "klammer zu": ")",
    "eckige klammer auf": "[",
    "eckige klammer zu": "]",
    "geschweifte klammer auf": "{",
    "geschweifte klammer zu": "}",
    "kleiner zeichen": "<",
    "größer zeichen": ">",
    "ist gleich zeichen": "=",
    "tilde": "~",
    "zirkumflex": "^",
}

mod.list("number", desc="Words for a positive nonzero number")
number_words = {
    "eins": "1",
    "zwei": "2",
    "drei": "3",
    "vier": "4",
    "fünf": "5",
    "sechs": "6",
    "sieben": "7",
    "acht": "8",
    "neun": "9",
    "zehn": "10",
}
number_words.update({str(i): str(i) for i in range(10)})
ctx.lists["self.number"] = number_words

@mod.capture
def number_small(m) -> int:
    """A small number"""

@ctx.capture(
    "user.number_small", rule=f"({'|'.join(number_words.keys())})"
)
def number_small(m) -> int:
    return int(number_words[str(m)])


mod.list("count", desc="Words for a positive nonzero count of actions")
count_words = {
    "einfach": "1",
    "zweifach": "2",
    "dreifach": "3",
    "vierfach": "4",
    "fünffach": "5",
    "sechsfach": "6",
    "siebenfach": "7",
    "achtfach": "8",
    "neunfach": "9",
    "zehnfach": "10",
}
ctx.lists["self.count"] = count_words

@mod.capture
def count_small(m) -> int:
    """A small count of instances of actions"""

@ctx.capture(
    "user.count_small", rule=f"({'|'.join(count_words.keys())})"
)
def count_small(m) -> int:
    return int(count_words[str(m)])

_space_after = ".,!?:;)]}–“‘$£€"
_no_space_before = ".,-!?:;)]}␣“‘’$£€"
_ascii_replace = {'–': '-', '„': '"', '“': '"', "‚": "'", "‘": "'", "’": "'"}

mod.list("modifier", desc="Modifiers for upper casement")
ctx.lists["self.modifier"] = {
    "schiff": "CAP",  # groß often becomes große/großer/großes
    "schiffs": "CAP",
    "schifft": "CAP",
    "holzschiff": "ALLCAPS",  # hold shift
    "zwerg": "LOWER",
}

@mod.capture
def vocabulary_german(m: str) -> str:
    """user vocabulary"""

@mod.capture
def wort(m: str) -> str:
    """word or spelled word or number, inserts space in the end"""


@mod.capture
def gk_wort(m: str) -> str:
    """potentially upper case word"""


@mod.capture
def satzglied(m: str) -> str:
    """word or symbol"""


@mod.capture
def satz(m: str) -> str:
    """sentence"""


@mod.capture
def weg(m: str, count: str) -> str:
    """capture multiple "weg"s"""

@mod.capture
def acronym(m: str) -> str:
    """an acronym composed of multiple letters"""


@mod.action_class
class Actions:

    def smart_delete(txt: str, count: str):
        """delete word and optionally space"""
        # TODO: Somehow a space he's left behind:
        # foo bar| baz -> foo|_ baz (_is selection)
        # foo bar |baz -> foo|_baz (_is selection)
        # perhaps just use a community action - is there one with smart delete?

        with ClipScanner() as clip:
            for i in range(len(str(txt).split())):
                for j in range(int(count)):
                    # first just delete all spaces until next word
                    clip.clear()
                    actions.edit.extend_word_left()
                    before = clip.get_selection()
                    if before != '' and before[-1] in [" ", "\n"]:
                        actions.edit.extend_word_right()
                        actions.key("backspace")
                        continue

                    # if there were none, delete next word
                    actions.key("backspace")

                    # delete spaces before that as well
                    clip.clear()
                    actions.edit.extend_left()
                    before = clip.get_selection()
                    if before in [" ", "\n"]:
                        actions.key("backspace")
                    elif before != '':
                        actions.edit.extend_right()
