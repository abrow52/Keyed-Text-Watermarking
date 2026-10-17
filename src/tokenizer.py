# the tokenizer

import re

WORD_PATTERN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def tokenize(text):
    tokens = []

    for match in WORD_PATTERN.finditer(text):
        original = match.group()
        normalized = original.lower().replace("'", "")

        tokens.append({
            "original": original,
            "normalized": normalized,
            "start": match.start(),
            "end": match.end()
        })

    return tokens