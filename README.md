# Heads-up Poker Agent

Play a fixed heads-up no-limit Hold'em hand, save it in Poker Hand History (PHH) format, and replay it to recover the river decision and final stacks. The example starts both players at 100 chips, or 50 big blinds at 1/2.

Run from the repository root with Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pokerkit==0.7.7
.\.venv\Scripts\python.exe scripts/poker_demo.py .poker-agent/first-hand.phh
```

On Linux/macOS, use `.venv/bin/python`. Give each run a new output path.

The demo checks the original hand and the replay against a known result: Hero faces a call of 12 into a pot of 36, and the final stacks are 124 for Hero and 76 for the opponent. The command prints the river decision and final stacks as JSON.

The demo uses [PokerKit's PHH reader](https://pokerkit.readthedocs.io/en/stable/notation.html). The project retains the original [CoreCoder history and documentation](https://github.com/he-yufeng/CoreCoder/tree/bd64cfe7ad2789fa0ab1b3a689ad160567b5cdb0) and [MIT license](LICENSE).
