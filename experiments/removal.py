# watermark removal attack

import csv
import re
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "experiments/results/attack_removal"

QUERY_BUDGET = 100
TIME_BUDGET_SECONDS = 15 * 60

# words an attacker may try and replace
SYNONYMS = {
    "quick": ["fast", "swift"],
    "small": ["little", "tiny"],
    "big": ["large", "great"],
    "happy": ["glad", "pleased"],
    "begin": ["start", "commence"],
    "end": ["finish", "conclude"],
    "help": ["aid", "assist"],
    "show": ["display", "reveal"],
    "make": ["create", "produce"],
    "use": ["employ", "utilize"],
}


class QueryBudgetExceeded(Exception):
    pass

# count attacker issued requests
class AttackQuery:
    def __init__(self, query, budget=QUERY_BUDGET,
                 timeBudget=TIME_BUDGET_SECONDS):
        self._query = query
        self.budget = budget
        self.timeBudget = timeBudget
        self.count = 0
        self.started = time.monotonic() #dont let time go backward

    def __call__(self, text):
        if self.count >= self.budget:
            raise QueryBudgetExceeded("Query budget exhausted")

        if time.monotonic() - self.started >= self.timeBudget:
            raise QueryBudgetExceeded("Time budget exhausted")

        self.count += 1
        return self._query(text)


def passageScore(response):
    if "error" in response:
        return None
    score = response.get("score")
    return float(score) if score is not None else None



def substitutionAttack(text, query):
    #Try synonym substitutions using only the detector's responses.
    current = text
    initialResponse = query(current)
    initialScore = passageScore(initialResponse)

    if initialScore is None:
        return {
            "variant": "wordSubsitution",
            "startingResponse": initialResponse,
            "finalResponse": initialResponse,
            "text": current,
            "status": "score unavailable; cannot run score-guided search",
            "queries": query.count,
        }

    bestScore = initialScore
    word_pattern = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)
    attempted = set()

    while query.count < query.budget:
        improved = False

        # Recalculate matches from the current text every iteration.
        for match in word_pattern.finditer(current):
            originalWord = match.group()
            candidates = SYNONYMS.get(originalWord.lower(), [])

            for candidate in candidates:
                # Don't repeat the same word replacement attempt.
                attempt_key = (
                    current,
                    match.start(),
                    match.end(),
                    candidate.lower(),
                )
                if attempt_key in attempted:
                    continue
                attempted.add(attempt_key)

                if query.count >= query.budget:
                    break

                if originalWord.isupper():
                    replacement = candidate.upper()
                elif originalWord.istitle():
                    replacement = candidate.capitalize()
                else:
                    replacement = candidate

                trial = (
                    current[:match.start()]
                    + replacement
                    + current[match.end():]
                )

                response = query(trial)
                score = passageScore(response)

                if score is None:
                    continue

                if response.get("decision") == "unflagged":
                    return {
                        "variant": "wordSubsitution",
                        "startingResponse": initialResponse,
                        "finalResponse": response,
                        "text": trial,
                        "status": "unflagged",
                        "queries": query.count,
                    }

                # Keep a substitution only when the detector score improves.
                if score < bestScore:
                    current = trial
                    bestScore = score
                    improved = True
                    break

            if improved or query.count >= query.budget:
                break

        if not improved:
            break

    # Query the final candidate if budget remains.
    if query.count < query.budget:
        finalResponse = query(current)
    else:
        finalResponse = {"error": "queryBudgetUsed"}

    return {
        "variant": "wordSubsitution",
        "startingResponse": initialResponse,
        "finalResponse": finalResponse,
        "text": current,
        "status": "finished;",
        "queries": query.count,
    }


def charChangeTests(text, query):
    #Test three independent changes, each starting from original text.
    variants = {
        "caseChange": text.swapcase(),
        "punctuationChange": re.sub(r"[^\w\s]", "", text),
        "zeroWidthInsertion": re.sub(
            r"(?<=[A-Za-z])(?=[A-Za-z])",
            "\u200b",
            text,
        ),
    }

    # All three tests share one request budget for this passage.
    query = AttackQuery(query, budget=QUERY_BUDGET)
    results = []

    for name, editedText in variants.items():
        try:
            response = query(editedText)
            results.append({
                "variant": name,
                "response": response,
                "text": editedText,
                "queriesUsed": query.count,
                "status": (
                    "unflagged"
                    if response.get("decision") == "unflagged"
                    else "not removed"
                ),
            })
        except QueryBudgetExceeded as error:
            results.append({
                "variant": name,
                "response": {},
                "text": editedText,
                "queriesUsed": query.count,
                "status": str(error),
            })
            break

    return results


def saveResults(rows, filename):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / filename

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "passage_id",
                "variant",
                "startingResponse",
                "finalResponse",
                "queries",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path
