# the watermarker

from .tokenizer import tokenize
from .detector import wordColor, scoreWords

SYNONYMS = {}

def getGreenSynonym(word, key, synonyms):
    candidates = synonyms.get(word, [])

    for candidate in candidates:
        normalized = candidate.lower().replace("'", "")

        # if the replacement word is green return use it as replacement 
        if wordColor(normalized, key) == 1:
            return candidate

    return None

# substitute the words
def watermarkOnce(text, key, synonyms):
    tokens = tokenize(text)

    replacements = []

    for token in tokens:
        # if green ignore
        if wordColor(token["normalized"], key) == 1:
            continue

        replacement = getGreenSynonym(
            token["normalized"],
            key,
            synonyms
        )

        if replacement is not None:
            replacements.append((token["start"], token["end"], replacement))

    # replace the word
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]

    return text

# run watermarkOnce over and over to try and get a higher score
def watermark(text, key, target, synonyms, maxRounds=100):
    originalScore = scoreWords(tokenize(text), key)[0]

    currentText = text
    bestText = text
    bestScore = originalScore

    for _ in range(maxRounds):

        currentScore = scoreWords(tokenize(currentText), key)[0]

        if currentScore >= target:
            return {
                "text": currentText,
                "initialScore": originalScore,
                "finalScore": currentScore,
                "targetReached": True
            }

        newText = watermarkOnce(currentText, key, synonyms)

        # Nothing else could be changed
        if newText == currentText:
            break

        newScore = scoreWords(tokenize(newText), key)[0]

        if newScore > bestScore:
            bestText = newText
            bestScore = newScore

        currentText = newText

    return {
        "text": bestText,
        "initialScore": originalScore,
        "finalScore": bestScore,
        "targetReached": bestScore >= target
    }