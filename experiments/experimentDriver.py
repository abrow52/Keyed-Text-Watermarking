import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORIGINALS_DIR = (
    PROJECT_ROOT / "data/evaluation/passages/watermarking/100_200"
)
WATERMARKED_DIR = (
    PROJECT_ROOT / "data/evaluation/passages/watermarked"
)
RESULTS_DIR = PROJECT_ROOT / "experiments"


def loadPassages():
    if not ORIGINALS_DIR.is_dir():
        raise FileNotFoundError(
            f"Originals directory not found: {ORIGINALS_DIR}"
        )

    if not WATERMARKED_DIR.is_dir():
        raise FileNotFoundError(
            f"Watermarked directory not found: {WATERMARKED_DIR}"
        )

    originals = {
        path.name: path
        for path in ORIGINALS_DIR.iterdir()
        if path.is_file()
    }
    watermarked = {
        path.name: path
        for path in WATERMARKED_DIR.iterdir()
        if path.is_file()
    }

    missingWatermarked = sorted(
        set(originals) - set(watermarked)
    )
    missingOriginal = sorted(
        set(watermarked) - set(originals)
    )

    if missingWatermarked or missingOriginal:
        raise ValueError(
            "Passage files do not match.\n"
            f"Missing watermarked versions: {missingWatermarked}\n"
            f"Missing originals: {missingOriginal}"
        )

    pairs = [
        {
            "passageID": Path(name).stem,
            "originalPath": originals[name],
            "watermarkedPath": watermarked[name],
        }
        for name in sorted(originals)
    ]

    if not pairs:
        raise ValueError("No passage pairs found.")

    return pairs


def saveManifest(pairs):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifestPath = RESULTS_DIR / "manifest.csv"

    with manifestPath.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "passageID",
                "originalPath",
                "watermarkedPath",
            ],
        )
        writer.writeheader()

        for pair in pairs:
            writer.writerow({
                "passageID": pair["passageID"],
                "originalPath": str(pair["originalPath"]),
                "watermarkedPath": str(pair["watermarkedPath"]),
            })

    return manifestPath


if __name__ == "__main__":
    pairs = loadPassages()
    manifest = saveManifest(pairs)

    print(f"Found {len(pairs)} matching passage pairs.")
    print(f"Manifest saved to: {manifest}")

    for pair in pairs:
        print(f"- {pair['passageID']}")
