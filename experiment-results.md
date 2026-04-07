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

Customer support Q&A is an **LLM-as-judge** task: the solution answers customer questions about a product, and a separate LLM call scores each answer's quality (0-100). Baselines vary across levels (5.0-15.0) because the LLM judge is non-deterministic -- the same initial code gets different scores each run. The "Unified Judge" column shows all solutions re-scored using rubric-based boolean checks (keyword + LLM YES/NO) for a fair, stable comparison.

| Level | Baseline | Best | Unified Judge* | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|----------------|----------------|--------------|-----------|
| AutoResearch | 10.000 | 40.200 | **52.060** | 4/10 | 730.5 | 20 |
| Feedback Loop | 15.000 | 66.500 | **71.320** | 3/10 | 578.2 | 27 |
| HyperAgent | 4.670 | 63.500 | **72.860** | 4/18 | 1932.2 | 78 |
| Arena Loop | 10.000 | 22.390 | **72.860** | 6 rounds x 4 agents | 4032.0 | 152 |

*"Unified Judge" = all solutions scored using rubric-based boolean checks (keyword + LLM YES/NO) against the original 10 questions. Noise reduced from 30+ points to under 7 points. Arena Loop's Best (22.390) was scored against the expanded suite (28 cases).*

**AutoResearch**: 4 accepted, 5 rejected, 1 errors
**Feedback Loop**: 3 accepted, 5 rejected, 2 errors
**HyperAgent**: 4 accepted, 13 rejected, 1 errors
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

All solutions scored against the same 10 questions using boolean 
fact checks (keyword match + LLM YES/NO fallback) and quality checks. 
Noise reduced from 30+ points (old 0-100 judge) to under 7 points.

| Level | Original Run | Unified Judge | Difference |
|-------|-------------|--------------|------------|
| AutoResearch | 40.200 | 52.060 | +11.86 |
| Feedback Loop | 66.500 | 71.320 | +4.82 |
| HyperAgent | 63.500 | 72.860 | +9.36 |
| Arena Loop | 22.390 | 72.860 | +50.47 |
| Baseline | N/A | 22.550 | N/A |

**Winner: HyperAgent** with 72.860 -- 
scored using rubric-based boolean checks on the same questions as all other levels.

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

**email_validation**: Arena Loop is the winner. While AutoResearch and HyperAgent achieved 100% on the original 20 tests, Arena Loop's solution scored 84% on a significantly harder, expanded test suite of 50 cases, demonstrating superior robustness against adversarial edge cases.

**snake**: Feedback Loop achieved the highest score of 31.100. Its structured reviewer effectively identified specific failure patterns and suggested targeted fixes, leading to better performance than the other methods for this deterministic task.

**support**: HyperAgent and Arena Loop tied as winners, both achieving a score of 72.860 on the Unified Judge. The unified scoring method revealed that their solutions provided the most accurate and high-quality answers when evaluated against the same original questions.

## What Each Level Adds

**Level 1 - AutoResearch**: This basic loop provides immediate, cost-effective improvements, especially for simpler tasks. For email_validation, it hit 100% accuracy in just one LLM call for minimal cost. It demonstrated a respectable 291.0x improvement for snake, showing its utility for initial problem exploration.

**Level 2 - Feedback Loop**: Adding a structured reviewer significantly enhances performance on tasks that benefit from specific diagnostic feedback, as seen with snake where it achieved the highest score of 31.100. However, the overhead can sometimes hinder progress or introduce issues, as its email_validation solution dropped to 90% accuracy.

**Level 3 - HyperAgent**: The meta-agent's ability to rewrite its own source code led to substantial gains, particularly for the support task, achieving a 72.860 Unified Judge score. While effective, it generally incurs higher costs and iteration counts, indicating it's beneficial for complex problems requiring deeper systemic changes.

**Level 4 - Arena Loop**: This adversarial approach excels at producing robust solutions by expanding test suites with adversarial edge cases. While often appearing to have lower "Best" scores initially due to harder benchmarks, its solutions are consistently competitive or superior when fairly compared, proving their resilience, albeit at the highest cost and token usage.

## Cross-Validation Insight

The cross-validation data provides a critical insight into the true performance of the Arena Loop compared to the other levels. Arena Loop's reported scores often appear lower in the main table because its solutions are measured against significantly harder, expanded test suites, which the other levels never encountered during their training. When all solutions are scored against the same, fair benchmark, Arena Loop is consistently competitive or best.

For email_validation, levels 1-3 optimized for a fixed 20-case test suite and achieved 90-100% on it. However, these solutions proved brittle, dropping to 58-62% when tested against the expanded 50-case adversarial suite. In contrast, Arena Loop's solution, developed under adversarial pressure, scored 84% on the combined suite, demonstrating superior robustness. For support, Arena Loop's original run reported 22.390 against 28 expanded questions, but when re-scored with the Unified Judge against the original 10 questions, it achieved 72.860, on par with HyperAgent. This evidence strongly indicates that optimizing against a fixed benchmark leads to solutions that are easily gamed by adversarial tests.

## Cost-Effectiveness

Considering the "Improvement" factor from the main table, AutoResearch initially appears very cost-effective for tasks like email_validation (2.0x for $0.0019) and snake (291.0x for $0.0700). Feedback Loop also offers strong returns, especially for snake (622.0x for $0.0882). HyperAgent provides significant breakthroughs in quality (e.g., support) but at a higher cost per iteration. Arena Loop consistently has the highest costs (e.g., email_validation 1.7x for $0.2105; support 2.2x for $0.3433) due to its complex adversarial processes and larger token usage. While its "Improvement" factor might seem low against harder benchmarks, its value lies in robustness, not necessarily raw improvement percentage on initial, easier tests. There are clear diminishing returns in terms of simple improvement ratio per dollar as complexity (and cost) of the levels increases.

## When to Use Which Level

**AutoResearch** is best suited for initial problem exploration or for simpler, well-defined tasks where a quick, low-cost solution is sufficient. It is ideal for rapid prototyping and generating a basic working solution.

**Feedback Loop** should be employed when tasks require specific debugging or refinement based on identifiable failure patterns. It's effective for moderate complexity problems where structured feedback can directly guide the agent towards better performance.

**HyperAgent** is appropriate for complex problems that demand significant architectural changes or deep self-modification of the agent's core logic. It's for projects seeking more profound breakthroughs in agent capability, accepting a higher cost and longer development cycles.

**Arena Loop** is essential for high-stakes applications where robustness against adversarial inputs and unknown edge cases is paramount. It's the go-to choice when the goal is to develop highly resilient solutions capable of performing reliably under diverse and challenging conditions, justifying its substantial cost.
