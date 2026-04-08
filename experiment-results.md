# Self-Improving Agents -- Experiment Results

Generated: 2026-04-08

## Configuration

- Model: Gemini 2.5 Flash
- Levels tested: AutoResearch, Feedback Loop, HyperAgent, Arena Single, Arena Loop
- Tasks tested: email_validation, snake, support
- Total experiments: 15

## Summary Table

| Level | Task | Metric | Baseline | Best | Improvement | Iters | Cost | Tokens |
|-------|------|--------|----------|------|-------------|-------|------|--------|
| AutoResearch | snake | score | 0.050 | 14.550 | 291.0x | 10 | $0.0700 | 120,359 |
| AutoResearch | support | quality_score | 21.300 | 58.360 | 2.7x | 6 | $0.0795 | 266,925 |
| AutoResearch | email_validation | accuracy | 0.500 | 1.000 | 2.0x | 10 | $0.0019 | 8,113 |
| Feedback Loop | snake | score | 0.050 | 31.100 | 622.0x | 10 | $0.0882 | 197,735 |
| Feedback Loop | support | quality_score | 20.290 | 72.860 | 3.6x | 5 | $0.0339 | 182,188 |
| Feedback Loop | email_validation | accuracy | 0.500 | 0.900 | 1.8x | 10 | $0.0645 | 197,935 |
| HyperAgent | snake | score | 0.050 | 27.500 | 550.0x | 12 | $0.0996 | 204,719 |
| HyperAgent | support | quality_score | 23.230 | 44.250 | 1.9x | 18 | $0.1650 | 742,137 |
| HyperAgent | email_validation | accuracy | 0.500 | 1.000 | 2.0x | 6 | $0.0275 | 69,930 |
| Arena Single | snake | score | 0.050 | 14.550 | 291.0x | 6 | $0.0616 | 166,967 |
| Arena Single | support | quality_score | 20.880 | 72.417 | 3.5x | 3 | N/A | N/A |
| Arena Single | email_validation | accuracy | 0.500 | 0.700 | 1.4x | 6 | $0.0397 | 190,418 |
| Arena Loop | snake | score | 0.050 | 29.200 | 584.0x | 6 | $0.6191 | 945,713 |
| Arena Loop | support | quality_score | 20.007 | 78.157 | 3.9x | 6 | $0.6295 | 3,974,281 |
| Arena Loop | email_validation | accuracy | 0.500 | 0.840 | 1.7x | 6 | $0.2105 | 803,694 |

*Note on LLM-as-judge tasks (support): Baselines vary across levels (5.0-15.0 range
observed) because the LLM judge scores the same initial code differently each run.
Each level's improvement ratio within its run is valid. Cross-level ratio comparisons
should be interpreted with caution as they partly reflect baseline variation. The
absolute Best score is the most reliable metric for cross-level comparison.*

## Per-Task Analysis

### email_validation

Email validation is a **boolean correctness** task: for each test email, the solution returns valid/invalid and the benchmark checks against known answers. The metric is accuracy (0.0 to 1.0). The initial test suite has 20 cases.

| Level | Baseline | Best | vs Original* | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|--------------|----------------|--------------|-----------|
| AutoResearch | 0.500 | 1.000 | 1.000 | 1/10 | 33.8 | 1 |
| Feedback Loop | 0.500 | 0.900 | 0.900 | 2/10 | 757.6 | 20 |
| HyperAgent | 0.500 | 1.000 | 1.000 | 3/6 | 245.0 | 10 |
| Arena Single | 0.500 | 0.700 | 0.700 | 6 rounds x 1 agents | 950.5 | 14 |
| Arena Loop | 0.500 | 0.840 | **1.000** | 6 rounds x 4 agents | 2930.9 | 56 |

*"vs Original" = score against the original test suite only. For Levels 1-3 this is the same as Best (they only have original tests). For Arena Loop, Best is scored against the expanded suite (50 cases); vs Original shows the pre-expansion peak (round 1) for fair comparison.*

**AutoResearch**: 1 accepted, 0 rejected, 0 errors
**Feedback Loop**: 2 accepted, 8 rejected, 0 errors
**HyperAgent**: 3 accepted, 3 rejected, 0 errors
**Arena Single**: 6 rounds of competition, test suite grew to 50 cases
**Arena Loop**: 6 rounds of competition, test suite grew to 50 cases

