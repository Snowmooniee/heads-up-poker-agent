"""Compare keyword, direct and tool-calling approaches on frozen river lookup tasks."""

import argparse
import json
import os
import platform
import re
import sqlite3
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from statistics import median
from time import perf_counter
from uuid import uuid4

from dotenv import load_dotenv

from .poker_lookup import keyword_pipeline, lookup_calls, unknown_references
from .poker_lookup_agent import (
    INPUT_BYTES_PER_REQUEST,
    INPUT_USD_PER_MILLION,
    OUTPUT_TOKENS_PER_REQUEST,
    OUTPUT_USD_PER_MILLION,
    REQUESTS_PER_TRIAL,
    lookup_model,
    run_model_lookup,
)
from .poker_query import save_history

FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks" / "lookup"
MODES = ("keyword", "direct", "agent")
MODEL_TRIALS = 3
LIVE_WORKERS = 6
PLAYER = "hero"
ACCESS_ERRORS = {"AuthenticationError", "PermissionDeniedError", "PaymentRequiredError", "APIConnectionError"}
HAND_QUESTION = re.compile(
    r"\b(?:(?:which|what) hand(?: number)?|hand (?:number|did you mean)|decision id|choose (?:a|the) hand)\b",
)


def load_tasks():
    manifest = json.loads((FIXTURES / "v1.json").read_text(encoding="utf-8"))
    task_bytes = (FIXTURES / "tasks.json").read_bytes()
    if sha256(task_bytes).hexdigest() != manifest["tasks_sha256"]:
        raise ValueError("The labels differ from the frozen lookup-v1 manifest.")
    for history in manifest["histories"].values():
        if sha256((FIXTURES / history["path"]).read_bytes()).hexdigest() != history["sha256"]:
            raise ValueError(f"The history {history['path']} differs from lookup-v1.")
    return manifest, json.loads(task_bytes)


def unknown_reply_ids(reply, catalog):
    if not isinstance(reply, dict):
        return []
    ids = [reply.get("decision_id")]
    options = reply.get("candidate_ids")
    if isinstance(options, list):
        ids.extend(options)
    unknown = [str(value) for value in ids if value is not None and str(value) not in catalog]
    message = reply.get("message")
    if isinstance(message, str):
        unknown.extend(unknown_references(message, catalog))
    return unknown


def invented_ids(trace, catalog):
    unknown = []
    if trace["model"] == "keyword":
        unknown.extend(unknown_reply_ids(trace["report"], catalog))
        unknown.extend(
            key for event in trace["events"] if (key := event["arguments"].get("decision_id")) and key not in catalog
        )
    for event in trace["events"]:
        response = event.get("response")
        if not response:
            continue
        raw = response["content"]
        if raw:
            try:
                unknown.extend(unknown_reply_ids(json.loads(raw), catalog))
            except ValueError:
                unknown.extend(unknown_references(raw, catalog))
        for call in response.get("tool_calls", []):
            decision = json.loads(call["function"]["arguments"]).get("decision_id")
            if decision is not None and str(decision) not in catalog and str(decision) not in trace["request"]:
                unknown.append(str(decision))
    return unknown


def clarifies(message, rows):
    hand_numbers = {row["hand_no"] for row in rows}
    amounts = {row["to_call"] for row in rows}
    cards = {row["board"][-1] for row in rows}
    text = message.lower()
    for question in re.findall(r"[^.!?]+\?", text):
        asks_hand = HAND_QUESTION.search(question)
        options = set(re.findall(r"\b(?:hands?|or|and)\s*#?\s*(\d+)\b", text))
        offers_choice = re.search(r"\b(?:which one|which call|do you mean|did you mean|would you like)\b", question)
        if offers_choice and all(str(number) in options for number in hand_numbers):
            asks_hand = True
        asks_amount = re.search(r"\b(?:which|what|how many)\b.{0,32}\b(?:chips|amount|cost)\b", question)
        asks_card = re.search(r"\b(?:which|what)\b.{0,28}\b(?:river card|last card|fifth card)\b", question)
        if ((asks_hand and len(hand_numbers) == len(rows)) or "decision id" in question
                or (asks_amount and len(amounts) == len(rows)) or (asks_card and len(cards) == len(rows))):
            return True
    return False


def attempted_calculation(events):
    return any(
        event.get("name") == "calculate_call_ev"
        or any(call["function"]["name"] == "calculate_call_ev"
               for call in (event.get("response") or {}).get("tool_calls", []))
        for event in events
    )


