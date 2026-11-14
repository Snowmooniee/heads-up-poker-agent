# Natural-language river lookup evaluation

Dataset `lookup-v1`.

## heldout

| Mode | Exact ID | Next action | Clarification | Invented IDs | Joint lookup | All trials | EV | Explicit EV | Requests | Median s | Est. USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| keyword | 4/6 | 16/18 | 3/5 | 0 | 14/18 | 14/18 | 4/5 | 2/2 | 0 | 0.0022 | 0.000000 |
| direct | 10/18 | 38/54 | 8/15 | 0 | 36/54 | 8/18 | 5/15 | 5/6 | 216 | 3.9397 | 0.086574 |
| agent | 17/18 | 40/54 | 6/15 | 0 | 38/54 | 8/18 | 12/15 | 6/6 | 113 | 2.035 | 0.039603 |

| Mode | Clear | Ambiguous | No match | Out of scope |
| --- | ---: | ---: | ---: | ---: |
| keyword | 4/6 | 3/5 | 4/4 | 3/3 |
| direct | 10/18 | 8/15 | 11/12 | 7/9 |
| agent | 17/18 | 6/15 | 8/12 | 7/9 |

## dev

| Mode | Exact ID | Next action | Clarification | Invented IDs | Joint lookup | All trials | EV | Explicit EV | Requests | Median s | Est. USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| keyword | 4/4 | 9/10 | 2/3 | 0 | 9/10 | 9/10 | 4/4 | 2/2 | 0 | 0.0088 | 0.000000 |
| direct | 11/12 | 25/30 | 6/9 | 1 | 24/30 | 6/10 | 4/12 | 1/6 | 120 | 4.3549 | 0.046095 |
| agent | 9/12 | 20/30 | 4/9 | 0 | 20/30 | 3/10 | 8/12 | 4/6 | 65 | 1.7945 | 0.022385 |

| Mode | Clear | Ambiguous | No match | Out of scope |
| --- | ---: | ---: | ---: | ---: |
| keyword | 4/4 | 2/3 | 2/2 | 1/1 |
| direct | 11/12 | 6/9 | 5/6 | 2/3 |
| agent | 9/12 | 4/9 | 5/6 | 2/3 |

## Trials

