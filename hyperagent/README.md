# HyperAgent Loop -- True Code-Rewriting Self-Improvement

The agent doesn't just improve code -- it **rewrites its own source code**.

The meta-agent reads evaluation results and proposes modifications to `task_agent.py`
(how solutions are proposed) and `meta_agent.py` (its own code). A fixed harness
validates every rewrite with 3-stage crash recovery and versions every generation.

```
seed/          -> immutable original agent code
agent_code/    -> live working copies (rewritten by meta-agent each generation)
generations/   -> versioned snapshots (gen_000/, gen_001/, ...)
```

## How It Works

Two nested loops:

- **Inner loop** (every generation): `task_agent.py` proposes code improvements to the
  task solution. Benchmark it, keep or reject. Runs N iterations per generation.
- **Outer loop** (every generation): `meta_agent.py` reads recent evaluation results and
  rewrites the agent source code. The rewrite is validated, versioned, and either
  accepted or reverted.

The meta-agent sees its own source code and can modify it. This is true
metacognitive self-modification -- not just updating a text strategy, but rewriting
the actual Python code that drives improvement.

### The Generation Loop

```
Generation 1:
  Inner loop: seed task_agent proposes 3 solutions, 2 accepted
  Meta-agent: reads results, rewrites task_agent.py to add better heuristics
  Validation: compile -> import -> signature check -> ACCEPTED
  Saved to generations/gen_001/

Generation 2:
  Inner loop: MODIFIED task_agent proposes 3 solutions (using new heuristics)
  Meta-agent: reads results, rewrites both task_agent.py AND meta_agent.py
  Validation: compile OK, import OK, signature check -> ACCEPTED
  Saved to generations/gen_002/

Generation 3:
  Inner loop: FURTHER MODIFIED task_agent proposes solutions
  Meta-agent: proposes rewrite with syntax error
  Validation: compile -> FAILED -- reverts to gen_002
  ...
```

## 3-Stage Crash Recovery

Every proposed rewrite goes through validation before being accepted:

1. **Compile check** -- `compile()` on each modified file. Catches syntax errors.
2. **Import check** -- write files and `importlib` them. Catches missing imports,
   runtime init errors. Reverts on failure.
3. **Signature check** -- verify `task_agent.propose()` and
   `meta_agent.propose_modifications()` still exist with correct parameter counts.

If any stage fails, the agent code reverts to the last valid generation.

## Files

| File | Purpose |
|------|---------|
| `run.py` | Generation loop with validation -- read this first |
| `llm.py` | Gemini 2.5 Flash wrapper |
| `experiment.py` | Run experiments with checkpointing and analysis |
| `seed/task_agent.py` | Original task agent (immutable seed) |
| `seed/meta_agent.py` | Original meta-agent (immutable seed) |

The `agent_code/` directory contains the live working copies that get rewritten.
The `generations/` directory stores every version with metadata.

Tasks are defined in the shared `../tasks/` folder (snake, support, email_validation).

## Run It

```bash
python run.py                    # snake (default)
python run.py --task email_validation  # Email validation
python run.py --task support     # Customer support (LLM-as-judge)
python run.py --gens 8           # more generations

python experiment.py --task snake --gens 6
```

Experiments support **checkpoint/resume** -- if interrupted, re-run the same
command and it picks up from the last checkpoint.

## What to Look For

- **Generation history**: each generation shows VALID/FAILED and which files changed
- **Agent code evolution**: compare `seed/task_agent.py` vs `agent_code/task_agent.py`
  to see how the meta-agent modified the improvement strategy
- **Self-modification**: the meta-agent can rewrite its own `propose_modifications()`
  function -- look for generations where `meta_agent.py` was changed
- **Crash recovery in action**: watch for FAILED generations that safely revert

## How It Differs from Meta's HyperAgents (DGM-H)

Inspired by Meta's HyperAgents paper (March 2026, arxiv 2603.19461), which introduced
metacognitive self-modification -- an outer loop that modifies the agent's own code.

Key differences from the original:

- **No Docker**: Meta uses containerized execution for safety. We use subprocess
  isolation with compile/import/signature validation instead.
- **Folder-based versioning**: every generation is saved as a folder with source files
  and metadata, rather than container snapshots.
- **Simplified recursion**: the meta-agent can modify itself, but the harness (`run.py`)
  is fixed and never modified -- it provides the ground truth anchor.
- **Real LLM calls**: uses Gemini 2.5 Flash at inference time with frozen weights,
  no RL training.

## Key Concept

**True code-rewriting, not prompt engineering.** The meta-agent doesn't just change a
strategy string -- it rewrites the actual Python source code that drives improvement.
The 3-stage validation ensures this is safe, and generational versioning ensures
nothing is lost.
