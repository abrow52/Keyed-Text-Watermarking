
import csv
import secrets
from pathlib import Path

from experiments.serviceHarness import prepConfig
from experiments.removal import (
    AttackQuery,
    substitutionAttack,
    charChangeTests,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "experiments" / "results" / "manifest.csv"
OUT_DIR = PROJECT_ROOT / "experiments" / "results" / "attack_removal"
CANDIDATE_DIR = OUT_DIR / "removalAttempts"

ELIGIBLE_IDS = {"007", "009", "010"} # eligible passages


def setPath(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def passageID(row):
    raw_id = str(row["passageID"]).strip()
    return raw_id.zfill(3) if raw_id.isdigit() else raw_id


def saveText(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    with MANIFEST.open(newline="", encoding="utf-8") as f:
        manifestRows = list(csv.DictReader(f))

    selected = [
        row for row in manifestRows
        if passageID(row) in ELIGIBLE_IDS
    ]

    foundIDs = {passageID(row) for row in selected}
    missing = ELIGIBLE_IDS - foundIDs
    if missing:
        raise ValueError(
            f"These eligible IDs were not found in the manifest: "
            f"{sorted(missing)}. Check the passageID column."
        )

    # Configuration A: score mode, no rate limit.
    # The attack functions receive only the query interface.
    harness = prepConfig("A")
    resultRows = []
    reviewKeyRows = []
    reviewCounter = 0

    try:
        for row in selected:
            pid = passageID(row)
            watermarkedPath = setPath(row["watermarkedPath"])
            originalPath = setPath(row["originalPath"])

            watermarkedText = watermarkedPath.read_text(
                encoding="utf-8"
            )
            # Load original text for later quality review/reference.
            originalText = originalPath.read_text(encoding="utf-8")

            print(f"Running removal attacks for passage {pid}...")

            # Word substitution: its own 100-query / 15-minute budget.
            query = AttackQuery(
                harness["query"],
                budget=100,
                timeBudget=15 * 60,
            )
            subsitutionResults = substitutionAttack(
                watermarkedText, query
            )

            # Save candidate separately for quality assessment.
            variants = [{
                "variant": "substitution",
                "text": subsitutionResults["text"],
                "startingResponse": subsitutionResults["startingResponse"],
                "finalResponse": subsitutionResults["finalResponse"],
                "queries": subsitutionResults["queries"],
                "status": subsitutionResults["status"],
            }]

            # Case, punctuation and zero-width tests start independently
            # from the same watermarked input and share one 100-query budget.
            charChangeResults = charChangeTests(
                watermarkedText, harness["query"]
            )

            for item in charChangeResults:
                response = item["response"]
                variants.append({
                    "variant": item["variant"],
                    "text": item["text"],
                    "startingResponse": {"decision": "flagged"},
                    "finalResponse": response,
                    "queries": item["queriesUsed"],
                    "status": item["status"],
                })

            for item in variants:
                reviewCounter += 1

                candidatePath = (
                    CANDIDATE_DIR
                    / f"{pid}_{item['variant']}.txt"
                )
                saveText(candidatePath, item["text"])

                reviewKeyRows.append({
                    "passageID": pid,
                    "variant": item["variant"],
                })

                response = item["finalResponse"] or {}
                resultRows.append({
                    "passageID": pid,
                    "variant": item["variant"],
                    "startingResponse": str(item["startingResponse"]),
                    "finalResponse": str(response),
                    "queries": item["queries"],
                    "status": item["status"],
                })

        resultsPath = OUT_DIR / "removalAttackResults.csv"
        with resultsPath.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=resultRows[0].keys()
            )
            writer.writeheader()
            writer.writerows(resultRows)

        print("\nFinished.")
        print(f"Results: {resultsPath}")

    finally:
        harness["service"] = None


if __name__ == "__main__":
    main()
