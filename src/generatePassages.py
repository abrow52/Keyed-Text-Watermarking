# separate the sources into length groups

from .tokenizer import tokenize
from pathlib import Path
import random


def createPassages(text, totalPassages, minWords, maxWords, outputFolder, startToken=0):
    outputFolder = Path(outputFolder)
    outputFolder.mkdir(parents=True, exist_ok=True)

    tokens = tokenize(text)
    currentToken = startToken

    existingNumbers = [
        int(p.stem)
        for p in outputFolder.glob("*.txt")
        if p.stem.isdigit()
    ]
    nextNumber = max(existingNumbers, default=0) + 1

    for _ in range(1, totalPassages + 1):

        wordCount = random.randint(minWords, maxWords)

        if currentToken + wordCount > len(tokens):
            print("Not enough words remaining in {outputFolder}.")
            break

        # find start and end of passage to be generated
        startPos = tokens[currentToken]["start"]
        endPos = tokens[currentToken + wordCount - 1]["end"]

        passage = text[startPos:endPos]

        outputFile = outputFolder / f"{nextNumber:03d}.txt"
        with open(outputFile, "w", encoding="utf-8") as outfile:
            outfile.write(passage)

        nextNumber += 1
        currentToken += wordCount

    return currentToken

#calibration passages

