# set up isolated service configd for experiments

import sqlite3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from service import DetectionService
from src.serviceDetector import detectorConnection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "experiments" / "serviceStates"

THRESHOLD = 0.65
RATE_LIMIT = 20
WINDOW_SECONDS = 60

class SimulatedClock:
    # controlled by experiment driver
    def __init__(self, start=1_000_000.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        if seconds < 0:
            raise ValueError("Cannot move clock backwards")
        self.now += seconds


def prepConfig(config):
    # fresh service for each config

    settings = {
        "A": {"mode": "score", "rate_limit": None},
        "B": {"mode": "score", "rate_limit": RATE_LIMIT},
        "C": {"mode": "binary", "rate_limit": RATE_LIMIT},
    }

    if config not in settings:
        raise ValueError("Configuration must be A, B, or C")

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    dbPath = STATE_DIR / f"config_{config}.sqlite3"

    # start each config with empty database.
    for suffix in ("", "-wal", "-shm"):
        path = Path(str(dbPath) + suffix)
        if path.exists():
            path.unlink()

    clock = SimulatedClock()
    options = settings[config]

    service = DetectionService(
        dbPath=dbPath,
        detector=detectorConnection(threshold=THRESHOLD),
        threshold=THRESHOLD,
        rateLimit=options["rate_limit"],
        windowSeconds=WINDOW_SECONDS,
        clock=clock,
    )

    attackerToken = service.createAccount(f"attacker-{config}", "submitter")
    auditorToken = service.createAccount(f"auditor-{config}", "auditor")

    # The attacker receives only this function, not the service,
    # account database, clock, or auditor credentials.
    def query(text):
        from service import ServiceError

        try:
            return service.detect(
                attackerToken,
                text,
                mode=options["mode"],
            )
        except ServiceError as error:
            return {"error": error.code}

    # Driver-only controls stay outside the attack interface.
    return {
        "query": query,
        "clock": clock,
        "service": service,
        "auditorToken": auditorToken,
        "config": config,
    }


def getLogs(harness):
    return harness["service"].inspectLogs(
        harness["auditorToken"]
    )


def main():
    sample = "The quick brown fox jumps over the lazy dog."

    for config in ("A", "B", "C"):
        harness = prepConfig(config)

        try:
            result = harness["query"](sample)
            print(f"Configuration {config}: {result}")
        finally:
            # close SQLite connections after each config.
            with sqlite3.connect(
                str(STATE_DIR / f"config_{config}.sqlite3")
            ) as con:
                con.execute("PRAGMA optimize")

            harness["service"] = None


if __name__ == "__main__":
    main()
