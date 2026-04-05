# Arena Loop: Adversarial Arena Evolution

## The Assumption Nobody Questions

Every self-improving AI system has a hidden assumption baked in from the start:

**The benchmark is fixed.**

The code gets better. The tests stay the same.

This is fine for benchmarks that reflect reality perfectly. But benchmarks are
human-written approximations of reality. They have blind spots. They don't cover
edge cases you haven't thought of yet. They reward gaming over genuine quality.

What if the benchmark evolved alongside the code?

---

## Three Innovations That Change Everything

### 1. Adversarial Self-Improvement — GANs for Code

Generative Adversarial Networks (GANs) produce photorealistic images by
having two neural networks fight each other:
- The **Generator** tries to produce realistic images
- The **Discriminator** tries to detect fakes
- They improve each other — the race *is* the training signal

Apply this to code:

```
CODE AGENT (mini-HyperAgent)  TEST AGENT
──────────────────            ──────────────────────────────
Tries to write faster,  ←──→  Tries to write harder tests:
cleaner, more correct         - edge cases that expose bugs
code. Can mutate its own      - inputs that trigger worst-case
propose() method.             - benchmarks that reveal hidden
                                inefficiencies
```

The code agent makes bubble sort → the test agent finds a 10-million-item case
The code agent handles large n → the test agent finds a degenerate pivot input
The code agent patches the pivot → the test agent finds integer overflow
The code agent handles overflow → the test agent finds a stability violation

This arms race produces **battle-tested code** — quality earned against the
hardest adversary you can generate.

The key: the test agent's job is not to *break* the code. It's to find the
inputs that *reveal the most information* about code quality. This is
adversarial, but constructive.

### 2. Arena Evolution — Genetic Algorithms for Strategies

Instead of one agent improving over time, run N agents in parallel.
Each starts with a different meta-strategy (system prompt for improvement):

```
Agent A — strategy α: "focus on algorithmic complexity"
Agent B — strategy β: "focus on Python runtime characteristics"
Agent C — strategy γ: "focus on memory allocation patterns"
Agent D — strategy δ: "focus on adversarial edge cases first"
...
Agent N — strategy ω: "focus on benchmark-specific optimisation"
```

Every K rounds, run a **tournament**: evaluate all agents against the
current shared test suite. Which agent produced the best code quality?

- **Tournament winners survive** — their strategies seed the next generation
- **Losers are replaced** — their slots get new strategies derived from winners
- **Mutation** — small random changes to winning strategies prevent stagnation

This is **genetic algorithms applied to improvement strategies** — evolution
in the space of "how to think about improvement", not just "what to improve".

The winner isn't the best code. It's the best *process for producing* good code.

### 3. Cross-Pollination — Universal Strategy Transfer

The final piece: agents working on *different tasks* share meta-strategies.

```
Arena 1: Snake AI
  Agent A discovers: "check for degenerate inputs before proposing strategies"

                           ↓  Cross-pollination

Arena 2: Graph algorithms
  Agent B receives: "check for degenerate inputs before proposing algorithms"
  Agent B adapts:   "check for empty graphs and disconnected components first"

                           ↓  Cross-pollination

Arena 3: String algorithms
  Agent C receives: "check for degenerate edge cases first"
  Agent C adapts:   "check for empty strings and unicode boundaries first"
```

**Universal improvement heuristics emerge from task-specific experiments.**

