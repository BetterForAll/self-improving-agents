# Self-Improving Agents -- Project Context for Claude Code

## Project Overview

This repo demonstrates **4 levels of self-improving code agents**, from the simplest possible loop to a competitive adversarial arena. Each level adds one key idea. All demos use **real LLM calls** (Gemini 2.5 Flash) with multiple task types.

A side-by-side comparison of approaches to autonomous code improvement.

---

## Background & History

I built a self-improving review loop for his Graph RAG project ([BetterForAll/graph-rag-ui](https://github.com/BetterForAll/graph-rag-ui), private) starting **February 1, 2026** -- 5 weeks before Karpathy's AutoResearch (March 6-7, 2026) and 6 weeks before Meta's HyperAgents paper (March 17, 2026, arxiv 2603.19461).

My original approach (in graph-rag-ui) introduced several techniques that later appeared independently in those papers:
- **Asymmetric context windows** -- small focused worker, 1M-token evaluator
- **Structured issue taxonomy** -- categorized feedback with severity + fix suggestions
- **Step-by-step pipeline logging** -- queryable JSON logs instead of raw context
- **Fully autonomous from a single Cursor instruction** -- no human in the loop

---

## Repo Structure

```
tasks/                      Shared task definitions (real files, not strings)
  snake/                      Snake game AI (deterministic: score) + visual player
  support/                    Customer support Q&A (LLM-as-judge: quality)
  email_validation/           Email validation (adversarial: accuracy)
  task_runner.py              Central module: load_task, write_solution, run_solution
  checkpoint.py               Shared checkpoint/resume (atomic writes, all levels)

autoresearch/               Level 1: AutoResearch Loop
  run.py                      The main loop (--task snake|support|email_validation)
  llm.py                      Gemini 2.5 Flash wrapper
  experiment.py               Run experiments with real-time JSON logging

feedback-loop/              Level 2: Feedback Loop
  run.py                      Orchestrates worker + reviewer
  worker.py                   Proposes improvements (small context, focused)
  reviewer.py                 Structured JSON feedback (full context, sees everything)
  llm.py                      Gemini wrapper

hyperagent/                 Level 3: HyperAgent Loop (true code-rewriting)
  run.py                      Generation loop with 3-stage validation
  llm.py                      Gemini wrapper
  seed/                       Original agent code (immutable reference)
    task_agent.py               Seed task agent
    meta_agent.py               Seed meta-agent
  agent_code/                 Live working copies (rewritten by meta-agent)
  generations/                Versioned snapshots (gen_000/, gen_001/, ...)

arena-loop/                 Level 4: Arena Loop (adversarial + self-modifying)
  run.py                      Arena loop with tournament selection
  code_agent.py               Mini-HyperAgent code agents (can mutate propose())
  test_agent.py               Test hardening agents (adversarial inputs)
  arena.py                    Tournament selection + strategy evolution
  llm.py                      Gemini wrapper
  CONCEPT.md                  Full architectural writeup (GAN analogy, roadmap)
```

---

## The 4 Levels

### Level 1 -- autoresearch/

The AutoResearch Loop. LLM proposes code -> write to file -> run as subprocess -> benchmark -> keep if better -> repeat.

### Level 2 -- feedback-loop/

The Feedback Loop. Adds a reviewer agent with structured feedback. Worker proposes (small context). Reviewer explains WHY it failed (full context, structured JSON with issue type, severity, fix suggestion, pattern detection).

### Level 3 -- hyperagent/

The HyperAgent Loop. True code-rewriting self-improvement. Meta-agent rewrites its own source code (task_agent.py, meta_agent.py) with 3-stage crash recovery (compile, import, signature). Generational versioning in generations/ folders. Inspired by Meta's DGM-H (HyperAgents, arxiv 2603.19461), simplified without Docker.

### Level 4a -- arena-loop/ (single agent)

Arena Single. Pure adversarial co-evolution: 1 code agent vs 1 test agent, no tournament selection. Isolates the adversarial mechanism from population dynamics. Run with `--code 1 --test 1 --label single`.

### Level 4b -- arena-loop/ (4 agents)

Arena Loop. Adversarial co-evolution with self-modifying agents and tournament selection. Code agents are mini-HyperAgents that can mutate their own propose() method. Test agents write harder tests. Tournament selection evolves strategies. Resume is fully supported via serialize/deserialize. See CONCEPT.md.

---

## Task Types

Tasks live in the shared `tasks/` folder. Each task is a folder with real runnable files:

| Task | Eval type | Files |
|------|-----------|-------|
| snake | Deterministic (score) | initial_solution.py, benchmark.py, config.py, play.py |
| support | LLM-as-judge (quality) | initial_solution.py, benchmark.py, config.py, knowledge_base.txt, test_cases.json |
| email_validation | Adversarial (accuracy) | initial_solution.py, benchmark.py, config.py, initial_tests.json |

All levels support all tasks via `--task` flag. Each level writes `solution.py` to its own folder (parallel-safe).

---

## Running

```bash
pip install -r requirements.txt    # google-genai, python-dotenv

# Quick demo
python autoresearch/run.py                     # snake (default)
python autoresearch/run.py --task support      # Customer support (LLM judge)
python autoresearch/run.py --task email_validation  # Email validation

# Experiments with logging
python autoresearch/experiment.py --task snake --iters 6

# Watch Snake AI play
python tasks/snake/play.py path/to/solution.py
```

---

## Key Concepts

| Concept | What it means |
|---------|--------------|
| Verifiable rewards | Measurable outcomes (timing, score, quality) as the signal |
| Rejection is free | Bad proposals revert instantly, zero cost to trying |
| Asymmetric context | Evaluator sees more than the worker -- match context to role |
| Structured feedback | Categorized issues with severity/fix vs binary pass/fail |
| True code-rewriting | The agent rewrites its own source code (not just strategy text) |
| Metacognitive self-modification | The improvement process itself is editable |
| Adversarial co-evolution | Code agents and test agents drive each other to improve |
| LLM-as-judge | Quality evaluation for tasks without numeric benchmarks |

---

## Related Repositories

| Repo | Description |
|------|-------------|
| BetterForAll/graph-rag-ui (private) | My original Graph RAG project -- review loop first implemented Feb 1, 2026 |
| karpathy/autoresearch | Karpathy's AutoResearch (March 6-7, 2026) |
| facebookresearch/HyperAgents | Meta's DGM-H paper code (March 17, 2026, arxiv 2603.19461) |

Local clones for reference:
- `C:/Users/befre/Documents/Code/autoresearch/`
- `C:/Users/befre/Documents/Code/HyperAgents/`

---

## Coding Conventions

- Dependencies: `google-genai` (Gemini API), `python-dotenv` (env loading)
- Shared tasks in `tasks/` folder -- all levels import from `tasks/task_runner.py`
- Each level folder has its own `llm.py` (Gemini wrapper, duplicated for independence)
- Agent files contain only agent logic (propose, review) -- no task definitions
- File-based execution: write solution.py, run benchmark.py as subprocess, parse stdout
- Each level writes solution.py to its own folder (parallel-safe)
- No type annotations, no docstrings beyond what exists
- ASCII only in .py files (no Unicode em-dashes) -- Windows cp1252 safe
