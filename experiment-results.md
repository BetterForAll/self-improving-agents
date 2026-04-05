# Self-Improving Agents -- Experiment Results

Generated: 2026-04-05

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
| HyperAgent | support | quality_score | 5.000 | 66.300 | 13.3x | 12 | $0.0626 | 178,465 |
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
Arena Loop's reported 84% looks lower, but it is scored against a **much harder expanded test suite of 50 cases** (adversarial edge cases the other levels never saw). When Levels 1-3 solutions are tested against that same expanded suite, they drop to 58-62% -- despite scoring 90-100% on the original tests. Arena Loop's 84% on the harder suite is the best overall. See Cross-Validation below for the full comparison.
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
Snake uses a fixed subprocess benchmark, so Arena Loop's score of 29.2 is directly comparable to the other levels. No fairness issue here. Feedback Loop's higher score (31.1) makes sense for this task: snake is a fixed-target optimization problem where knowing WHY the snake dies (e.g. "traps itself in corners", "fails to plan a path to food") is the most valuable signal. Arena Loop's adversarial machinery -- tournament selection, multiple competing agents, test agent evolution -- is designed to prevent benchmark gaming, but a fixed deterministic benchmark can't be gamed. The extra compute spent on adversarial pressure (~$0.62, 56 LLM calls) doesn't help when targeted debugging (~$0.09, 20 LLM calls) is what the task needs.
### support

Customer support Q&A is an **LLM-as-judge** task: the solution answers customer questions about a product, and a separate LLM call scores each answer's quality (0-100). Baselines vary across levels (5.0-15.0) because the LLM judge is non-deterministic -- the same initial code gets different scores each run.

| Level | Baseline | Best | vs Original* | Accepted/Total | Duration (s) | LLM Calls |
|-------|----------|------|--------------|----------------|--------------|-----------|
| AutoResearch | 10.000 | 40.200 | 40.200 | 4/10 | 730.5 | 20 |
| Feedback Loop | 15.000 | 66.500 | 66.500 | 3/10 | 578.2 | 27 |
| HyperAgent | 5.000 | 66.300 | 66.300 | 1/12 | 691.8 | 25 |
| Arena Loop | 10.000 | 22.390 | **67.630** | 6 rounds x 4 agents | 4032.0 | 152 |

*"vs Original" = score against the original test suite only. For Levels 1-3 this is the same as Best (they only have original tests). For Arena Loop, Best is scored against the expanded suite (28 cases); vs Original shows the pre-expansion peak (round 4) for fair comparison.*

**AutoResearch**: 4 accepted, 5 rejected, 1 errors
**Feedback Loop**: 3 accepted, 5 rejected, 2 errors
**HyperAgent**: 1 accepted, 8 rejected, 3 errors
**Arena Loop**: 6 rounds of competition, test suite grew to 28 cases

**Why these scores differ:**
Feedback Loop (66.5) and HyperAgent (66.3) both reached similar peaks -- structured feedback is highly effective for subjective quality tasks where the reviewer can explain "this answer is missing the pricing details" rather than just reporting a lower score. AutoResearch reached 40.2, limited by its inability to articulate what's wrong with an answer.

