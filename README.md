# Heads-up Poker Agent

Review recorded heads-up no-limit Hold'em river decisions against a supplied opponent range. CoreCoder calls two tools to retrieve the decision from SQLite and calculate its exact equity and call EV with PokerKit.

## Run the review demo

From a clean Linux or macOS checkout with Python 3.11 or newer:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . pokerkit==0.7.7
.venv/bin/python -m scripts.poker_eval .poker-agent/demo
~~~

On Windows PowerShell:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . pokerkit==0.7.7
.\.venv\Scripts\python.exe -m scripts.poker_eval .poker-agent/demo
~~~

Open the [example review](benchmarks/river/run-2026-11-14/agent/mixed-range/report.md) and the [DeepSeek comparison](benchmarks/river/run-2026-11-14/README.md). The offline demo uses scripted model responses to exercise CoreCoder's tool loop. It generates seven checked cases, including a report and trace under `.poker-agent/demo/offline/mixed-range/`. Each evaluation run takes a new output directory. The Ubuntu CI run publishes the reports, traces, and checks as the `poker-review` artifact.

~~~sh
.venv/bin/python -m scripts.poker_query benchmarks/river/decisions.phhs --save-to .poker-agent/review.sqlite3
.venv/bin/python -m scripts.poker_review .poker-agent/review.sqlite3 --hand 1 --range 'KcKd 9c9d' --output .poker-agent/review
~~~

The selector accepts a hand number or the full decision ID. The review connects to SQLite in read-only mode. Its tools receive the selected decision's public board, acting player's cards, pot and call cost. The tool evidence and matched call ID appear in `report.md`. The `trace.json` file contains request messages, tool arguments, results, timings and model usage. Reproduce the tool and data checks with `python -m scripts.check_poker_review`.

Set `DEEPSEEK_API_KEY` in the local environment and add `--live` to the review command to use DeepSeek Flash. Evaluation supports `--mode compare` and repeated `--task` arguments to select the cases.

## Generate and inspect hand histories

Play a fixed hand or a scripted two-hand match, save it in Poker Hand History (PHH) format, and replay it to recover decisions and final stacks. Both players start with 100 chips, or 50 big blinds at 1/2. With the project environment above, run:

```powershell
.\.venv\Scripts\python.exe scripts/poker_demo.py .poker-agent/first-hand.phh
```

On Linux/macOS, use `.venv/bin/python`. Give each run a new output path.

The demo checks the original hand and the replay against a known result: Hero faces a call of 12 into a pot of 36, and the final stacks are 124 for Hero and 76 for the opponent. The command prints the river decision and final stacks as JSON.

The match command writes both hands to one `.phhs` file.

```powershell
.\.venv\Scripts\python.exe scripts/poker_demo.py --match .poker-agent/two-hands.phhs
```

| Hand | Button | Starting stacks (Hero / opponent) | Final stacks (Hero / opponent) |
| --- | --- | --- | --- |
| 1 | Hero | 100 / 100 | 124 / 76 |
| 2 | Opponent | 124 / 76 | 200 / 0 |

The replay prints a flop and river decision for each hand. Each decision contains the public cards at that point and the acting player's hole cards. The match ends when the opponent reaches zero chips.

Read an existing `.phh` or `.phhs` file to index its recorded decisions.

```powershell
.\.venv\Scripts\python.exe -m scripts.poker_import .poker-agent/two-hands.phhs
```

The JSON uses the SHA-256 of the file contents as `source_id`. A `hand_id` adds the hand number, and a `decision_id` adds the PHH action number. Each decision includes the recorded action and a snapshot from before that action. The `players` mapping gives the player name for each PHH seat (`p1` or `p2`).

The query command loads the hand and decision records into an in-memory SQLite database and returns the decisions matching the requested street and action.

```powershell
.\.venv\Scripts\python.exe -m scripts.poker_query .poker-agent/two-hands.phhs --street river --action call
```

The two-hand example returns action 14 from each hand, with call amounts of 12 and 64.

Save the same hand histories to a SQLite file, query the file, then retrieve the first decision's snapshot by ID.

```powershell
$historyFile = '.poker-agent/two-hands.phhs'
$reviewDb = '.poker-agent/review.sqlite3'
.\.venv\Scripts\python.exe -m scripts.poker_query $historyFile --save-to $reviewDb
$riverCalls = .\.venv\Scripts\python.exe -m scripts.poker_query $reviewDb --street river --action call | ConvertFrom-Json
.\.venv\Scripts\python.exe -m scripts.poker_query $reviewDb --decision-id $riverCalls[0].decision_id
```

The import reports 2 hands and 18 decisions. The saved snapshot for the first call shows a pot of 36 and a call amount of 12. The file queries open SQLite in read-only mode. Reimporting the same hand history keeps one record per ID.

Calculate exact river equity and call EV for the saved decision with an equal-weight opponent range:

```powershell
.\.venv\Scripts\python.exe -m scripts.poker_equity $reviewDb $riverCalls[0].decision_id 'KcKd 9c9d'
```

The first decision has two compatible combinations. The player wins against one and loses against the other, for equity of `1/2` and call EV of `12` chips. The calculation uses a heads-up, rake-free pot. Each compatible combination has equal weight and ties split the pot. Run the save command above to populate the uncalled amount in databases created before river analysis.

Run the import, query, and saved snapshot checks with `python -m scripts.check_poker_import` in the project environment.

The demo uses [PokerKit's PHH reader](https://pokerkit.readthedocs.io/en/stable/notation.html). The project retains the original [CoreCoder history and documentation](https://github.com/he-yufeng/CoreCoder/tree/bd64cfe7ad2789fa0ab1b3a689ad160567b5cdb0) and [MIT license](LICENSE).