| Split | Mode | Task | Trial | Check | Trace |
| --- | --- | --- | ---: | --- | --- |
| dev | keyword | d01-mixed-ev | 1 | Pass | [Trace](keyword/d01-mixed-ev/trial-1.json) |
| dev | direct | d01-mixed-ev | 1 | ev | [Trace](direct/d01-mixed-ev/trial-1.json) |
| dev | direct | d01-mixed-ev | 2 | ev | [Trace](direct/d01-mixed-ev/trial-2.json) |
| dev | direct | d01-mixed-ev | 3 | ev | [Trace](direct/d01-mixed-ev/trial-3.json) |
| dev | agent | d01-mixed-ev | 1 | Pass | [Trace](agent/d01-mixed-ev/trial-1.json) |
| dev | agent | d01-mixed-ev | 2 | response_error, next_action, decision_id, ev | [Trace](agent/d01-mixed-ev/trial-2.json) |
| dev | agent | d01-mixed-ev | 3 | Pass | [Trace](agent/d01-mixed-ev/trial-3.json) |
| dev | keyword | d02-negative-ev | 1 | Pass | [Trace](keyword/d02-negative-ev/trial-1.json) |
| dev | direct | d02-negative-ev | 1 | Pass | [Trace](direct/d02-negative-ev/trial-1.json) |
| dev | direct | d02-negative-ev | 2 | ev | [Trace](direct/d02-negative-ev/trial-2.json) |
| dev | direct | d02-negative-ev | 3 | ev | [Trace](direct/d02-negative-ev/trial-3.json) |
| dev | agent | d02-negative-ev | 1 | Pass | [Trace](agent/d02-negative-ev/trial-1.json) |
| dev | agent | d02-negative-ev | 2 | ev | [Trace](agent/d02-negative-ev/trial-2.json) |
| dev | agent | d02-negative-ev | 3 | Pass | [Trace](agent/d02-negative-ev/trial-3.json) |
| dev | keyword | d03-unique-amount | 1 | Pass | [Trace](keyword/d03-unique-amount/trial-1.json) |
| dev | direct | d03-unique-amount | 1 | ev | [Trace](direct/d03-unique-amount/trial-1.json) |
| dev | direct | d03-unique-amount | 2 | Pass | [Trace](direct/d03-unique-amount/trial-2.json) |
| dev | direct | d03-unique-amount | 3 | response_error, next_action, decision_id, ev | [Trace](direct/d03-unique-amount/trial-3.json) |
| dev | agent | d03-unique-amount | 1 | Pass | [Trace](agent/d03-unique-amount/trial-1.json) |
| dev | agent | d03-unique-amount | 2 | response_error, next_action, decision_id, ev | [Trace](agent/d03-unique-amount/trial-2.json) |
| dev | agent | d03-unique-amount | 3 | Pass | [Trace](agent/d03-unique-amount/trial-3.json) |
| dev | keyword | d04-board-plays | 1 | Pass | [Trace](keyword/d04-board-plays/trial-1.json) |
| dev | direct | d04-board-plays | 1 | Pass | [Trace](direct/d04-board-plays/trial-1.json) |
| dev | direct | d04-board-plays | 2 | Pass | [Trace](direct/d04-board-plays/trial-2.json) |
| dev | direct | d04-board-plays | 3 | ev | [Trace](direct/d04-board-plays/trial-3.json) |
| dev | agent | d04-board-plays | 1 | Pass | [Trace](agent/d04-board-plays/trial-1.json) |
| dev | agent | d04-board-plays | 2 | response_error, next_action, decision_id, ev | [Trace](agent/d04-board-plays/trial-2.json) |
| dev | agent | d04-board-plays | 3 | Pass | [Trace](agent/d04-board-plays/trial-3.json) |
| dev | keyword | d05-same-cost | 1 | Pass | [Trace](keyword/d05-same-cost/trial-1.json) |
| dev | direct | d05-same-cost | 1 | next_action, unexpected_selection | [Trace](direct/d05-same-cost/trial-1.json) |
| dev | direct | d05-same-cost | 2 | next_action | [Trace](direct/d05-same-cost/trial-2.json) |
| dev | direct | d05-same-cost | 3 | next_action | [Trace](direct/d05-same-cost/trial-3.json) |
| dev | agent | d05-same-cost | 1 | Pass | [Trace](agent/d05-same-cost/trial-1.json) |
| dev | agent | d05-same-cost | 2 | Pass | [Trace](agent/d05-same-cost/trial-2.json) |
| dev | agent | d05-same-cost | 3 | Pass | [Trace](agent/d05-same-cost/trial-3.json) |
| dev | keyword | d06-missing-hand | 1 | Pass | [Trace](keyword/d06-missing-hand/trial-1.json) |
| dev | direct | d06-missing-hand | 1 | Pass | [Trace](direct/d06-missing-hand/trial-1.json) |
| dev | direct | d06-missing-hand | 2 | Pass | [Trace](direct/d06-missing-hand/trial-2.json) |
| dev | direct | d06-missing-hand | 3 | Pass | [Trace](direct/d06-missing-hand/trial-3.json) |
| dev | agent | d06-missing-hand | 1 | Pass | [Trace](agent/d06-missing-hand/trial-1.json) |
| dev | agent | d06-missing-hand | 2 | response_error, next_action, unexpected_selection | [Trace](agent/d06-missing-hand/trial-2.json) |
| dev | agent | d06-missing-hand | 3 | next_action | [Trace](agent/d06-missing-hand/trial-3.json) |
| dev | keyword | d07-same-river | 1 | next_action | [Trace](keyword/d07-same-river/trial-1.json) |
| dev | direct | d07-same-river | 1 | Pass | [Trace](direct/d07-same-river/trial-1.json) |
| dev | direct | d07-same-river | 2 | Pass | [Trace](direct/d07-same-river/trial-2.json) |
| dev | direct | d07-same-river | 3 | Pass | [Trace](direct/d07-same-river/trial-3.json) |
| dev | agent | d07-same-river | 1 | next_action | [Trace](agent/d07-same-river/trial-1.json) |
| dev | agent | d07-same-river | 2 | next_action | [Trace](agent/d07-same-river/trial-2.json) |
| dev | agent | d07-same-river | 3 | next_action | [Trace](agent/d07-same-river/trial-3.json) |
| dev | keyword | d08-unknown-hand | 1 | Pass | [Trace](keyword/d08-unknown-hand/trial-1.json) |
| dev | direct | d08-unknown-hand | 1 | Pass | [Trace](direct/d08-unknown-hand/trial-1.json) |
| dev | direct | d08-unknown-hand | 2 | invented_id | [Trace](direct/d08-unknown-hand/trial-2.json) |
| dev | direct | d08-unknown-hand | 3 | Pass | [Trace](direct/d08-unknown-hand/trial-3.json) |
| dev | agent | d08-unknown-hand | 1 | Pass | [Trace](agent/d08-unknown-hand/trial-1.json) |
| dev | agent | d08-unknown-hand | 2 | Pass | [Trace](agent/d08-unknown-hand/trial-2.json) |
| dev | agent | d08-unknown-hand | 3 | Pass | [Trace](agent/d08-unknown-hand/trial-3.json) |
| dev | keyword | d09-unknown-amount | 1 | Pass | [Trace](keyword/d09-unknown-amount/trial-1.json) |
| dev | direct | d09-unknown-amount | 1 | Pass | [Trace](direct/d09-unknown-amount/trial-1.json) |
| dev | direct | d09-unknown-amount | 2 | Pass | [Trace](direct/d09-unknown-amount/trial-2.json) |
| dev | direct | d09-unknown-amount | 3 | Pass | [Trace](direct/d09-unknown-amount/trial-3.json) |
| dev | agent | d09-unknown-amount | 1 | Pass | [Trace](agent/d09-unknown-amount/trial-1.json) |
| dev | agent | d09-unknown-amount | 2 | response_error, next_action, unexpected_selection | [Trace](agent/d09-unknown-amount/trial-2.json) |
| dev | agent | d09-unknown-amount | 3 | Pass | [Trace](agent/d09-unknown-amount/trial-3.json) |
| dev | keyword | d10-invitation | 1 | Pass | [Trace](keyword/d10-invitation/trial-1.json) |
| dev | direct | d10-invitation | 1 | response_error, next_action, unexpected_selection | [Trace](direct/d10-invitation/trial-1.json) |
| dev | direct | d10-invitation | 2 | Pass | [Trace](direct/d10-invitation/trial-2.json) |
| dev | direct | d10-invitation | 3 | Pass | [Trace](direct/d10-invitation/trial-3.json) |
| dev | agent | d10-invitation | 1 | Pass | [Trace](agent/d10-invitation/trial-1.json) |
| dev | agent | d10-invitation | 2 | Pass | [Trace](agent/d10-invitation/trial-2.json) |
| dev | agent | d10-invitation | 3 | response_error, next_action, unexpected_selection | [Trace](agent/d10-invitation/trial-3.json) |
| heldout | keyword | h01-explicit-win | 1 | Pass | [Trace](keyword/h01-explicit-win/trial-1.json) |
| heldout | direct | h01-explicit-win | 1 | Pass | [Trace](direct/h01-explicit-win/trial-1.json) |
| heldout | direct | h01-explicit-win | 2 | ev | [Trace](direct/h01-explicit-win/trial-2.json) |
| heldout | direct | h01-explicit-win | 3 | Pass | [Trace](direct/h01-explicit-win/trial-3.json) |
| heldout | agent | h01-explicit-win | 1 | Pass | [Trace](agent/h01-explicit-win/trial-1.json) |
| heldout | agent | h01-explicit-win | 2 | Pass | [Trace](agent/h01-explicit-win/trial-2.json) |
| heldout | agent | h01-explicit-win | 3 | Pass | [Trace](agent/h01-explicit-win/trial-3.json) |
| heldout | keyword | h02-numbered-loss | 1 | Pass | [Trace](keyword/h02-numbered-loss/trial-1.json) |
| heldout | direct | h02-numbered-loss | 1 | Pass | [Trace](direct/h02-numbered-loss/trial-1.json) |
| heldout | direct | h02-numbered-loss | 2 | Pass | [Trace](direct/h02-numbered-loss/trial-2.json) |
| heldout | direct | h02-numbered-loss | 3 | Pass | [Trace](direct/h02-numbered-loss/trial-3.json) |
| heldout | agent | h02-numbered-loss | 1 | Pass | [Trace](agent/h02-numbered-loss/trial-1.json) |
| heldout | agent | h02-numbered-loss | 2 | Pass | [Trace](agent/h02-numbered-loss/trial-2.json) |
| heldout | agent | h02-numbered-loss | 3 | Pass | [Trace](agent/h02-numbered-loss/trial-3.json) |
| heldout | keyword | h03-amount-in-words | 1 | next_action, decision_id, ev | [Trace](keyword/h03-amount-in-words/trial-1.json) |
| heldout | direct | h03-amount-in-words | 1 | ev | [Trace](direct/h03-amount-in-words/trial-1.json) |
| heldout | direct | h03-amount-in-words | 2 | ev | [Trace](direct/h03-amount-in-words/trial-2.json) |
| heldout | direct | h03-amount-in-words | 3 | response_error, next_action, decision_id, ev | [Trace](direct/h03-amount-in-words/trial-3.json) |
| heldout | agent | h03-amount-in-words | 1 | ev | [Trace](agent/h03-amount-in-words/trial-1.json) |
| heldout | agent | h03-amount-in-words | 2 | ev | [Trace](agent/h03-amount-in-words/trial-2.json) |
| heldout | agent | h03-amount-in-words | 3 | response_error, next_action, decision_id, ev | [Trace](agent/h03-amount-in-words/trial-3.json) |
| heldout | keyword | h04-card-and-amount | 1 | Pass | [Trace](keyword/h04-card-and-amount/trial-1.json) |
| heldout | direct | h04-card-and-amount | 1 | next_action, decision_id, ev | [Trace](direct/h04-card-and-amount/trial-1.json) |
| heldout | direct | h04-card-and-amount | 2 | response_error, next_action, decision_id, ev | [Trace](direct/h04-card-and-amount/trial-2.json) |
| heldout | direct | h04-card-and-amount | 3 | decision_id, ev | [Trace](direct/h04-card-and-amount/trial-3.json) |
| heldout | agent | h04-card-and-amount | 1 | Pass | [Trace](agent/h04-card-and-amount/trial-1.json) |
| heldout | agent | h04-card-and-amount | 2 | Pass | [Trace](agent/h04-card-and-amount/trial-2.json) |
| heldout | agent | h04-card-and-amount | 3 | Pass | [Trace](agent/h04-card-and-amount/trial-3.json) |
| heldout | keyword | h05-ordinal | 1 | next_action, decision_id | [Trace](keyword/h05-ordinal/trial-1.json) |
| heldout | direct | h05-ordinal | 1 | response_error, next_action, decision_id | [Trace](direct/h05-ordinal/trial-1.json) |
| heldout | direct | h05-ordinal | 2 | Pass | [Trace](direct/h05-ordinal/trial-2.json) |
| heldout | direct | h05-ordinal | 3 | Pass | [Trace](direct/h05-ordinal/trial-3.json) |
| heldout | agent | h05-ordinal | 1 | Pass | [Trace](agent/h05-ordinal/trial-1.json) |
| heldout | agent | h05-ordinal | 2 | Pass | [Trace](agent/h05-ordinal/trial-2.json) |
| heldout | agent | h05-ordinal | 3 | Pass | [Trace](agent/h05-ordinal/trial-3.json) |
| heldout | keyword | h06-river-paraphrase | 1 | Pass | [Trace](keyword/h06-river-paraphrase/trial-1.json) |
| heldout | direct | h06-river-paraphrase | 1 | next_action, decision_id, ev | [Trace](direct/h06-river-paraphrase/trial-1.json) |
| heldout | direct | h06-river-paraphrase | 2 | next_action, decision_id, ev | [Trace](direct/h06-river-paraphrase/trial-2.json) |
| heldout | direct | h06-river-paraphrase | 3 | next_action, decision_id, ev | [Trace](direct/h06-river-paraphrase/trial-3.json) |
| heldout | agent | h06-river-paraphrase | 1 | Pass | [Trace](agent/h06-river-paraphrase/trial-1.json) |
| heldout | agent | h06-river-paraphrase | 2 | Pass | [Trace](agent/h06-river-paraphrase/trial-2.json) |
| heldout | agent | h06-river-paraphrase | 3 | Pass | [Trace](agent/h06-river-paraphrase/trial-3.json) |
| heldout | keyword | h07-same-sixteen | 1 | Pass | [Trace](keyword/h07-same-sixteen/trial-1.json) |
| heldout | direct | h07-same-sixteen | 1 | Pass | [Trace](direct/h07-same-sixteen/trial-1.json) |
| heldout | direct | h07-same-sixteen | 2 | Pass | [Trace](direct/h07-same-sixteen/trial-2.json) |
| heldout | direct | h07-same-sixteen | 3 | next_action, unexpected_selection | [Trace](direct/h07-same-sixteen/trial-3.json) |
| heldout | agent | h07-same-sixteen | 1 | clarification | [Trace](agent/h07-same-sixteen/trial-1.json) |
| heldout | agent | h07-same-sixteen | 2 | Pass | [Trace](agent/h07-same-sixteen/trial-2.json) |
| heldout | agent | h07-same-sixteen | 3 | clarification | [Trace](agent/h07-same-sixteen/trial-3.json) |
| heldout | keyword | h08-same-king | 1 | Pass | [Trace](keyword/h08-same-king/trial-1.json) |
| heldout | direct | h08-same-king | 1 | Pass | [Trace](direct/h08-same-king/trial-1.json) |
| heldout | direct | h08-same-king | 2 | next_action, unexpected_selection | [Trace](direct/h08-same-king/trial-2.json) |
| heldout | direct | h08-same-king | 3 | next_action, unexpected_selection | [Trace](direct/h08-same-king/trial-3.json) |
| heldout | agent | h08-same-king | 1 | Pass | [Trace](agent/h08-same-king/trial-1.json) |
| heldout | agent | h08-same-king | 2 | Pass | [Trace](agent/h08-same-king/trial-2.json) |
| heldout | agent | h08-same-king | 3 | Pass | [Trace](agent/h08-same-king/trial-3.json) |
| heldout | keyword | h09-same-eight | 1 | clarification | [Trace](keyword/h09-same-eight/trial-1.json) |
| heldout | direct | h09-same-eight | 1 | next_action | [Trace](direct/h09-same-eight/trial-1.json) |
| heldout | direct | h09-same-eight | 2 | next_action | [Trace](direct/h09-same-eight/trial-2.json) |
| heldout | direct | h09-same-eight | 3 | next_action, unexpected_selection | [Trace](direct/h09-same-eight/trial-3.json) |
| heldout | agent | h09-same-eight | 1 | Pass | [Trace](agent/h09-same-eight/trial-1.json) |
| heldout | agent | h09-same-eight | 2 | Pass | [Trace](agent/h09-same-eight/trial-2.json) |
| heldout | agent | h09-same-eight | 3 | response_error, next_action, unexpected_selection | [Trace](agent/h09-same-eight/trial-3.json) |
| heldout | keyword | h10-no-selector | 1 | Pass | [Trace](keyword/h10-no-selector/trial-1.json) |
| heldout | direct | h10-no-selector | 1 | Pass | [Trace](direct/h10-no-selector/trial-1.json) |
| heldout | direct | h10-no-selector | 2 | Pass | [Trace](direct/h10-no-selector/trial-2.json) |
| heldout | direct | h10-no-selector | 3 | Pass | [Trace](direct/h10-no-selector/trial-3.json) |
| heldout | agent | h10-no-selector | 1 | response_error, next_action, unexpected_selection | [Trace](agent/h10-no-selector/trial-1.json) |
| heldout | agent | h10-no-selector | 2 | response_error, next_action, unexpected_selection | [Trace](agent/h10-no-selector/trial-2.json) |
| heldout | agent | h10-no-selector | 3 | response_error, next_action, unexpected_selection | [Trace](agent/h10-no-selector/trial-3.json) |
| heldout | keyword | h11-negated-cost | 1 | clarification | [Trace](keyword/h11-negated-cost/trial-1.json) |
| heldout | direct | h11-negated-cost | 1 | clarification | [Trace](direct/h11-negated-cost/trial-1.json) |
| heldout | direct | h11-negated-cost | 2 | Pass | [Trace](direct/h11-negated-cost/trial-2.json) |
| heldout | direct | h11-negated-cost | 3 | Pass | [Trace](direct/h11-negated-cost/trial-3.json) |
| heldout | agent | h11-negated-cost | 1 | next_action, unexpected_selection | [Trace](agent/h11-negated-cost/trial-1.json) |
| heldout | agent | h11-negated-cost | 2 | next_action, unexpected_selection | [Trace](agent/h11-negated-cost/trial-2.json) |
| heldout | agent | h11-negated-cost | 3 | next_action | [Trace](agent/h11-negated-cost/trial-3.json) |
| heldout | keyword | h12-opponent-only | 1 | Pass | [Trace](keyword/h12-opponent-only/trial-1.json) |
| heldout | direct | h12-opponent-only | 1 | Pass | [Trace](direct/h12-opponent-only/trial-1.json) |
| heldout | direct | h12-opponent-only | 2 | Pass | [Trace](direct/h12-opponent-only/trial-2.json) |
| heldout | direct | h12-opponent-only | 3 | Pass | [Trace](direct/h12-opponent-only/trial-3.json) |
| heldout | agent | h12-opponent-only | 1 | Pass | [Trace](agent/h12-opponent-only/trial-1.json) |
| heldout | agent | h12-opponent-only | 2 | response_error, next_action, unexpected_selection | [Trace](agent/h12-opponent-only/trial-2.json) |
| heldout | agent | h12-opponent-only | 3 | response_error, next_action, unexpected_selection | [Trace](agent/h12-opponent-only/trial-3.json) |
| heldout | keyword | h13-absent-hand | 1 | Pass | [Trace](keyword/h13-absent-hand/trial-1.json) |
| heldout | direct | h13-absent-hand | 1 | Pass | [Trace](direct/h13-absent-hand/trial-1.json) |
| heldout | direct | h13-absent-hand | 2 | Pass | [Trace](direct/h13-absent-hand/trial-2.json) |
| heldout | direct | h13-absent-hand | 3 | Pass | [Trace](direct/h13-absent-hand/trial-3.json) |
| heldout | agent | h13-absent-hand | 1 | Pass | [Trace](agent/h13-absent-hand/trial-1.json) |
| heldout | agent | h13-absent-hand | 2 | Pass | [Trace](agent/h13-absent-hand/trial-2.json) |
| heldout | agent | h13-absent-hand | 3 | Pass | [Trace](agent/h13-absent-hand/trial-3.json) |
| heldout | keyword | h14-conflicting-filters | 1 | Pass | [Trace](keyword/h14-conflicting-filters/trial-1.json) |
| heldout | direct | h14-conflicting-filters | 1 | Pass | [Trace](direct/h14-conflicting-filters/trial-1.json) |
| heldout | direct | h14-conflicting-filters | 2 | next_action, unexpected_selection | [Trace](direct/h14-conflicting-filters/trial-2.json) |
| heldout | direct | h14-conflicting-filters | 3 | Pass | [Trace](direct/h14-conflicting-filters/trial-3.json) |
| heldout | agent | h14-conflicting-filters | 1 | response_error, next_action, unexpected_selection | [Trace](agent/h14-conflicting-filters/trial-1.json) |
| heldout | agent | h14-conflicting-filters | 2 | Pass | [Trace](agent/h14-conflicting-filters/trial-2.json) |
| heldout | agent | h14-conflicting-filters | 3 | Pass | [Trace](agent/h14-conflicting-filters/trial-3.json) |
| heldout | keyword | h15-missing-river-card | 1 | Pass | [Trace](keyword/h15-missing-river-card/trial-1.json) |
| heldout | direct | h15-missing-river-card | 1 | Pass | [Trace](direct/h15-missing-river-card/trial-1.json) |
| heldout | direct | h15-missing-river-card | 2 | Pass | [Trace](direct/h15-missing-river-card/trial-2.json) |
| heldout | direct | h15-missing-river-card | 3 | Pass | [Trace](direct/h15-missing-river-card/trial-3.json) |
| heldout | agent | h15-missing-river-card | 1 | response_error, next_action, unexpected_selection | [Trace](agent/h15-missing-river-card/trial-1.json) |
| heldout | agent | h15-missing-river-card | 2 | Pass | [Trace](agent/h15-missing-river-card/trial-2.json) |
| heldout | agent | h15-missing-river-card | 3 | Pass | [Trace](agent/h15-missing-river-card/trial-3.json) |
| heldout | keyword | h16-rewrite | 1 | Pass | [Trace](keyword/h16-rewrite/trial-1.json) |
| heldout | direct | h16-rewrite | 1 | Pass | [Trace](direct/h16-rewrite/trial-1.json) |
| heldout | direct | h16-rewrite | 2 | Pass | [Trace](direct/h16-rewrite/trial-2.json) |
| heldout | direct | h16-rewrite | 3 | Pass | [Trace](direct/h16-rewrite/trial-3.json) |
| heldout | agent | h16-rewrite | 1 | Pass | [Trace](agent/h16-rewrite/trial-1.json) |
| heldout | agent | h16-rewrite | 2 | Pass | [Trace](agent/h16-rewrite/trial-2.json) |
| heldout | agent | h16-rewrite | 3 | response_error, next_action, unexpected_selection | [Trace](agent/h16-rewrite/trial-3.json) |
| heldout | keyword | h17-turn-only | 1 | Pass | [Trace](keyword/h17-turn-only/trial-1.json) |
| heldout | direct | h17-turn-only | 1 | next_action | [Trace](direct/h17-turn-only/trial-1.json) |
| heldout | direct | h17-turn-only | 2 | Pass | [Trace](direct/h17-turn-only/trial-2.json) |
| heldout | direct | h17-turn-only | 3 | next_action | [Trace](direct/h17-turn-only/trial-3.json) |
| heldout | agent | h17-turn-only | 1 | Pass | [Trace](agent/h17-turn-only/trial-1.json) |
| heldout | agent | h17-turn-only | 2 | Pass | [Trace](agent/h17-turn-only/trial-2.json) |
| heldout | agent | h17-turn-only | 3 | Pass | [Trace](agent/h17-turn-only/trial-3.json) |
| heldout | keyword | h18-unrelated | 1 | Pass | [Trace](keyword/h18-unrelated/trial-1.json) |
| heldout | direct | h18-unrelated | 1 | Pass | [Trace](direct/h18-unrelated/trial-1.json) |
| heldout | direct | h18-unrelated | 2 | Pass | [Trace](direct/h18-unrelated/trial-2.json) |
| heldout | direct | h18-unrelated | 3 | Pass | [Trace](direct/h18-unrelated/trial-3.json) |
| heldout | agent | h18-unrelated | 1 | Pass | [Trace](agent/h18-unrelated/trial-1.json) |
| heldout | agent | h18-unrelated | 2 | response_error, next_action, unexpected_selection | [Trace](agent/h18-unrelated/trial-2.json) |
| heldout | agent | h18-unrelated | 3 | Pass | [Trace](agent/h18-unrelated/trial-3.json) |
