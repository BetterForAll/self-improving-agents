"""
Feedback Loop -- Asymmetric Review (Real LLM)
==============================================
Worker: small prompt, proposes improvements (focused)
Reviewer: full history, returns structured feedback (sees everything)

Uses Gemini 2.5 Flash. Set GEMINI_API_KEY in ../.env

Tasks:
  python run.py                  # default: snake
  python run.py --task support   # Customer support (LLM-as-judge)
  python run.py --task    # Sorting optimization
"""

import argparse
import os
import sys

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tasks.task_runner import load_task, write_solution, run_solution

import llm
import worker
import reviewer

DIR = os.path.dirname(os.path.abspath(__file__))


def run(iterations=5, on_step=None, start_from=0, resume_state=None, task_name="snake"):
    # on_step: called by experiment.py to save checkpoints. None when running directly.
    task = load_task(task_name)
    higher_is_better = task.HIGHER_IS_BETTER
    metric_name = task.METRIC_NAME
    solution_file = os.path.join(DIR, f"solution_{task_name}.py")

    print("=" * 65)
    print(f"  Feedback Loop -- {task.TASK_NAME} (Real LLM)")
    print("=" * 65)
    print("  Worker: small prompt  |  Reviewer: full history + structured feedback")
    print()

    perfect_score = getattr(task, "PERFECT_SCORE", None)

    def is_better(new, old):
        return new > old if higher_is_better else new < old

    def is_perfect(score):
        if perfect_score is None:
            return False
        return score >= perfect_score if higher_is_better else score <= perfect_score

    def improvement_pct(new, old):
        if higher_is_better:
            return (new - old) / max(old, 0.0001) * 100
        else:
            return (old - new) / old * 100

    # Resume from previous state if provided
    if resume_state:
        current_code = resume_state["current_code"]
        best_metric = resume_state["best_metric"]
        baseline_metric = resume_state["baseline_metric"]
        history = resume_state["history"]
        write_solution(current_code, solution_file)
        print(f"[RESUME] Resuming from step {start_from + 1}, best: {best_metric:.3f}\n")
    else:
        current_code = task.INITIAL_CODE
        write_solution(current_code, solution_file)
        best_metric, err = run_solution(task, solution_file, llm_module=llm)
        if err:
            print(f"Baseline failed: {err}")
            return None
        baseline_metric = best_metric

        history = []
        print(f"[INIT] Baseline {metric_name}: {best_metric:.3f}\n")

    for i in range(start_from, iterations):
        print(f"-- Step {i + 1}/{iterations} " + "-" * 42)

        print("  Worker  -> proposing...")
        try:
            proposed_code, raw_response = worker.propose(current_code, best_metric, metric_name=metric_name)
        except Exception as e:
            print(f"  Worker ERROR: {e}")
            step = {"step": i + 1, "action": "ERROR", "error": str(e)}
            history.append(step)
            if on_step:
                on_step(step)
            continue

        write_solution(proposed_code, solution_file)
        new_metric, err = run_solution(task, solution_file, llm_module=llm)

        if err:
            print(f"  ERROR: {err}")
            write_solution(current_code, solution_file)
            step = {"step": i + 1, "action": "ERROR", "error": err}
            history.append(step)
            if on_step:
                on_step(step)
            continue

        print("  Reviewer -> analyzing with full context...")
        try:
            feedback = reviewer.review(
                current_code, proposed_code, new_metric, best_metric, history
            )
        except Exception as e:
            print(f"  Reviewer ERROR: {e} -- using default feedback")
            feedback = {"issue_type": "unknown", "severity": "minor",
                        "fix_suggestion": str(e), "confidence": 0.0,
                        "pattern_detected": None}

        sev = (feedback.get("severity") or "?").upper()
        suggestion = (feedback.get("fix_suggestion") or "")[:72]
        pattern = feedback.get("pattern_detected")

        print(f"  Reviewer [{sev:8}] {suggestion}...")
        if pattern:
            print(f"  Reviewer !  Pattern: {pattern}")

        if is_better(new_metric, best_metric):
            pct = improvement_pct(new_metric, best_metric)
            direction = "better" if higher_is_better else "faster"
            print(f"  Decision -> + ACCEPTED  {best_metric:.3f} -> {new_metric:.3f} {metric_name}  ({pct:.1f}% {direction})")
            step = {
                "step": i + 1, "action": "ACCEPTED",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "improvement": f"{pct:.1f}% {direction}",
                "feedback": feedback, "code": proposed_code,
                "llm_response": raw_response,
            }
            history.append(step)
            current_code = proposed_code
            best_metric = new_metric
        else:
            pct = abs(improvement_pct(best_metric, new_metric))
            direction = "worse" if higher_is_better else "slower"
            print(f"  Decision -> x REJECTED  {new_metric:.3f} {metric_name}  ({pct:.1f}% {direction})")
            write_solution(current_code, solution_file)
            step = {
                "step": i + 1, "action": "REJECTED",
                "reason": f"{pct:.1f}% {direction} than current best",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "feedback": feedback, "code": proposed_code,
                "llm_response": raw_response,
            }
            history.append(step)

        if on_step:
            on_step(step)

        if is_perfect(best_metric):
            print(f"\n  PERFECT SCORE reached ({best_metric:.3f}). Stopping early.")
            break

    print("\n" + "=" * 65)
    print("  RESULTS & STRUCTURED FEEDBACK LOG")
    print("=" * 65)
    print(f"  Final best {metric_name}: {best_metric:.3f}\n")

    for h in history:
        if "feedback" not in h:
            continue
        fb = h["feedback"]
        print(f"  Step {h['step']} [{h['action']:8}] -- {fb.get('severity', '?')}, "
              f"confidence {fb.get('confidence', 0):.0%}")
        print(f"    {(fb.get('fix_suggestion') or '')[:100]}")
        if fb.get("pattern_detected"):
            print(f"    Pattern: {fb['pattern_detected']}")

    return {
        "task": task_name,
        "metric_name": metric_name,
        "higher_is_better": higher_is_better,
        "baseline_metric": baseline_metric,
        "best_metric": best_metric,
        "final_code": current_code,
        "history": history,
        "iterations": iterations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, support")
    parser.add_argument("--iters", type=int, default=5)
    args = parser.parse_args()
    run(iterations=args.iters, task_name=args.task)
