import csv
import json
import re
import time
from pathlib import Path

from src.synonyms import SYNONYMS
from experiments.serviceHarness import prepConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "experiments" / "results" / "manifest.csv"
OUTPUT_DIR = PROJECT_ROOT / "experiments" / "results" / "attack_queryForgery"

SELECTED_IDS = {"002", "003", "005", "007", "009"}

PREPARATION_BUDGET = 100
EDITING_BUDGET_PER_PASSAGE = 100

# Repeating one word creates an all-red or all-green probe.
REPEAT_COUNT = 20
DEMO_WORD = "watermark"

RATE_LIMIT_WINDOW_SECONDS = 60

CONFIGS = {
    "A": {"description": "Score + decision; no rate limit"},
    "B": {"description": "Score + decision; rate limit enabled"},
    "C": {"description": "Decision only; rate limit enabled"},
}

WORD_PATTERN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalize(word):
    return word.lower().replace("'", "").replace("’", "")

def getWord(text):
    """Return word spans without changing the original text."""
    return list(WORD_PATTERN.finditer(text))


def readManifest():
    passages = {}

    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            passageID = Path(row["originalPath"]).stem

            passageID = row.get("passageID", passageID).strip()

            if passageID not in SELECTED_IDS:
                continue

            originalPath = Path(row["originalPath"])
            if not originalPath.is_absolute():
                originalPath = PROJECT_ROOT / originalPath

            watermarkedPath = Path(row["watermarkedPath"])
            if not watermarkedPath.is_absolute():
                watermarkedPath = PROJECT_ROOT / watermarkedPath

            passages[passageID] = {
                "originalPath": originalPath,
                "watermarkedPath": watermarkedPath,
                "original": originalPath.read_text(encoding="utf-8"),
                "watermarked": watermarkedPath.read_text(encoding="utf-8"),
            }

    missing = SELECTED_IDS - set(passages)
    if missing:
        raise RuntimeError(
            f"Selected passage IDs missing from manifest: {sorted(missing)}"
        )

    return passages


#communication with the detector
class AttackQueries:
    def __init__(self, baseQuery, config, clock):
        self.baseQuery = baseQuery
        self.clock = clock
        self.config = config
        self.requests = 0
        self.rejectedRequests = 0

    def query(self, text):
        # Count every submitted request, including rejected requests.
        self.requests += 1
        response = self.baseQuery(text)

        if isinstance(response, dict) and response.get("error"):
            self.rejectedRequests += 1
            error_text = str(response["error"]).lower()

            # rejected requests still count
            if "rate" in error_text or "limit" in error_text:
                self.clock.advance(RATE_LIMIT_WINDOW_SECONDS + 1)

        return response


def guessColor(response, config):
    if not isinstance(response, dict) or response.get("error"):
        return None

    if config in ("A", "B") and "score" in response:
        try:
            score = float(response["score"])
        except (TypeError, ValueError):
            score = None

        if score == 1.0:
            return 1
        if score == 0.0:
            return 0

    decision = response.get("decision", response.get("flagged"))

    if isinstance(decision, bool):
        return 1 if decision else 0

    if decision is not None:
        value = str(decision).strip().lower()
        if value in {"flagged", "true", "1", "yes"}:
            return 1
        if value in {"unflagged", "false", "0", "no"}:
            return 0

    return None


def probe(api, word):
    text = " ".join([word] * REPEAT_COUNT)
    response = api.query(text)
    return guessColor(response, api.config), response



def setProbVocab(passages):
    synonymMap = {
        normalize(key): values
        for key, values in SYNONYMS.items()
    }

    ordered = []
    seen = set()

    def add(word):
        word = str(word).strip()
        normalized = normalize(word)

        if not normalized or not normalized.isalpha():
            return

        if normalized not in seen:
            seen.add(normalized)
            ordered.append(word)

    for passageID in sorted(passages):
        original = passages[passageID]["original"]

        for match in getWord(original):
            sourceWord = match.group(0)
            sourceWordNorm = normalize(sourceWord)

            add(sourceWord)

            for candidate in synonymMap.get(sourceWordNorm, []):
                add(candidate)

    for key, candidates in synonymMap.items():
        add(key)
        for candidate in candidates:
            add(candidate)

    return ordered, synonymMap


