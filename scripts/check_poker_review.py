"""Verify the data and tools available to the river-review agent."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from .poker_demo import run_demo
from .poker_query import open_saved_database, save_history
from .poker_review import DemoModel, review


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        first = root / "first.phh"
        second = root / "second.phh"
        run_demo(first)
        second.write_text(first.read_text(encoding="utf-8").replace("KcKd", "TcTd"), encoding="utf-8")
        snapshots = []
        for source in (first, second):
            database = source.with_suffix(".sqlite3")
            save_history(source, database)
            trace = review(database, {"hand_no": 1}, "QcQd", root / source.stem, DemoModel())
            assert trace["status"] == "report_ready"
            names = [schema["function"]["name"] for schema in trace["tools"]]
            assert names == ["find_river_calls", "calculate_call_ev"]
            calls = [event for event in trace["events"] if event["type"] == "tool"]
            snapshots.append(json.loads(calls[0]["result"])[0]["snapshot"])
            messages = json.dumps([event["messages"] for event in trace["events"] if event["type"] == "model"])
            assert all(card not in messages for card in ("Kc", "Kd", "Tc", "Td"))

        assert snapshots[0] == snapshots[1]
        with closing(open_saved_database(database)) as db:
            try:
                db.execute("UPDATE decisions SET snapshot = snapshot")
            except sqlite3.OperationalError as error:
                assert "readonly" in str(error)
            else:
                raise AssertionError("The review database accepted a write.")

    print(json.dumps({
        "registered_tools": names,
        "visible_snapshot_matches_after_hidden_cards_change": True,
        "opponent_hole_cards_absent_from_model_messages": True,
        "review_connection_is_read_only": True,
    }, indent=2))


if __name__ == "__main__":
    main()
