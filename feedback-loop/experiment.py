"""
Experiment Runner for Feedback Loop
====================================
Runs the asymmetric review loop with real-time logging.
Each step is saved to JSON immediately -- resumable if interrupted.

Focus: demonstrates the value of structured reviewer feedback.

Usage:
    python experiment.py              # default: 5 iterations
    python experiment.py --iters 8    # more iterations
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


def run_experiment(iterations=5, resume=True, task_name="snake", run_id=None):
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

    metric_name = None

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

        fb = step.get("feedback", {})
        sev = fb.get("severity", "?") if fb else "?"
        print(f"  >> Saved checkpoint ({step_num}/{iterations})"
              f"  reviewer=[{sev}]")

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

    # Build feedback analysis
    patterns_detected = []
    severity_counts = {"critical": 0, "major": 0, "minor": 0, "ok": 0}
    feedback_log = []
    for h in results["history"]:
        fb = h.get("feedback")
        if fb:
            sev = fb.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            if fb.get("pattern_detected"):
                patterns_detected.append(fb["pattern_detected"])
            feedback_log.append({
                "step": h["step"],
                "action": h["action"],
                "proposed_metric": h.get("proposed_metric"),
                "severity": sev,
                "issue_type": fb.get("issue_type"),
                "confidence": fb.get("confidence"),
                "pattern": fb.get("pattern_detected"),
                "suggestion": (fb.get("fix_suggestion") or "")[:200],
            })

    metric_name = results.get("metric_name", "time_ms")
    higher_is_better = results.get("higher_is_better", False)

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
    log["iterations"] = iterations
    log["accepted"] = len([h for h in results["history"] if h["action"] == "ACCEPTED"])
    log["rejected"] = len([h for h in results["history"] if h["action"] == "REJECTED"])
    log["errors"] = len([h for h in results["history"] if h["action"] == "ERROR"])

    # Token usage and cost
    usage = llm_module.get_token_usage()
    log["token_usage"] = usage
    log["estimated_cost_usd"] = round(
        usage["prompt_tokens"] * 0.30 / 1_000_000 +
        usage["completion_tokens"] * 2.50 / 1_000_000, 4
    )

    # Feedback-loop-specific keys
    log["severity_counts"] = severity_counts
    log["patterns_detected"] = patterns_detected
    log["feedback_log"] = feedback_log
    if not higher_is_better and results.get("baseline_metric") and results["best_metric"] > 0:
        log["speedup"] = round(results["baseline_metric"] / results["best_metric"], 1)
    else:
        log["speedup"] = None
    save_final(results_path, log)

    # Print summary
    print("\n")
    print("=" * 65)
    print("  EXPERIMENT SUMMARY")
    print("=" * 65)
    print(f"  Task           : {log.get('task', 'snake')}")
    print(f"  Metric         : {metric_name}")
    print(f"  Duration       : {log['elapsed_seconds']} seconds")
    print(f"  Iterations     : {log['iterations']}")
    baseline = log.get('baseline_metric')
    best = log.get('best_metric')
    print(f"  Baseline       : {baseline:.3f}" if baseline is not None else "  Baseline       : N/A")
    print(f"  Best achieved  : {best:.3f}" if best is not None else "  Best achieved  : N/A")
    if log.get("speedup") is not None:
        print(f"  Speedup        : {log['speedup']}x")
    print(f"  Accepted       : {log['accepted']}")
    print(f"  Rejected       : {log['rejected']}")
    print(f"  Errors         : {log['errors']}")
    print(f"  LLM calls      : {usage['calls']}")
    print(f"  Tokens         : {usage['total_tokens']:,} ({usage['prompt_tokens']:,} in, {usage['completion_tokens']:,} out)")
    print(f"  Est. cost      : ${log['estimated_cost_usd']:.4f}")

    # Reviewer feedback analysis
    print(f"\n  Reviewer feedback analysis:")
    print(f"    Severity distribution: {severity_counts}")
    if patterns_detected:
        print(f"    Patterns detected: {patterns_detected}")
    else:
        print(f"    No cross-step patterns detected by reviewer")

    # Step-by-step with feedback
    print(f"\n  Step-by-step with reviewer feedback:")
    for entry in feedback_log:
        marker = "+" if entry["action"] == "ACCEPTED" else "x"
        conf = entry["confidence"] if entry["confidence"] is not None else 0.0
        print(f"    [{marker}] step {entry['step']}: [{entry['severity']:8}] "
              f"confidence={conf:.0%}")
        print(f"        {entry['suggestion'][:80]}...")
        if entry["pattern"]:
            print(f"        Pattern: {entry['pattern']}")

    # Conclusions
    print(f"\n  Conclusions:")
    if patterns_detected:
        unique_patterns = list(set(patterns_detected))
        print(f"    - Reviewer detected {len(patterns_detected)} pattern(s): {unique_patterns}")
        print(f"    - This demonstrates the value of full-context review -- "
              f"a memoryless reviewer would miss these.")
    else:
        print(f"    - No patterns detected. May need more iterations for patterns to emerge.")

    high_confidence = [e for e in feedback_log if (e.get("confidence") or 0) >= 0.9]
    if high_confidence:
        print(f"    - Reviewer gave high-confidence (>=90%) feedback on "
              f"{len(high_confidence)}/{len(feedback_log)} steps.")

    if log.get("speedup") is not None and log["speedup"] > 100:
        print(f"    - Massive {log['speedup']}x speedup -- task may be too easy.")
        print(f"    - Structured feedback is most valuable on harder tasks where "
              f"the reviewer can guide the worker past plateaus.")

    print(f"\n  Results saved to: {get_log_file(task_name)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Feedback loop experiment")
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, support")
    parser.add_argument("--iters", type=int, default=5, help="Number of iterations")
    parser.add_argument("--fresh", action="store_true", help="Ignore previous results, start fresh")
    parser.add_argument("--run-id", default=None, help="Run ID from run_all.py")
    args = parser.parse_args()
    run_experiment(iterations=args.iters, resume=not args.fresh, task_name=args.task,
                   run_id=args.run_id)
