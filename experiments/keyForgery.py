
import csv
from pathlib import Path
import time

from experiments.serviceHarness import prepConfig
from src.watermarker import watermark
from src.synonyms import SYNONYMS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "experiments" / "results" / "manifest.csv"
KEY_PATH = PROJECT_ROOT / "secret.key"
OUT_DIR = PROJECT_ROOT / "experiments" / "results" / "attack_keyForgery"
CANDIDATE_DIR = OUT_DIR / "keyForgeryAttempts"

TARGET_SCORE = 0.75
MAX_ROUNDS = 100

def load_key(path): 
    raw = path.read_bytes()

    if len(raw) == 32:
        return raw

    try:
        decoded = bytes.fromhex(raw.decode("utf-8").strip())
    except (ValueError, UnicodeDecodeError):
        decoded = b""

    if len(decoded) == 32:
        return decoded

    raise ValueError(
        f"Could not interpret {path} as a 32-byte key "
        "or a 64-character hexadecimal key."
    )


def setPath(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def normalizeID(value):
    value = str(value).strip()
    return value.zfill(3) if value.isdigit() else value


def main():
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")
    if not KEY_PATH.exists():
        raise FileNotFoundError(f"Secret key not found: {KEY_PATH}")

    key = load_key(KEY_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    with MANIFEST.open(newline="", encoding="utf-8") as file:
        passages = list(csv.DictReader(file))

    # Configuration A provides score-mode responses without rate limiting.
    # The key-access attack may use the key, but service outcomes are still
    # measured through the service interface.
    harness = prepConfig("A")
    rows = []

    try:
        for passage in passages:
            passageID = normalizeID(passage["passageID"])
            originalPath = setPath(passage["originalPath"])
            originalText = originalPath.read_text(encoding="utf-8")

            startTime = time.perf_counter()
            forged = watermark(originalText, key, target=0.68, synonyms=SYNONYMS, maxRounds=100,)
            elapsedTime = time.perf_counter() - startTime
            candidateText = forged["text"]
            initialScore = forged["initialScore"]
            candidatePath = (
                CANDIDATE_DIR / f"{passageID}_forged.txt"
            )
            candidatePath.write_text(
                candidateText, encoding="utf-8"
            )

            # verify the result 
            forgedResponse = harness["query"](candidateText)

            rows.append({
                "passageID": passageID,
                "originalDescision": "unflagged",
                "originalScore": round(initialScore, 4),
                "forgedDecision": forgedResponse.get("decision", ""),
                "forgedScore": forgedResponse.get("score", ""),
                "elapsedSeconds": round(elapsedTime, 4),
            })

            print(
                f"forged={forgedResponse.get('decision')}, "
                f"candidate={candidatePath.name}"
            )
        output_path = OUT_DIR / "keyForgeryResults.csv"
        with output_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=rows[0].keys() if rows else [
                    "passageID", "originalDescision", "originalScore",
                    "forgedDecision", "forgedScore",
                ]
            )
            writer.writeheader()
            writer.writerows(rows)

    finally:
        harness["service"] = None


if __name__ == "__main__":
    main()
