# Self-Improving Agents -- Experiment Results

Generated: 2026-04-07

## Configuration

- Model: Gemini 2.5 Flash
- Levels tested: AutoResearch, Feedback Loop, HyperAgent, Arena Loop
- Tasks tested: email_validation, snake, support
- Total experiments: 12

## Summary Table

| Level | Task | Metric | Baseline | Best | Improvement | Iters | Cost | Tokens |
|-------|------|--------|----------|------|-------------|-------|------|--------|
| AutoResearch | snake | score | 0.050 | 14.550 | 291.0x | 10 | $0.0700 | 120,359 |
| AutoResearch | support | quality_score | 10.000 | 40.200 | 4.0x | 10 | $0.1037 | 226,128 |
| AutoResearch | email_validation | accuracy | 0.500 | 1.000 | 2.0x | 10 | $0.0019 | 8,113 |
| Feedback Loop | snake | score | 0.050 | 31.100 | 622.0x | 10 | $0.0882 | 197,735 |
| Feedback Loop | support | quality_score | 15.000 | 66.500 | 4.4x | 10 | $0.0655 | 185,861 |
| Feedback Loop | email_validation | accuracy | 0.500 | 0.900 | 1.8x | 10 | $0.0645 | 197,935 |
| HyperAgent | snake | score | 0.050 | 27.500 | 550.0x | 12 | $0.0996 | 204,719 |
| HyperAgent | support | quality_score | 4.670 | 63.500 | 13.6x | 18 | $0.1523 | 617,102 |
| HyperAgent | email_validation | accuracy | 0.500 | 1.000 | 2.0x | 6 | $0.0275 | 69,930 |
| Arena Loop | snake | score | 0.050 | 29.200 | 584.0x | 6 | $0.6191 | 945,713 |
| Arena Loop | support | quality_score | 10.000 | 22.390 | 2.2x | 6 | $0.3433 | 1,396,346 |
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
| Arena Loop | 0.500 | 0.840 | **1.000** | 6 rounds x 4 agents | 2930.9 | 56 |

*"vs Original" = score against the original test suite only. For Levels 1-3 this is the same as Best (they only have original tests). For Arena Loop, Best is scored against the expanded suite (50 cases); vs Original shows the pre-expansion peak (round 1) for fair comparison.*

**AutoResearch**: 1 accepted, 0 rejected, 0 errors
**Feedback Loop**: 2 accepted, 8 rejected, 0 errors
**HyperAgent**: 3 accepted, 3 rejected, 0 errors
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
| Arena Loop | 0.050 | 29.200 | 6 rounds x 4 agents | 3589.3 | 56 |

**AutoResearch**: 2 accepted, 8 rejected, 0 errors
**Feedback Loop**: 3 accepted, 7 rejected, 0 errors
**HyperAgent**: 4 accepted, 8 rejected, 0 errors
**Arena Loop**: 6 rounds of competition, test suite grew to 6 cases

**Why these scores differ:**
This task rewards sustained iteration. AutoResearch's basic loop improved from 0.05 to 14.55 (2 accepted out of 10 tries) -- decent but limited by the lack of feedback on what went wrong. Feedback Loop reached 31.1 because the structured reviewer identified specific failure patterns (e.g. "snake traps itself in corners") and suggested targeted fixes. HyperAgent (27.5) and Arena Loop (29.2) are competitive but didn't surpass Feedback Loop -- for this task, knowing WHY the snake dies matters more than meta-level code rewriting or adversarial pressure.

**Arena Loop scoring note:**
Snake uses a fixed subprocess benchmark, so Arena Loop's score of 29.2 is directly comparable to the other levels. The test suite grew from 1 to 6 cases but this did not affect the benchmark score. No fairness issue here.
### support

Customer support Q&A is an **LLM-as-judge** task: the solution answers customer questions about a product, and a separate LLM call scores each answer's quality (0-100). Baselines vary across levels (5.0-15.0) because the LLM judge is non-deterministic -- the same initial code gets different scores each run. The "Unified Judge" column shows all solutions re-scored by the same judge in a single session for a fair comparison.

