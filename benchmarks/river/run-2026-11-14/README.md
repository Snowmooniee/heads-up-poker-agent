# DeepSeek Flash river review comparison

On 2026-11-14, DeepSeek Flash ran five synthetic review tasks across four river decisions, once per mode. The agent selected its query and calculator calls through CoreCoder. The direct mode received the same candidate snapshot and range in its input. Both used non-thinking mode, the same 512-token output cap per request, and the same reference answers. The agent had a maximum of four requests per case. Direct mode used one request per case.

| Mode | Structured checks | Structured checks and explanation review | Tool calls | API requests | Input and output tokens | Median time | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CoreCoder agent | 5/5 | 3/5 | 10 | 15 | 12,364 + 1,584 | 3.313 s | $0.0056100 |
| Direct answer | 0/5 | 0/5 | 0 | 5 | 2,209 + 1,299 | 1.735 s | $0.0022215 |

The structured score requires the reference status, decision, equity, call EV and recommendation as applicable. The agent score also checks the observed tool sequence and calculation result. The explanation review looks for a factual or numerical error after the structured check passes.

| Task | Agent explanation review | Direct result |
| --- | --- | --- |
| Mixed range | One win and one loss, call EV +12. [Trace](agent/mixed-range/trace.json) | Reported +6 for 24 − 12. [Trace](direct/mixed-range/trace.json) |
| Board plays | Correct split-pot result, but described the board's royal flush as a straight. [Trace](agent/board-plays/trace.json) | Gave zero equity to a tie. [Trace](direct/board-plays/trace.json) |
| Short call | Correctly removed 66 unmatched chips and reported +34. [Trace](agent/short-call/trace.json) | Gave aces versus kings 50% equity on a finished board and inconsistent EV. [Trace](direct/short-call/trace.json) |
| Blocked break-even | Correct final EV of zero, but the explanation gave both 36 and 48 for the contested pot. [Trace](agent/blocked-break-even/trace.json) | Response at the 512-token cap contained incomplete JSON. [Trace](direct/blocked-break-even/trace.json) |
| Fully blocked | Asked for a range compatible with the visible cards. [Trace](agent/fully-blocked/trace.json) | Identified the blocked hand but returned a recommendation. [Trace](direct/fully-blocked/trace.json) |

The generated report presents the checked decision, equity, EV and tool evidence. The trace preserves the original model response. [Report rendered from the mixed range run](agent/mixed-range/report.md)

[Machine-readable results](evaluation.json) · [Cases and reference answers](../tasks.json) · [Pilot implementation](https://github.com/Snowmooniee/heads-up-poker-agent/commit/9e26b3abc266a81f12a09dbe055644f9f166a937) · [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/)
