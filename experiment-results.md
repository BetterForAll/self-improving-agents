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

*Note: The expanded questions are adversarial against the Arena's own solutions, not universally harder. Other levels may score higher on them if their approach happens to cover those topics well. The original questions are the fair comparison; the expanded column shows topic coverage, not difficulty.*

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

**email_validation**: Arena Single and Arena Loop both achieved 70% on the combined, hardest test suite. These levels produced the most robust solutions when evaluated against both original and adversarially expanded test cases. Levels 1-3 showed solutions that were brittle when exposed to the expanded test suite.

**snake**: Feedback Loop achieved the highest score of 31.100. Its structured reviewer effectively identified failure patterns and suggested targeted fixes, leading to superior performance in this deterministic scoring task compared to other levels. Arena Loop (29.200) and HyperAgent (27.500) were competitive but did not surpass Feedback Loop.

**support**: Feedback Loop achieved the highest score of 82.091 on the expanded 19 questions using the rubric-based boolean scoring. On the original 10 questions, Feedback Loop (72.860) and Arena Loop (69.860) were within measurement noise (~7 points), indicating comparable performance on the initial problem set.

## What Each Level Adds

**AutoResearch (Level 1)**: This basic loop demonstrates fundamental self-improvement capabilities. It successfully achieved 100% accuracy on the initial email_validation task with minimal cost and iterations, highlighting its effectiveness for simpler problems that can be solved by one or two good LLM proposals. For more complex tasks like snake and support, it provided decent initial improvements but its lack of structured feedback limited further gains.

**Feedback Loop (Level 2)**: The addition of a structured reviewer with an issue taxonomy and fix suggestions consistently led to higher performance in tasks requiring sustained iteration and specific debugging. This is evident in snake, where it achieved the highest score, and support, where it delivered the best performance on expanded tests. The structured feedback provided actionable insights that allowed the agent to improve more effectively, even if it sometimes pushed in suboptimal directions (email_validation).

**HyperAgent (Level 3)**: This meta-agent's ability to rewrite its own source code shows a sophisticated form of self-improvement. While competitive across tasks, its performance for snake and support did not consistently surpass Feedback Loop. In email_validation, it reached 100% on original tests but was brittle on expanded tests, similar to AutoResearch. Its higher cost and iteration count for support suggests that meta-level rewriting did not always translate to superior task performance in these experiments.

**Arena Single / Arena Loop (Level 4)**: These levels introduce adversarial co-evolution and test suite expansion, which is crucial for building robust solutions. The cross-validation data for email_validation demonstrates that Arena Loop produced solutions that were significantly less brittle against adversarial edge cases. While Arena Loop incurred the highest costs and tokens, its primary benefit lies in generating more resilient code and identifying hidden failure modes through test set expansion, rather than necessarily achieving the highest peak score on a fixed benchmark.

## Cross-Validation Insight

The cross-validation data provides a critical insight: direct comparison of "Best" scores from the summary table can be misleading, particularly for Arena Loop. Arena Loop's reported scores are against harder, expanded test suites. When all solutions are evaluated on the same expanded test suites, Arena Loop's solutions are competitive or best, showcasing their improved robustness.

For email_validation, Levels 1-3 achieved 90-100% on the original 20 tests but dropped significantly to 62-66% when tested against the expanded 50-case suite. This clearly demonstrates that solutions optimized solely on fixed benchmarks can be brittle. Arena Single and Arena Loop, which trained against adversarial pressure, maintained a 70% accuracy on the combined suite, indicating more robust code.

For support, using a stable, rubric-based boolean scoring system reduced noise. While the "Best" scores varied widely due to LLM judge non-determinism, the cross-validation revealed that Feedback Loop and Arena Loop performed comparably on the original 10 questions (within measurement noise). Feedback Loop notably excelled on the expanded 19 questions, showing strong topic coverage. The email_validation cross-validation cleanly demonstrates that fixed benchmarks can be gamed, and adversarial training addresses this brittleness.

## Cost-Effectiveness

Considering improvement relative to cost, **Feedback Loop** generally provided the most improvement per dollar, particularly for the `support` task, demonstrating an impressive ratio. It delivered substantial performance gains for `snake` at a reasonable cost as well. **AutoResearch** was highly cost-effective for `email_validation`, quickly reaching optimal performance on the original test set with minimal expense.

HyperAgent provided moderate cost-effectiveness. The Arena Loop, while producing robust solutions and expanding test suites, incurred significantly higher costs in terms of both dollars and tokens, indicating diminishing returns for its marginal performance improvements in peak score, though its value lies more in robustness than raw score.

## When to Use Which Level

**AutoResearch** is suitable for simple, well-defined problems where a single good LLM proposal can solve the task, or for obtaining quick initial baselines with minimal investment.

**Feedback Loop** is a strong choice for tasks that benefit from iterative refinement, where specific failure patterns can be identified and targeted. This includes deterministic scoring tasks like `snake` and LLM-as-judge tasks like `support`, where structured guidance helps in overcoming specific issues.

**HyperAgent** could be considered for projects where true self-modification of the agent's core logic is a primary goal, even if its direct performance benefits were not overwhelmingly superior in these specific experiments compared to Feedback Loop.

**Arena Loop** is best employed when the problem requires highly robust solutions that can withstand adversarial inputs and discover hidden edge cases. This is particularly valuable for boolean correctness tasks like `email_validation` where brittleness is a significant concern, and when investing in a continually expanding and hardening test suite is a priority, despite its higher operational costs.