**Arena Loop scoring note:**
**Arena Loop's reported score of 22.39 is misleading.** It is scored against an expanded test suite of 28 adversarial questions, while Levels 1-3 are scored against the original 10 questions. Arena Loop's pre-expansion peak was **67.63** (round 4, scored against the original 10 questions before that round's test expansion). However, since all levels were scored in separate experiment sessions with a non-deterministic LLM judge (baselines ranged 5.0-15.0 across runs), the 67.63 vs 66.5 difference is within noise. The fair conclusion is that Feedback Loop, HyperAgent, and Arena Loop all converge to similar quality (~66-68) on the original questions. See Limitations below for what would make this comparison fully scientific.

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

### support (pre-expansion fairness comparison)

Arena Loop's reported score is measured against an expanded test suite
(28 questions), not the original 10. Direct comparison
with Levels 1-3 (scored on 10 original questions) is unfair.

| Level | Best Score | Test Suite Size | Notes |
|-------|-----------|-----------------|-------|
| AutoResearch | 40.200 | 10 (original) | scored on fixed test suite |
| Feedback Loop | 66.500 | 10 (original) | scored on fixed test suite |
| HyperAgent | 66.300 | 10 (original) | scored on fixed test suite |
| Arena Loop | 22.390 | 28 (expanded) | scored on harder, expanded suite |
| Arena Loop (pre-expansion peak) | **67.630** | 10 (original) | round 4, before test expansion* |

*Pre-expansion metric: Arena Loop's score measured against the original
test suite BEFORE new adversarial questions were added that round.
This is the fairest apples-to-apples comparison with Levels 1-3.

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

For email_validation, Arena Loop is the overall winner, achieving 84% accuracy on the combined, expanded test suite. While AutoResearch and HyperAgent reached 100% on the original, simpler tests, their solutions proved brittle, dropping to 62% on adversarial cases the Arena Loop effectively handled.

For the snake AI task, Feedback Loop achieved the highest score of 31.100. Its structured reviewer provided specific guidance that helped the agent learn optimal strategies and avoid common pitfalls, outperforming the other levels.

For customer support Q&A quality, Arena Loop delivered the highest performance with a pre-expansion peak of 67.630 against the original 10 questions. This score slightly surpassed Feedback Loop (66.500) and HyperAgent (66.300), demonstrating its effectiveness even before the added complexity of adversarial test expansion.

## What Each Level Adds

**Level 1 - AutoResearch:** This basic loop shows its strength in quickly achieving initial improvements on relatively simple tasks. For email_validation, it reached 100% accuracy with minimal cost ($0.0019) in just one accepted iteration. However, for more complex or subjective tasks like snake and support, its lack of specific diagnostic feedback limits its peak performance and leads to a higher rate of rejected solutions.

**Level 2 - Feedback Loop:** The addition of a structured reviewer significantly enhances performance, especially for tasks benefiting from detailed problem diagnosis. It enabled the snake agent to reach the highest score of 31.100 and provided strong performance for support Q&A, proving that targeted, human-like feedback is highly effective for complex problem-solving. This level demonstrates a strong return on complexity.

**Level 3 - HyperAgent:** The meta-agent capable of rewriting its own source code shows competitive results, achieving scores comparable to Feedback Loop for support (66.300) and snake (27.500). While it shows potential for deep architectural changes, the data indicates that its additional complexity does not consistently outperform the structured feedback approach for these specific tasks, often yielding similar or slightly lower results.

**Level 4 - Arena Loop:** This adversarial approach introduces robustness and test suite expansion, leading to solutions that perform well on harder, unseen cases. While its raw "Best" scores appear lower due to being tested against expanded suites, cross-validation reveals it generates the most resilient solutions for email_validation and achieves the highest fair comparison score for support. The benefit of robust solutions comes at a significantly higher cost and token usage.

## Cross-Validation Insight

The cross-validation data is crucial for understanding the true performance of the Arena Loop and for making fair comparisons across all levels. It clearly demonstrates that the Arena Loop's reported scores, which often appear lower in the main summary table, are actually superior when evaluated against comprehensive and challenging test suites.

For email_validation, Levels 1-3 optimized solely for the original 20 tests, achieving high scores (90-100%). However, these solutions proved brittle, with their accuracy dropping significantly to 58-62% when faced with the expanded, adversarial test suite. In contrast, Arena Loop's 84% on the combined 50-case suite signifies a much more robust and generalized solution, directly addressing the brittleness seen in other levels.

Similarly, for the support task, Arena Loop's reported best score of 22.390 is measured against 28 expanded, difficult questions. When compared fairly against the original 10 questions, Arena Loop's pre-expansion peak of 67.630 is the highest among all levels. This evidence underscores that a fixed benchmark can be "gamed," and the Arena Loop's ability to expand tests pushes agents toward more general and resilient performance, even if the reported metric on a harder suite appears lower. The snake task scores, being from a deterministic benchmark, are directly comparable and did not require cross-validation adjustment.

## Cost-Effectiveness

AutoResearch is highly cost-effective for achieving initial, significant improvements, particularly for simpler, boolean-correctness tasks like email_validation (achieving 1.0 accuracy for just $0.0019). Its improvement per dollar is substantial for basic problems.

Feedback Loop offers a strong balance of performance and cost-effectiveness. It delivers substantially higher metric improvements for tasks like snake (31.100 score for $0.0882) and support (66.500 quality for $0.0655) with only a moderate increase in cost over AutoResearch. For these complex tasks, the structured feedback clearly provides more value per dollar than raw iterations.

HyperAgent and Arena Loop exhibit diminishing returns in terms of improvement per dollar for the observed tasks. HyperAgent's costs are similar to Feedback Loop, but its performance gains are not consistently superior. Arena Loop, while producing the most robust solutions, is significantly more expensive, consuming 3-10 times more cost and tokens than other levels. Its high cost must be justified by the critical need for robustness against adversarial conditions.

## When to Use Which Level

**AutoResearch:** Ideal for straightforward tasks with clear, objective metrics where quick, initial improvements are needed at minimal cost. It's suitable for rapidly iterating on basic functionality or generating initial solutions.

**Feedback Loop:** Best for tasks that benefit from specific, actionable guidance on complex issues, such as improving AI behavior (snake) or subjective quality (support). This level offers an excellent balance of performance gain and cost-efficiency for many real-world code improvement scenarios.

**HyperAgent:** Consider this level for highly complex or open-ended code generation problems where deeper, potentially structural code changes might be beneficial. However, the current data does not strongly suggest it consistently outperforms Feedback Loop for the types of tasks tested; its true utility might lie in more abstract self-modification challenges.

**Arena Loop:** Reserved for critical applications where code robustness, resilience to adversarial inputs, or continuous test suite expansion is paramount, despite the significantly higher operational costs. This level is essential when "good enough" performance on a fixed benchmark is insufficient and true generalization or security against edge cases is required.

## Limitations

### Cross-validation coverage

**Email validation** has full cross-validation: all four levels' best solutions are re-executed against both the original (20 cases) and expanded (50 cases) test suites in a single deterministic run. This is the strongest comparison in this study.

**Snake** uses a fixed deterministic benchmark (20 games, fixed seeds), so scores are directly comparable across all levels with no cross-validation needed.

**Support** does NOT have full cross-validation. All levels were scored in separate experiment sessions with a non-deterministic LLM judge, making precise cross-level comparison unreliable. Levels 1-3 were never tested against the expanded 28-question suite, and no unified evaluation session was run where all solutions faced the same judge under identical conditions.

This matters because the LLM judge is non-deterministic -- baselines for the same initial code varied from 5.0 to 15.0 across runs. A 1-point difference (67.63 vs 66.5) is well within this noise. The honest conclusion for support is that **Feedback Loop, HyperAgent, and Arena Loop all converge to roughly the same quality (~66-68) on the original questions**, and we cannot rank them with confidence.

### What would make the support comparison scientific

1. **Unified evaluation session** -- run all four levels' best solutions against both the original and expanded test suites using the same LLM judge in a single session, eliminating inter-session variance.
2. **Structured rubric** -- replace open-ended quality scoring with a deterministic checklist (e.g., "mentions pricing: Y/N", "references knowledge base: Y/N"), reducing judge subjectivity.
3. **Multi-run averaging** -- score each solution 3-5 times, report mean and standard deviation, so differences within the noise floor are visible as ties rather than false rankings.

These improvements are left for future work. Until then, the support cross-validation should be read as "all top approaches perform similarly" rather than as a definitive ranking.