def grade(task, trace, catalog, source_id):
    report = trace["report"] or {}
    expected_decision = f"{source_id}:{task['decision']}" if "decision" in task else None
    selected = report.get("decision_id")
    action = report.get("action") == task["action"]
    question_ok = None
    if task["action"] == "ask":
        candidates = {f"{source_id}:{key}" for key in task["candidates"]}
        question_ok = action and set(report["candidate_ids"]) == candidates and clarifies(
            report["message"], [catalog[key] for key in candidates],
        ) and not attempted_calculation(trace["events"])
    unknown = invented_ids(trace, catalog)
    decision = trace["report"] is not None and selected == expected_decision
    ev = None
    if "call_ev" in task:
        ev = decision and action and report.get("equity") == task["equity"] and report.get("call_ev") == task["call_ev"]
    errors = []
    if trace["error"]:
        errors.append("response_error")
    if not action:
        errors.append("next_action")
    elif question_ok is False:
        errors.append("clarification")
    if not decision:
        errors.append("decision_id" if expected_decision else "unexpected_selection")
    if unknown:
        errors.append("invented_id")
    if ev is False:
        errors.append("ev")
    return {
        "exact_id": decision if expected_decision else None,
        "next_action": action,
        "clarification": question_ok,
        "invented_ids": unknown,
        "ev": ev,
        "explicit_ev": ev is not None and bool(re.search(r"\bhand #?\d+", task["request"].lower())),
        "lookup_pass": decision and action and question_ok is not False and not unknown,
        "errors": errors,
    }


def run_keyword(database, task):
    start = perf_counter()
    report, events = keyword_pipeline(database, PLAYER, task["request"], task.get("range"))
    return {
        "run_id": uuid4().hex, "request": task["request"], "opponent_range": task.get("range"), "player": PLAYER,
        "report": report, "raw": None, "error": None, "events": events, "elapsed_seconds": perf_counter() - start,
        "api_requests": 0, "input_tokens": 0, "output_tokens": 0,
        "estimated_cost_usd": 0, "model": "keyword", "served_model": None,
    }