This is how human expertise actually transfers — not by copying solutions
(a sorting fix doesn't apply to graphs), but by copying *patterns of thinking*
(checking degenerate cases applies everywhere).

The system discovers transferable meta-knowledge that no individual agent
was explicitly designed to find.

---

## Why This Is a Phase Transition

| Dimension | Current loops | Arena Evolution |
|-----------|--------------|-----------------|
| Improvement curve | Linear | Exponential (competing agents) |
| Quality ceiling | Bounded (benchmark games) | Raised by adversarial tests |
| Plateau behavior | Stagnates when LLM runs out of ideas | Adversary creates new challenges |
| Knowledge type | Task-specific | Universal meta-strategies emerge |
| Failure mode | Gets stuck locally | Tournament breaks local optima |

The arms race between code agents and test agents is self-sustaining.
When code quality peaks, test quality must improve to maintain pressure.
When tests get harder, code quality must improve to pass them.

This is the difference between a treadmill and a race with other runners.

---

## The GAN Analogy Made Precise

| GAN Component | Arena Evolution Equivalent |
|---------------|---------------------------|
| Generator | Code improvement agents |
| Discriminator | Test hardening agents |
| Training signal | Pass/fail + benchmark timing |
| Mode collapse | All agents converge to same local optimum |
| GAN convergence | Nash equilibrium: best code against hardest tests |
| Discriminator overfitting | Test agent makes unrealistic/impossible tests |
| Progressive training | Gradually increasing test difficulty |

The failure modes are symmetric too. Mode collapse (agents converge to the
same strategy) is prevented by explicit diversity enforcement in tournament
selection. Discriminator overfitting (test agent writes impossible tests) is
prevented by requiring tests to be *executable* — fake adversaries don't survive.

---

## Technical Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      THE ARENA                           │
│                                                          │
│  CODE AGENTS                    TEST AGENTS              │
│  ┌──────────────────┐           ┌──────────────────┐     │
│  │ Agent A (strat α)│ ◄───────► │ Tester X (strat a│     │
│  │ Agent B (strat β)│ ◄───────► │ Tester Y (strat b│     │
│  │ Agent C (strat γ)│ ◄───────► │ Tester Z (strat c│     │
│  └────────┬─────────┘           └────────┬─────────┘     │
│           │                              │               │
│           ▼                              ▼               │
│    Tournament (code quality)    Tournament (test hardness│
│           │                              │               │
│           └────────────┬─────────────────┘               │
│                        ▼                                 │
│                 Shared Strategy Pool                     │
│                 (evolving, versioned)                    │
│                        │                                 │
│                        ▼                                 │
│              Cross-Task Pollination                      │
│         (Snake ↔ Email ↔ Support arenas)                │
└──────────────────────────────────────────────────────────┘
```

---

## The Deeper Question

When agents improve their improvement strategies, which themselves improve
through competition, which transfer across tasks...

**Where does the recursion stop?**

It doesn't need to. That's the point.

The arena provides the **ground truth anchor**: code that actually works,
tested against inputs that actually reveal failures. The recursive
self-improvement is grounded in execution reality at every step.

This is what makes it productive rather than unstable:
- Strategies that produce working code survive
- Strategies that game metrics without producing quality die
- The adversarial tests keep raising the standard for "working"

---

## Related Work

### Adversarial Code/Test Co-Evolution (Weight Training)

Several groups have explored adversarial co-evolution of code generation and test
generation through RL weight training:

- **CURE** (June 2025, NeurIPS 2025 Spotlight, arxiv 2506.03136) -- Co-evolves a
  coder and unit tester via RL. The tester learns from the coder's mistakes. Single
  coder + single tester, trained end-to-end.

- **UTRL** (Microsoft Research, August 2025, arxiv 2508.21107) -- Adversarial RL
  alternating between a unit test generator and a code generator. The test generator
  learns to distinguish near-correct from correct solutions.

- **ATGen** (October 2025, ICLR 2026 Poster, arxiv 2510.14635) -- Adversarial RL
  where a test generator competes against a code generator that crafts harder bugs,
  creating an escalating difficulty curriculum.

- **Code-A1** (March 2026, arxiv 2603.15611) -- The closest structural match. A Code
  LLM and Test LLM with opposing RL objectives, adversarial co-evolution with
  validity-aware reward shaping and experience replay.

All of these operate through **RL weight training** -- fine-tuning model parameters
to improve code and test generation. They train one code model against one test model.

### How This Project Differs

This project takes a fundamentally different approach along three dimensions:

**1. Inference-time, not training-time.** We use frozen models (Gemini 2.5 Flash)
with no fine-tuning. The "evolution" happens in prompt space -- strategies are text
that gets mutated and selected, not weight vectors that get gradient-updated. This
requires no training infrastructure and works with any API-accessible LLM.

**2. Population-based strategy tournament with self-modifying agents.** Instead of
training one code model against one test model, we run N code agents and M test agents
simultaneously, each with a different meta-strategy. Code agents are mini-HyperAgents
that can mutate their own `propose()` method -- the code that generates proposals is
itself subject to evolution. Tournament selection identifies which *strategies and
methods* produce the best results, and losing strategies are replaced by mutated
copies of winners. This is genetic algorithms applied to the meta-level -- evolution
in the space of "how to think about improvement."

**3. Cross-task strategy transfer.** Meta-strategies discovered in one domain
(e.g., "check degenerate inputs first" from Snake AI) can transfer to other domains
(email validation, customer support). The RL papers are task-specific by design -- they train
weights for a particular code generation task. Our strategies are natural language and
can be evaluated across tasks. Use `cross_validate.py` to verify that solutions
evolved in one arena generalize to test suites from others.

### Other Related Work

- **AlphaEvolve** (Google DeepMind, May 2025, arxiv 2506.13131) -- Population-based
  evolutionary search with LLMs. Uses mutation and selection but with fixed evaluators,
  not adversarial test evolution.

- **Sol-Ver** (February 2025, arxiv 2502.14948) -- Self-play where a single model
  plays both solver and verifier roles. Not adversarial in the competitive sense.

- **Digital Red Queen** (Sakana AI + MIT, January 2026, arxiv 2601.03335) --
  LLM-driven adversarial program evolution in Core War. Self-play with escalating
  difficulty, but for assembly programs competing directly, not code+test co-evolution.

- **Meta HyperAgents** (March 2026, arxiv 2603.19461) -- Metacognitive
  self-modification where a meta-agent modifies the task agent and itself. Does not
  include adversarial test evolution or population-based selection. See
  `../hyperagent/` for our simplified implementation (Level 3).

---

## Implementation Status

```
DONE -- Adversarial Arena with real LLMs (Gemini 2.5 Flash):
  4 code agents vs 4 test agents, tournament selection every 2 rounds
  Code agents receive current code + strategy + recent test failures
  Test agents receive current tests + failing code + "make harder"
  Strategy mutation via LLM when losers are replaced
  Task-agnostic: Snake AI, email validation (adversarial), customer support

NEXT -- Multi-task arena:
  Run Snake + email validation + other arenas simultaneously
  Implement cross-pollination: extract meta-patterns from each arena
  Measure: does Snake meta-knowledge improve email validation performance?

FUTURE -- Strategy extraction:
  After N generations, extract "what did successful strategies have in common?"
  This is unsupervised discovery of software engineering best practices

FUTURE -- Real codebases:
  Apply to production code, not toy algorithms
  Test agent becomes a fuzzer / property-based tester
  Code agent becomes a refactoring + optimization engine
```

---

## Try It Now

```bash
python run.py                                    # snake arena (default)
python run.py --task email_validation            # email validation (adversarial)
python run.py --task snake                       # Snake AI (code agents only)
python experiment.py                   # run with logging and analysis
python experiment.py --code 2 --test 2 --rounds 4   # smaller run
```

Watch code agents and test agents compete. Watch strategies evolve through
tournament selection. Watch the arms race dynamic emerge.

Then run `python ../tasks/snake/play.py path/to/solution.py` to watch the
winning Snake AI play visually in your terminal.
