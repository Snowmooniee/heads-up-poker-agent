"""Calculate exact river equity and call EV against an equal-weight range."""

import argparse
import json
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from pokerkit import Card, StandardHighHand, parse_range

from .poker_query import get_snapshot, open_saved_database


class RiverInputError(ValueError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def river_call(snapshot, opponent_range):
    board = tuple(Card.parse(*snapshot["board"]))
    hole = tuple(Card.parse(*snapshot["hole_cards"]))
    known = set(board + hole)
    if len(board) != 5 or len(hole) != 2 or len(known) != 7 or any(card.unknown_status for card in known):
        raise RiverInputError("needs_cards", "River analysis requires five board cards and two known hole cards.")
    pot = Fraction(snapshot["pot"])
    to_call = Fraction(snapshot["to_call"])
    if not 0 < to_call <= pot:
        raise RiverInputError("not_facing_bet", "Select a river decision facing a bet.")
    if "uncalled_excess" not in snapshot:
        raise RiverInputError("needs_import", "Import the source PHH again to record the uncalled amount.")

    try:
        combos = parse_range(opponent_range)
    except ValueError as error:
        raise RiverInputError("invalid_range", str(error)) from error
    if not combos or any(len(combo) != 2 or any(card.unknown_status for card in combo) for combo in combos):
        raise RiverInputError("invalid_range", "Supply a range such as KK, AKs, or KcKd 9c9d.")
    available = [combo for combo in combos if combo.isdisjoint(known)]
    if not available:
        raise RiverInputError("invalid_range", "The visible cards block every combo in the range.")

    hero = StandardHighHand.from_game(hole, board)
    opponents = [StandardHighHand.from_game(combo, board) for combo in available]
    wins = sum(hero > opponent for opponent in opponents)
    ties = sum(hero == opponent for opponent in opponents)
    equity = Fraction(2 * wins + ties, 2 * len(available))
    # In heads-up play, a short call leaves unmatched chips to be returned.
    unmatched = Fraction(snapshot["uncalled_excess"])
    contested_pot = pot - unmatched + to_call
    return {
        "range": opponent_range,
        "combos": len(available),
        "blocked": len(combos) - len(available),
        "wins": wins,
        "ties": ties,
        "losses": len(available) - wins - ties,
        "equity": str(equity),
        "call_ev": str(equity * contested_pot - to_call),
        "fold_ev": "0",
        "break_even_equity": str(to_call / contested_pot),
        "pot": str(pot),
        "to_call": str(to_call),
        "uncalled_excess": str(unmatched),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("decision_id")
    parser.add_argument("opponent_range")
    args = parser.parse_args()
    with closing(open_saved_database(args.database)) as db:
        snapshot = get_snapshot(db, args.decision_id)
    if snapshot is None:
        parser.error("Decision ID was not found.")
    print(json.dumps(river_call(snapshot, args.opponent_range), indent=2))


if __name__ == "__main__":
    main()