def prepAttack(passages, api):
    startTime = time.monotonic()
    startSim = api.clock.now

    color = None
    response = None

    if api.requests < PREPARATION_BUDGET:
        color, response = probe(api, DEMO_WORD)

    vocabulary, synonymMap = setProbVocab(passages)

    learnedColors = {}
    probeLog = [{
        "word": DEMO_WORD,
        "purpose": "artificial repeated-word disclosure demonstration",
        "guessedColor": color,
        "response": response,
    }]

    for word in vocabulary:
        if api.requests >= PREPARATION_BUDGET:
            break

        normalized = normalize(word)
        if normalized in learnedColors:
            continue

        color, response = probe(api, word)

        if color is not None:
            learnedColors[normalized] = color

        probeLog.append({
            "word": word,
            "purpose": "color learning",
            "guessedColor": color,
            "response": response,
        })

    return {
        "colors": learnedColors,
        "synonymMap": synonymMap,
        "probeLog": probeLog,
        "requests": api.requests,
        "rejectedRequests": api.rejectedRequests,
        "time": time.monotonic() - startTime,
        "simulatedSeconds": api.clock.now - startSim,
        "demo": {
            "word": DEMO_WORD,
            "repeatCount": REPEAT_COUNT,
            "guessedColor": color,
            "response": response,
            "exclusionSuccessRates": True,
        },
    }


def substitute(original, learnedColors, synonymMap):
    plan = []

    for match in getWord(original):
        source = match.group(0)
        sourceWordNorm = normalize(source)

        # Only replace a word when its color was learned as red.
        if learnedColors.get(sourceWordNorm) != 0:
            continue

        for candidate in synonymMap.get(sourceWordNorm, []):
            candidateWordNorm = normalize(candidate)

            if learnedColors.get(candidateWordNorm) == 1:
                plan.append({
                    "start": match.start(),
                    "end": match.end(),
                    "source": source,
                    "replacement": candidate,
                })
                break

    return plan


def applyReplacements(original, plan, count):
    candidate = original

    for edit in reversed(plan[:count]):
        candidate = (
            candidate[:edit["start"]]
            + edit["replacement"]
            + candidate[edit["end"]:]
        )

    return candidate


def editPassage(passageID, original, api, learnedColors, synonymMap):
    startTime = time.monotonic()
    startSim = api.clock.now
    requestsBefore = api.requests
    rejectedBefore = api.rejectedRequests

    plan = substitute(
        original,
        learnedColors,
        synonymMap,
    )

    bestText = original
    finalResponse = None
    flagged = False
    attemptedReplacements = 0
    status = "no known green synonyms"

    if plan:
        status = "editing budget used"

        for count in range(1, len(plan) + 1):
            passageRequests = api.requests - requestsBefore

            if passageRequests >= EDITING_BUDGET_PER_PASSAGE:
                break

            candidate = applyReplacements(original, plan, count)
            response = api.query(candidate)
            attemptedReplacements = count
            bestText = candidate
            finalResponse = response

            if response.get("error"):
                continue

            decision = response.get("decision", response.get("flagged"))

            if isinstance(decision, bool):
                flagged = decision
            elif decision is not None:
                flagged = str(decision).strip().lower() in {
                    "flagged", "true", "1", "yes"
                }
            else:
                flagged = False

            if flagged:
                status = "flaggedCandidate found"
                break
        else:
            status = "editing budget used"

        if finalResponse and not finalResponse.get("error") and not flagged:
            status = "candidate not flagged"

    return {
        "passageID": passageID,
        "originalText": original,
        "candidateText": bestText,
        "flaggedCandidate": flagged,
        "status": status,
        "availableSubs": len(plan),
        "subsAttempted": attemptedReplacements,
        "changedWords": sum(
            1 for edit in plan[:attemptedReplacements]
            if edit["source"] != edit["replacement"]
        ),
        "editingRequests": api.requests - requestsBefore,
        "editingRejectedRequests": api.rejectedRequests - rejectedBefore,
        "editingTime": time.monotonic() - startTime,
        "editingSimSeconds": api.clock.now - startSim,
        "finalResponse": finalResponse,
    }

