# Heads-up Poker Agent

Play a fixed heads-up no-limit Hold'em hand or a scripted two-hand match, save the hand histories in Poker Hand History (PHH) format, and replay them to recover decisions and final stacks. Both players start with 100 chips, or 50 big blinds at 1/2.

Run from the repository root with Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pokerkit==0.7.7
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

The demo uses [PokerKit's PHH reader](https://pokerkit.readthedocs.io/en/stable/notation.html). The project retains the original [CoreCoder history and documentation](https://github.com/he-yufeng/CoreCoder/tree/bd64cfe7ad2789fa0ab1b3a689ad160567b5cdb0) and [MIT license](LICENSE).
