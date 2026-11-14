# Natural-language river lookup benchmark

This benchmark asks whether model-directed tools help with locating a recorded poker decision and deciding when to ask a clarifying question. It includes requests with an explicit selector and range to measure when a fixed pipeline is sufficient.

## Dataset v1

There are 28 synthetic English requests. Development uses the [four original hands](../river/decisions.phhs). Held-out uses [six separate hands](heldout.phhs), with different betting sequences and Hero in both seats. Hand numbers are local to each file and follow deal order. Each review is scoped to Hero's recorded river calls. One held-out hand contains only the opponent's river call.

| Split | Clear | Ambiguous | No match | Out of scope | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 4 | 3 | 2 | 1 | 10 |
| Held-out | 6 | 5 | 4 | 3 | 18 |

[Task labels](tasks.json) include a manual rationale, selected decision or candidate set, and exact expected equity and call EV for applicable cases. [The v1 manifest](v1.json) pins the two histories and labels by SHA-256. An annotated ID such as `3:13` uses the hand number and original action number. The evaluator adds the source file's SHA-256 prefix at runtime. For example, the development negative-EV case uses AA against `9c9d` on `2c 7d 9h Jc 3s`. Aces lose to three nines, so the call has zero equity and costs 12 chips.

## Scoring

- **Decision ID.** Exact ID match on requests with one intended decision. Any other outcome on those cases misses the ID. Requests with no unique decision must leave the selection empty.
- **Next action.** Compare `act`, `ask`, `no_match` or `out_of_scope` on every request.
- **Clarification quality.** On ambiguous cases, require the exact candidate set and a question that distinguishes the candidates. Calling the calculator before resolving an ambiguous request fails this check. Joint lookup requires the correct decision, action and clarification as applicable, with zero invented IDs.
- **Invented IDs.** Count IDs absent from the current task's scope that are emitted as a decision, candidate, reference in the response, or tool argument. Selecting the wrong existing record is graded separately as a lookup error.
- **End-to-end EV.** On labeled EV cases, require the correct decision and exact equity and call EV. Report the explicit hand-number cases separately.

## Comparison

The keyword parser and fixed pipeline query the same database and use the same EV function as the tool-calling agent. DeepSeek direct answering receives the same eligible facts in a catalog. Both model modes use DeepSeek Flash in non-thinking mode and share a ceiling of four requests per trial, with 8 KiB per request and 512 generated tokens per request. Direct answering gets an initial draft and three revisions. The agent uses the tool calls it selects and stops when it answers.

Run each model three times per task with fresh state. The deterministic pipeline runs once per task. Report per-trial scores and cases that pass on all three trials. Each held-out result row links to the evidence used to diagnose its failures.

## Keyword baseline

| Split | Exact ID | Next action | Clarification | Invented IDs | Joint lookup | EV | Explicit hand EV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development | 4/4 | 10/10 | 3/3 | 0 | 10/10 | 4/4 | 2/2 |
| Held-out | 4/6 | 16/18 | 3/5 | 0 | 14/18 | 4/5 | 2/2 |

On held-out requests, the keyword pipeline reached 4/6 on clear requests, 3/5 on ambiguous requests, 4/4 on missing records, and 3/3 on out-of-scope requests. It used zero API requests. Model scores come from the live three-way comparison.

## Keyword error analysis

Four held-out requests missed the joint lookup check. The parser handles exact amounts and river cards, and the fixed pipeline asks a question when the parsed query returns multiple decisions.

| Task | Expected | Observed and cause |
| --- | --- | --- |
| `h03-amount-in-words` | Select hand 5 and report EV of −20. | “Put in twenty to match the last raise” produced an empty filter. The parser recognized the review intent and asked the user to choose from all five Hero calls. Its amount rule expects a unit such as “twenty chips.” |
| `h05-ordinal` | Select hand 1, the earlier of the two eight-chip calls. | The parser found both hands 1 and 6 but passed no ordering instruction to the pipeline. It asked which hand the user meant. |
| `h09-same-eight` | Ask the user to select hand 1 or 6. | “Matched eight” produced no amount filter. The parser correctly asked a question but offered all five hands. |
| `h11-negated-cost` | Ask the user to select hand 2 or 3. | The parser read “eight-chip” as an exact positive filter. It offered hands 1 and 6, which were precisely the calls the user excluded. |

The four failures are in parsing the query and ranking its matches. For requests that specified the hand number, the fixed pipeline calculated every labeled EV exactly.

## Reproduce

From the repository root in the project environment, run the offline tool and grader checks, then the fixed pipeline over the frozen dataset.

```sh
python -m scripts.check_poker_lookup
python -m scripts.poker_lookup_eval .poker-agent/lookup-keyword
```

To run the complete comparison, set `DEEPSEEK_API_KEY` locally and choose a new output directory. The evaluator stores `evaluation.md`, `evaluation.json` and each trial's trace in that directory.

```sh
python -m scripts.poker_lookup_eval .poker-agent/lookup-live --mode compare
```

To try one natural-language review, import the development hand history and run the agent with the selected player.

```sh
python -m scripts.poker_query benchmarks/river/decisions.phhs --save-to .poker-agent/lookup-dev.sqlite3
python -m scripts.poker_lookup_agent .poker-agent/lookup-dev.sqlite3 "Review my 12-chip river call." --player hero --output .poker-agent/lookup-example.json
```

Importing the hand history records the seat-to-player mapping for each hand. For databases made before that mapping was stored, run the import again to populate it.