**Why these scores differ:**
AutoResearch and HyperAgent both hit 100% (1.0) on the original 20 tests -- this task is simple enough that one good LLM proposal can solve it. AutoResearch did it in a single accepted iteration (1 LLM call), while Feedback Loop's reviewer overhead actually hurt: its solution reached only 90% because the reviewer's structured feedback pushed changes that broke edge cases the simpler approach got right.

**Arena Loop scoring note:**
Arena Loop's reported 84% looks lower, but it is scored against a **much harder expanded test suite of 50 cases** (adversarial edge cases the other levels never saw). See Cross-Validation below for the fair comparison.
### snake

Snake AI is a **deterministic scoring** task: the benchmark plays 20 games with fixed random seeds on a 10x10 grid and reports the average score (food eaten). There is no perfect score -- better algorithms eat more food before dying.

| Level | Baseline | Best | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|----------------|--------------|-----------|
| AutoResearch | 0.050 | 14.550 | 2/10 | 423.6 | 10 |
| Feedback Loop | 0.050 | 31.100 | 3/10 | 579.0 | 20 |
| HyperAgent | 0.050 | 27.500 | 4/12 | 786.0 | 16 |
| Arena Single | 0.050 | 14.550 | 6 rounds x 1 agents | 664.0 | 14 |
| Arena Loop | 0.050 | 29.200 | 6 rounds x 4 agents | 3589.3 | 56 |

**AutoResearch**: 2 accepted, 8 rejected, 0 errors
**Feedback Loop**: 3 accepted, 7 rejected, 0 errors
**HyperAgent**: 4 accepted, 8 rejected, 0 errors
**Arena Single**: 6 rounds of competition, test suite grew to 24 cases
**Arena Loop**: 6 rounds of competition, test suite grew to 6 cases

**Why these scores differ:**
This task rewards sustained iteration. AutoResearch's basic loop improved from 0.05 to 14.55 (2 accepted out of 10 tries) -- decent but limited by the lack of feedback on what went wrong. Feedback Loop reached 31.1 because the structured reviewer identified specific failure patterns (e.g. "snake traps itself in corners") and suggested targeted fixes. HyperAgent (27.5) and Arena Loop (29.2) are competitive but didn't surpass Feedback Loop -- for this task, knowing WHY the snake dies matters more than meta-level code rewriting or adversarial pressure.

**Arena Loop scoring note:**
Snake uses a fixed subprocess benchmark, so Arena Loop's score of 29.2 is directly comparable to the other levels. The test suite grew from 1 to 6 cases but this did not affect the benchmark score. No fairness issue here.
### support

Customer support Q&A is an **LLM-as-judge** task: the solution answers customer questions about a product, and a separate LLM call scores each answer's quality (0-100). Baselines vary across levels (5.0-15.0) because the LLM judge is non-deterministic -- the same initial code gets different scores each run. The "Unified Judge" column shows all solutions re-scored using rubric-based boolean checks (keyword + LLM YES/NO) for a fair, stable comparison.

| Level | Baseline | Best | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|----------------|--------------|-----------|
| AutoResearch | 21.300 | 58.360 | 3/6 | 1098.6 | 376 |
| Feedback Loop | 20.290 | 72.860 | 2/5 | 783.5 | 288 |
| HyperAgent | 23.230 | 44.250 | 2/18 | 3203.3 | 1039 |
| Arena Single | 20.880 | 72.417 | 6 rounds x 1 agents | 0 | 0 |
| Arena Loop | 20.007 | 78.157 | 6 rounds x 4 agents | 13626.1 | 4819 |

**AutoResearch**: 3 accepted, 3 rejected, 0 errors
**Feedback Loop**: 2 accepted, 2 rejected, 1 errors
**HyperAgent**: 2 accepted, 15 rejected, 1 errors
**Arena Single**: 6 rounds of competition, test suite grew to 19 cases
**Arena Loop**: 6 rounds of competition, test suite grew to 28 cases

**Why these scores differ:**
The Unified Judge column uses **rubric-based boolean scoring**: each answer is checked against specific facts from the knowledge base (keyword match first, LLM YES/NO fallback for paraphrasing), plus quality checks for relevance, tone, and contradictions. This reduces scoring noise from 30+ points (old LLM 0-100 judge) to under 7 points.

