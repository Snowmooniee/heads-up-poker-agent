"""Play, save, and verify one fixed heads-up Hold'em hand."""

import argparse
import json
from pathlib import Path

from pokerkit import Automation, HandHistory, Mode, NoLimitTexasHoldem

PLAYERS = ("opponent", "hero")  # PokerKit heads-up order: big blind, button/small blind.


def stacks(state):
    return dict(zip(PLAYERS, state.stacks))


def river_decision(state):
    actor = state.actor_index
    return {
        "actor": PLAYERS[actor],
        "board": [repr(card) for card in state.get_board_cards(0)],
        "hole_cards": [repr(card) for card in state.hole_cards[actor]],
        "pot": state.total_pot_amount,
        "to_call": state.checking_or_calling_amount,
        "stacks": stacks(state),
    }


def hand_result(state, decision):
    return {"river": decision, "final_stacks": stacks(state), "finished": not state.status}


def play_hand():
    game = NoLimitTexasHoldem(
        (
            Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.BET_COLLECTION,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING,
            Automation.CHIPS_PULLING,
        ),
        True, 0, (1, 2), 2, mode=Mode.TOURNAMENT,
    )
    state = game((100, 100), 2)
    state.deal_hole("KcKd")  # Opponent, big blind
    state.deal_hole("AsAh")  # Hero, small blind and button
    state.complete_bet_or_raise_to(6)  # Hero raises to 6, including the small blind.
    state.check_or_call()  # Opponent calls.

    state.burn_card("??")
    state.deal_board("2c7d9h")
    state.check_or_call()  # Opponent checks.
    state.complete_bet_or_raise_to(6)  # Hero bets.
    state.check_or_call()  # Opponent calls.

    state.burn_card("??")
    state.deal_board("Jc")
    state.check_or_call()
    state.check_or_call()

    state.burn_card("??")
    state.deal_board("3s")
    state.complete_bet_or_raise_to(12)  # Opponent bets.
    decision = river_decision(state)
    state.check_or_call()  # Hero calls; the engine handles showdown and payout.
    return game, state, hand_result(state, decision)


def replay(path):
    with path.open("rb") as file:
        hand = HandHistory.load(file)
    decision = None
    for state in hand:
        if state.street_index == 3 and state.actor_index == 1 and state.checking_or_calling_amount:
            # PokerKit advances the same state object, so copy the decision fields now.
            decision = river_decision(state)
    return hand_result(state, decision)


def run_demo(path):
    game, state, original = play_hand()
    expected = {
        "river": {
            "actor": "hero",
            "board": ["2c", "7d", "9h", "Jc", "3s"],
            "hole_cards": ["As", "Ah"],
            "pot": 36,
            "to_call": 12,
            "stacks": {"opponent": 76, "hero": 88},
        },
        "final_stacks": {"opponent": 76, "hero": 124},
        "finished": True,
    }
    if original != expected:
        raise ValueError(f"The original hand differs from the reference: {original}")

    hand = HandHistory.from_game_state(game, state)
    hand.players = list(PLAYERS)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as file:
        hand.dump(file)
    replayed = replay(path)
    if replayed != original:
        raise ValueError(f"The PHH replay differs from the original: {replayed}")
    return replayed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for a new .phh file")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output), indent=2))


if __name__ == "__main__":
    main()