def ratio(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return f"{sum(values)}/{len(values)}" if values else "—"


def summary(rows):
    per_task = {}
    for row in rows:
        per_task.setdefault(row["task"], []).append(row["lookup_pass"])
    costs = [row["estimated_cost_usd"] for row in rows]
    expected_trials = 1 if rows[0]["mode"] == "keyword" else MODEL_TRIALS
    consistent = sum(len(trials) == expected_trials and all(trials) for trials in per_task.values())
    return {
        "decision_id": ratio(rows, "exact_id"), "next_action": ratio(rows, "next_action"),
        "clarification": ratio(rows, "clarification"),
        "lookup": ratio(rows, "lookup_pass"), "all_trials": f"{consistent}/{len(per_task)}",
        "invented_ids": sum(len(row["invented_ids"]) for row in rows),
        "trials_with_invented_ids": sum(bool(row["invented_ids"]) for row in rows),
        "ev": ratio(rows, "ev"), "explicit_ev": ratio([row for row in rows if row["explicit_ev"]], "ev"),
        "api_requests": sum(row["api_requests"] for row in rows), "input_tokens": sum(row["input_tokens"] for row in rows),
        "output_tokens": sum(row["output_tokens"] for row in rows),
        "estimated_cost_usd": None if None in costs else sum(costs),
        "median_seconds": round(median(row["elapsed_seconds"] for row in rows), 4),
        "errors": Counter(error for row in rows for error in row["errors"]),
    }


def write_summary(output, manifest, rows):
    totals = {
        split: {
            mode: summary([row for row in rows if row["split"] == split and row["mode"] == mode])
            for mode in MODES if any(row["split"] == split and row["mode"] == mode for row in rows)
        }
        for split in manifest["histories"] if any(row["split"] == split for row in rows)
    }
    config = {
        "player": PLAYER, "model_trials_per_task": MODEL_TRIALS, "requests_per_trial": REQUESTS_PER_TRIAL,
        "input_bytes_per_request": INPUT_BYTES_PER_REQUEST, "output_tokens_per_request": OUTPUT_TOKENS_PER_REQUEST,
        "input_usd_per_million": INPUT_USD_PER_MILLION, "output_usd_per_million": OUTPUT_USD_PER_MILLION,
        "live_case_workers": LIVE_WORKERS, "thinking": "disabled",
        "pricing_source": "https://api-docs.deepseek.com/quick_start/pricing/",
    }
    environment = {"system": platform.system(), "python": platform.python_version(), "sqlite": sqlite3.sqlite_version}
    result = {"dataset": manifest, "configuration": config, "environment": environment, "totals": totals, "trials": rows}
    (output / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Natural-language river lookup evaluation", "", f"Dataset `{manifest['version']}`.", ""]
    for split in reversed(totals):
        lines.extend((
            f"## {split}", "",
            "| Mode | Exact ID | Next action | Clarification | Invented IDs | Joint lookup | All trials | EV | Explicit EV | Requests | Median s | Est. USD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ))
        for mode, total in totals[split].items():
            columns = ("decision_id", "next_action", "clarification", "invented_ids", "lookup", "all_trials", "ev", "explicit_ev",
                       "api_requests", "median_seconds")
            cost = total["estimated_cost_usd"]
            values = [mode, *(str(total[key]) for key in columns), f"{cost:.6f}" if cost is not None else "—"]
            lines.append("| " + " | ".join(values) + " |")
        lines.extend((
            "", "| Mode | Clear | Ambiguous | No match | Out of scope |", "| --- | ---: | ---: | ---: | ---: |",
        ))
        for mode in totals[split]:
            selected = [row for row in rows if row["split"] == split and row["mode"] == mode]
            scores = [ratio([row for row in selected if row["category"] == category], "lookup_pass")
                      for category in ("clear", "ambiguous", "no_match", "out_of_scope")]
            lines.append("| " + " | ".join([mode, *scores]) + " |")
        lines.append("")
    lines.extend(("## Trials", "", "| Split | Mode | Task | Trial | Check | Trace |", "| --- | --- | --- | ---: | --- | --- |"))
    for row in rows:
        errors = ", ".join(row["errors"]) or "Pass"
        lines.append(f"| {row['split']} | {row['mode']} | {row['task']} | {row['trial']} | {errors} | [Trace]({row['trace']}) |")
    (output / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def run_case(task, sources, modes, api_key, output):
    database, source_id, catalog = sources[task["split"]]
    rows = []
    for approach in modes:
        trials = 1 if approach == "keyword" else MODEL_TRIALS
        for trial in range(1, trials + 1):
            if approach == "keyword":
                trace = run_keyword(database, task)
            else:
                trace = run_model_lookup(
                    database, PLAYER, task["request"], task.get("range"), lookup_model(api_key), direct=approach == "direct",
                )
            path = Path(approach) / task["id"] / f"trial-{trial}.json"
            (output / path).parent.mkdir(parents=True, exist_ok=True)
            score = grade(task, trace, catalog, source_id)
            (output / path).write_text(json.dumps({**trace, "score": score}, indent=2) + "\n", encoding="utf-8")
            rows.append({
                "mode": approach, "task": task["id"], "category": task["category"], "split": task["split"], "trial": trial,
                "trace": path.as_posix(), "report": trace["report"], "error": trace["error"], **score,
                **{key: trace[key] for key in ("api_requests", "input_tokens", "output_tokens", "estimated_cost_usd",
                                              "elapsed_seconds", "served_model")},
            })
            if trace["error"] in ACCESS_ERRORS:
                return rows
    return rows


def evaluate(output, *, split="all", mode="keyword", api_key=None):
    manifest, tasks = load_tasks()
    output.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name, history in manifest["histories"].items():
        if split in ("all", name):
            database = output / f"{name}.sqlite3"
            source = save_history(FIXTURES / history["path"], database)["source_id"]
            sources[name] = database, source, {row["decision_id"]: row for row in lookup_calls(database, PLAYER)}
    tasks = [task for task in tasks if task["split"] in sources]
    modes = MODES if mode == "compare" else (mode,)
    if mode == "keyword":
        rows = [row for task in tasks for row in run_case(task, sources, modes, api_key, output)]
    else:
        # The first case checks provider access before starting the parallel evaluation.
        rows = run_case(tasks[0], sources, modes, api_key, output)
        expected = sum(1 if approach == "keyword" else MODEL_TRIALS for approach in modes)
        if len(rows) < expected or rows[-1]["error"] in ACCESS_ERRORS:
            write_summary(output, manifest, rows)
            raise SystemExit(f"Live comparison stopped at {tasks[0]['id']}: {rows[-1]['error']}.")
        print(f"Finished {tasks[0]['id']}", flush=True)
        with ThreadPoolExecutor(max_workers=LIVE_WORKERS) as pool:
            futures = [pool.submit(run_case, task, sources, modes, api_key, output) for task in tasks[1:]]
            for task, future in zip(tasks[1:], futures):
                runs = future.result()
                rows.extend(runs)
                print(f"{task['id']}: {len(runs)}/{expected} trials", flush=True)
    return write_summary(output, manifest, rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--split", choices=("all", "dev", "heldout"), default="all")
    parser.add_argument("--mode", choices=("keyword", "direct", "agent", "compare"), default="keyword")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    api_key = None
    if args.mode != "keyword":
        load_dotenv(args.env_file)
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            parser.error("Set DEEPSEEK_API_KEY or pass the local dotenv file with --env-file.")
    result = evaluate(args.output, split=args.split, mode=args.mode, api_key=api_key)
    print(json.dumps(result["totals"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
