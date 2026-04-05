"""
Experiment Runner for AutoResearch Loop
=======================================
Runs the self-improving loop with real-time logging.
Each iteration is saved to JSON immediately -- resumable if interrupted.

Usage:
    python experiment.py              # default: snake, 6 iterations
    python experiment.py --iters 10   # custom iteration count
    python experiment.py --task support  # Customer support (LLM-as-judge)
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import run
from tasks.checkpoint import save_checkpoint, load_latest_checkpoint, save_final, is_in_progress, clean_results

DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(DIR, "results")


def get_log_file(task_name):
    return os.path.join(RESULTS_DIR, task_name, "experiment-log.json")



def save_solution(task_name, filename, code):
    sol_dir = os.path.join(RESULTS_DIR, task_name, "solutions")
    os.makedirs(sol_dir, exist_ok=True)
    with open(os.path.join(sol_dir, filename), "w") as f:
        f.write(code)


def run_experiment(iterations=6, resume=True, task_name="snake", run_id=None):
    if run_id is None:
        run_id = "run_" + time.strftime("%Y%m%d_%H%M%S")
    import llm as llm_module
    llm_module.reset_token_usage()

    # Check for resumable state
    start_from = 0
    resume_state = None
    results_path = os.path.join(RESULTS_DIR, task_name)

    if not resume:
        clean_results(results_path)
    os.makedirs(results_path, exist_ok=True)

    if resume and is_in_progress(results_path):
        loaded = load_latest_checkpoint(results_path)
        if loaded:
            start_from, resume_state, code_files = loaded
            resume_state["current_code"] = code_files.get("best.py", "")
            print(f"Resuming from step {start_from + 1}...")

    # Initialize log
    if resume_state:
        log = {
            "status": "in_progress",
            "run_id": run_id,
            "task": task_name,
            "metric_name": None,
            "higher_is_better": None,
            "baseline_metric": resume_state.get("baseline_metric"),
            "best_metric": resume_state.get("best_metric"),
            "iterations": iterations,
            "history": resume_state.get("history", []),
        }
    else:
        log = {
            "status": "in_progress",
            "run_id": run_id,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "task": task_name,
            "metric_name": None,
            "higher_is_better": None,
            "baseline_metric": None,
            "best_metric": None,
            "iterations": iterations,
            "history": [],
        }

    start = time.time()

    def on_step(step):
        step_num = step.get("step", 0)
        code = step.pop("code", "")
        step.pop("llm_response", None)

        # Save solution files
        if code:
            save_solution(task_name, f"iter_{step_num:02d}.py", code)

        log["history"].append(step)

        if step.get("action") == "ACCEPTED":
            log["best_metric"] = step.get("proposed_metric")

        # Checkpoint
        checkpoint_state = {
            "step": step_num,
            "run_id": run_id,
            "best_metric": log.get("best_metric"),
            "baseline_metric": log.get("baseline_metric"),
            "history": log["history"],
        }
        code_files = {"best.py": code} if code and step.get("action") == "ACCEPTED" else {}
        save_checkpoint(results_path, step_num, checkpoint_state, code_files if code_files else None)

        print(f"  >> Saved checkpoint ({step_num}/{iterations})")

    results = run.run(
        iterations=iterations,
        on_step=on_step,
        start_from=start_from,
        resume_state=resume_state,
        task_name=task_name,
    )

    elapsed = time.time() - start

    if results is None:
        log["status"] = "failed"
        save_final(results_path, log)
        print("\nExperiment failed -- baseline could not run.")
        return

    metric_name = results["metric_name"]
    higher_is_better = results["higher_is_better"]

    # Finalize log
    log["status"] = "completed"
    log["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    log["elapsed_seconds"] = round(elapsed, 1)
    log["task"] = results.get("task", task_name)
    log["metric_name"] = metric_name
    log["higher_is_better"] = higher_is_better
    log["baseline_metric"] = results["baseline_metric"]
    log["best_metric"] = results["best_metric"]
    if results.get("final_code"):
        save_solution(task_name, "best.py", results["final_code"])
    log["accepted"] = len([h for h in log["history"] if h.get("action") == "ACCEPTED"])
    log["rejected"] = len([h for h in log["history"] if h.get("action") == "REJECTED"])
    log["errors"] = len([h for h in log["history"] if h.get("action") == "ERROR"])

    # Token usage and cost
    usage = llm_module.get_token_usage()
    log["token_usage"] = usage
    log["estimated_cost_usd"] = round(
        usage["prompt_tokens"] * 0.30 / 1_000_000 +
        usage["completion_tokens"] * 2.50 / 1_000_000, 4
    )
    save_final(results_path, log)

    # Print summary
    print("\n")
    print("=" * 60)
    print("  EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"  Task           : {log.get('task', 'snake')}")
    print(f"  Metric         : {metric_name} ({'higher' if higher_is_better else 'lower'} is better)")
    print(f"  Duration       : {log['elapsed_seconds']} seconds")
    print(f"  Iterations     : {log['iterations']}")
    print(f"  Baseline       : {log['baseline_metric']:.3f} {metric_name}")
    print(f"  Best achieved  : {log['best_metric']:.3f} {metric_name}")
    print(f"  Accepted       : {log['accepted']}")
    print(f"  Rejected       : {log['rejected']}")
    print(f"  Errors         : {log['errors']}")
    print(f"  LLM calls      : {usage['calls']}")
    print(f"  Tokens         : {usage['total_tokens']:,} ({usage['prompt_tokens']:,} in, {usage['completion_tokens']:,} out)")
    print(f"  Est. cost      : ${log['estimated_cost_usd']:.4f}")

    # Iteration-by-iteration
    print(f"\n  Iteration-by-iteration:")
    for h in log["history"]:
        marker = "+" if h["action"] == "ACCEPTED" else ("x" if h["action"] == "REJECTED" else "!")
        metric_val = h.get("proposed_metric")
        metric_str = f"{metric_val:.3f} {metric_name}" if metric_val is not None else "ERROR"
        if h["action"] == "ACCEPTED":
            detail = f"  ({h.get('improvement', '')})"
        elif h["action"] == "REJECTED":
            detail = f"  ({h.get('reason', '')})"
        else:
            detail = ""
        print(f"    [{marker}] step {h['step']:2}: {metric_str}{detail}")

    # Conclusions
    print(f"\n  Conclusions:")
    if log["accepted"] == 0:
        print("    - No improvements found. The LLM could not beat the baseline.")
    else:
        if not higher_is_better and log["best_metric"] > 0:
            ratio = round(log["baseline_metric"] / log["best_metric"], 1)
        elif higher_is_better and log["baseline_metric"] > 0:
            ratio = round(log["best_metric"] / log["baseline_metric"], 1)
        else:
            ratio = float("inf")

        if ratio > 100:
            print(f"    - Massive {ratio}x improvement -- LLM found an algorithmic jump.")
            print(f"    - Task may be too easy (solved by known algorithms).")
        elif ratio > 2:
            print(f"    - Solid {ratio}x improvement over {log['iterations']} iterations.")
        else:
            print(f"    - Marginal improvement ({ratio}x). Baseline may be near-optimal.")

    if log["errors"] > log["iterations"] * 0.3:
        print(f"    - High error rate ({log['errors']}/{log['iterations']}). "
              f"LLM producing unparseable or incorrect code.")

    first_accept = next((h for h in log["history"] if h["action"] == "ACCEPTED"), None)
    if first_accept and first_accept["step"] == 1:
        print(f"    - Solved in first iteration -- consider a harder task.")

    print(f"\n  Results saved to: {get_log_file(task_name)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutoResearch loop experiment")
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, support")
    parser.add_argument("--iters", type=int, default=6, help="Number of iterations")
    parser.add_argument("--fresh", action="store_true", help="Ignore previous results, start fresh")
    parser.add_argument("--run-id", default=None, help="Run ID from run_all.py")
    args = parser.parse_args()
    run_experiment(iterations=args.iters, resume=not args.fresh, task_name=args.task,
                   run_id=args.run_id)
