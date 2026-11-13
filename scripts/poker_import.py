"""Read a heads-up Hold'em PHH or PHHS file and index its recorded decisions."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from pokerkit import HandHistory

from .poker_demo import decision_snapshot

SEATS = ("p1", "p2")
STREETS = ("preflop", "flop", "turn", "river")
BETTING_ACTIONS = {"f": "fold", "cc": "check_or_call", "cbr": "bet_or_raise"}


def normalize_hand(hand, source_id, hand_no):
    if hand.variant != "NT" or len(hand.starting_stacks) != 2:
        raise ValueError(f"Hand {hand_no} must be heads-up no-limit Hold'em.")

    hand_id = f"{source_id}:{hand_no}"
    actions, decisions = [], []
    before = None
    for state, action in hand.state_actions:
        if action is not None:
            action_no = len(actions) + 1
            actions.append({"action_no": action_no, "phh": action})
            words = action.partition("#")[0].split()
            if len(words) >= 2 and words[1] in BETTING_ACTIONS:
                street, snapshot = before
                kind = BETTING_ACTIONS[words[1]]
                if kind == "check_or_call":
                    kind = "call" if snapshot["to_call"] else "check"
                decisions.append({
                    "decision_id": f"{hand_id}:{action_no}",
                    "action_no": action_no,
                    "street": street,
                    "action": kind,
                    "snapshot": snapshot,
                })

        # The next iteration advances this state in place.
        before = None
        if state.actor_index is not None:
            street = STREETS[state.street_index]
            before = street, decision_snapshot(state, SEATS, include_uncalled=street == "river")

    return {
        "hand_id": hand_id,
        "hand_no": hand_no,
        "players": dict(zip(SEATS, hand.players or SEATS)),
        "rules": {
            "variant": hand.variant,
            "ante_trimming_status": hand.ante_trimming_status,
            "antes": hand.antes,
            "blinds_or_straddles": hand.blinds_or_straddles,
            "min_bet": hand.min_bet,
        },
        "starting_stacks": dict(zip(SEATS, hand.starting_stacks)),
        "actions": actions,
        "decisions": decisions,
    }


def read_history(path):
    suffix = path.suffix.lower()
    if suffix not in (".phh", ".phhs"):
        raise ValueError("Use a .phh or .phhs file.")
    data = path.read_bytes()
    source_id = sha256(data).hexdigest()
    text = data.decode("utf-8")
    hands = [HandHistory.loads(text)] if suffix == ".phh" else HandHistory.loads_all(text)
    return {
        "source_id": source_id,
        "hands": [normalize_hand(hand, source_id, i) for i, hand in enumerate(hands, 1)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Existing .phh or .phhs file")
    args = parser.parse_args()
    print(json.dumps(read_history(args.path), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
