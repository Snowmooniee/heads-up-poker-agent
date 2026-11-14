# Three-way river lookup comparison

On November 14, 2026 we ran [lookup-v1](../v1.json) on Windows with Python 3.11 and SQLite. Each of the 28 requests ran once through the fixed keyword pipeline and three times each through direct DeepSeek Flash and the CoreCoder agent. Both model modes used non-thinking mode and the same four-request, 512-output-token-per-request ceiling. Direct mode saw the eligible catalog and made three revisions after its first draft. The agent looked up eligible decisions through SQLite and used the shared calculator when it chose to.

The run used [implementation adf043a](https://github.com/Snowmooniee/heads-up-poker-agent/commit/adf043ad669bfa255d58d5acf392afcd6de5da5d). Before publishing the table, we replayed the grader over the original traces and corrected five false negatives in the clarification rubric. The dataset, model outputs and tool results stayed fixed. [Original scores](original-evaluation.json) · [Regraded scores](evaluation.json) · [Trial index](evaluation.md)

## Held-out results

| System | Exact decision ID | Correct next action | Valid clarification | Invented IDs | Joint lookup | All trials passed | End-to-end EV | Explicit hand EV | Requests | Median trial | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Keyword pipeline | 4/6 | 16/18 | 3/5 | 0 | 14/18 | 14/18 | 4/5 | 2/2 | 0 | 0.0022 s | $0 |
| DeepSeek direct | 10/18 | 38/54 | 8/15 | 0 | 36/54 | 8/18 | 5/15 | 5/6 | 216 | 3.940 s | $0.08657 |
| CoreCoder agent | 17/18 | 40/54 | 6/15 | 0 | 38/54 | 8/18 | 12/15 | 6/6 | 113 | 2.035 s | $0.03960 |

Joint lookup requires the correct ID and next action, a valid clarification where applicable, and zero invented IDs. EV is scored separately. “All trials passed” counts cases where every run passed joint lookup, with one run for the deterministic pipeline and three for each model. Full-run estimates use peak cache-miss prices for all tokens. Total recorded use was **514 requests and US$0.1946562 estimated**. Across both splits, direct mode produced one invented ID in a draft; the agent produced zero. [Raw draft and subsequent revisions](direct/d08-unknown-hand/trial-2.json) · [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/)

| Joint lookup by request type | Clear | Ambiguous | No match | Out of scope |
| --- | ---: | ---: | ---: | ---: |
| Keyword pipeline | 4/6 | 3/5 | 4/4 | 3/3 |
| DeepSeek direct | 10/18 | 8/15 | 11/12 | 7/9 |
| CoreCoder agent | 17/18 | 6/15 | 8/12 | 7/9 |

The fixed pipeline had the highest joint lookup rate on these 18 requests and calculated both explicitly numbered EV cases exactly. The agent had the highest exact-ID rate on clear requests and the highest EV rate. It handled phrases such as “matched eight on the last betting round,” where the keyword parser lost the amount, but its clarification quality lagged both alternatives. Both model approaches passed all three trials on eight held-out cases. [Agent recognizing “matched eight”](agent/h09-same-eight/trial-1.json) · [Keyword trace for the same request](keyword/h09-same-eight/trial-1.json)

## Error analysis

| Case | Expected | Observed and cause |
| --- | --- | --- |
| **Decimal-rank river card** (`d07-same-river`) | Ask which of hands 1 or 3 ended on `3s`. | All three agent trials asked the tool to look up `3s`, got an empty list, and returned `no_match`. The shared lookup used Python's `str.title()`, which turns `3s` into `3S`; PokerKit stores `3s`. The keyword pipeline failed the same way. Card normalization now uppercases the rank and lowercases the suit. The offline check follows the original tool argument through CoreCoder and verifies both returned hands. [Recorded failure](agent/d07-same-river/trial-1.json) · [Regression check](../../../scripts/check_poker_lookup.py) |
| **Calculating before the user chooses** (`h07-same-sixteen`) | Ask the user to choose hand 2 or 3 before running the calculator. | The agent found both correct IDs all three times. On trials 1 and 3 it calculated both EVs before asking, which failed clarification. Trial 2 looked up the same two hands and asked directly. This is a tool-use decision error even though the two EV calculations were correct. [Early calculations](agent/h07-same-sixteen/trial-1.json) · [Correct clarification](agent/h07-same-sixteen/trial-2.json) |
| **Negative constraint with multiple matches** (`h11-negated-cost`) | Ask about hands 2 and 3, both below 20 chips and different from eight. | The keyword parser treated “eight-chip” as a positive filter and offered hands 1 and 6. One agent trial got all five eligible calls, selected one 16-chip call, and missed the other. Direct mode asked about the correct pair on two trials. [Keyword query](keyword/h11-negated-cost/trial-1.json) · [Agent query and selection](agent/h11-negated-cost/trial-1.json) · [Correct direct answer](direct/h11-negated-cost/trial-2.json) |
| **Exact range treated as invalid** (`h03-amount-in-words`) | Locate hand 5 and calculate −20 against the single combination `8c8d`. | Two agent trials selected hand 5 but treated one explicit combination as an invalid range. The third supplied unsupported EV without a calculator call. Direct mode also got the EV wrong. On `Jd 6h 4c 9s 2h`, AK loses to a pair of eights. [Agent trace](agent/h03-amount-in-words/trial-1.json) · [Direct arithmetic](direct/h03-amount-in-words/trial-1.json) |
| **Correct query, malformed final schema** (`h12-opponent-only`) | Return `no_match` because only the opponent called in hand 4. | The agent correctly queried hand 4 and saw an empty list. Two final responses put “no_match” in `type` and left the required `action` null. The response parser rejected them. Eleven held-out agent trials had response errors, including invalid schema and unsupported EV. [Trace showing raw response](agent/h12-opponent-only/trial-2.json) |

The clarification grader initially missed real questions that named a comma-separated list of valid hands or asked the user to supply “hand_no” or “hand number.” Offline regrading changed one agent development score and four direct scores, including two held-out scores. It left candidate sets, premature calculations, ID checks and EV checks intact. The table above measures the recorded run with the corrected rubric. The card-normalization fix was checked offline using the original selector.

The labels include hand-derived rationales and nine EV values cross-checked with the deterministic calculator. They were prepared for this project. The 18 held-out requests use six synthetic hands and characterize this workload.
