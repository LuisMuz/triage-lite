# Eval results summary

One row per (prompt, model, split) run on `seed-v1`. Tuning rows guide prompt changes; the holdout row is run once (Session 2.5) and is the number quoted in the README. Full reports and per-item predictions are in the files next to this one.

## Tuning

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v1 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.726** [0.620-0.817] | 71.7% | 91.7% | 90.0% | 71.7% (100.0%) | 100.0% | 0.0% | $0.070 | 4482 / 5561 |
| classify/v1 (c10, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.658-0.827] | 74.4% | 91.7% | 90.6% | 74.4% (100.0%) | 100.0% | 0.0% | $0.071 | 4569 / 5767 |
| classify/v2 (c10, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.673-0.822] | 73.9% | 92.8% | 91.7% | 73.9% (100.0%) | 100.0% | 0.0% | $0.076 | 4964 / 5702 |
| **classify/v3 (c10, x3)** ✅ | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.746** [0.651-0.828] | 73.9% | 93.9% | 91.7% | 73.9% (100.0%) | 100.0% | 0.0% | $0.073 | 4614 / 5230 |
| classify/v4 (c10, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.668-0.823] | 75.0% | 90.6% | 89.4% | 75.4% (99.4%) | 100.0% | 0.0% | $0.075 | 4874 / 5349 |
| classify/v3 (c5, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.726** [0.628-0.805] | 70.6% | 91.1% | 88.9% | 72.6% (97.2%) | 91.9% | 2.8% | $0.105 | 2778 / 3192 |
| classify/v5 (c10, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.720** [0.627-0.795] | 72.2% | 95.6% | 89.4% | 72.2% (100.0%) | 94.4% | 0.0% | $0.070 | 3682 / 4010 |

`c` = incidents per call, `x` = repeats. The first row is a single run; the others pool 3 runs (v1's three runs alone ranged 0.716-0.810).

### Other Bedrock models (Converse API, same prompt `classify/v3`, TL-25)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 (c10, x3) | moonshotai.kimi-k2.5 | tuning | **0.748** [0.657-0.825] | 74.4% | 95.6% | 86.1% | 74.4% (100.0%) | 100.0% | 0.0% | $0.032 | 5988 / 10085 |
| classify/v3 (c10, x3) | amazon.nova-lite-v1:0 | tuning | **0.598** [0.498-0.684] | 58.9% | 92.2% | 81.7% | 58.9% (100.0%) | 100.0% | 0.0% | $0.003 | 5415 / 6991 |
| classify/v3 (c10, x3) | openai.gpt-oss-120b-1:0 | tuning | **0.630** [0.505-0.737] | 62.8% | 92.2% | 80.6% | 62.8% (100.0%) | 0.0% | 0.0% | $0.023 | 8036 / 10788 |
| classify/v3 (c10, x3) | deepseek.v3.2 | tuning | **0.635** [0.539-0.730] | 62.8% | 90.0% | 86.1% | 62.8% (100.0%) | 94.4% | 0.0% | $0.029 | 20887 / 31942 |

Paired against Haiku 4.5 `classify/v3 (c10, x3)`:

| model | Δ macro-F1 [95% CI] | Δ category acc [95% CI] | $/100 vs $0.073 | p95 ms | verdict |
|---|---|---|---|---|---|
| Kimi K2.5 | +0.002 [-0.102, +0.103] | **-0.056 [-0.106, -0.011]** | $0.032 (-56%) | 10085 | no significant difference on severity |
| Nova Lite | **-0.148 [-0.244, -0.050]** | **-0.100 [-0.200, -0.011]** | $0.003 (-96%) | 6991 | regression |
| gpt-oss-120b | -0.116 [-0.245, +0.011] | **-0.111 [-0.194, -0.039]** | $0.023 (-68%) | 10788 | regression (≥ 5 points) |
| DeepSeek V3.2 | **-0.111 [-0.216, -0.001]** | -0.056 [-0.117, +0.000] | $0.029 (-60%) | 31942 | regression |

### Paired comparisons (Session 2.4, `make eval-compare`)

Δ = candidate − base on the same 60 items, paired bootstrap 95% CI; verdict on severity macro-F1 (TL-08).

| candidate vs base | change tested | Δ macro-F1 [95% CI] | Δ component acc [95% CI] | $/100 | verdict |
|---|---|---|---|---|---|
| v2 vs v1 | severity decision steps + boundary examples | -0.001 [-0.078, +0.072] | +0.011 [-0.017, +0.044] | +7% | no significant difference; rejected |
| v3 vs v1 | component = where the fix goes, one example | -0.006 [-0.076, +0.060] | **+0.022 [+0.006, +0.044]** | +3% | no significant difference on severity; kept for component |
| v4 vs v3 | anchored confidence scale | +0.005 [-0.067, +0.081] | **-0.033 [-0.072, -0.006]** | +3% | no significant difference; rejected |
| v3 c5 vs v3 c10 | 5 incidents per call instead of 10 | -0.021 [-0.100, +0.075] | -0.028 [-0.061, +0.000] | **+44%** | cost gate failed; rejected |
| v5 vs v3 | rationale ≤ 20 words | -0.026 [-0.088, +0.035] | +0.017 [-0.017, +0.050] | -4% | no significant difference; rejected |

## Dedupe (tuning)

Precision and recall on cluster-implied pairs vs. gold duplicate groups, 95% CI (bootstrap over connected groups). Titan V2 1024 dims, threshold 0.30, top-5, star clusters (max 8).

| judge prompt | judge model | split | arm | precision [95% CI] | recall [95% CI] | judge valid first try | $/100 (embed + judge) |
|---|---|---|---|---|---|---|---|
| — | — | tuning | threshold + top-k only | **17.9%** [13.5%-25.3%] | **83.3%** [73.3%-100.0%] | — | $0.0001 |
| dedupe_judge/v1 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | threshold + top-k + judge | **94.7%** [80.0%-100.0%] | **100.0%** [100.0%-100.0%] | 75.0% | $0.182 |
| dedupe_judge/v2 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | threshold + top-k + judge | **94.7%** [80.0%-100.0%] | **100.0%** [100.0%-100.0%] | 66.7% | $0.209 |
| **dedupe_judge/v3** ✅ | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | threshold + top-k + judge | **90.0%** [71.4%-100.0%] | **100.0%** [100.0%-100.0%] | 100.0% | $0.141 |

v2 adds "a possible cause or consequence is a different report"; v3 instead limits the rationale to under 40 words. Single runs (the dedupe eval has no repeats yet); judge pair-level false positives: v1 3, v2 2, v3 3.

## Holdout (run once, 2026-10-30; frozen)

Chosen config: `classify/v3` (10 incidents per call), `dedupe_judge/v3`, Claude Haiku 4.5 (global profile), Titan V2 1024 dims, threshold 0.30, top-5, star clusters (max 8). Run once with `--confirm-holdout`, 3 repeats in that one run (same protocol as tuning). No prompt or config changed after it.

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 (c10, x3) | global.anthropic.claude-haiku-4-5-20251001-v1:0 | holdout | **0.768** [0.673-0.849] | 76.1% | 91.7% | 87.8% | 76.1% (100.0%) | 100.0% | 0.0% | $0.074 | 4830 / 5607 |

Per class (holdout): critical F1 0.90 · high 0.79 · medium 0.63 (recall 0.56) · low 0.76.

| judge prompt | judge model | split | arm | precision [95% CI] | recall [95% CI] | judge valid first try | $/100 (embed + judge) |
|---|---|---|---|---|---|---|---|
| — | — | holdout | threshold + top-k only | **26.9%** [13.3%-50.0%] | **100.0%** [100.0%-100.0%] | — | — |
| dedupe_judge/v3 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | holdout | threshold + top-k + judge | **91.3%** [73.9%-100.0%] | **100.0%** [100.0%-100.0%] | 100.0% | $0.105 |

81 candidate pairs, 9 judge calls; all 21 gold pairs (15 same-language, 6 cross-language) confirmed; 2 of 59 unrelated pairs merged.

### Cost per 100 incidents (holdout, measured)

| stage | $/100 |
|---|---|
| classify | $0.074 |
| embed + dedupe judge | $0.105 |
| report (2 calls per language per batch, fixed per batch) | ≈ $0.012-0.024 per batch |
| **total, 60-incident batch** | **≈ $0.20-0.22** (TL-08 ceiling $1.00) |

Tuning → holdout: macro-F1 0.746 → 0.768, dedupe precision 90.0% → 91.3%. Holdout did not drop, so there is no sign the prompts learned the tuning items. Medium recall stays the weakest number in both splits.
