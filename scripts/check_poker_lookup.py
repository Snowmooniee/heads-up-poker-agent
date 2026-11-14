"""Exercise decision lookup, clarification and scoring through CoreCoder without an API key."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from corecoder.llm import LLMResponse, ToolCall

from .poker_lookup import lookup_calls, outcome
from .poker_lookup_agent import REQUESTS_PER_TRIAL, run_model_lookup
from .poker_lookup_eval import FIXTURES, clarifies, grade, load_tasks
from .poker_query import save_history


class ScriptedModel:
    model = "scripted"

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.api_requests = 0

    def chat(self, messages, tools=None, **callbacks):
        self.api_requests += 1
        return next(self.responses)


def check():
    manifest, tasks = load_tasks()
    labeled = {task["id"]: task for task in tasks}
    with TemporaryDirectory() as root:
        database = Path(root) / "heldout.sqlite3"
        source = save_history(FIXTURES / manifest["histories"]["heldout"]["path"], database)["source_id"]
        catalog = {row["decision_id"]: row for row in lookup_calls(database, "hero")}
        assert [row["hand_no"] for row in catalog.values()] == [1, 2, 3, 5, 6]
        assert [row["hand_no"] for row in lookup_calls(database, "opponent")] == [4]
        assert not lookup_calls(database, "hero", decision_id=f"{source}:4:15")
        assert [row["hand_no"] for row in lookup_calls(database, "hero", river_card="4S")] == [2]
        assert [row["hand_no"] for row in lookup_calls(database, "hero", river_card="2h")] == [5]

        def run(task_id, *replies, direct=False):
            task = labeled[task_id]
            model = ScriptedModel(*replies)
            trace = run_model_lookup(database, "hero", task["request"], task.get("range"), model, direct=direct)
            return trace, grade(task, trace, catalog, source)

        choices = [f"{source}:2:14", f"{source}:3:13"]
        find_pair = LLMResponse(tool_calls=[ToolCall("q1", "find_river_calls", {"call_cost": 16})])
        ask = LLMResponse(content=json.dumps(outcome("ask", "Which hand did you mean, 2 or 3?", candidate_ids=choices)))
        trace, score = run("h07-same-sixteen", find_pair, ask)
        assert score["lookup_pass"] and trace["api_requests"] == 2
        assert [event["name"] for event in trace["events"] if event["type"] == "tool"] == ["find_river_calls"]
        pair = [catalog[key] for key in choices]
        assert clarifies("Which hand_no?", pair)
        assert clarifies("Which river call do you mean? Share the hand number.", pair)
        assert clarifies("Two calls match (hands 2, 3). Which one?", pair)
        assert not clarifies("Two calls match (hands 2, 5). Which one?", pair)

        generic = LLMResponse(content=json.dumps(outcome("ask", "Can you clarify?", candidate_ids=choices)))
        _, score = run("h07-same-sixteen", find_pair, generic)
        assert score["next_action"] and not score["clarification"]
        calc_early = LLMResponse(tool_calls=[ToolCall("bad", "calculate_call_ev", {"decision_id": choices[0]})])
        _, score = run("h07-same-sixteen", find_pair, calc_early, ask)
        assert score["next_action"] and not score["clarification"]

        find_loss = LLMResponse(tool_calls=[ToolCall("q2", "find_river_calls", {"hand_no": 3})])
        calculate = LLMResponse(tool_calls=[ToolCall("ev", "calculate_call_ev", {"decision_id": choices[1]})])
        loss = LLMResponse(content=json.dumps(outcome("act", "Calling costs 16 chips.", decision_id=choices[1],
                                                      equity="0", call_ev="-16")))
        _, score = run("h02-numbered-loss", find_loss, calculate, loss)
        assert score["lookup_pass"] and score["ev"]
        wrong = LLMResponse(content=json.dumps(outcome("act", "Found it.", decision_id=choices[0])))
        _, score = run("h02-numbered-loss", wrong, loss, loss, loss, direct=True)
        assert score["lookup_pass"] and score["ev"] and not score["invented_ids"]
        invented = f"{source}:9:14"
        draft = LLMResponse(content=json.dumps(outcome("act", "Found it.", decision_id=invented)))
        trace, score = run("h02-numbered-loss", draft, loss, loss, loss, direct=True)
        assert trace["api_requests"] == REQUESTS_PER_TRIAL and trace["report"]["decision_id"] == choices[1]
        assert score["invented_ids"] == [invented] and not score["lookup_pass"]
        tool_guess = LLMResponse(tool_calls=[ToolCall("invented", "calculate_call_ev", {"decision_id": invented})])
        _, score = run("h02-numbered-loss", tool_guess, find_loss, calculate, loss)
        assert score["invented_ids"] == [invented] and score["ev"]

        dev = Path(root) / "dev.sqlite3"
        dev_source = save_history(FIXTURES / manifest["histories"]["dev"]["path"], dev)["source_id"]
        original = labeled["d07-same-river"]
        options = [f"{dev_source}:{key}" for key in original["candidates"]]
        request = LLMResponse(tool_calls=[ToolCall("river", "find_river_calls", {"river_card": "3s"})])
        question = LLMResponse(content=json.dumps(outcome("ask", "Which hand did you mean?", candidate_ids=options)))
        trace = run_model_lookup(dev, "hero", original["request"], None, ScriptedModel(request, question))
        returned = next(event for event in trace["events"] if event["type"] == "tool")
        assert [row["hand_no"] for row in json.loads(returned["result"])] == [1, 3]
        assert trace["report"]["candidate_ids"] == options
    print("Lookup, player scope, clarification, exact EV and raw ID scoring passed.")


if __name__ == "__main__":
    check()
