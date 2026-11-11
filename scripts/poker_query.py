"""Find recorded decisions in a heads-up PHH or PHHS file using SQLite."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .poker_import import read_history


def query_history(path, street, action):
    hands = read_history(path)["hands"]
    with closing(sqlite3.connect(":memory:")) as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE hands (
                hand_id TEXT PRIMARY KEY,
                hand_no INTEGER NOT NULL
            );
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY,
                hand_id TEXT NOT NULL REFERENCES hands(hand_id),
                action_no INTEGER NOT NULL,
                street TEXT NOT NULL,
                action TEXT NOT NULL,
                snapshot TEXT NOT NULL
            );
        """)
        with db:
            db.executemany(
                "INSERT INTO hands (hand_id, hand_no) VALUES (?, ?)",
                ((hand["hand_id"], hand["hand_no"]) for hand in hands),
            )
            db.executemany(
                "INSERT INTO decisions (decision_id, hand_id, action_no, street, action, snapshot) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    (
                        decision["decision_id"],
                        hand["hand_id"],
                        decision["action_no"],
                        decision["street"],
                        decision["action"],
                        json.dumps(decision["snapshot"], default=str),
                    )
                    for hand in hands
                    for decision in hand["decisions"]
                ),
            )
        rows = db.execute("""
            SELECT h.hand_no, d.decision_id, d.action_no, d.street, d.action, d.snapshot
            FROM decisions AS d
            JOIN hands AS h ON d.hand_id = h.hand_id
            WHERE d.street = ? AND d.action = ?
            ORDER BY h.hand_no, d.action_no
        """, (street, action))
        matches = []
        for row in rows:
            result = dict(row)
            result["snapshot"] = json.loads(result["snapshot"])
            matches.append(result)
        return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Existing .phh or .phhs file")
    parser.add_argument("--street", required=True, help="Betting street, such as river")
    parser.add_argument("--action", required=True, help="Recorded action, such as call")
    args = parser.parse_args()
    print(json.dumps(query_history(args.path, args.street, args.action), indent=2))


if __name__ == "__main__":
    main()
