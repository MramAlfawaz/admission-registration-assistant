# Experiment 5: efficiency

Timing from `holdout_before.json`: its first run, with no model call cached, on a MacBook Pro (Intel Core i5, 8 GB RAM, CPU only, `qwen2.5:3b`). Cached reruns are not timed.

| responses | n | median (s) | p90 (s) |
|---|---|---|---|
| all | 40 | 32.4 | 42.88 |
| answered | 25 | 34.8 | 41.88 |
| non_answers | 15 | 1.8 | 41.81 |

**Baseline (current process): not available.** The Deanship's current response time to an inquiry could not be obtained, so no reduction is claimed. It is recorded as unknown, as the brief requires measuring rather than estimating.

## self-service rate
Correct answers given with no staff involvement, over all inquiries:

- `holdout_after.json`: 0.35
- `e2e_v2.json`: 0.53
