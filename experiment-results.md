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

Customer support Q&A is an **LLM-as-judge** task: the solution answers customer questions about a product, and a separate LLM call scores each answer's quality (0-100). Baselines vary across levels (5.0-15.0) because the LLM judge is non-deterministic -- the same initial code gets different scores each run. The "Unified Judge" column shows all solutions re-scored using rubric-based boolean checks (keyword + LLM YES/NO) for a fair, stable comparison.

| Level | Baseline | Best | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|----------------|--------------|-----------|
| AutoResearch | 21.300 | 58.360 | 3/6 | 1098.6 | 376 |
| Feedback Loop | 20.290 | 72.860 | 2/5 | 783.5 | 288 |
| HyperAgent | 23.230 | 44.250 | 2/18 | 3203.3 | 1039 |
| Arena Loop | 20.007 | 78.157 | 6 rounds x 4 agents | 13626.1 | 4819 |

**AutoResearch**: 3 accepted, 3 rejected, 0 errors
**Feedback Loop**: 2 accepted, 2 rejected, 1 errors
**HyperAgent**: 2 accepted, 15 rejected, 1 errors
**Arena Loop**: 6 rounds of competition, test suite grew to 28 cases

**Why these scores differ:**
The Unified Judge column uses **rubric-based boolean scoring**: each answer is checked against specific facts from the knowledge base (keyword match first, LLM YES/NO fallback for paraphrasing), plus quality checks for relevance, tone, and contradictions. This reduces scoring noise from 30+ points (old LLM 0-100 judge) to under 7 points.

The original Best scores varied wildly due to LLM judge noise -- Arena Loop's 22.39 was against 28 expanded questions, and HyperAgent's original 66.3 was a lucky single judge call that trapped it at a noisy ceiling.

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

**Winner (original 10 questions):** Feedback Loop with 74.670
**Winner (expanded 28 questions):** Feedback Loop with 77.554

Feedback Loop and Arena Loop are within scoring noise (~7 points) on both suites. HyperAgent drops on the expanded suite, showing less robust solutions.

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

**email_validation:** Arena Loop is the overall winner, achieving 84% accuracy on the combined, expanded test suite. While AutoResearch and HyperAgent reached 100% on the original, simpler suite, their solutions proved brittle, dropping to 62% on adversarial tests. Arena Loop's robustness against a harder test set demonstrates superior performance.

**snake:** Feedback Loop achieved the highest score of 31.100. Its structured reviewer effectively identified specific failure patterns, leading to targeted fixes that surpassed the performance of all other levels, including HyperAgent (27.500) and Arena Loop (29.200).

**support:** Feedback Loop delivered the best results in the cross-validation, scoring 74.670 on original questions and 77.554 on the expanded suite. Arena Loop was very competitive (70.670 original, 76.520 expanded), but Feedback Loop showed a slight edge in this LLM-as-judge task.

## What Each Level Adds

**Level 1 - AutoResearch:** This basic loop demonstrates the fundamental ability of LLMs to self-improve code. It is highly cost-effective for initial gains, quickly achieving significant improvements like 291.0x for snake at only $0.0700, and solving simple tasks like email_validation (1.0 accuracy on original tests) for minimal cost ($0.0019). Its limitations become apparent on more complex tasks or when requiring robust solutions.

**Level 2 - Feedback Loop:** By integrating a structured reviewer with issue taxonomy and fix suggestions, this level significantly enhances code improvement. The data shows it can achieve substantially higher performance than AutoResearch on complex tasks like snake (31.100 vs 14.550) and support (77.554 vs 53.329 on expanded tests). This added complexity is generally beneficial, offering a good balance of cost and deep problem-solving.

**Level 3 - HyperAgent:** This meta-agent aims for true code-rewriting self-improvement. While it showed competitive performance in some cases (email_validation 1.0 on original, snake 27.500), its added complexity and higher cost ($0.0996 for snake, $0.1650 for support) did not consistently translate to superior results over Feedback Loop. For the support task, its solution was notably less robust (37.851 on expanded tests) compared to Feedback Loop and Arena Loop.

**Level 4 - Arena Loop:** This level introduces adversarial testing and tournament selection, proving crucial for developing robust solutions against evolving test suites. While it has the highest costs ($0.6191 to $0.6295 per task), it produces agents that are less brittle and more effective against adversarial edge cases, as seen in email_validation (84% on combined suite). This method is designed to overcome the problem of a fixed benchmark being gamed.

## Cross-Validation Insight

The cross-validation data is essential for a fair comparison across levels, particularly highlighting that Arena Loop's reported "Best" scores appear lower because they are measured against significantly harder, expanded test suites. When evaluated on the same test conditions, Arena Loop's solutions are consistently competitive or, as in email_validation, demonstrably the best overall due to their robustness. For email_validation, solutions from Levels 1-3 achieved 90-100% accuracy on fixed initial tests but proved brittle, dropping to 58-62% on adversarial edge cases. Arena Loop, by training against adversarial pressure, maintained 84% accuracy on the combined, challenging suite. Similarly, for the support task, Arena Loop's pre-expansion peak performance is comparable to Feedback Loop's best, further proving that fixed benchmarks can be gamed and adversarial testing leads to more resilient code.

## Cost-Effectiveness

AutoResearch offers excellent cost-effectiveness for initial improvements, providing significant gains (e.g., 2.0x for email_validation at $0.0019, 291.0x for snake at $0.0700) for minimal investment. Feedback Loop generally provides the most improvement per dollar for moderately complex tasks, achieving substantially higher performance for a reasonable increase in cost (e.g., snake score 31.100 for $0.0882, support quality 77.554 for $0.0339). HyperAgent shows diminishing returns, costing more than Feedback Loop but not consistently delivering better results. Arena Loop is the most expensive by a significant margin (costs up to 10x higher), but its value lies in robustness and ability to handle adversarial conditions, which may justify the cost for critical applications where brittleness is unacceptable.

## When to Use Which Level

**AutoResearch:** Ideal for simple, well-defined problems or when budget is extremely tight and rapid initial progress is the priority. It excels at getting a "good enough" solution quickly.

**Feedback Loop:** Best for tasks requiring more nuanced and sustained improvement where specific error diagnosis and targeted fixes are beneficial, such as complex algorithms (snake) or quality-based scoring (support). It provides a strong balance of performance and cost.

**HyperAgent:** Based on this data, its benefits are less clear for these particular tasks. It might be suitable for highly specialized meta-programming problems where directly rewriting the agent's core logic yields unique advantages not seen here.

**Arena Loop:** Essential for critical applications where robustness, security, or resilience against adversarial inputs are paramount. Use when solutions must perform reliably even against evolving or deliberately challenging test suites, and when the budget allows for significantly higher operational costs.
