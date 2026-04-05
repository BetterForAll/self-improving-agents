"""
Experiment Runner for Arena Loop
=================================
Runs the arena (code agents vs test agents) with real-time logging.
Each round is checkpointed -- resumable if interrupted.

WARNING: This makes many LLM calls (~60-80 per full run). Monitor costs.

Usage:
    python experiment.py                          # defaults (4 agents, 6 rounds)
    python experiment.py --code 2 --test 2 --rounds 4   # smaller run
    python experiment.py --task email_validation  # email validation task
"""

import argparse
import json
import os
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, ".."))

from tasks.checkpoint import save_checkpoint, load_latest_checkpoint, save_final, is_in_progress, clean_results

import run as arena_run
import code_agent
import test_agent


RESULTS_DIR = os.path.join(DIR, "results")


def get_results_dir(task_name):
    return os.path.join(RESULTS_DIR, task_name)


def save_solution(task_name, filename, code):
    sol_dir = os.path.join(RESULTS_DIR, task_name, "solutions")
    os.makedirs(sol_dir, exist_ok=True)
    with open(os.path.join(sol_dir, filename), "w", encoding="utf-8") as f:
        f.write(code)


def save_tests(task_name, filename, test_suite):
    test_dir = os.path.join(RESULTS_DIR, task_name, "tests")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, filename), "w") as f:
        json.dump(test_suite, f, indent=2)


def save_agent_code(task_name, agent_id, propose_source):
    if not propose_source:
        return
    agent_dir = os.path.join(RESULTS_DIR, task_name, "agent_code")
    os.makedirs(agent_dir, exist_ok=True)
    with open(os.path.join(agent_dir, f"{agent_id}_propose.py"), "w", encoding="utf-8") as f:
        f.write(propose_source)