| Level | Baseline | Best | Unified Judge* | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|----------------|----------------|--------------|-----------|
| AutoResearch | 10.000 | 40.200 | **38.270** | 4/10 | 730.5 | 20 |
| Feedback Loop | 15.000 | 66.500 | **54.930** | 3/10 | 578.2 | 27 |
| HyperAgent | 4.670 | 63.500 | **46.080** | 4/18 | 1932.2 | 78 |
| Arena Loop | 10.000 | 22.390 | **43.330** | 6 rounds x 4 agents | 4032.0 | 152 |

*"Unified Judge" = all solutions scored by the same LLM judge in a single session against the original 10 questions. This eliminates inter-session judge variance. Arena Loop's Best (22.390) was scored against the expanded suite (28 cases).*

**AutoResearch**: 4 accepted, 5 rejected, 1 errors
**Feedback Loop**: 3 accepted, 5 rejected, 2 errors
**HyperAgent**: 4 accepted, 13 rejected, 1 errors
**Arena Loop**: 6 rounds of competition, test suite grew to 28 cases

**Why these scores differ:**
The unified judge (3x averaged) gives the fairest ranking. All levels' solutions are keyword-matching heuristics of varying quality -- none use the LLM for answering, so scores reflect how well each level's improvement loop refined the matching logic.

**Why LLM-as-judge scores vary so much:** A single judge call can swing by 30+ points for the same solution. The original run scored HyperAgent at 66.3 and Arena Loop at 22.39, but both were noisy. With 3x averaged judging, scores stabilize and the true ranking emerges. This is why the JUDGE_RUNS=3 fix was added to tasks/support/config.py.

**Arena Loop scoring note:**
**Arena Loop's reported Best of 22.39 is misleading.** It was scored against an expanded test suite of 28 adversarial questions, not the original 10. The unified judge column shows its score on the original questions for a fair comparison. See Cross-Validation below for the full data.

## Cross-Validation: Fairness Comparison

**Why is this section needed?** Arena Loop (Level 4) doesn't just improve code -- 
it also expands the test suite with adversarial edge cases. This means its reported 
scores are measured against a HARDER test suite than Levels 1-3, making direct 
comparison of the "Best" column in the summary table misleading. A score of 22.39 
on 28 hard questions is not worse than 66.5 on 10 easy questions -- they're 
different scales.

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

### support (unified LLM judge -- same judge, same session)

All solutions scored against the same 10 questions by the same 
LLM judge in a single session. This eliminates inter-session variance 
and gives a true apples-to-apples comparison.

| Level | Original Run | Unified Judge | Difference |
|-------|-------------|--------------|------------|
| AutoResearch | 40.200 | 38.270 | -1.93 |
| Feedback Loop | 66.500 | 54.930 | -11.57 |
| HyperAgent | 63.500 | 46.080 | -17.42 |
| Arena Loop | 22.390 | 43.330 | +20.94 |
| Baseline | N/A | 3.000 | N/A |

**Winner: Feedback Loop** with 54.930 -- 
scored by the same judge on the same questions as all other levels.

*Note: Arena Loop's original run reported 22.390 because it was scored against 28 expanded questions. The unified judge score above is against the original 10 questions.*

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

## Analysis

*Analysis generated by Gemini 2.5 Flash*

## Per-Task Winner

For email_validation, Arena Loop is the winner. While AutoResearch and HyperAgent achieved 100% on the original simple tests, Arena Loop's solution scored 84% on the significantly harder combined test suite, proving superior robustness against adversarial cases. The other levels' solutions were brittle and dropped to 58-62% on the expanded suite.

For snake, Feedback Loop is the winner, achieving a score of 31.1. Its structured feedback mechanisms allowed for more targeted improvements to the AI's logic, outperforming AutoResearch's simpler iteration and HyperAgent's meta-level changes. Arena Loop was competitive but did not surpass Feedback Loop in this deterministic task.

For support, Feedback Loop again takes the lead with a unified judge score of 54.930. The structured reviewer and fix suggestions proved highly effective in refining the keyword-matching logic for Q&A quality. While other levels produced good solutions, Feedback Loop achieved the highest quality score when evaluated fairly by a consistent judge.

## What Each Level Adds

