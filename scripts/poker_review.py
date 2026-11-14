"""Review a saved river call with CoreCoder and write a report and trace."""

import argparse
import json
import os
from contextlib import closing
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from time import perf_counter
from typing import ClassVar
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

from corecoder import Agent
from corecoder.llm import LLMResponse, ToolCall
from corecoder.tools.base import Tool

from .poker_equity import RiverInputError, river_call
from .poker_query import find_decisions, open_saved_database

MAX_ROUNDS = 4
MAX_INPUT_BYTES = 16000
MAX_OUTPUT_TOKENS = 512
STATUSES = {"reviewed", "needs_range", "no_match", "ambiguous", "invalid_range", "needs_import", "needs_cards"}
REPORT = """Review a recorded heads-up river call using the supplied selector and equal-weight opponent range.
If the range is absent, ask for it. If there are zero matches, report no_match. If there are multiple matches, ask for the decision ID.
If the calculation returns a status and explanation instead of a result, use that status and explain the issue.
For a reviewed decision, compare the call EV to folding for zero chips and explain the result under the supplied range.
The pot includes the current bet. The contested pot after calling is pot minus uncalled_excess plus to_call.
Use the hero's known cards and public board to discard blocked combinations. A tie is half a win for equity.
Return a JSON object with status, decision_id, equity, call_ev, recommendation, and explanation.
Status is reviewed, needs_range, no_match, ambiguous, invalid_range, needs_import, or needs_cards. For reviewed, copy the exact decision ID and
give equity and call_ev as fraction or integer strings and recommendation as call, fold, or indifferent.
For the other statuses, use null for the decision ID, numbers, and recommendation, and explain what is needed."""


def lookup_calls(database, selector):
    with closing(open_saved_database(database)) as db:
        return [
            {"decision_id": row["decision_id"], "snapshot": row["snapshot"]}
            for row in find_decisions(db, "river", "call", **selector)
        ]


class FindRiverCalls(Tool):
    name = "find_river_calls"
    description = "Look up recorded river calls for this review's selector and return their IDs and pre-action snapshots."
    parameters: ClassVar[dict] = {"type": "object", "properties": {}}

    def __init__(self, database, selector):
        self.database = database
        self.selector = selector
        self.snapshots = {}

    def execute(self) -> str:
        matches = lookup_calls(self.database, self.selector)
        if len(matches) == 1:
            self.snapshots = {matches[0]["decision_id"]: matches[0]["snapshot"]}
        else:
            matches = [{"decision_id": row["decision_id"]} for row in matches]
        return json.dumps(matches)


class CalculateCallEV(Tool):
    name = "calculate_call_ev"
    description = "Calculate exact equity and call EV for a decision returned by find_river_calls, using the supplied range."
    parameters: ClassVar[dict] = {
        "type": "object", "properties": {"decision_id": {"type": "string"}}, "required": ["decision_id"],
    }

    def __init__(self, lookup, opponent_range):
        self.lookup = lookup
        self.opponent_range = opponent_range

    def execute(self, decision_id: str) -> str:
        snapshot = self.lookup.snapshots.get(decision_id)
        if snapshot is None:
            raise ValueError("Look up the decision with find_river_calls first.")
        try:
            result = river_call(snapshot, self.opponent_range)
        except RiverInputError as error:
            return json.dumps({"status": error.status, "explanation": str(error)})
        return json.dumps({"decision_id": decision_id, **result})


