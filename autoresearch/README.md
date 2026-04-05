# AutoResearch Loop -- Self-Improving Code

The simplest self-improving loop. One agent, one task, one feedback signal.

```
LLM proposes code -> write to file -> run & benchmark -> keep if better -> repeat
```

## How It Works

1. Start with a baseline (e.g., dumb Snake AI that always goes right)
2. Ask Gemini to write a better version
3. Write the proposal to `solution.py` and run the benchmark
4. If better -- keep it. If worse -- revert.
5. Repeat.

This is hill-climbing in code space. The LLM explores, the benchmark provides the signal.

## Files

| File | Purpose |
|------|---------|
| `run.py` | The main loop -- read this first |
| `llm.py` | Gemini 2.5 Flash wrapper |
| `experiment.py` | Run experiments with real-time logging and analysis |

Tasks are defined in the shared `../tasks/` folder (snake, support, email_validation).

## Run It

```bash
# See the concept in action
python run.py                    # snake (default)
python run.py --task support     # Customer support (LLM-as-judge)
python run.py --task email_validation  # Email validation

# Run experiment with logging
python experiment.py --task snake --iters 6

# Watch the Snake AI play (after running an experiment)
python ../tasks/snake/play.py results/snake/solutions/best.py
```

## Key Concept

**Rejection is free.** Bad proposals revert instantly. Only improvements accumulate. The LLM doesn't need to be right every time -- it just needs to be right sometimes.

## Prior Art

This loop implements the **verifiable rewards** pattern from reinforcement learning:
an agent takes an action, receives a machine-checkable reward (the benchmark), and
keeps or discards the result -- no human in the loop. This pattern was established
by AlphaGo (Silver et al., 2016) and resurfaced in DeepSeek-R1's RLVR (2025), where
automated verification of math answers caused reasoning to emerge from the reward
signal alone. Karpathy's AutoResearch (March 2026) applies the same pattern to code
research, using `val_bpb` as the verifiable reward. This implementation demonstrates
the concept with multiple task types (timing, game score, LLM-as-judge).
