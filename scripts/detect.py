# calibrated detector

from pathlib import Path
import json
from src.detector import detect

KEY_FILE = "secret.key"
THRESHOLD  = 0.65 
EVALUATION_UNMARKED = Path("data/evaluation/passages/unmarked")
OUTPUT_DIR = Path("data/evaluation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# load key
with open(KEY_FILE, "rb") as f:
    key = f.read()

results = []

for file in EVALUATION_UNMARKED.rglob("*.txt"):

    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

        
    result = detect(text, key, 0)

    row = {
        "file": str(file),
        "threshold": THRESHOLD,
        "score": result["score"],
        "wordCount": result["wordCount"],
        "greenWordCount": result["greenWordCount"],
        "distinctWords": result["distinctWords"],
        "flagged": result["score"] > THRESHOLD,
    }

    results.append(row)

with open(OUTPUT_DIR / "unmarkedScores.json", "w") as f:
    json.dump(results, f, indent=2)

