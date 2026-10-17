# calibrate the watermarker

from pathlib import Path
import json

from src.watermarker import watermark
from src.synonyms import SYNONYMS
from src.detector import detect


KEY_FILE = "secret.key"
THRESHOLD = 0.65 
TARGETS = [0.68, 0.70, 0.75]

CALIBRATION_WATERMARKING = Path("data/calibration/passages/watermarking/100_200")
WATERMARKED_OUTPUT = Path("data/calibration/passages/watermarked")
WATERMARKED_OUTPUT.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path("data/calibration/results")

# load key
with open(KEY_FILE, "rb") as f:
    key = f.read()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results = []

for target in TARGETS:
    for file in CALIBRATION_WATERMARKING.glob("*.txt"):

        with open(file, "r", encoding="utf-8") as f:
            originalText = f.read()

        # score unmarked passage
        originalResult = detect(originalText, key, THRESHOLD)

        # watermark passage
        result = watermark(originalText, key, target=target, synonyms=SYNONYMS)
        watermarkedText = result["text"]

        # save watermarked passage
        target_output_dir = WATERMARKED_OUTPUT / f"target_{target:.2f}"
        target_output_dir.mkdir(parents=True, exist_ok=True)

        output_file = target_output_dir / file.name
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(watermarkedText)

        # score watermarked passage
        watermarkedResult = detect(watermarkedText, key, THRESHOLD)

        results.append({
            "file": str(file),
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
            "target": target,
            "targetReached": result["targetReached"]
        })


with open(OUTPUT_DIR / "watermarkedScores3.json", "w") as f:
    json.dump(results, f, indent=2)
