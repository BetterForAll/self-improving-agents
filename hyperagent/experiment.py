"""
Experiment Runner for HyperAgent Loop
======================================
Runs the code-rewriting self-improvement loop with real-time logging.
Each generation is checkpointed -- resumable if interrupted.

Usage:
    python experiment.py                    # default: snake
    python experiment.py --task support     # Customer support (LLM-as-judge)
    python experiment.py --task      # Sorting optimization
    python experiment.py --gens 4           # custom generation count
"""

import argparse
import json
import os
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, ".."))
from tasks.checkpoint import save_checkpoint, load_latest_checkpoint, save_final, is_in_progress, clean_results

import run

RESULTS_DIR = os.path.join(DIR, "results")


def save_solution(task_name, filename, code):
    sol_dir = os.path.join(RESULTS_DIR, task_name, "solutions")
    os.makedirs(sol_dir, exist_ok=True)
    with open(os.path.join(sol_dir, filename), "w", encoding="utf-8") as f:
        f.write(code)


def run_experiment(generations=6, inner_iters=3, resume=True, task_name="snake", run_id=None):
    if run_id is None:
        run_id = "run_" + time.strftime("%Y%m%d_%H%M%S")
    import llm as llm_module
    llm_module.reset_token_usage()

    results_path = os.path.join(RESULTS_DIR, task_name)

    if not resume:
        clean_results(results_path)
    os.makedirs(results_path, exist_ok=True)

    # Check for resumable state
    start_from = 0
    resume_state = None

    if resume and is_in_progress(results_path):
        loaded = load_latest_checkpoint(results_path)
        if loaded:
            start_from, resume_state, code_files = loaded
            resume_state["current_code"] = code_files.get("best.py", "")
            print(f"Resuming experiment from generation {start_from + 1}/{generations}...\n")

    start = time.time()

    # Accumulate history for checkpointing
    accumulated_history = list(resume_state["history"]) if resume_state else []
    accumulated_gen_log = list(resume_state.get("generation_log", [])) if resume_state else []
    baseline_holder = [resume_state["baseline_metric"]] if resume_state else [None]

    def on_step(step):
        if step.get("type") == "task_step":
            step_num = step.get("step", 0)
            code = step.pop("code", "")
            step.pop("llm_response", None)
            if code:
                save_solution(task_name, f"iter_{step_num:02d}.py", code)
            if step.get("action") == "ACCEPTED" and code:
                save_solution(task_name, "best.py", code)
            accumulated_history.append(step)

        elif step.get("type") == "generation":
            gen_id = step.get("gen_id", 0)
            best_metric = step.get("best_metric", 0)
            accumulated_gen_log.append(step)

            # Read current agent files for checkpoint
            _, agent_code_dir, generations_dir = run._task_dirs(task_name)
            agent_files = run.read_agent_files(agent_code_dir)
            code_files = {}
            best_path = os.path.join(RESULTS_DIR, task_name, "solutions", "best.py")
            if os.path.exists(best_path):
                with open(best_path) as f:
                    code_files["best.py"] = f.read()
            for fname, source in agent_files.items():
                code_files[fname] = source

            checkpoint_state = {
                "generation": gen_id,
                "run_id": run_id,
                "best_metric": best_metric,
                "baseline_metric": baseline_holder[0] or best_metric,
                "last_valid_gen": run.find_last_valid_gen(generations_dir),
                "history": accumulated_history,
                "generation_log": accumulated_gen_log,
            }
            save_checkpoint(results_path, gen_id, checkpoint_state, code_files)

            valid_str = "VALID" if step.get("valid") else "FAILED"
            files_str = ", ".join(step.get("files_changed", [])) or "no changes"
            print(f"  >> Checkpoint saved (gen {gen_id}, {valid_str}, {files_str})")

    results = run.run(
        total_generations=generations,
        inner_iters=inner_iters,
        on_step=on_step,
        start_from=start_from,
        resume_state=resume_state,
        task_name=task_name,
    )

    elapsed = time.time() - start

    if results is None:
        final_log = {"status": "failed", "task": task_name}
        save_final(results_path, final_log)
        print("\nExperiment failed -- baseline could not run.")
        return

    baseline_holder[0] = results["baseline_metric"]

    metric_name = results["metric_name"]
    higher_is_better = results["higher_is_better"]
    task_steps = [h for h in results["history"] if h.get("type") == "task_step"]
    generation_log = results.get("generation_log", [])

    if results.get("final_code"):
        save_solution(task_name, "best.py", results["final_code"])

    # Token usage
    usage = llm_module.get_token_usage()

    final_log = {
        "status": "completed",
        "run_id": run_id,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 1),
        "task": task_name,
        "metric_name": metric_name,
        "higher_is_better": higher_is_better,
        "baseline_metric": results["baseline_metric"],
        "best_metric": results["best_metric"],
        "iterations": len(task_steps),
        "generations": results["total_generations"],
        "accepted": len([h for h in task_steps if h.get("action") == "ACCEPTED"]),
        "rejected": len([h for h in task_steps if h.get("action") == "REJECTED"]),
        "errors": len([h for h in task_steps if h.get("action") == "ERROR"]),
        "valid_generations": len([g for g in generation_log if g.get("valid")]),
        "code_modifications": len([g for g in generation_log if g.get("files_changed")]),
        "last_valid_gen": results["last_valid_gen"],
        "generation_log": generation_log,
        "history": [{k: v for k, v in h.items() if k not in ("code", "llm_response")}
                    for h in results["history"]],
        "token_usage": usage,
        "estimated_cost_usd": round(
            usage["prompt_tokens"] * 0.30 / 1_000_000 +
            usage["completion_tokens"] * 2.50 / 1_000_000, 4
        ),
    }
    save_final(results_path, final_log)

    # Print summary
    print("\n")
    print("=" * 65)
    print("  EXPERIMENT SUMMARY")
    print("=" * 65)
    print(f"  Task                : {task_name}")
    print(f"  Metric              : {metric_name} ({'higher' if higher_is_better else 'lower'} is better)")
    print(f"  Duration            : {final_log['elapsed_seconds']} seconds")
    print(f"  Generations         : {final_log['generations']}")
    print(f"  Baseline            : {final_log['baseline_metric']:.3f} {metric_name}")
    print(f"  Best achieved       : {final_log['best_metric']:.3f} {metric_name}")
    print(f"  Code improvements   : {final_log['accepted']} accepted, {final_log['rejected']} rejected")
    print(f"  Agent code modified : {final_log['code_modifications']} times ({final_log['valid_generations']} valid)")
    print(f"  LLM calls           : {usage['calls']}")
    print(f"  Tokens              : {usage['total_tokens']:,}")
    print(f"  Est. cost           : ${final_log['estimated_cost_usd']:.4f}")

    # Generation history
    print(f"\n  Generation history:")
    for i, g in enumerate(generation_log):
        status = "VALID" if g.get("valid") else "FAILED"
        changed = g.get("files_changed", [])
        files_str = ", ".join(changed) if changed else "no changes"
        err_str = f" -- {g['error']}" if g.get("error") else ""
        print(f"    gen {i + 1}: [{status:6}] {files_str}{err_str}")

    # Task step history
    print(f"\n  Iteration-by-iteration:")
    for h in task_steps:
        marker = "+" if h["action"] == "ACCEPTED" else ("x" if h["action"] == "REJECTED" else "!")
        metric_val = h.get("proposed_metric")
        if metric_val is not None:
            print(f"    [{marker}] step {h['step']:2}: {metric_val:.3f} {metric_name}")
        else:
            print(f"    [{marker}] step {h['step']:2}: ERROR")

    print(f"\n  Results saved to: {results_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run HyperAgent experiment")
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, support, email_validation")
    parser.add_argument("--gens", type=int, default=6, help="Number of generations")
    parser.add_argument("--inner", type=int, default=3, help="Inner iterations per generation")
    parser.add_argument("--fresh", action="store_true", help="Ignore previous results, start fresh")
    parser.add_argument("--run-id", default=None, help="Run ID from run_all.py")
    args = parser.parse_args()
    run_experiment(generations=args.gens, inner_iters=args.inner,
                   resume=not args.fresh, task_name=args.task, run_id=args.run_id)