class DeepSeekModel:
    model = "deepseek-flash"

    def __init__(self, api_key, max_requests=MAX_ROUNDS):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", max_retries=0, timeout=30)
        self.max_requests = max_requests
        self.api_requests = 0
        self.served_model = None

    def chat(self, messages, tools=None, **callbacks):
        params = {
            "model": self.model, "messages": messages, "max_tokens": MAX_OUTPUT_TOKENS,
            "extra_body": {"thinking": {"type": "disabled"}}, "response_format": {"type": "json_object"},
        }
        if tools:
            params["tools"] = tools
        if self.api_requests >= self.max_requests or len(json.dumps(params, ensure_ascii=False).encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError("The review request limit was reached.")
        self.api_requests += 1
        reply = self.client.chat.completions.create(**params)
        self.served_model = reply.model
        message = reply.choices[0].message
        return LLMResponse(
            content=message.content or "",
            tool_calls=[
                ToolCall(call.id, call.function.name, json.loads(call.function.arguments))
                for call in (message.tool_calls or [])
            ],
            prompt_tokens=reply.usage.prompt_tokens,
            completion_tokens=reply.usage.completion_tokens,
        )


class DemoModel:
    """Follow recorded response rules for the offline demonstration."""

    model = "scripted-demo"
    api_requests = 0

    def chat(self, messages, tools=None, **callbacks):
        last = messages[-1]
        request = json.loads(messages[1]["content"])
        if last["role"] == "user":
            return LLMResponse(tool_calls=[ToolCall("lookup", FindRiverCalls.name, {})])

        report = {"decision_id": None, "equity": None, "call_ev": None, "recommendation": None}
        if not request["opponent_range"]:
            report.update(status="needs_range", explanation="Supply an equal-weight opponent range.")
        elif last["tool_call_id"] == "lookup":
            matches = json.loads(last["content"])
            if len(matches) == 1:
                return LLMResponse(tool_calls=[
                    ToolCall("ev", CalculateCallEV.name, {"decision_id": matches[0]["decision_id"]}),
                ])
            if matches:
                report.update(status="ambiguous", explanation="Multiple calls match. Specify a decision ID.")
            else:
                report.update(status="no_match", explanation="No recorded river call matches this hand.")
        else:
            result = json.loads(last["content"])
            if "status" in result:
                report.update(result)
            else:
                ev = Fraction(result["call_ev"])
                choice = "call" if ev > 0 else "fold" if ev < 0 else "indifferent"
                report.update(
                    status="reviewed", decision_id=result["decision_id"], equity=result["equity"],
                    call_ev=result["call_ev"], recommendation=choice,
                    explanation=f"Against {result['range']}, equity is {result['equity']} and calling is worth "
                    f"{result['call_ev']} chips relative to folding. The higher-EV choice is {choice}.",
                )
        return LLMResponse(content=json.dumps(report))


class RecordedModel:
    def __init__(self, model, events):
        self.model = model
        self.events = events

    def chat(self, messages, tools=None, **callbacks):
        event = {"type": "model", "messages": deepcopy(messages)}
        self.events.append(event)
        started = perf_counter()
        try:
            reply = self.model.chat(messages, tools=tools, **callbacks)
            event.update(response=reply.message, input_tokens=reply.prompt_tokens, output_tokens=reply.completion_tokens)
            return reply
        except Exception as error:
            event["error"] = type(error).__name__
            raise
        finally:
            event["elapsed_seconds"] = perf_counter() - started


class ReviewAgent(Agent):
    def __init__(self, model, tools, events, prompt):
        super().__init__(RecordedModel(model, events), tools=tools, max_rounds=MAX_ROUNDS)
        self.events = events
        self._system = prompt

    def _exec_tool(self, call):
        started = perf_counter()
        result = super()._exec_tool(call)
        self.events.append({
            "type": "tool", "call_id": call.id, "name": call.name, "arguments": call.arguments,
            "result": result, "elapsed_seconds": perf_counter() - started,
        })
        return result


def parse_report(raw, events, with_tools):
    report = json.loads(raw)
    if not isinstance(report, dict) or report.get("status") not in STATUSES:
        raise ValueError("The report is missing a supported status.")
    if not isinstance(report.get("explanation"), str) or not report["explanation"].strip():
        raise ValueError("The report is missing a supported status or explanation.")
    if report["status"] == "reviewed":
        equity, ev = Fraction(report["equity"]), Fraction(report["call_ev"])
        choice = "call" if ev > 0 else "fold" if ev < 0 else "indifferent"
        if report["recommendation"] != choice:
            raise ValueError("The recommendation must match the call EV.")
        if with_tools:
            results = (
                json.loads(event["result"]) for event in events
                if event.get("name") == CalculateCallEV.name and event["result"].startswith("{")
            )
            if not any(
                item.get("decision_id") == report["decision_id"]
                and Fraction(item["equity"]) == equity and Fraction(item["call_ev"]) == ev
                for item in results if "decision_id" in item
            ):
                raise ValueError("The decision and values must match the calculation tool result.")
    elif any(report[key] is not None for key in ("decision_id", "equity", "call_ev", "recommendation")):
        raise ValueError("An incomplete review must leave the decision and numeric fields empty.")
    return report


def review(database, selector, opponent_range, output, model, *, with_tools=True):
    output.mkdir(parents=True, exist_ok=False)
    request = {"selector": selector, "opponent_range": opponent_range}
    lookup = FindRiverCalls(database, selector)
    tools = []
    if with_tools:
        tools.append(lookup)
        if opponent_range:
            tools.append(CalculateCallEV(lookup, opponent_range))
        prompt = REPORT + "\nFind the recorded call with find_river_calls. Use calculate_call_ev for the numeric result."
    else:
        request["candidate_decisions"] = json.loads(lookup.execute())
        prompt = REPORT + "\nUse the supplied candidate decisions to compute the numeric result."
    events = []
    agent = ReviewAgent(model, tools, events, prompt)
    run_id = uuid4().hex
    started = perf_counter()
    report = None
    try:
        raw = agent.chat(json.dumps(request))
    except Exception as error:  # noqa: BLE001 - save the execution trace at the review boundary
        status = "execution_error"
        events.append({"type": "error", "error": type(error).__name__})
    else:
        if agent.messages[-1].get("tool_calls"):
            status = "round_limit"
        else:
            try:
                report = parse_report(raw, events, with_tools)
                status = "report_ready"
            except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
                report = None
                status = "invalid_report"
                events.append({"type": "error", "error": str(error)})

    input_tokens = sum(event.get("input_tokens", 0) for event in events)
    output_tokens = sum(event.get("output_tokens", 0) for event in events)
    cost = (input_tokens * 0.30 + output_tokens * 1.20) / 1_000_000
    if model.api_requests != sum("input_tokens" in event for event in events) and model.api_requests:
        cost = None
    result = {"run_id": run_id, "status": status, "report": report}
    trace = {
        **result, "request": request, "model": model.model, "served_model": getattr(model, "served_model", None),
        "tools": [tool.schema() for tool in tools], "events": events, "elapsed_seconds": perf_counter() - started,
        "api_requests": model.api_requests, "input_tokens": input_tokens, "output_tokens": output_tokens,
        "estimated_cost_usd": cost,
        "pricing": {"source": "https://api-docs.deepseek.com/quick_start/pricing/", "input_per_million": 0.30,
                    "output_per_million": 1.20, "currency": "USD", "checked_on": "2026-11-14"} if model.api_requests else None,
    }
    for name, data in (("report", result), ("trace", trace)):
        (output / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--hand", type=int)
    selector.add_argument("--decision-id")
    parser.add_argument("--range", dest="opponent_range")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="Use DeepSeek instead of the offline demonstration model")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    selection = {"hand_no": args.hand} if args.hand is not None else {"decision_id": args.decision_id}
    if args.hand is not None and args.hand < 1:
        parser.error("--hand must be a positive integer")
    if args.live:
        load_dotenv(args.env_file)
        model = DeepSeekModel(os.environ["DEEPSEEK_API_KEY"])
    else:
        model = DemoModel()
    result = review(args.database, selection, args.opponent_range, args.output, model)
    print(json.dumps({key: result[key] for key in ("run_id", "status", "report", "api_requests")}, indent=2))
    return int(result["status"] != "report_ready")


if __name__ == "__main__":
    raise SystemExit(main())
