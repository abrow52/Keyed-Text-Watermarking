# the detector

from .tokenizer import tokenize
import hmac

with open("secret.key", "rb") as f:
    key = f.read()

# assign each word a color based on the key (1 = green, 0 = red)
def wordColor(word, key):
    return hmac.digest(key, word.encode("utf-8"), "sha256" )[-1] & 1

# score of the document by counting green word occurances
def scoreWords(tokens, key):
    if not tokens:
        raise ValueError("no words to score")

    # count normalized words
    greenWords = sum(
        wordColor(token["normalized"], key)
        for token in tokens
    )

    return greenWords / len(tokens), greenWords

def detect(text, key, threshold):
    tokens = tokenize(text)

    if not tokens:
        raise ValueError("no words to detect")

    score, greenWordCount = scoreWords(tokens, key)

    return {
        "score": score,
        "flagged": score > threshold,
        "wordCount": len(tokens),
        "greenWordCount": greenWordCount,
        "distinctWords": len(set(
            token["normalized"] for token in tokens
        ))
    }
