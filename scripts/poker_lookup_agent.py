"""Review a natural-language request with the recorded river lookup tools."""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from typing import ClassVar
from uuid import uuid4

from dotenv import load_dotenv

from corecoder.tools.base import Tool

from .poker_lookup import calculate_call, lookup_calls, parse_outcome
from .poker_review import DeepSeekModel, ReviewAgent

REQUESTS_PER_TRIAL = 4
OUTPUT_TOKENS_PER_REQUEST = 512
INPUT_BYTES_PER_REQUEST = 8_192
INPUT_USD_PER_MILLION = 0.30
OUTPUT_USD_PER_MILLION = 1.20

PROMPT = """Review the selected player's recorded river calls. Hand numbers are in deal order.
Each record is the state before calling. to_call is the extra amount paid. The last board card is the river.
Honor every explicit criterion, including exclusions and order. Reply in JSON with action, decision_id,
candidate_ids, equity, call_ev and message. Use:
- act: one intended decision. Copy its full ID.
- ask: multiple possible decisions. Copy every matching ID and ask which hand or another distinguishing question.
- no_match: zero matches. out_of_scope: the request is outside river-call reviews.
Outside act set decision_id, equity and call_ev to null. Outside ask use [] for candidate_ids.
Use exact fractions or integers as strings for equity and call_ev only for a unique decision with a supplied range.
Remove combos blocked by known cards. Equity = (wins + ties/2) / compatible combos.
Call EV = equity * (pot - uncalled_excess + to_call) - to_call. Keep message short."""

AGENT_PROMPT = PROMPT + """
Use find_river_calls to look up relevant records. Its filters are exact and optional. If you need a comparison or an
exclusion, use a broader lookup and reason over the returned rows. For EV on exactly one intended decision, call
calculate_call_ev with the ID from lookup and use the result. If no valid EV is available, state why and leave it null."""

DIRECT_PROMPT = PROMPT + """
The request includes the full catalog of eligible decisions. Work from those records and calculate EV yourself.
Each draft and revision must follow the same JSON format."""

REVISE = "Check your draft against the request and catalog. Correct any errors and return the complete JSON."


class FindRiverCalls(Tool):
    name = "find_river_calls"
    description = "Find recorded river calls for the selected player. All filters are exact and optional."
    parameters: ClassVar[dict] = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "hand_no": {"type": "integer", "minimum": 1},
            "call_cost": {"type": "integer", "minimum": 1},
            "river_card": {"type": "string", "description": "Fifth board card, for example 3s, Ks or Ah."},
            "decision_id": {"type": "string", "description": "A complete decision ID explicitly provided in the request."},
        },
    }

    def __init__(self, database, player):
        self.database = database
        self.player = player
        self.seen = {}

    def execute(self, *, hand_no=None, call_cost=None, river_card=None, decision_id=None):
        rows = lookup_calls(self.database, self.player, hand_no=hand_no, call_cost=call_cost,
                            river_card=river_card, decision_id=decision_id)
        self.seen.update((row["decision_id"], row) for row in rows)
        return json.dumps(rows, separators=(",", ":"))


class CalculateCallEV(Tool):
    name = "calculate_call_ev"
    description = "Calculate exact river call EV for the supplied range and one decision found by lookup."
    parameters: ClassVar[dict] = {
        "type": "object", "additionalProperties": False,
        "properties": {"decision_id": {"type": "string"}}, "required": ["decision_id"],
    }

    def __init__(self, lookup, opponent_range):
        self.lookup = lookup
        self.opponent_range = opponent_range

    def execute(self, decision_id):
        if decision_id not in self.lookup.seen:
            raise ValueError("Look up this decision before calculating EV.")
        return json.dumps(calculate_call(self.lookup.seen[decision_id], self.opponent_range))