def run_experiment(n_code=4, n_test=4, n_rounds=6, resume=True, task_name="snake", run_id=None):
    if run_id is None:
        run_id = "run_" + time.strftime("%Y%m%d_%H%M%S")
    import llm as llm_module
    llm_module.reset_token_usage()

    results_dir = get_results_dir(task_name)

    if not resume:
        clean_results(results_dir)
    os.makedirs(results_dir, exist_ok=True)

    # Check for resumable checkpoint
    start_from = 0
    resume_state = None
    history = []

    if resume:
        checkpoint = load_latest_checkpoint(results_dir)
        if checkpoint:
            step_num, state, code_files = checkpoint
            cfg = state.get("config", {})
            same_config = (
                cfg.get("code_agents") == n_code
                and cfg.get("test_agents") == n_test
                and cfg.get("rounds") == n_rounds
                and state.get("task", "snake") == task_name
            )
            if same_config and step_num < n_rounds:
                start_from = step_num
                history = state.get("history", [])
                # Reconstruct agent objects from serialized dicts
                ca_data = state.get("code_agents_full", [])
                ta_data = state.get("test_agents_full", [])
                resume_state = {
                    "code_agents": ca_data,
                    "test_agents": ta_data,
                    "code_map": state.get("code_map", {}),
                    "test_suite": state.get("test_suite"),
                    "global_best_code": state.get("global_best_code", ""),
                    "global_best_metric": state.get("global_best_metric"),
                    "baseline_metric": state.get("baseline_metric"),
                }
                # Load best code from file if available
                best_code = code_files.get("best.py", "")
                if best_code:
                    resume_state["global_best_code"] = best_code
                print(f"Resuming experiment from round {start_from + 1}/{n_rounds}...\n")

    start = time.time()

    # Track per-agent accepts/rejects across all rounds
    agent_stats = {"accepted": 0, "rejected": 0, "errors": 0}

    def on_agent_step(agent_step):
        round_num = agent_step["round"]
        agent_id = agent_step["agent_id"]
        code = agent_step.get("code", "")
        if code:
            save_solution(task_name, f"round_{round_num:02d}_{agent_id}.py", code)
        action = agent_step["action"]
        if action == "ACCEPTED":
            agent_stats["accepted"] += 1
        elif action == "REJECTED":
            agent_stats["rejected"] += 1
        else:
            agent_stats["errors"] += 1
        print(f"    >> Saved {agent_id} ({action}, {agent_step['new_metric']:.3f})")

    def on_step(step):
        round_num = step["step"]
        # Save code to file, not JSON
        code = step.pop("global_best_code", "")
        if code:
            save_solution(task_name, f"round_{round_num:02d}_best.py", code)
            save_solution(task_name, "best.py", code)
        # Save test suite to file for adversarial tasks
        test_suite_data = step.pop("test_suite", None)
        if test_suite_data:
            save_tests(task_name, f"round_{round_num:02d}_tests.json", test_suite_data)
            save_tests(task_name, "final_tests.json", test_suite_data)

        # Save agent code versions
        for a in step.get("code_agents_full", []):
            save_agent_code(task_name, a.get("agent_id", ""), a.get("propose_source", ""))

        history.append(step)

        # Build checkpoint state
        checkpoint_state = {
            "task": task_name,
            "run_id": run_id,
            "config": {"code_agents": n_code, "test_agents": n_test, "rounds": n_rounds},
            "history": history,
            "global_best_code": code,
            "global_best_metric": step["proposed_metric"],
            "baseline_metric": step.get("baseline_metric", step["previous_metric"]),
            "code_agents_full": step.get("code_agents_full", []),
            "test_agents_full": step.get("test_agents_full", []),
            "code_map": step.get("code_map", {}),
            "test_suite": test_suite_data,
        }
        code_files = {"best.py": code} if code else None
        save_checkpoint(results_dir, round_num, checkpoint_state, code_files)

        print(f"  >> Checkpoint saved (round {round_num}/{n_rounds},"
              f" best_metric={step['proposed_metric']:.3f},"
              f" pre_expansion={step.get('pre_expansion_metric', 'N/A')},"
              f" suite={step['test_suite_size']} cases)")

    results = arena_run.run_arena(
        n_code=n_code,
        n_test=n_test,
        n_rounds=n_rounds,
        on_step=on_step,
        on_agent_step=on_agent_step,
        start_from=start_from,
        resume_state=resume_state,
        task_name=task_name,
    )

    elapsed = time.time() - start

    if results is None:
        print("\nExperiment failed.")
        return

    metric_name = results["metric_name"]
    higher_is_better = results.get("higher_is_better")

    # Build final log
    log = {
        "status": "completed",
        "run_id": run_id,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 1),
        "task": results.get("task", task_name),
        "metric_name": metric_name,
        "higher_is_better": higher_is_better,
        "baseline_metric": results.get("baseline_metric"),
        "best_metric": results["best_metric"],
        "iterations": n_rounds,
        "accepted": agent_stats["accepted"],
        "rejected": agent_stats["rejected"],
        "errors": agent_stats["errors"],
        "config": {"code_agents": n_code, "test_agents": n_test, "rounds": n_rounds},
        "test_suite_size": results["test_suite_size"],
        "final_code_agents": results["code_agents"],
        "final_test_agents": results["test_agents"],
        "history": history,
    }

    if results.get("final_code"):
        save_solution(task_name, "best.py", results["final_code"])

    # Token usage and cost
    usage = llm_module.get_token_usage()
    log["token_usage"] = usage
    log["estimated_cost_usd"] = round(
        usage["prompt_tokens"] * 0.30 / 1_000_000 +
        usage["completion_tokens"] * 2.50 / 1_000_000, 4
    )

    save_final(results_dir, log)

    # Print summary
    print("\n")
    print("=" * 70)
    print("  EXPERIMENT SUMMARY")
    print("=" * 70)
    print(f"  Task              : {log.get('task', 'snake')}")
    print(f"  Metric            : {metric_name}")
    print(f"  Duration          : {log['elapsed_seconds']} seconds")
    print(f"  Rounds            : {n_rounds}")
    print(f"  Code agents       : {n_code}")
    print(f"  Test agents       : {n_test}")
    print(f"  Best metric       : {log['best_metric']:.3f} {metric_name}")
    print(f"  Test suite grew   : 1 -> {log['test_suite_size']} cases")
    print(f"  LLM calls         : {usage['calls']}")
    print(f"  Tokens            : {usage['total_tokens']:,} ({usage['prompt_tokens']:,} in, {usage['completion_tokens']:,} out)")
    print(f"  Est. cost         : ${log['estimated_cost_usd']:.4f}")

    # Agent rankings
    print(f"\n  Code agent rankings (by wins):")
    for a in sorted(log["final_code_agents"], key=lambda x: -x["wins"]):
        print(f"    {a['id']:10}  wins={a['wins']}  gen={a['gen']}"
              f"  strategy={a['strategy'][:50]}...")

    print(f"\n  Test agent rankings (by wins):")
    for a in sorted(log["final_test_agents"], key=lambda x: -x["wins"]):
        print(f"    {a['id']:10}  wins={a['wins']}  gen={a['gen']}"
              f"  strategy={a['strategy'][:50]}...")

    # Round-by-round progress
    print(f"\n  Round-by-round:")
    for r in log["history"]:
        t_marker = "  [T]" if r.get("tournament") else "     "
        pre_exp = r.get("pre_expansion_metric")
        pre_str = f"  pre_exp={pre_exp:.3f}" if pre_exp is not None else ""
        print(f"    round {r['step']:2}{t_marker}  best={r['proposed_metric']:.3f} {metric_name}"
              f"{pre_str}  suite={r['test_suite_size']}")

    # Conclusions
    print(f"\n  Conclusions:")

    max_gen_code = max((a["gen"] for a in log["final_code_agents"]), default=0)
    max_gen_test = max((a["gen"] for a in log["final_test_agents"]), default=0)
    if max_gen_code > 0 or max_gen_test > 0:
        print(f"    - Evolution occurred: code agents reached gen {max_gen_code}, "
              f"test agents reached gen {max_gen_test}.")
    else:
        print(f"    - No evolution -- all original agents survived every tournament.")

    if log["test_suite_size"] > n_rounds:
        print(f"    - Test suite grew to {log['test_suite_size']} cases -- "
              f"test agents successfully proposed harder inputs.")
    else:
        print(f"    - Test suite barely grew -- test agents may need better strategies.")

    if log["final_code_agents"]:
        top_code = sorted(log["final_code_agents"], key=lambda x: -x["wins"])[0]
        if top_code["wins"] > n_rounds / 2:
            print(f"    - Dominant code strategy: \"{top_code['strategy'][:60]}...\" "
                  f"({top_code['wins']} wins)")

    if log["final_test_agents"]:
        top_test = sorted(log["final_test_agents"], key=lambda x: -x["wins"])[0]
        if top_test["wins"] > n_rounds / 2:
            print(f"    - Dominant test strategy: \"{top_test['strategy'][:60]}...\" "
                  f"({top_test['wins']} wins)")

    # Arms race analysis
    if len(log["history"]) >= 2:
        first_val = log["history"][0]["proposed_metric"]
        last_val = log["history"][-1]["proposed_metric"]
        if last_val != first_val:
            pct = abs(last_val - first_val) / max(abs(first_val), 1e-9) * 100
            print(f"    - Arms race is working: best metric changed {pct:.1f}% "
                  f"over the run ({first_val:.3f} -> {last_val:.3f} {metric_name}).")
        else:
            print(f"    - No improvement in best metric over rounds -- "
                  f"adversarial pressure may need more rounds to show effect.")

    log_file = os.path.join(results_dir, "experiment-log.json")
    print(f"\n  Results saved to: {log_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Arena Loop experiment")
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, email_validation, support")
    parser.add_argument("--code", type=int, default=4, help="Number of code agents")
    parser.add_argument("--test", type=int, default=4, help="Number of test agents")
    parser.add_argument("--rounds", type=int, default=6, help="Number of rounds")
    parser.add_argument("--fresh", action="store_true", help="Ignore previous results, start fresh")
    parser.add_argument("--run-id", default=None, help="Run ID from run_all.py")
    args = parser.parse_args()
    run_experiment(n_code=args.code, n_test=args.test, n_rounds=args.rounds,
                   resume=not args.fresh, task_name=args.task, run_id=args.run_id)