def write_json(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def runConfig(config, passages):
    print(f"\n=== Configuration {config}: {CONFIGS[config]['description']} ===")

    # A fresh service state and request counters are created per config.
    harness = prepConfig(config)
    api = AttackQueries(
        baseQuery=harness["query"],
        config=config,
        clock=harness["clock"],
    )

    config_dir = OUTPUT_DIR / f"config_{config}"
    config_dir.mkdir(parents=True, exist_ok=True)

    review_dir = config_dir / "quality_review"
    review_dir.mkdir(parents=True, exist_ok=True)

    runStartTime = time.monotonic()
    runStartSim = harness["clock"].now

    preparation = prepAttack(passages, api)
    learnedColors = preparation["colors"]
    synonymMap = preparation["synonymMap"]

    results = []

    for passageID in sorted(SELECTED_IDS):
        passage = passages[passageID]

        # Baseline eligibility is checked using the unmarked original.
        baselineResponse = api.query(passage["original"])
        baselineColor = guessColor(baselineResponse, config)
        baselineFlagged = baselineColor == 1

        if baselineFlagged:
            results.append({
                "passageID": passageID,
                "baselineFlagged": True,
                "eligible": False,
                "status": "falsePositives",
                "originalText": passage["original"],
                "candidateText": "",
                "flaggedCandidate": False,
                "editingRequests": 0,
                "editingRejectedRequests": 0,
                "editingTime": 0,
                "editingSimSeconds": 0,
                "changedWords": 0,
            })
            continue

        result = editPassage(
            passageID=passageID,
            original=passage["original"],
            api=api,
            learnedColors=learnedColors,
            synonymMap=synonymMap,
        )
        result["baselineFlagged"] = False
        result["eligible"] = True
        results.append(result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save color learning and the artificial demonstration separately.
    config_dir = OUTPUT_DIR / f"config_{config}"
    config_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        config_dir / "prep.json",
        {
            "config": config,
            "preparation": preparation,
            "learnedColorCount": len(learnedColors),
            "learnedColors": learnedColors,
            "probeLog": preparation["probeLog"],
        },
    )


    for result in results:
        if not result.get("eligible", False):
            continue

        passageID = result["passageID"]

        review_text = (
            "ORIGINAL TEXT:\n\n"
            + result["originalText"]
            + "\n\n"
            + "=" * 60
            + "\n\nCANDIDATE TEXT:\n\n"
            + result["candidateText"]
        )

        review_path = review_dir / f"{passageID}.txt"

        review_path.write_text(
            review_text,
            encoding="utf-8",
        )

    summary = {
        "config": config,
        "description": CONFIGS[config]["description"],
        "passageIDs": sorted(SELECTED_IDS),
        "prepRequests": preparation["requests"],
        "prepRejectedRequests": preparation["rejectedRequests"],
        "prepTime": preparation["time"],
        "prepSimilatedSeconds": preparation["simulatedSeconds"],
        "learnedColorCount": len(learnedColors),
        "editingRequests": sum(r.get("editingRequests", 0) for r in results),
        "editingRejectedRequests": sum(
            r.get("editingRejectedRequests", 0) for r in results
        ),
        "totalRequests": api.requests,
        "totalRejectedRequests": api.rejectedRequests,
        "totalTime": time.monotonic() - runStartTime,
        "totalSimSeconds": harness["clock"].now - runStartSim,
        "eligiblePassages": sum(r.get("eligible", False) for r in results),
        "baselineFalsePositives": sum(
            r.get("status") == "falsePositives"
            for r in results
        ),
        "flaggedCandidates": sum(
            r.get("flaggedCandidate", False) for r in results
        ),
        "quality_review_csv": str(review_dir),
        "passage_results": results,
    }

    write_json(config_dir / "summary.json", summary)

    print(f"Preparation requests: {summary['prepRequests']}")
    print(f"Learned colors: {summary['learnedColorCount']}")
    print(f"Editing requests: {summary['editingRequests']}")
    print(f"Rejected requests: {summary['totalRejectedRequests']}")
    print(f"Flagged candidates: {summary['flaggedCandidates']}")

    return summary


def main():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    passages = readManifest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_summaries = []

    for config in ("A", "B", "C"):
        all_summaries.append(runConfig(config, passages))

    write_json(
        OUTPUT_DIR / "all_configs_summary.json",
        all_summaries,
    )

    print("\nFinished all three configurations.")
    print(f"Results saved under: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