with open("sources/oz.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
position = createPassages(
    text,
    totalPassages=12,
    minWords=30,
    maxWords=99,
    outputFolder="data/calibration/passages/unmarked/30_99",
    startToken = position
)
# 100-199
position = createPassages(
    text,
    totalPassages=12,
    minWords=100,
    maxWords=199,
    outputFolder="data/calibration/passages/unmarked/100_199",
    startToken = position
)
# 200-400
position = createPassages(
    text,
    totalPassages=12,
    minWords=200,
    maxWords=400,
    outputFolder="data/calibration/passages/unmarked/200_400",
    startToken = position
)
# 100-200
position = createPassages(
    text,
    totalPassages=2,
    minWords=100,
    maxWords=200,
    outputFolder="data/calibration/passages/watermarking/100_200",
    startToken = position
)

with open("sources/glass.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
position = createPassages(
    text,
    totalPassages=12,
    minWords=30,
    maxWords=99,
    outputFolder="data/calibration/passages/unmarked/30_99",
    startToken = position
)
# 100-199
position = createPassages(
    text,
    totalPassages=12,
    minWords=100,
    maxWords=199,
    outputFolder="data/calibration/passages/unmarked/100_199",
    startToken = position
)
# 200-400
position = createPassages(
    text,
    totalPassages=12,
    minWords=200,
    maxWords=400,
    outputFolder="data/calibration/passages/unmarked/200_400",
    startToken = position
)
# 100-200
position = createPassages(
    text,
    totalPassages=1,
    minWords=100,
    maxWords=200,
    outputFolder="data/calibration/passages/watermarking/100_200",
    startToken = position
)

with open("sources/pinnochio.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
position = createPassages(
    text,
    totalPassages=13,
    minWords=30,
    maxWords=99,
    outputFolder="data/calibration/passages/unmarked/30_99",
    startToken = position
)
# 100-199
position = createPassages(
    text,
    totalPassages=13,
    minWords=100,
    maxWords=199,
    outputFolder="data/calibration/passages/unmarked/100_199",
    startToken = position
)
# 200-400
position = createPassages(
    text,
    totalPassages=13,
    minWords=200,
    maxWords=400,
    outputFolder="data/calibration/passages/unmarked/200_400",
    startToken = position
)
# 100-200
position = createPassages(
    text,
    totalPassages=1,
    minWords=100,
    maxWords=200,
    outputFolder="data/calibration/passages/watermarking/100_200",
    startToken = position
)

with open("sources/space.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
position = createPassages(
    text,
    totalPassages=13,
    minWords=30,
    maxWords=99,
    outputFolder="data/calibration/passages/unmarked/30_99",
    startToken = position
)
# 100-199
position = createPassages(
    text,
    totalPassages=13,
    minWords=100,
    maxWords=199,
    outputFolder="data/calibration/passages/unmarked/100_199",
    startToken = position
)
# 200-400
position = createPassages(
    text,
    totalPassages=13,
    minWords=200,
    maxWords=400,
    outputFolder="data/calibration/passages/unmarked/200_400",
    startToken = position
)
# 100-200
position = createPassages(
    text,
    totalPassages=1,
    minWords=100,
    maxWords=200,
    outputFolder="data/calibration/passages/watermarking/100_200",
    startToken = position
)





# evaluation passages

with open("sources/neverland.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
createPassages(
    text,
    totalPassages=13,
    minWords=30,
    maxWords=99,
    outputFolder="data/evaluation/passages/unmarked/30_99",
    startToken = position
)
# 100-199
createPassages(
    text,
    totalPassages=13,
    minWords=100,
    maxWords=199,
    outputFolder="data/evaluation/passages/unmarked/100_199",
    startToken = position
)
# 200-400
createPassages(
    text,
    totalPassages=13,
    minWords=200,
    maxWords=400,
    outputFolder="data/evaluation/passages/unmarked/200_400",
    startToken = position
)
# 100-200
createPassages(
    text,
    totalPassages=2,
    minWords=100,
    maxWords=200,
    outputFolder="data/evaluation/passages/watermarking/100_200",
    startToken = position
)

with open("sources/goblin.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
createPassages(
    text,
    totalPassages=13,
    minWords=30,
    maxWords=99,
    outputFolder="data/evaluation/passages/unmarked/30_99",
    startToken = position
)
# 100-199
createPassages(
    text,
    totalPassages=13,
    minWords=100,
    maxWords=199,
    outputFolder="data/evaluation/passages/unmarked/100_199",
    startToken = position
)
# 200-400
createPassages(
    text,
    totalPassages=13,
    minWords=200,
    maxWords=400,
    outputFolder="data/evaluation/passages/unmarked/200_400",
    startToken = position
)
# 100-200
createPassages(
    text,
    totalPassages=2,
    minWords=100,
    maxWords=200,
    outputFolder="data/evaluation/passages/watermarking/100_200",
    startToken = position
)

with open("sources/boston.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
createPassages(
    text,
    totalPassages=12,
    minWords=30,
    maxWords=99,
    outputFolder="data/evaluation/passages/unmarked/30_99",
    startToken = position
)
# 100-199
createPassages(
    text,
    totalPassages=12,
    minWords=100,
    maxWords=199,
    outputFolder="data/evaluation/passages/unmarked/100_199",
    startToken = position
)
# 200-400
createPassages(
    text,
    totalPassages=12,
    minWords=200,
    maxWords=400,
    outputFolder="data/evaluation/passages/unmarked/200_400",
    startToken = position
)
# 100-200
createPassages(
    text,
    totalPassages=3,
    minWords=100,
    maxWords=200,
    outputFolder="data/evaluation/passages/watermarking/100_200",
    startToken = position
)

with open("sources/grimm.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

position = 0

# 30-99
createPassages(
    text,
    totalPassages=12,
    minWords=30,
    maxWords=99,
    outputFolder="data/evaluation/passages/unmarked/30_99",
    startToken = position
)
# 100-199
createPassages(
    text,
    totalPassages=12,
    minWords=100,
    maxWords=199,
    outputFolder="data/evaluation/passages/unmarked/100_199",
    startToken = position
)
# 200-400
createPassages(
    text,
    totalPassages=12,
    minWords=200,
    maxWords=400,
    outputFolder="data/evaluation/passages/unmarked/200_400",
    startToken = position
)
# 100-200
createPassages(
    text,
    totalPassages=3,
    minWords=100,
    maxWords=200,
    outputFolder="data/evaluation/passages/watermarking/100_200",
    startToken = position
)