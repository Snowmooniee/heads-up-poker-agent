"""Find a player's recorded river call from an English request."""

import json
import re
from contextlib import closing
from fractions import Fraction

from .poker_equity import RiverInputError, river_call
from .poker_query import find_decisions, open_saved_database

CARD = r"[2-9tjqka][cdhs]"
NUMBERS = dict(zip(
    ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen",
     "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"),
    range(1, 21),
))
ORDINALS = dict(zip(("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"),
                    range(1, 11)))
NUMBER = r"\d+|" + "|".join(sorted(NUMBERS, key=len, reverse=True))
RANKS = dict(zip(("two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "jack", "queen", "king", "ace"),
                 "23456789TJQKA"))
SUITS = dict(zip(("clubs", "diamonds", "hearts", "spades"), "cdhs"))
DECISION_ID = re.compile(r"(?<![\w:])(?:[a-f0-9]{64}:)?[0-9]+:[0-9]+(?![\w:])", re.IGNORECASE)


def card_code(value):
    return value[0].upper() + value[1].lower()


def unknown_references(message, catalog):
    known = set(catalog) | {key.split(":", 1)[1] for key in catalog}
    return [match for match in DECISION_ID.findall(message) if match not in known]


def lookup_calls(database, player, *, hand_no=None, call_cost=None, river_card=None, decision_id=None):
    with closing(open_saved_database(database)) as db:
        rows = find_decisions(db, "river", "call", hand_no=hand_no, decision_id=decision_id, player=player)
    river_card = card_code(river_card) if river_card is not None else None
    return [
        {
            "decision_id": row["decision_id"], "hand_no": row["hand_no"],
            **{key: row["snapshot"][key] for key in ("board", "hole_cards", "pot", "to_call", "uncalled_excess")},
        }
        for row in rows
        if (call_cost is None or Fraction(row["snapshot"]["to_call"]) == call_cost)
        and (river_card is None or row["snapshot"]["board"][-1] == river_card)
    ]


def outcome(action, message, *, decision_id=None, candidate_ids=(), equity=None, call_ev=None):
    return {
        "action": action, "decision_id": decision_id, "candidate_ids": list(candidate_ids),
        "equity": equity, "call_ev": call_ev, "message": message,
    }


def clarification(matches):
    hands = sorted({row["hand_no"] for row in matches})
    if len(hands) == len(matches):
        return f"Which hand did you mean? The matching hand numbers are {', '.join(map(str, hands))}."
    return "Which decision ID did you mean? " + ", ".join(row["decision_id"] for row in matches) + "."


def calculate_call(row, opponent_range):
    try:
        return {"decision_id": row["decision_id"], **river_call(row, opponent_range)}
    except RiverInputError as error:
        return {"decision_id": row["decision_id"], "status": error.status, "explanation": str(error)}


def keyword_pipeline(database, player, request, opponent_range):
    """Parse common selectors and use the same lookup and calculator as the agent."""
    text = request.lower()
    other_task = re.search(r"^\s*(?:write|rewrite|draft|translate|convert)\b", text)
    other_street = re.search(r"\b(?:preflop|flop|turn)\s+(?:call|decision)\b", text)
    poker_terms = re.search(r"\b(?:river|call|final street|last betting round|match(?:ed)?)\b", text)
    if other_task or other_street or poker_terms is None:
        return outcome("out_of_scope", "This tool reviews recorded river calls."), []

    hand = re.search(rf"\bhand\s*#?\s*({NUMBER})\b", text)
    ordinal_hand = re.search(rf"\b({'|'.join(ORDINALS)}) hand\b", text)
    amount = re.search(rf"\b({NUMBER})(?:\s+|-)chips?\b", text)
    compact_card = re.search(rf"\b({CARD})\b", text)
    named_card = re.search(rf"\b({'|'.join(RANKS)}) of ({'|'.join(SUITS)})\b", text)
    selectors = {}
    explicit_id = DECISION_ID.search(text)
    if explicit_id and explicit_id[0].count(":") == 2:
        selectors["decision_id"] = explicit_id[0]
    for key, match in (("hand_no", hand), ("call_cost", amount)):
        if match:
            value = match[1]
            selectors[key] = int(value) if value.isdecimal() else NUMBERS[value]
    if ordinal_hand and not hand:
        selectors["hand_no"] = ORDINALS[ordinal_hand[1]]
    if named_card:
        selectors["river_card"] = RANKS[named_card[1]] + SUITS[named_card[2]]
    elif compact_card:
        selectors["river_card"] = card_code(compact_card[1])

    matches = lookup_calls(database, player, **selectors)
    events = [{
        "type": "tool", "name": "find_river_calls", "call_id": "fixed-lookup", "arguments": selectors,
        "result": json.dumps(matches),
    }]
    if not matches:
        return outcome("no_match", "No recorded river call matches those conditions."), events
    if len(matches) > 1:
        return outcome("ask", clarification(matches), candidate_ids=[row["decision_id"] for row in matches]), events

    decision = matches[0]
    decision_id = decision["decision_id"]
    if opponent_range:
        result = calculate_call(decision, opponent_range)
        events.append({
            "type": "tool", "name": "calculate_call_ev", "call_id": "fixed-ev",
            "arguments": {"decision_id": decision_id}, "result": json.dumps(result),
        })
        if "call_ev" in result:
            ev = result["call_ev"]
            return outcome(
                "act", f"Found the call in hand {decision['hand_no']}. Call EV is {ev} chips.",
                decision_id=decision_id, equity=result["equity"], call_ev=ev,
            ), events
        return outcome("act", result["explanation"], decision_id=decision_id), events
    return outcome("act", f"Found the call in hand {decision['hand_no']}.", decision_id=decision_id), events


def parse_outcome(raw, catalog):
    reply = json.loads(raw)
    action = reply["action"]
    decision = reply["decision_id"]
    candidates = reply["candidate_ids"]
    message = reply["message"]
    equity, ev = reply["equity"], reply["call_ev"]
    if action not in {"act", "ask", "no_match", "out_of_scope"} or not isinstance(message, str) or not message.strip():
        raise ValueError("Expected a supported next action and a user-facing message.")
    if unknown_references(message, catalog):
        raise ValueError("The message referenced a decision outside the recorded player view.")
    if not isinstance(candidates, list) or any(key not in catalog for key in candidates):
        raise ValueError("Clarifying options must be recorded decisions in the player's view.")
    if action == "act":
        if decision not in catalog or candidates:
            raise ValueError("An acting response needs one recorded decision.")
        if (equity is None) != (ev is None):
            raise ValueError("Return both equity and call EV for a calculated review.")
        if equity is not None:
            equity, ev = str(Fraction(equity)), str(Fraction(ev))
    else:
        if any(value is not None for value in (decision, equity, ev)):
            raise ValueError("A response without a unique target cannot have a selection or EV.")
        if action == "ask" and (len(candidates) < 2 or len(set(candidates)) != len(candidates)):
            raise ValueError("A clarification needs at least two distinct candidate IDs.")
        if action != "ask" and candidates:
            raise ValueError("Only clarifications list alternative decisions.")
    return outcome(action, message, decision_id=decision, candidate_ids=candidates, equity=equity, call_ev=ev)