def lookup_model(api_key):
    return DeepSeekModel(api_key, REQUESTS_PER_TRIAL, max_output_tokens=OUTPUT_TOKENS_PER_REQUEST,
                         max_input_bytes=INPUT_BYTES_PER_REQUEST)


def run_model_lookup(database, player, request, opponent_range, model, *, direct=False):
    started = perf_counter()
    catalog = {row["decision_id"]: row for row in lookup_calls(database, player)}
    payload = {"request": request, "opponent_range": opponent_range}
    tools = []
    if direct:
        payload["catalog"] = list(catalog.values())
    else:
        lookup = FindRiverCalls(database, player)
        tools.append(lookup)
        if opponent_range:
            tools.append(CalculateCallEV(lookup, opponent_range))
    events = []
    agent = ReviewAgent(model, tools, events, DIRECT_PROMPT if direct else AGENT_PROMPT, REQUESTS_PER_TRIAL)
    raw, report, error = None, None, None
    try:
        raw = agent.chat(json.dumps(payload))
        if direct:
            # The direct baseline sees its own draft and may revise within the same budget.
            for _ in range(REQUESTS_PER_TRIAL - 1):
                raw = agent.chat(REVISE)
                del agent.messages[1:3]
        if agent.messages[-1].get("tool_calls"):
            raise ValueError("The model ran out of rounds before returning its answer.")
        report = parse_outcome(raw, catalog)
        if not direct:
            returned = [event for event in events if event.get("name") == "find_river_calls"]
            if report["action"] == "act" and report["decision_id"] not in lookup.seen:
                raise ValueError("The selected decision must come from lookup.")
            if report["action"] == "ask" and not set(report["candidate_ids"]) <= lookup.seen.keys():
                raise ValueError("Clarifying options must come from lookup.")
            if report["action"] == "no_match" and not any(event["result"].startswith("[") for event in returned):
                raise ValueError("Use the lookup tool to check whether a decision exists.")
            if report["call_ev"] is not None:
                calculations = [
                    json.loads(event["result"]) for event in events
                    if event.get("name") == "calculate_call_ev" and event["result"].startswith("{")
                ]
                if not any(all(item.get(field) == report[field] for field in ("decision_id", "equity", "call_ev"))
                           for item in calculations):
                    raise ValueError("The reported EV must match the observed calculation for that decision.")
    except Exception as exc:  # noqa: BLE001 - preserve the failed trial and its trace for analysis
        error = str(exc) if isinstance(exc, (KeyError, TypeError, ValueError)) else type(exc).__name__
        report = None

    requests = model.api_requests
    input_tokens = sum(event.get("input_tokens", 0) for event in events)
    output_tokens = sum(event.get("output_tokens", 0) for event in events)
    cost = None
    if requests == sum("input_tokens" in event for event in events):
        cost = (input_tokens * INPUT_USD_PER_MILLION + output_tokens * OUTPUT_USD_PER_MILLION) / 1_000_000
    return {
        "run_id": uuid4().hex, "request": request, "opponent_range": opponent_range, "player": player,
        "report": report, "raw": raw, "error": error, "events": events, "elapsed_seconds": perf_counter() - started,
        "api_requests": requests, "input_tokens": input_tokens, "output_tokens": output_tokens,
        "estimated_cost_usd": cost, "model": model.model, "served_model": getattr(model, "served_model", None),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="SQLite database from scripts.poker_query --save-to")
    parser.add_argument("request")
    parser.add_argument("--player", required=True, help="Player name stored in the hand history, for example hero")
    parser.add_argument("--range", dest="opponent_range")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(args.env_file)
    model = lookup_model(os.environ["DEEPSEEK_API_KEY"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        result = run_model_lookup(args.database, args.player, args.request, args.opponent_range, model)
        json.dump(result, file, indent=2)
    print(json.dumps(result["report"] or {"error": result["error"]}, indent=2))
    return int(result["report"] is None)


if __name__ == "__main__":
    raise SystemExit(main())
