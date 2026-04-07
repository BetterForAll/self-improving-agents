# Background & Prior Work

## The Verifiable Rewards Pattern

The core mechanism underlying all four levels is the **verifiable rewards** pattern
from reinforcement learning: an agent takes an action, receives a machine-checkable
reward with no human in the loop, and keeps or discards the result.

This pattern was established by AlphaGo (Silver et al., 2016), where the board rules
themselves verify win/loss -- enabling fully autonomous self-play. It resurfaced in
DeepSeek-R1's RLVR (2025), where math answers are checked against known solutions,
causing reasoning to emerge from the reward signal alone.

Karpathy's AutoResearch (March 2026) applies this same pattern at the agent level:
an LLM proposes code changes, a benchmark metric (`val_bpb`) provides the verifiable
reward, and the loop runs unsupervised overnight. Karpathy himself noted that software
engineering is "infinitely verifiable" (Karpathy, 2025) and identified RLVR as a major
advance -- AutoResearch is the natural synthesis of these two observations, though the
connection was not made explicit in its documentation.

Related work in this space includes Google's AlphaEvolve (May 2025), which uses
population-based evolutionary search with LLMs but fixed evaluators, and Meta's
HyperAgents (March 2026, arxiv 2603.19461), which adds metacognitive self-modification
where the improvement strategy itself is editable.

## Independent Convergence

Autonomous self-improvement loops emerged independently across multiple groups in
early 2026. I implemented a review-based improvement loop for a Graph RAG
system in February 2026, employing asymmetric context windows (small focused worker,
1M-token evaluator) and structured issue taxonomies -- techniques that later appeared
independently in Karpathy's AutoResearch (March 6, 2026) and Meta's HyperAgents
(March 17, 2026). This convergence suggests the pattern was a natural next step given
the capabilities of early-2026 LLMs, rather than a single invention.

## What This Repo Adds

This project presents a **layered progression** from basic verifiable-reward loops to
a full adversarial arena, with each level adding one concept:

1. The loop itself (verifiable rewards at the agent level)
2. Asymmetric structured review (reviewer sees full history, returns categorized feedback)
3. True code-rewriting (meta-agent rewrites its own source code with crash recovery)
4a. Adversarial co-evolution (1v1 arms race isolates the adversarial signal)
4b. Population-based tournament selection (adds competition and strategy evolution)

Prior work on adversarial code/test co-evolution (Code-A1, CURE, UTRL, ATGen) operates
through RL weight training -- fine-tuning model parameters. This project takes a
fundamentally different approach: **inference-time strategy evolution with frozen models**,
requiring no training infrastructure. The adversarial dynamic serves as selection pressure
for a population of competing strategies that evolve through tournament selection -- a
genetic algorithm operating in the space of "how to think about improvement," not in
weight space. See `arena-loop/CONCEPT.md` for the full architectural comparison.
