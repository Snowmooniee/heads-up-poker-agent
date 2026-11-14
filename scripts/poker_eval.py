"""Run river-review scenarios and grade their reports and actual tool calls."""

import argparse
import json
import os
import platform
import sqlite3
from fractions import Fraction
from pathlib import Path
from statistics import median

from dotenv import load_dotenv

from .poker_query import save_history
from .poker_review import DeepSeekModel, DemoModel, review

FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks" / "river"


def grade(trace, expected, source_id, mode):
    if trace["status"] != "report_ready":
        return [trace["status"]]

    report = trace["report"]
    errors = []
    if report["status"] != expected["status"]:
        return ["status"]
    if expected["status"] == "reviewed":
        decision_id = f"{source_id}:{expected['decision']}"
        if report["decision_id"] != decision_id:
            errors.append("decision")
        for field in ("equity", "call_ev"):
            if Fraction(report[field]) != Fraction(expected[field]):
                errors.append(field)
        if report["recommendation"] != expected["recommendation"]:
            errors.append("recommendation")

    if mode != "direct":
        calls = [event for event in trace["events"] if event["type"] == "tool"]
        expected_names = ["find_river_calls"]
        if expected["status"] in ("reviewed", "invalid_range"):
            expected_names.append("calculate_call_ev")
        if [call["name"] for call in calls] != expected_names:
            errors.append("tool_sequence")
        elif expected["status"] == "reviewed":
            result = json.loads(calls[-1]["result"])
            if (
                calls[-1]["arguments"]["decision_id"] != decision_id or result.get("decision_id") != decision_id
                or result["range"] != trace["request"]["opponent_range"]
                or Fraction(result["call_ev"]) != Fraction(expected["call_ev"])
            ):
                errors.append("tool_result")
    return errors


def run_eval(output, modes, split="all", ids=(), api_key=None):
    tasks = json.loads((FIXTURES / "tasks.json").read_text(encoding="utf-8"))
    tasks = [task for task in tasks if (split == "all" or task["split"] == split) and (not ids or task["id"] in ids)]
    if not tasks:
        raise ValueError("No evaluation tasks matched.")
    output.mkdir(parents=True, exist_ok=False)
    database = output / "decisions.sqlite3"
    imported = save_history(FIXTURES / "decisions.phhs", database)
    source_id = imported["source_id"]
    rows = []
    for mode in modes:
        for task in tasks:
            model = DemoModel() if mode == "offline" else DeepSeekModel(api_key, **({"max_requests": 1} if mode == "direct" else {}))
            path = Path(mode) / task["id"]
            trace = review(
                database, {"hand_no": task["hand"]}, task["range"], output / path, model, with_tools=mode != "direct",
            )
            errors = grade(trace, task["expected"], source_id, mode)
            rows.append({
                "mode": mode, "task": task["id"], "split": task["split"], "passed": not errors, "errors": errors,
                "expected": task["expected"], "report": trace["report"], "trace": (path / "trace.json").as_posix(),
                "run_id": trace["run_id"], "tool_calls": sum(event["type"] == "tool" for event in trace["events"]),
                **{key: trace[key] for key in (
                    "model", "served_model", "elapsed_seconds", "api_requests", "input_tokens", "output_tokens",
                    "estimated_cost_usd",
                )},
            })
    totals = {}
    for mode in modes:
        samples = [row for row in rows if row["mode"] == mode]
        costs = [row["estimated_cost_usd"] for row in samples]
        totals[mode] = {
            "passed": sum(row["passed"] for row in samples),
            "total": len(samples),
            "tool_calls": sum(row["tool_calls"] for row in samples),
            "api_requests": sum(row["api_requests"] for row in samples),
            "input_tokens": sum(row["input_tokens"] for row in samples),
            "output_tokens": sum(row["output_tokens"] for row in samples),
            "median_seconds": round(median(row["elapsed_seconds"] for row in samples), 3),
            "estimated_cost_usd": None if None in costs else sum(costs),
        }
    environment = {"system": platform.system(), "python": platform.python_version(), "sqlite": sqlite3.sqlite_version}
    result = {"environment": environment, "source_id": source_id, "totals": totals, "tasks": rows}
    (output / "evaluation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# River review evaluation", "",
        f"{environment['system']} · Python {environment['python']} · SQLite {environment['sqlite']}", "",
        "| Mode | Passed | Tool calls | API requests | Input / output tokens | Median s | Estimated USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, total in totals.items():
        lines.append(
            f"| {mode} | {total['passed']}/{total['total']} | {total['tool_calls']} | {total['api_requests']} | "
            f"{total['input_tokens']} / {total['output_tokens']} | {total['median_seconds']} | {total['estimated_cost_usd']} |"
        )
    lines.extend(("", "| Mode | Scenario | Check | Trace |", "| --- | --- | --- | --- |"))
    for row in rows:
        check = "Pass" if row["passed"] else ", ".join(row["errors"])
        lines.append(f"| {row['mode']} | {row['task']} | {check} | [Trace]({row['trace']}) |")
    (output / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--split", choices=("all", "dev", "heldout"), default="all")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--mode", choices=("offline", "agent", "direct", "compare"), default="offline")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    api_key = None
    if args.mode != "offline":
        load_dotenv(args.env_file)
        api_key = os.environ["DEEPSEEK_API_KEY"]
    modes = ("agent", "direct") if args.mode == "compare" else (args.mode,)
    result = run_eval(args.output, modes, args.split, args.task, api_key)
    print(json.dumps(result["totals"], indent=2))
    return int(not all(row["passed"] for row in result["tasks"])) if args.mode == "offline" else 0


if __name__ == "__main__":
    raise SystemExit(main())
