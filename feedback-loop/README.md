# Feedback Loop -- Asymmetric Review

Two agents with different roles and different context sizes.

```
Worker (small prompt)  -> proposes improvements (focused)
Reviewer (full history) -> returns structured feedback (sees everything)
```

## How It Works

1. **Worker** gets a small, focused prompt -- just the current code and metric. No history, no context. It stays focused on proposing improvements.
2. **Reviewer** gets everything -- both code versions, full timing history, all previous feedback. It returns structured JSON with issue type, severity, fix suggestion, and cross-step pattern detection.
3. The loop accepts or rejects based on the metric, but the reviewer's feedback is logged for analysis.

The key innovation: **asymmetric information**. Workers don't need full history -- it's noise for proposal generation. Reviewers need full context to spot patterns that span multiple iterations.

## Files

| File | Purpose |
|------|---------|
| `run.py` | Orchestrates worker + reviewer -- read this first |
| `worker.py` | Proposes code improvements (small prompt) |
| `reviewer.py` | Returns structured JSON feedback (full context) |
| `llm.py` | Gemini 2.5 Flash wrapper |
| `experiment.py` | Run experiments with real-time logging and analysis |

Tasks are defined in the shared `../tasks/` folder (snake, support, email_validation).

## Run It

```bash
python run.py                    # snake (default)
python run.py --task email_validation  # Email validation
python run.py --task support     # Customer support (LLM-as-judge)

python experiment.py --task snake --iters 5
```

## Structured Feedback Schema

The reviewer returns JSON with this structure:

```json
{
    "issue_type": "performance | correctness | architecture | ok",
    "severity": "critical | major | minor | ok",
    "fix_suggestion": "concrete, actionable suggestion",
    "confidence": 0.0 to 1.0,
    "pattern_detected": "cross-step pattern name or null"
}
```

## Key Concept

**Structured feedback bridges focused workers and informed reviewers.** When feedback has a schema, other agents can act on it programmatically. This is how good engineering teams work -- developers focus on their task, tech leads see the full picture.

## Origin & Prior Art

The author first implemented this asymmetric review pattern in February 2026 for a
Graph RAG system, using a small focused worker and a 1M-token evaluator with
structured issue taxonomies. The same techniques -- asymmetric context windows and
structured feedback -- later appeared independently in Karpathy's AutoResearch
(March 6, 2026) and Meta's HyperAgents (March 17, 2026), suggesting the pattern was
a natural next step given early-2026 LLM capabilities rather than a single invention.
