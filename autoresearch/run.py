"""
AutoResearch Loop -- Real LLM Version
=====================================
LLM proposes code -> write to file -> run & benchmark -> keep if better -> repeat

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

DIR = os.path.dirname(os.path.abspath(__file__))


def run(iterations=6, on_step=None, start_from=0, resume_state=None, task_name="snake"):
    # on_step: called by experiment.py to save checkpoints. None when running directly.
    task = load_task(task_name)
    higher_is_better = task.HIGHER_IS_BETTER
    metric_name = task.METRIC_NAME
    solution_file = os.path.join(DIR, f"solution_{task_name}.py")

    print("=" * 60)
    print(f"  AutoResearch Loop -- {task.TASK_NAME} (Real LLM)")
    print("=" * 60)

    if resume_state:
        current_code = resume_state["current_code"]
        best_metric = resume_state["best_metric"]
        baseline_metric = resume_state["baseline_metric"]
        history = resume_state["history"]
        write_solution(current_code, solution_file)
        print(f"\n[RESUME] Resuming from iteration {start_from + 1}, best: {best_metric:.3f}\n")
    else:
        current_code = task.INITIAL_CODE
        write_solution(current_code, solution_file)
        best_metric, err = run_solution(task, solution_file, llm_module=llm)
        if err:
            print(f"Baseline failed: {err}")
            return None
        baseline_metric = best_metric
        history = []
        print(f"\n[INIT] Baseline {metric_name}: {best_metric:.3f}\n")

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

    for i in range(start_from, iterations):
        print(f"-- Iteration {i + 1}/{iterations} " + "-" * 35)

        prompt = task.build_prompt(current_code, best_metric)
        print("  Asking LLM for proposal...")
        try:
            raw_response = llm.ask(prompt)
            proposed_code = llm.extract_code(raw_response)
        except Exception as e:
            print(f"  LLM ERROR: {e} -- skipping iteration")
            step = {"step": i + 1, "action": "ERROR", "error": str(e)}
            history.append(step)
            if on_step:
                on_step(step)
            continue
        print(f"  LLM proposed {len(proposed_code.splitlines())} lines")

        write_solution(proposed_code, solution_file)
        new_metric, err = run_solution(task, solution_file, llm_module=llm)

        if err or new_metric is None:
            err_msg = err or "Benchmark returned no metric"
            print(f"  ERROR: {err_msg} -- reverting")
            write_solution(current_code, solution_file)
            step = {"step": i + 1, "action": "ERROR", "error": err_msg}
            history.append(step)
            if on_step:
                on_step(step)
            continue

        print(f"  Proposed {metric_name}: {new_metric:.3f}  |  Current best: {best_metric:.3f}")

        if is_better(new_metric, best_metric):
            pct = improvement_pct(new_metric, best_metric)
            print(f"  + ACCEPTED  ({pct:.1f}% better)")
            step = {
                "step": i + 1,
                "action": "ACCEPTED",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "improvement": f"{pct:.1f}% better",
                "code": proposed_code,
                "llm_response": raw_response,
            }
            history.append(step)
            current_code = proposed_code
            best_metric = new_metric
        else:
            direction = "worse" if higher_is_better else "slower"
            print(f"  x REJECTED  ({direction} -- reverting)")
            write_solution(current_code, solution_file)
            step = {
                "step": i + 1,
                "action": "REJECTED",
                "reason": f"worse than current best",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "code": proposed_code,
                "llm_response": raw_response,
            }
            history.append(step)

        if on_step:
            on_step(step)

        if is_perfect(best_metric):
            print(f"\n  PERFECT SCORE reached ({best_metric:.3f}). Stopping early.")
            break

    print("\n" + "=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)
    accepted = [h for h in history if h["action"] == "ACCEPTED"]
    rejected = [h for h in history if h["action"] == "REJECTED"]
    errors = [h for h in history if h["action"] == "ERROR"]
    print(f"  Accepted: {len(accepted)}  |  Rejected: {len(rejected)}  |  Errors: {len(errors)}")
    print(f"  Final best {metric_name}: {best_metric:.3f}")
    if accepted:
        print(f"\n  Improvement history:")
        for h in accepted:
            val = h.get("proposed_metric", 0)
            print(f"    step {h['step']}: {metric_name}={val:.3f}  ({h['improvement']})")
    print(f"\n  Final code:\n")
    for line in current_code.strip().splitlines():
        print(f"    {line}")

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
    parser.add_argument("--iters", type=int, default=6)
    args = parser.parse_args()
    run(iterations=args.iters, task_name=args.task)
