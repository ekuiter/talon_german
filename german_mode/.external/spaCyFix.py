#!/usr/bin/env python3
import sys
import signal
import spacy
from pathlib import Path
from typing import List, Set

# exit cleanly on SIGINT
def handler(signum, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, handler)

# Load spaCy once at startup
nlp = spacy.load(
    "de_core_news_sm",
    disable=[ "parser", "ner", "lemmatizer", "textcat", "attribute_ruler" ]
)


def process_phrase(text: str) -> str:
    """
    Apply POS-based capitalization rules.
    """
    tagged_phrase = nlp(text)

    # print([(w.text, w.pos_) for w in doc])

    out_tokens = []
    # Capitalize nouns and proper nouns; preserve original token spacing
    for token in tagged_phrase:
        if token.pos_ in ["NOUN", "PROPN"]:
            tok_text = token.text.capitalize()
        else:
            tok_text = token.text
        # Append the token text plus the original trailing whitespace
        out_tokens.append(tok_text + token.whitespace_)

    # print(out_tokens)
    return "".join(out_tokens)


def main():
    for line in sys.stdin:
        result = process_phrase(line.strip())
        print(result, flush=True)


if __name__ == "__main__":
    main()
