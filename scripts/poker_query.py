"""Save and query recorded heads-up Hold'em decisions with SQLite."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .poker_import import read_history


def write_hands(db, hands):
    db.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS hands (
            hand_id TEXT PRIMARY KEY,
            hand_no INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS decisions (
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
            "INSERT INTO hands (hand_id, hand_no) VALUES (?, ?) "
            "ON CONFLICT (hand_id) DO NOTHING",
            ((hand["hand_id"], hand["hand_no"]) for hand in hands),
        )
        db.executemany(
            "INSERT INTO decisions (decision_id, hand_id, action_no, street, action, snapshot) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (decision_id) DO UPDATE SET snapshot = excluded.snapshot",
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


def find_decisions(db, street, action, *, hand_no=None, decision_id=None):
    rows = db.execute("""
        SELECT h.hand_no, d.decision_id, d.action_no, d.street, d.action, d.snapshot
        FROM decisions AS d
        JOIN hands AS h ON d.hand_id = h.hand_id
        WHERE d.street = :street AND d.action = :action
          AND (:hand_no IS NULL OR h.hand_no = :hand_no)
          AND (:decision_id IS NULL OR d.decision_id = :decision_id)
        ORDER BY h.hand_no, h.hand_id, d.action_no
    """, {"street": street, "action": action, "hand_no": hand_no, "decision_id": decision_id})
    matches = []
    for row in rows:
        result = dict(row)
        result["snapshot"] = json.loads(result["snapshot"])
        matches.append(result)
    return matches


def query_history(path, street, action):
    hands = read_history(path)["hands"]
    with closing(sqlite3.connect(":memory:")) as db:
        db.row_factory = sqlite3.Row
        write_hands(db, hands)
        return find_decisions(db, street, action)


def save_history(path, database):
    history = read_history(path)
    hands = history["hands"]
    with closing(sqlite3.connect(database)) as db:
        write_hands(db, hands)
    return {
        "source_id": history["source_id"],
        "hands": len(hands),
        "decisions": sum(len(hand["decisions"]) for hand in hands),
    }


def open_saved_database(path):
    db = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def get_snapshot(db, decision_id):
    row = db.execute(
        "SELECT snapshot FROM decisions WHERE decision_id = ?", (decision_id,),
    ).fetchone()
    return json.loads(row["snapshot"]) if row is not None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="PHH/PHHS file or SQLite database")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--save-to", type=Path, help="Import this hand history into a SQLite file")
    mode.add_argument("--street", help="Betting street, such as river")
    mode.add_argument("--decision-id", help="Read one saved decision snapshot by ID")
    parser.add_argument("--action", help="Recorded action, such as call")
    args = parser.parse_args()
    if (args.street is None) != (args.action is None):
        parser.error("--street and --action must be used together")

    if args.save_to is not None:
        result = save_history(args.path, args.save_to)
    elif args.street is not None and args.path.suffix.lower() in (".phh", ".phhs"):
        result = query_history(args.path, args.street, args.action)
    else:
        with closing(open_saved_database(args.path)) as db:
            if args.decision_id is not None:
                result = get_snapshot(db, args.decision_id)
            else:
                result = find_decisions(db, args.street, args.action)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