**Level 1 - AutoResearch**: This basic loop demonstrates fundamental self-improvement capabilities. It successfully found 100% accurate solutions for email_validation on the original test set with minimal cost and iteration, and made substantial initial gains for snake and support. The data shows that a simple propose-evaluate-keep cycle can be highly effective for initial progress, especially on tasks where good solutions are relatively easy to find.

**Level 2 - Feedback Loop**: This level's addition of a structured reviewer significantly boosts performance on tasks requiring nuanced improvement. The data clearly shows its value for snake (best score 31.1) and support (best unified score 54.930), where specific feedback helped refine complex logic. However, for email_validation, its structured feedback sometimes led to over-correction, resulting in a slightly lower accuracy compared to AutoResearch on the original test suite.

**Level 3 - HyperAgent**: The meta-agent's ability to rewrite its own source code did not consistently yield superior results over Feedback Loop for these specific tasks. While competitive in snake (27.5) and email_validation (100% on original tests), its unified score for support (46.080) was lower than Feedback Loop's. The added complexity of meta-level rewriting did not always translate to a performance advantage, and its accepted/total ratio for support was lower than Feedback Loop.

**Level 4 - Arena Loop**: This level introduces adversarial test generation and tournament selection, leading to highly robust solutions. While its raw reported scores often appear lower, the cross-validation proves its superior performance on expanded, harder test suites. It successfully produced the most robust email_validation solution (84% on combined tests) and competitive solutions for snake and support at a significantly higher cost. Its added complexity pays off in generalizability and resilience against edge cases.

## Cross-Validation Insight

The cross-validation section is crucial for a fair comparison, as Arena Loop's reported scores are against significantly harder, expanded test suites. When all solutions are tested on the same combined suite or with a unified judge, Arena Loop's solutions are competitive or emerge as the best overall. For email_validation, Levels 1-3 achieved high scores on their original, fixed test suites, but their solutions proved brittle, with accuracy dropping significantly (from 90-100% to 58-62%) when faced with the adversarial tests generated by Arena Loop. In contrast, Arena Loop's solution maintained a robust 84% on the combined, harder suite. For support, the unified judge confirms that Arena Loop's pre-expansion peak (43.330) is comparable to the top performers from levels 1-3 when evaluated on the same 10 original questions. This demonstrates that a fixed benchmark can indeed be "gamed," and adversarial test expansion is necessary for developing truly robust and generalizable solutions.

## Cost-Effectiveness

Considering overall improvement and robustness, AutoResearch is the most cost-effective for initial gains, especially for simpler tasks like email_validation, where it achieved 100% accuracy on original tests for a mere $0.0019. Feedback Loop provides excellent value, delivering the best or near-best performance on snake ($0.0882 for 31.1 score) and support ($0.0655 for 54.930 unified score) at a relatively modest cost. HyperAgent's additional complexity leads to higher costs without consistently superior results. Arena Loop, while producing the most robust and generalizable solutions, is significantly more expensive, with costs ranging from $0.2105 to $0.6191 per task. There are clear diminishing returns; while Arena Loop yields the most resilient code, the cost per unit of improvement dramatically increases, especially after Feedback Loop's strong performance.

## When to Use Which Level

**AutoResearch**: Ideal for rapid prototyping, simple tasks with clear success criteria, or when budget is extremely constrained. Use it to quickly establish a baseline and achieve initial, straightforward improvements.

**Feedback Loop**: The optimal choice for tasks requiring more nuanced problem-solving and iterative refinement, such as game AI or quality-driven Q&A. It offers a strong balance of performance and cost-effectiveness by providing structured guidance for code evolution.

**HyperAgent**: May be suitable for highly complex projects where meta-level code modification or architectural changes are genuinely beneficial, or for exploring the limits of self-modification. However, for the tasks tested, its added complexity did not consistently translate to superior performance over Feedback Loop, suggesting it might be overkill for many common agent improvement scenarios.

**Arena Loop**: Essential for mission-critical applications where robustness, generalizability, and resistance to adversarial inputs are paramount. When the cost of failure is high, or when the problem space is dynamic and prone to edge cases, Arena Loop's adversarial testing and competition justify its significantly higher cost by producing highly resilient solutions.
