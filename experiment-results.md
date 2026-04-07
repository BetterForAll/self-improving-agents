# Self-Improving Agents -- Experiment Results

Generated: 2026-04-07

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
| Arena Single | 0.500 | 0.840 | **1.000** | 6 rounds x 4 agents | 2930.9 | 56 |
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
| Arena Single | 0.050 | 29.200 | 6 rounds x 4 agents | 3589.3 | 56 |
| Arena Loop | 0.050 | 29.200 | 6 rounds x 4 agents | 3589.3 | 56 |

**AutoResearch**: 2 accepted, 8 rejected, 0 errors
**Feedback Loop**: 3 accepted, 7 rejected, 0 errors
**HyperAgent**: 4 accepted, 8 rejected, 0 errors
**Arena Single**: 6 rounds of competition, test suite grew to 6 cases
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
| Arena Single | 20.007 | 78.157 | 6 rounds x 4 agents | 13626.1 | 4819 |
| Arena Loop | 20.007 | 78.157 | 6 rounds x 4 agents | 13626.1 | 4819 |

**AutoResearch**: 3 accepted, 3 rejected, 0 errors
**Feedback Loop**: 2 accepted, 2 rejected, 1 errors
**HyperAgent**: 2 accepted, 15 rejected, 1 errors
**Arena Single**: 6 rounds of competition, test suite grew to 28 cases
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
| AutoResearch | 100% | 62% | 62% (brittle) |
| Feedback Loop | 90% | 58% | 58% (drops on harder tests) |
| HyperAgent | 100% | 62% | 62% (brittle) |
| Arena Loop | 95% | 84% | 84% **best overall** |
| Baseline | 50% | 52% | 52% |

*Combined = all unique tests from both suites.

Levels 1-3 optimized for the original 20 tests and scored 90-100% on them -- 
but those solutions are **brittle**: they drop to 58-62% on the expanded tests 
(adversarial edge cases they never trained against). Arena Loop scored 84% on 
the combined suite because it trained against adversarial pressure throughout.

### support (rubric-based boolean scoring)

All solutions scored using boolean fact checks (keyword match + LLM YES/NO fallback) and quality checks.

Original test suite: 10 questions | Arena-expanded test suite: 28 questions

| Level | vs Original (10) | vs Expanded (28) | Original Run |
|-------|-------------|-------------|------------|
| AutoResearch | 56.140 | 53.329 | 58.360 |
| Feedback Loop | 74.670 | 77.554 | 72.860 |
| HyperAgent | 42.670 | 37.851 | 44.250 |
| Arena Loop | 70.670 | 76.520 | 78.157 |
| Baseline | 18.090 | 16.427 | N/A |

**Original 10 questions:** Feedback Loop (74.670) and Arena Loop (70.670) are within measurement noise (~7 points)
**Expanded 28 questions:** Feedback Loop (77.554) and Arena Loop (76.520) are within measurement noise (~7 points)

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

**email_validation:** Arena Loop performed best. When evaluated against the combined, harder test suite, its solution achieved 84% accuracy, outperforming AutoResearch and HyperAgent (62%) and Feedback Loop (58%), which were brittle against adversarial cases. This highlights its ability to produce robust code.

**snake:** Feedback Loop achieved the highest score of 31.100. Its structured reviewer effectively identified specific issues and guided targeted improvements, leading to superior performance compared to AutoResearch (14.550), HyperAgent (27.500), and Arena Loop (29.200).

**support:** Feedback Loop (77.554) and Arena Loop (76.520) achieved the highest scores when fairly compared on the expanded test suite using the unified judge. These scores are within the expected measurement noise of approximately 7 points, indicating comparable performance between these two levels for this task.

## What Each Level Adds

**Level 1 - AutoResearch:** This basic loop demonstrates initial self-improvement capability, successfully finding better code versions. For simple tasks like email_validation, it can achieve optimal performance on a limited test suite with minimal cost and iterations. Its benefit lies in its simplicity and low overhead for quick gains.

**Level 2 - Feedback Loop:** The addition of a structured reviewer significantly enhances the improvement process by providing targeted feedback and fix suggestions. This leads to substantial gains in tasks like snake (highest score of 31.100) and support (competitive 77.554 vs expanded tests), often outperforming more complex levels by guiding more effective iterations.

**Level 3 - HyperAgent:** This level introduces meta-level code rewriting, allowing the agent to modify its own source. While it achieved high scores on email_validation (100% on original tests), its solutions were less robust on expanded test suites for email_validation (62%) and support (37.851), and its performance was not consistently superior to Feedback Loop.

**Level 4 - Arena Loop:** This level integrates adversarial testing and tournament selection, leading to test suite expansion. It excels at producing robust solutions, as demonstrated by email_validation where its 84% accuracy on combined tests surpassed other levels, whose solutions were brittle. However, this robustness comes at a significantly higher cost and increased computational load.

## Cross-Validation Insight

The cross-validation data is crucial for a fair comparison, as Arena Loop's reported "Best" scores are against harder, expanded test suites. For email_validation, Levels 1-3 achieved 90-100% on their original 20-case test suite but dropped to 58-62% when evaluated against Arena Loop's 50-case expanded suite, showing brittleness. Arena Loop, having trained against adversarial pressure, maintained 84% on the combined suite, demonstrating superior robustness. For the support task, using a unified, rubric-based judge shows that Feedback Loop and Arena Loop achieve comparable results (within ~7 points of measurement noise) on both original and expanded test suites, while HyperAgent's solution proved less robust against expanded questions. This highlights that fixed benchmarks can lead to solutions that are not robust against real-world edge cases.

## Cost-Effectiveness

Considering improvement relative to cost, **Feedback Loop** frequently offers excellent cost-effectiveness. For snake, it achieved the highest score (31.100) at a cost of $0.0882, yielding approximately 7052x improvement per dollar relative to its baseline. In support, it achieved a high absolute score (72.860) for a low cost of $0.0339, offering high value. **AutoResearch** is very cost-effective for simple tasks, achieving a 2.0x improvement in email_validation for just $0.0019. **Arena Loop** is significantly more expensive across all tasks (e.g., $0.6191 for snake, $0.6295 for support), indicating diminishing returns in terms of absolute score improvement per dollar, despite its robust solutions.

## When to Use Which Level

**AutoResearch** is suitable for initial rapid prototyping and tasks where a quick, basic improvement is sufficient, especially with very limited budgets and for problems that might have simple, direct solutions.

**Feedback Loop** is ideal for tasks requiring sustained, directed improvement and refinement, particularly when specific error patterns or areas for optimization can be identified. It offers a strong balance of performance and cost-effectiveness across varied tasks.

**HyperAgent** may be considered for complex problems where the agent's core logic or approach needs fundamental restructuring, assuming that the meta-agent can consistently identify and implement beneficial self-modifications. However, it demonstrated less consistent robustness in these experiments.

**Arena Loop** is best suited for high-stakes applications where solution robustness against unforeseen or adversarial inputs is paramount, and test suite expansion is a critical capability. It comes with a higher cost, so it is appropriate when budget is secondary to achieving highly resilient and adaptive code.
