"""Play, save, and verify a fixed heads-up Hold'em hand or match."""

import argparse
import json
from pathlib import Path

from pokerkit import Automation, HandHistory, Mode, NoLimitTexasHoldem

PLAYERS = ("opponent", "hero")  # PokerKit heads-up order: big blind, button/small blind.
STARTING_STACKS = {"opponent": 100, "hero": 100}
HOLE_CARDS = {"opponent": "KcKd", "hero": "AsAh"}
HAND_SCRIPTS = (
    (("2c7d9h", "Jc", "3s"), 12),
    (("4s5c9d", "Jh", "2s"), 64),
)


def stacks(state, players):
    return dict(zip(players, state.stacks))


def decision_snapshot(state, players, *, include_uncalled=False):
    actor = state.actor_index
    snapshot = {
        "actor": players[actor],
        "board": [repr(card) for card in state.get_board_cards(0)],
        "hole_cards": [repr(card) for card in state.hole_cards[actor]],
        "pot": state.total_pot_amount,
        "to_call": state.checking_or_calling_amount,
        "stacks": stacks(state, players),
    }
    if include_uncalled and snapshot["to_call"]:
        excess = max(state.bets) - state.bets[actor] - snapshot["to_call"]
        if excess:
            snapshot["uncalled_excess"] = excess
    return snapshot


def hand_result(state, players, decisions):
    return {
        "button": players[1],
        "starting_stacks": dict(zip(players, state.starting_stacks)),
        **decisions,
        "final_stacks": stacks(state, players),
        "finished": not state.status,
    }


def play_hand(players, starting_stacks, board, river_bet):
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
    state = game(tuple(starting_stacks[player] for player in players), 2)
    for player in players:
        state.deal_hole(HOLE_CARDS[player])
    state.complete_bet_or_raise_to(6)  # Button raises to 6, including the small blind.
    state.check_or_call()  # Big blind calls.

    state.burn_card("??")
    state.deal_board(board[0])
    state.check_or_call()  # Big blind checks.
    state.complete_bet_or_raise_to(6)  # Button bets.
    decisions = {"flop": decision_snapshot(state, players)}
    state.check_or_call()  # Big blind calls.

    state.burn_card("??")
    state.deal_board(board[1])
    state.check_or_call()
    state.check_or_call()

    state.burn_card("??")
    state.deal_board(board[2])
    state.complete_bet_or_raise_to(river_bet)  # Big blind bets.
    decisions["river"] = decision_snapshot(state, players)
    state.check_or_call()  # Button calls; the engine handles showdown and payout.
    hand = HandHistory.from_game_state(game, state)
    hand.players = list(players)
    return hand, hand_result(state, players, decisions)


def play_match():
    players = PLAYERS
    starting_stacks = STARTING_STACKS
    scripts = iter(HAND_SCRIPTS)
    hands = []
    while min(starting_stacks.values()) > 0:
        board, river_bet = next(scripts)
        hand, result = play_hand(players, starting_stacks, board, river_bet)
        hands.append((hand, result))
        starting_stacks = result["final_stacks"]
        players = players[::-1]
    return hands


def replay(hand):
    streets = {1: "flop", 3: "river"}
    decisions = {}
    for state in hand:
        street = streets.get(state.street_index)
        if street and state.checking_or_calling_amount:
            # PokerKit advances the same state object, so copy the decision fields now.
            decisions[street] = decision_snapshot(state, hand.players)
    return hand_result(state, hand.players, decisions)


REFERENCE_HANDS = [
    {
        "button": "hero",
        "starting_stacks": {"opponent": 100, "hero": 100},
        "flop": {
            "actor": "opponent",
            "board": ["2c", "7d", "9h"],
            "hole_cards": ["Kc", "Kd"],
            "pot": 18,
            "to_call": 6,
            "stacks": {"opponent": 94, "hero": 88},
        },
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
    },
    {
        "button": "opponent",
        "starting_stacks": {"hero": 124, "opponent": 76},
        "flop": {
            "actor": "hero",
            "board": ["4s", "5c", "9d"],
            "hole_cards": ["As", "Ah"],
            "pot": 18,
            "to_call": 6,
            "stacks": {"hero": 118, "opponent": 64},
        },
        "river": {
            "actor": "opponent",
            "board": ["4s", "5c", "9d", "Jh", "2s"],
            "hole_cards": ["Kc", "Kd"],
            "pot": 88,
            "to_call": 64,
            "stacks": {"hero": 48, "opponent": 64},
        },
        "final_stacks": {"hero": 200, "opponent": 0},
        "finished": True,
    },
]


def run_demo(path, match=False):
    if match:
        played = play_match()
        expected = REFERENCE_HANDS
    else:
        board, river_bet = HAND_SCRIPTS[0]
        played = [play_hand(PLAYERS, STARTING_STACKS, board, river_bet)]
        expected = REFERENCE_HANDS[:1]
    histories = [hand for hand, _ in played]
    original = [result for _, result in played]
    if original != expected:
        raise ValueError(f"The played hands differ from the reference: {original}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as file:
        if match:
            HandHistory.dump_all(histories, file)
        else:
            histories[0].dump(file)
    with path.open("rb") as file:
        hands = HandHistory.load_all(file) if match else [HandHistory.load(file)]
        replayed = [replay(hand) for hand in hands]
    if replayed != original:
        raise ValueError(f"The PHH replay differs from the played hands: {replayed}")
    if match:
        final_stacks = replayed[-1]["final_stacks"]
        return {"hands": replayed, "winner": max(final_stacks, key=final_stacks.get)}
    return {key: replayed[0][key] for key in ("river", "final_stacks", "finished")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for a new .phh or .phhs file")
    parser.add_argument("--match", action="store_true", help="Play and replay the two-hand match")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output, args.match), indent=2))


if __name__ == "__main__":
    main()