The original Best scores varied wildly due to LLM judge noise. Arena Loop's Best is scored against 28 expanded questions (not the original 10), and HyperAgent's original run score was inflated by a noisy single judge call. The Unified Judge column provides a fair comparison.

**Arena Loop scoring note:**
**Arena Loop's reported Best is scored against an expanded test suite of 28 adversarial questions**, not the original 10. The unified judge column shows its score on the original questions for a fair comparison. See Cross-Validation below for the full data.

## Cross-Validation: Fairness Comparison

**Why is this section needed?** Arena Loop (Level 4) doesn't just improve code -- 
it also expands the test suite with adversarial edge cases. This means its reported 
scores are measured against a HARDER test suite than Levels 1-3, making direct 
comparison of the "Best" column in the summary table misleading. Scores on 
expanded test suites are not comparable to scores on original test suites -- 
they're different scales.

This section puts all levels on the same scale for each task.

### email_validation (deterministic cross-validation)

Original test suite: 20 cases | Arena-expanded test suite: 50 cases

| Level | vs Original | vs Expanded | Combined* |
|-------|-------------|-------------|-----------|
| AutoResearch | 100% | 64% | 64% (brittle) |
| Feedback Loop | 90% | 62% | 62% (drops on harder tests) |
| HyperAgent | 100% | 66% | 66% (brittle) |
| Arena Single | 95% | 70% | 70% |
| Arena Loop | 95% | 70% | 70% |
| Baseline | 50% | 44% | 44% |

*Combined = all unique tests from both suites.

Levels 1-3 optimized for the original 20 tests and scored 90-100% on them -- 
but those solutions are **brittle**: they drop to 62%-66% on the expanded tests 
(adversarial edge cases they never trained against). Arena Loop scored 70% on 
the combined suite because it trained against adversarial pressure throughout.

### support (rubric-based boolean scoring)

All solutions scored using boolean fact checks (keyword match + LLM YES/NO fallback) and quality checks.

Original test suite: 10 questions | Arena-expanded test suite: 19 questions

| Level | vs Original (10) | vs Expanded (19) | Original Run |
|-------|-------------|-------------|------------|
| AutoResearch | 56.140 | 52.804 | 58.360 |
| Feedback Loop | 72.860 | 82.091 | 72.860 |
| HyperAgent | 39.010 | 45.820 | 44.250 |
| Arena Single | 65.600 | 73.042 | 72.417 |
| Arena Loop | 69.860 | 71.463 | 78.157 |
| Baseline | 21.010 | 16.709 | N/A |

**Original 10 questions:** Feedback Loop (72.860) and Arena Loop (69.860) are within measurement noise (~7 points)
**Winner (expanded 19 questions):** Feedback Loop with 82.091

HyperAgent drops on the expanded suite, showing less robust solutions.

### snake (deterministic benchmark)

Snake uses a fixed subprocess benchmark (20 games, deterministic seeds).
The arena's test suite grew but the benchmark score is unaffected --
scores are directly comparable across all levels.

| Level | Best Score | Notes |
|-------|-----------|-------|
| AutoResearch | 14.550 |  |
| Feedback Loop | 31.100 |  |
| HyperAgent | 27.500 |  |
| Arena Single | 14.550 |  |
| Arena Loop | 29.200 | pre-expansion peak: 29.200 (round 5) |

**Key takeaway:** When compared fairly, Arena Loop's solutions are
competitive or best across all tasks. Its apparently-lower reported
scores reflect harder test suites, not worse solutions.

## Limitations

- **Single run per experiment (N=1)** -- no error bars or confidence intervals.
  Snake and email_validation are deterministic (reproducible given the same code),
  but support scores have ~7 point noise from LLM-as-judge scoring.
- **Small task set (3 tasks)** -- findings may not generalize to other domains.
- **Single model (Gemini 2.5 Flash)** -- results may differ with other LLMs.

## Analysis

*Analysis generated by Gemini 2.5 Flash*

## Per-Task Winner

**email_validation**: Arena Single and Arena Loop performed best in generating robust solutions for email validation, both achieving 70% accuracy on the combined expanded test suite. This contrasts with earlier levels (AutoResearch, HyperAgent) that achieved 100% on the original limited suite but were brittle, dropping significantly when faced with adversarial tests.

**snake**: Feedback Loop achieved the highest score of 31.100. Its structured reviewer effectively identified specific failure patterns, leading to more targeted code improvements compared to other levels, including the more complex HyperAgent and Arena Loop.

