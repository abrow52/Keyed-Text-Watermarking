from pathlib import Path
import json
from src.watermarker import watermark
from src.synonyms import SYNONYMS
from src.detector import detect


KEY_FILE = "secret.key"
THRESHOLD = 0.65 
TARGET = 0.68

EVALUATION_WATERMARKING = Path("data/repetition")
WATERMARKED_OUTPUT = Path("data/repetition/watermarked")
WATERMARKED_OUTPUT.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path("data/repetition/results")

# Load key
with open(KEY_FILE, "rb") as f:
    key = f.read()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results = []

for file in EVALUATION_WATERMARKING.glob("*.txt"):

    with open(file, "r", encoding="utf-8") as f:
        originalText = f.read()

    # score unmarked passage
    originalResult = detect(originalText, key, THRESHOLD)

    # watermark
    result = watermark(originalText,key, target=TARGET, synonyms=SYNONYMS)

    watermarkedText = result["text"]

    # save watermarked passage
    target_output_dir = WATERMARKED_OUTPUT
    target_output_dir.mkdir(parents=True, exist_ok=True)

    output_file = target_output_dir / file.name

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(watermarkedText)

    # score watermarked passage
    watermarkedResult = detect(watermarkedText, key, THRESHOLD)

    results.append({
        "file": str(file),
        "target": TARGET,
        "originalScore": originalResult["score"],
        "originalWordCount": originalResult["wordCount"],
        "originalFlagged": originalResult["flagged"],
        "originalGreenWordCount": originalResult["greenWordCount"],
        "originalDistinctWords": originalResult["distinctWords"],
        "watermarkedScore": watermarkedResult["score"],
        "watermarkedlWordCount": watermarkedResult["wordCount"],
        "watermarkedFlagged": watermarkedResult["flagged"],
        "watermarkedGreenWordCount": watermarkedResult["greenWordCount"],
        "watermarkedDistinctWords": watermarkedResult["distinctWords"],
        "targetReached": result["targetReached"]
    })


with open(OUTPUT_DIR / "scores.json", "w") as f:
    json.dump(results, f, indent=2)
