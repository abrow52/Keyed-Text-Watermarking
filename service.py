# local detection service

import hashlib
import secrets
import sqlite3
import time
from pathlib import Path


class ServiceError(Exception):
    # request failed a service check
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class DetectionService:
    def __init__(
        self,
        dbPath,
        detector,
        threshold,
        rateLimit=20,
        windowSeconds=60,
        clock=None,
    ):
        self.dbPath = str(dbPath)
        self.detector = detector
        self.threshold = threshold
        self.rateLimit = rateLimit
        self.windowSeconds = windowSeconds
        self.clock = clock or time.time

        Path(self.dbPath).parent.mkdir(
            parents=True, exist_ok=True
        )
        self.initializeDatabase()

    def connect(self):
        con = sqlite3.connect(self.dbPath)
        con.row_factory = sqlite3.Row
        return con

    def initializeDatabase(self):
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    accountID TEXT PRIMARY KEY,
                    token TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accountID TEXT,
                    timestamp REAL NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    rateLimited INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS request_time_idx
                ON requests(accountID, timestamp);
            """)

    @staticmethod
    def hash(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def createAccount(self, accountID, role):
        # make account and return its token
        if role not in {"submitter", "auditor"}:
            raise ValueError("Unsupported role")

        token = secrets.token_urlsafe(32)

        with self.connect() as con:
            con.execute(
                "INSERT INTO accounts VALUES (?, ?, ?)",
                (accountID, self.hash(token), role),
            )

        return token

    def account(self, token):
        if not isinstance(token, str) or not token:
            return None

        with self.connect() as con:
            return con.execute(
                "SELECT accountID, role FROM accounts "
                "WHERE token = ?",
                (self.hash(token),),
            ).fetchone()

    def log(self, accountID, action, outcome, limited=False):
        # don't store submited text or score
        with self.connect() as con:
            con.execute(
                """INSERT INTO requests
                   (accountID, timestamp, action, outcome,
                    rateLimited)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    accountID,
                    self.clock(),
                    action,
                    outcome,
                    int(limited),
                ),
            )

    def authorize(self, token, action):
        account = self.account(token)

        if account is None:
            self.log(None, action, "invalid credentials")
            raise ServiceError(
                "unauthorized", "Invalid credentials"
            )

        if action == "inspectLogs" and account["role"] != "auditor":
            self.log(
                account["accountID"], action, "forbidden"
            )
            raise ServiceError(
                "forbidden", "This role cannot inspect logs"
            )

        return account

    def checkRateLimit(self, accountID):
        if self.rateLimit is None:
            return

        now = self.clock()
        cutoff = now - self.windowSeconds

        with self.connect() as con:
            count = con.execute(
                """SELECT COUNT(*) FROM requests
                   WHERE accountID = ? AND timestamp > ?
                   AND action = 'detect'""",
                (accountID, cutoff),
            ).fetchone()[0]

        if count >= self.rateLimit:
            self.log(
                accountID, "detect", "rateLimited", True
            )
            raise ServiceError(
                "rateLimited", "Request allowance exceeded"
            )

    def detect(self, token, text, mode="score"):
        account = self.authorize(token, "detect")

        if mode not in {"score", "binary"}:
            self.log(
                account["accountID"], "detect", "invalid mode"
            )
            raise ServiceError(
                "invalid mode", "Use score or binary mode"
            )

        if not isinstance(text, str) or not text.strip():
            self.log(
                account["accountID"], "detect", "invalid input"
            )
            raise ServiceError(
                "invalid input", "Passage must contain text"
            )

        self.checkRateLimit(account["accountID"])

        try:
            result = self.detector(text)
            score = float(result["score"])
            flagged = score > self.threshold
        except ValueError:
            self.log(
                account["accountID"], "detect", "invalid input"
            )
            raise ServiceError(
                "invalid input", "Detector rejected the passage"
            )

        self.log(
            account["accountID"], "detect",
            "flagged" if flagged else "unflagged",
        )

        response = {"decision": "flagged" if flagged else "unflagged"}

        if mode == "score":
            response["score"] = round(score, 4)

        return response

    def inspectLogs(self, token):
        self.authorize(token, "inspectLogs")

        with self.connect() as con:
            rows = con.execute(
                """SELECT accountID, timestamp, action,
                          outcome, rateLimited
                   FROM requests ORDER BY id"""
            ).fetchall()

        return [dict(row) for row in rows]
