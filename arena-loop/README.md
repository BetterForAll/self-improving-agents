# Arena Loop -- Adversarial Evolution with Self-Modifying Agents

Code agents compete to write the best code. Test agents compete to write the
hardest tests. Code agents are **mini-HyperAgents** that can mutate their own
`propose()` method. They evolve through tournament selection.

```
Code agents  -> propose better implementations (can rewrite their own propose())
Test agents  -> propose harder test inputs
Tournament   -> winners survive, losers replaced by mutated winners
```

## How It Works

1. **N code agents** each propose improvements, guided by different strategies.
   Each agent carries its own `propose_source` -- the code that generates proposals.
   Losing agents can mutate this code, evolving not just what they propose but
   *how they propose it*.
2. **M test agents** each propose harder test cases designed to expose weaknesses.
3. The hardest new test gets added to the shared test suite (ratchet -- tests only
   get harder).
4. Every K rounds: **tournament selection** -- rank agents, top half survive,
   bottom half replaced by mutated winners.

This is **GANs for code** -- code agents and test agents drive each other to
improve through competition. Code agents are mini-HyperAgents -- they can
rewrite their own improvement logic, adding a second axis of evolution beyond
just strategy text.

Read `CONCEPT.md` for the full architectural writeup including the GAN analogy
and failure mode analysis.

## The Arms Race

```
Round 1: Code agent reaches 100% accuracy.
         Test agent adds tricky edge cases.
         Score DROPS to 80%.
Round 2: Code agent adapts, recovers to 96%.
         Test agent finds new weaknesses.
         Score DROPS to 80% again.
Round 3: Code agent handles those too. 94%.
         Test agent keeps pushing. Repeat.
```

The arms race IS the training signal. When code quality peaks, test quality must
improve. When tests get harder, code must improve. Self-sustaining.

## Files

| File | Purpose |
|------|---------|
| `run.py` | Arena loop with tournament selection -- read this first |
| `code_agent.py` | Code agents with strategy + self-modifying propose() |
| `test_agent.py` | Test hardening agents that generate adversarial inputs |
| `arena.py` | Tournament selection + strategy evolution |
| `llm.py` | Gemini 2.5 Flash wrapper |
| `experiment.py` | Run experiments with checkpointing and analysis |
| `CONCEPT.md` | Full concept writeup -- the idea behind the arena |

Tasks are defined in the shared `../tasks/` folder. Email validation uses full
adversarial arena (code + test agents). Snake uses code agents only.

## Run It

```bash
python run.py                          # snake (default)
python run.py --task email_validation  # email validation (adversarial)

python experiment.py                   # full run (~60-80 API calls)
python experiment.py --code 2 --test 2 --rounds 4   # smaller run

# Watch the Snake AI play (after running an experiment)
python ../tasks/snake/play.py results/snake/solutions/best.py
```

Experiments support **checkpoint/resume** -- all agent state (including
`propose_source` for code agents) is serialized and restored via
serialize/deserialize methods. If interrupted, re-run the same command.

## Cross-Validation

After running experiments across levels, use `cross_validate.py` (in the
arena-loop/ folder) to compare solutions against each other's test suites.
Run it from inside arena-loop/: `python cross_validate.py` This proves that
arena-evolved solutions are genuinely robust, not just tuned to their own tests.

## Key Concepts

**Competition breaks plateaus.** A single agent hill-climbs to a local optimum.
Competing agents and adversarial tests push past it.

**Self-modifying agents.** Code agents are mini-HyperAgents -- they can mutate
their own `propose()` function. The code that generates code improvements is
itself subject to evolution. Tournament losers get both a new strategy AND
potentially a rewritten propose method.

**Strategies evolve, not just code.** Tournament selection operates on
meta-strategies. The winner isn't the best code, it's the best *process for
producing* good code.

## Prior Art & What's New

Adversarial co-evolution of code and test generation has been explored through RL
weight training: CURE (NeurIPS 2025 Spotlight), UTRL (Microsoft Research), ATGen
(ICLR 2026), and Code-A1 (March 2026) all train model parameters for this purpose.

This project differs in three ways: (1) **inference-time evolution** with frozen
models -- no training infrastructure needed, (2) **population-based tournament
selection** of N competing strategies rather than training a single model, and
(3) **self-modifying agents** where the code generation logic itself evolves
through tournament pressure. See `CONCEPT.md` for the full comparison.
