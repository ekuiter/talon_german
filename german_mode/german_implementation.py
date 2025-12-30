from pathlib import Path
from typing import Set, List, Optional

from talon import Context, actions, settings
from .external_transformer import ExternalTransformer

ctx = Context()
ctx.matches = """
mode: user.german
language: de_DE
"""

# dictionary for capitalization (set of lowercase words that should be capitalized)
here = Path(__file__).resolve().parent
german_dict = here / "dictionary" / "german.dic"
capitalized_words = None
with open(german_dict, "r", encoding="utf-8") as dict:
    capitalized_words = {word.strip().lower() for word in dict if word[0].isupper()}


def join_compounds(parts: List[str], compound_set: Set[str]) -> List[str]:
    """Joins words in phrase into compound nouns"""
    result: List[str] = []
    i = 0
    n = len(parts)
    while i < n:
        # join up to four words into a compound noun (words[i:i+4])
        longest = parts[i]
        skip = 1

        # consider joining up to 4 words, but don't go past the end
        max_words = min(4, n - i)
        # j is the number of additional words (j+1 total words)
        for j in range(1, max_words):
            # TODO: the parts contain trailing spaces which makes this unnecessarily ugly
            candidate = "".join(parts[i:i + j + 1]).lower().replace(" ", "")
            if candidate in compound_set:
                longest = candidate.capitalize() + ' '# restore stupid space after compound
                skip = j + 1

        result.append(longest)
        i += skip 

    return result

_space_after = ".,!?:;)]}–“‘$£€"
_no_space_before = ".,-!?:;)]}␣“‘’$£€"
_ascii_replace = {'–': '-', '„': '"', '“': '"', "‚": "'", "‘": "'", "’": "'"}




@ctx.capture("user.wort", rule='({user.number_key}+ | <user.vocabulary_german> | <word>)')
def wort(m) -> str:
    """word or spelled word or number, inserts space in the end"""
    return ''.join(str(m).split()) + ' '
    # XXX Continue here with capitlization
    #word = ''.join(str(m).split())
    # todo: capitalize here


@ctx.capture("user.gk_wort", rule='[{user.modifier}] <user.wort>')
def gk_wort(m) -> str:
    """potentially upper case word"""
    word = " ".join(m[1:])
    if m[0] == "CAP":
        return actions.user.formatted_text(word, "CAPITALIZE_ALL_WORDS")
    elif m[0] == "ALLCAPS":
        return actions.user.formatted_text(word, "ALL_CAPS")
    elif m[0] == "LOWER":
        return actions.user.formatted_text(word, "ALL_LOWERCASE")
    else:
        word = str(m)
        key = word.replace(" ", "")
        if key in capitalized_words:
            return key.capitalize() + " "
        else:
            return word


@ctx.capture("user.satzglied", rule='(<user.gk_wort> | {user.punctuation} | {user.symbol_key})')
def satzglied(m) -> str:
    """word or symbol"""
    if str(m)[0] in _space_after:
        return str(m) + ' '
    else:
        return str(m)

spaCyFix: Optional[ExternalTransformer] = None
def load_spaCyFix():
    global spaCyFix
    python_spacy = settings.get("user.german_python_spacy")
    spacy_path = here / ".external" / "spaCyFix.py"
    spaCyFix = ExternalTransformer([python_spacy, str(spacy_path.resolve())])

@ctx.capture("user.satz", rule='<user.satzglied>+')
def satz(m) -> str:
    """sentence"""
    parts = [str(x) for x in m]
    # print(f"parts: {parts}")

    parts = join_compounds(parts, capitalized_words)
    # print(f"after join_compounds: {parts}")

    out = []
    for i, p in enumerate(parts):
        if i > 0 and p and p[0] in _no_space_before and out and out[-1].endswith(' '):
            out[-1] = out[-1][:-1]
        out.append(p)
    result = ''.join(out).rstrip(' ')
    result = result.replace('␣', ' ')

    use_spacy = settings.get("user.german_use_spacy")
    if use_spacy and not spaCyFix:
        load_spaCyFix()

    # putting grammar-based correction at the end can result in explicit lowercase
    # words to be (wrongly) uppercased
    # print(f"Before spaCyFix: '{result}'")
    if use_spacy and spaCyFix:
        return spaCyFix.transform(result)
    else:
        return result



@ctx.capture("user.weg", rule='weg+')
def weg(m) -> str:
    """capture multiple "weg"s"""
    return str(m)


@ctx.capture("user.acronym", rule="{user.letter}+")
def acronym(m: str) -> str:
    return "".join(m.letter_list).upper()