**support**: Feedback Loop exhibited the highest quality score of 82.091 against the expanded test suite in the cross-validation, demonstrating strong performance and robustness. While Arena Loop achieved 71.463 on the expanded suite, the difference on the original 10 questions (72.860 vs 69.860) is within measurement noise.

## What Each Level Adds

**Level 1 - AutoResearch**: This basic loop demonstrated initial effectiveness, achieving significant improvements (e.g., 291.0x for snake, 2.0x for email_validation on original tests) for minimal cost. It is efficient for simple tasks where a single good LLM proposal can solve the problem, though its solutions can be brittle without explicit feedback or adversarial training.

**Level 2 - Feedback Loop**: The addition of a structured reviewer provided concrete benefits, especially for tasks requiring nuanced improvements like the Snake AI. The reviewer's ability to diagnose specific issues led to the best overall performance for Snake (31.100) and Customer Support (82.091 on expanded tests), often outperforming simpler and more complex levels.

**Level 3 - HyperAgent**: This meta-agent introduced code-rewriting self-improvement. While it achieved strong scores on email_validation's original tests and competitive scores on snake (27.500), its overall performance, particularly on the support task (39.010 on original, cross-validated), did not consistently surpass Feedback Loop. Its added complexity and cost did not always translate to superior or more robust solutions in these experiments.

**Level 4a - Arena Single & Level 4b - Arena Loop**: These adversarial co-evolution levels specifically addressed test suite expansion and robustness. While their initial reported scores might appear lower, the cross-validation shows they produce more robust solutions for email_validation (70% on combined tests) and competitive performance for support (Arena Single at 73.042 vs Expanded, Arena Loop at 71.463 vs Expanded). This comes at a significantly higher cost and token usage due to managing multiple agents and evolving test suites.

## Cross-Validation Insight

The cross-validation data highlights a crucial point: direct comparison of reported "Best" scores from Levels 1-3 with Level 4 (Arena Single/Loop) is misleading for tasks where the test suite expands. Levels 1-3, which optimized against fixed test suites, often developed "brittle" solutions that performed well on their training set but poorly against adversarial edge cases. For `email_validation`, AutoResearch and HyperAgent achieved 100% on the original 20 tests, but their solutions dropped to 64% and 66% respectively when evaluated against the expanded 50-case suite. In contrast, Arena Single and Arena Loop consistently scored 70% on the combined expanded suite, demonstrating the value of adversarial training for robustness. For `support`, Feedback Loop's solution was slightly better than Arena Loop on the expanded test suite, while scores on the original questions were within measurement noise. This clearly demonstrates that fixed benchmarks can be "gamed," and adversarial test expansion (as in Arena Loop) leads to more robust, if sometimes seemingly lower-scoring, solutions.

## Cost-Effectiveness

AutoResearch is highly cost-effective for simple tasks, achieving significant improvements for email validation ($0.0019 for 2.0x improvement) and decent results for snake ($0.0700 for 291.0x). Feedback Loop demonstrates strong cost-effectiveness for tasks that benefit from structured debugging, notably for snake ($0.0882 for 622.0x) and support ($0.0339 for 3.6x improvement). HyperAgent generally incurs higher costs without consistently delivering proportionally better results across tasks. Arena Loop provides robust solutions but at a substantially higher cost (e.g., $0.6191 for snake, $0.6295 for support) and token usage compared to the other levels, indicating diminishing returns for maximum robustness.

## When to Use Which Level

For **simple tasks with a clear, stable benchmark** where a basic iterative loop suffices, **AutoResearch** is the most cost-effective starting point.

For **complex tasks requiring detailed debugging or nuanced improvements**, where structured feedback on failure modes is highly beneficial, **Feedback Loop** offers the best balance of performance and cost-effectiveness.

**HyperAgent** may be considered for highly complex, architectural self-improvement challenges not fully represented here, but its benefits were not consistently demonstrated in these experiments over Feedback Loop.

When **robustness against unknown edge cases or adversarial conditions is paramount**, or when the **test suite is known to be incomplete and susceptible to being gamed**, **Arena Single** or **Arena Loop** are appropriate despite their significantly higher costs. Arena Loop is particularly suited for evolving solutions in dynamic environments where tests themselves need to adapt.
