# calibrate the detector

from pathlib import Path
import json
from src.detector import detect

KEY_FILE = "secret.key"
THRESHOLDS  = [0.55, 0.60, 0.65] 

CALIBRATION_UNMARKED = Path("data/calibration/passages/unmarked")
OUTPUT_DIR = Path("data/calibration/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# load key
with open(KEY_FILE, "rb") as f:
    key = f.read()

results = []

for file in CALIBRATION_UNMARKED.rglob("*.txt"):

    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    result = detect(text, key, 0)

    row = {
        "file": str(file),
        "score": result["score"],
        "wordCount": result["wordCount"],
        "greenWordCount": result["greenWordCount"],
        "distinctWords": result["distinctWords"],
        "thresholdResults": {}
    }

    # test each threshold against each passages score
    for threshold in THRESHOLDS:
        row["thresholdResults"][str(threshold)] = (
            result["score"] > threshold
        )

    results.append(row)


with open(OUTPUT_DIR / "unmarkedScores.json", "w") as f:
    json.dump(results, f, indent=2)

# sumarize candidate threhold values 
summary = {}

for threshold in THRESHOLDS:
    flaggedCount = sum(
        row["thresholdResults"][str(threshold)]
        for row in results
    )

    summary[str(threshold)] = {
        "totalPassages": len(results),
        "flagged": flaggedCount,
        "falsePositiveRate": (
            flaggedCount / len(results) if results else 0
        )
    }

with open(OUTPUT_DIR / "unmarkedThresholdSummary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

