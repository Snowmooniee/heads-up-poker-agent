"""Verify PHH imports and SQLite queries against known decisions."""

from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from .poker_demo import run_demo
from .poker_import import read_history
from .poker_query import find_decisions, get_snapshot, open_saved_database, query_history, save_history


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        single = root / "single.phh"
        match = root / "match.phhs"
        run_demo(single)
        run_demo(match, match=True)
        one_hand = read_history(single)
        two_hands = read_history(match)
        river_calls = query_history(match, "river", "call")
        turn_checks = query_history(match, "turn", "check")
        database = root / "review history.sqlite3"
        imported = save_history(match, database)
        assert (imported["hands"], imported["decisions"]) == (2, 18)
        save_history(match, database)
        with closing(open_saved_database(database)) as saved:
            assert find_decisions(saved, "river", "call") == river_calls
            decision_id = river_calls[0]["decision_id"]
            assert get_snapshot(saved, decision_id) == river_calls[0]["snapshot"]
        renamed = root / "renamed.phhs"
        renamed.write_bytes(match.read_bytes())
        assert read_history(renamed) == two_hands

    assert len(one_hand["hands"]) == 1
    first, second = two_hands["hands"]
    assert first["hand_id"] == f"{two_hands['source_id']}:1"
    assert second["hand_id"] == f"{two_hands['source_id']}:2"
    assert first["hand_id"] != one_hand["hands"][0]["hand_id"]
    assert first["players"]["p2"] == "hero"
    assert second["players"]["p2"] == "opponent"
    assert first["actions"][13] == {"action_no": 14, "phh": "p2 cc"}
    assert [entry["action_no"] for entry in first["decisions"]] == [3, 4, 6, 7, 8, 10, 11, 13, 14]
    assert first["decisions"][2]["action"] == "check"
    assert first["decisions"][2]["snapshot"]["board"] == ["2c", "7d", "9h"]
    river_call = first["decisions"][-1]
    assert (river_call["street"], river_call["action"]) == ("river", "call")
    assert river_call["decision_id"] == f"{first['hand_id']}:14"
    assert river_call["snapshot"] == {
        "actor": "p2",
        "board": ["2c", "7d", "9h", "Jc", "3s"],
        "hole_cards": ["As", "Ah"],
        "pot": 36,
        "to_call": 12,
        "stacks": {"p1": 76, "p2": 88},
    }
    assert one_hand["hands"][0]["decisions"][-1]["snapshot"] == river_call["snapshot"]
    assert second["decisions"][-1]["snapshot"]["to_call"] == 64
    assert [row["decision_id"] for row in river_calls] == [f"{first['hand_id']}:14", f"{second['hand_id']}:14"]
    assert river_calls[0]["snapshot"] == river_call["snapshot"]
    assert [row["snapshot"]["to_call"] for row in river_calls] == [12, 64]
    assert [(row["hand_no"], row["action_no"]) for row in turn_checks] == [(1, 10), (1, 11), (2, 10), (2, 11)]
    print("PHH import, SQLite query, and saved snapshot checks passed.")


if __name__ == "__main__":
    main()
