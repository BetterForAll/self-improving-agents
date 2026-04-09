"""
Run all experiments across all 4 levels, then generate the comparison analysis.

Experiments run IN PARALLEL for speed -- each level+task combo is independent.

This is the single entry point to reproduce everything:
    python run_all.py

Options:
    python run_all.py --tasks snake support          # specific tasks only
    python run_all.py --levels autoresearch hyperagent  # specific levels only
    python run_all.py --skip-analysis                # skip the final LLM analysis step
    python run_all.py --skip-cross-validation        # skip cross-validation
    python run_all.py --fresh                        # ignore previous results, start clean
    python run_all.py --sequential                   # run one at a time (less API pressure)
    python run_all.py --scale 2                      # 2x iterations/rounds (for deeper runs)
"""

import argparse
import json
import os
import subprocess
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(DIR, "results")
LOCK_FILE = os.path.join(RESULTS_DIR, ".lock")
REGISTRY_FILE = os.path.join(RESULTS_DIR, "registry.json")

LEVELS = {
    "autoresearch": {
        "name": "AutoResearch Loop",
        "script": os.path.join(DIR, "autoresearch", "experiment.py"),
        "default_args": ["--iters", "10"],
    },
    "feedback-loop": {
        "name": "Feedback Loop",
        "script": os.path.join(DIR, "feedback-loop", "experiment.py"),
        "default_args": ["--iters", "10"],
    },
    "hyperagent": {
        "name": "HyperAgent Loop",
        "script": os.path.join(DIR, "hyperagent", "experiment.py"),
        "default_args": ["--gens", "4"],
    },
    "arena-single": {
        "name": "Arena Single",
        "script": os.path.join(DIR, "arena-loop", "experiment.py"),
        "default_args": ["--rounds", "6", "--code", "1", "--test", "1", "--label", "single"],
    },
    "arena-loop": {
        "name": "Arena Loop",
        "script": os.path.join(DIR, "arena-loop", "experiment.py"),
        "default_args": ["--rounds", "6"],
    },
}

ALL_TASKS = ["snake", "support", "email_validation"]


def acquire_lock(run_id):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            existing_id = f.read().strip()
        print(f"ERROR: Lock file exists -- another run is in progress ({existing_id})")
        print(f"  Lock file: {LOCK_FILE}")
        print(f"  If the previous run crashed, delete the lock file and retry.")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write(run_id)


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return []


def save_registry(registry):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def collect_experiment_result(level_key, task):
    log_path = os.path.join(DIR, level_key, "results", task, "experiment-log.json")
    if not os.path.exists(log_path):
        return {"level": level_key, "task": task, "status": "missing"}
    with open(log_path) as f:
        log = json.load(f)
    return {
        "level": level_key,
        "task": task,
        "status": log.get("status", "unknown"),
        "best_metric": log.get("best_metric"),
        "cost_usd": log.get("estimated_cost_usd", 0),
    }


def scale_args(default_args, scale):
    """Apply scale multiplier to numeric args (--iters, --gens, --rounds)."""
    if scale == 1.0:
        return list(default_args)
    scaled = list(default_args)
    scalable = {"--iters", "--gens", "--rounds"}
    for i, arg in enumerate(scaled):
        if arg in scalable and i + 1 < len(scaled):
            scaled[i + 1] = str(max(1, int(int(scaled[i + 1]) * scale)))
    return scaled


def build_cmd(level_info, task, fresh, run_id, scale=1.0):
    cmd = (
        [sys.executable, level_info["script"], "--task", task]
        + scale_args(level_info["default_args"], scale)
        + ["--run-id", run_id]
    )
    if fresh:
        cmd.append("--fresh")
    return cmd


def run_sequential(jobs, fresh, run_id, scale=1.0):
    """Run experiments one at a time."""
    results = []
    for level_key, level_info, task in jobs:
        print(f"\n{'=' * 70}")
        print(f"  {level_info['name']} -- {task}")
        print(f"{'=' * 70}\n")

        cmd = build_cmd(level_info, task, fresh, run_id, scale)
        start = time.time()
        result = subprocess.run(cmd, cwd=DIR)
        elapsed = time.time() - start

        ok = result.returncode == 0
        status = "OK" if ok else "FAILED"
        print(f"\n  [{status}] {level_info['name']} / {task} -- {elapsed:.0f}s\n")
        results.append((level_key, task, ok))
    return results


def run_parallel(jobs, fresh, run_id, scale=1.0):
    """Run all experiments in parallel, report as they finish."""
    # Create log directory for each experiment's output
    log_dir = os.path.join(RESULTS_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    processes = []
    for level_key, level_info, task in jobs:
        cmd = build_cmd(level_info, task, fresh, run_id, scale)
        print(f"  Starting: {level_info['name']} / {task}")
        # Write each experiment's output to a log file (not a pipe)
        # This avoids pipe buffer deadlock when experiments print a lot
        log_file = os.path.join(log_dir, f"{level_key}_{task}.log")
        fh = open(log_file, "w")
        proc = subprocess.Popen(cmd, cwd=DIR, stdout=fh, stderr=subprocess.STDOUT)
        processes.append((level_key, level_info["name"], task, proc, time.time(), fh))

    print(f"\n  {len(processes)} experiments running in parallel...")
    print(f"  Logs: {log_dir}/\n")

    # Wait for all to finish, report as they complete
    results = []
    remaining = list(processes)
    while remaining:
        for entry in remaining[:]:
            level_key, name, task, proc, start, fh = entry
            retcode = proc.poll()
            if retcode is not None:
                fh.close()
                elapsed = time.time() - start
                ok = retcode == 0
                status = "OK" if ok else "FAILED"
                print(f"  [{status}] {name} / {task} -- {elapsed:.0f}s")
                results.append((level_key, task, ok))
                remaining.remove(entry)
        if remaining:
            time.sleep(2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Run all self-improving agent experiments")
    parser.add_argument("--tasks", nargs="+", default=ALL_TASKS,
                        help=f"Tasks to run (default: {' '.join(ALL_TASKS)})")
    parser.add_argument("--levels", nargs="+", default=list(LEVELS.keys()),
                        help=f"Levels to run (default: {' '.join(LEVELS.keys())})")
    parser.add_argument("--skip-analysis", action="store_true",
                        help="Skip the final analysis step")
    parser.add_argument("--skip-cross-validation", action="store_true",
                        help="Skip the cross-validation step")
    parser.add_argument("--fresh", action="store_true",
                        help="Ignore previous results, start clean")
    parser.add_argument("--sequential", action="store_true",
                        help="Run experiments one at a time (default: parallel)")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="Multiply default iterations/rounds (e.g. --scale 2 for 2x)")
    args = parser.parse_args()

    run_id = "run_" + time.strftime("%Y%m%d_%H%M%S")
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")

    acquire_lock(run_id)

    try:
        print("=" * 70)
        print("  Self-Improving Agents -- Full Experiment Suite")
        print("=" * 70)
        print(f"  Run ID: {run_id}")
        print(f"  Levels: {', '.join(args.levels)}")
        print(f"  Tasks:  {', '.join(args.tasks)}")
        print(f"  Mode:   {'sequential' if args.sequential else 'parallel'}")
        print(f"  Scale:  {args.scale}x")
        print(f"  Fresh:  {args.fresh}")
        print()

        # Build job list
        jobs = []
        for task in args.tasks:
            for level_key in args.levels:
                if level_key not in LEVELS:
                    print(f"  Unknown level: {level_key} -- skipping")
                    continue
                jobs.append((level_key, LEVELS[level_key], task))

        # Check for unfinished experiments from a previous run
        if not args.fresh:
            from tasks.checkpoint import is_in_progress, describe_progress
            unfinished = []
            for level_key, level_info, task in jobs:
                results_path = os.path.join(DIR, level_key, "results", task)
                if is_in_progress(results_path):
                    desc = describe_progress(results_path) or "in progress"
                    unfinished.append(f"    {level_key} / {task}: {desc}")
            if unfinished:
                print("  Found unfinished experiments from a previous run:")
                for line in unfinished:
                    print(line)
                print("  Resuming from checkpoints. Use --fresh to start over.\n")

        total_start = time.time()

        if args.sequential:
            results = run_sequential(jobs, args.fresh, run_id, args.scale)
        else:
            results = run_parallel(jobs, args.fresh, run_id, args.scale)

        total_elapsed = time.time() - total_start
        completed_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Summary
        print("\n" + "=" * 70)
        print("  ALL EXPERIMENTS COMPLETE")
        print("=" * 70)
        print(f"  Run ID:     {run_id}")
        print(f"  Total time: {total_elapsed:.0f}s ({total_elapsed / 60:.1f} min)\n")

        for level_key, task, ok in results:
            status = "OK" if ok else "FAILED"
            print(f"    [{status:6}] {level_key} / {task}")

        failed = [r for r in results if not r[2]]
        if failed:
            print(f"\n  {len(failed)} experiment(s) failed.")

        # Collect results into registry
        experiments = []
        total_cost = 0
        for level_key, task, ok in results:
            exp = collect_experiment_result(level_key, task)
            experiments.append(exp)
            total_cost += exp.get("cost_usd", 0) or 0

        run_record = {
            "run_id": run_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "experiments": experiments,
            "total_cost_usd": round(total_cost, 4),
        }

        registry = load_registry()
        registry.append(run_record)
        save_registry(registry)
        print(f"\n  Registry updated: {REGISTRY_FILE}")

        # Run cross-validation (scores all levels with same judge for fair comparison)
        if not args.skip_analysis and not args.skip_cross_validation:
            cross_val_tasks = args.tasks
            task_arg = "all" if set(cross_val_tasks) == set(ALL_TASKS) else None
            if task_arg:
                # Run once with --task all
                print(f"\n{'=' * 70}")
                print(f"  Running cross-validation (all tasks)...")
                print(f"{'=' * 70}\n")
                cross_val_script = os.path.join(DIR, "arena-loop", "cross_validate.py")
                result = subprocess.run(
                    [sys.executable, cross_val_script, "--task", "all"],
                    cwd=os.path.join(DIR, "arena-loop"),
                )
                if result.returncode != 0:
                    print(f"\n  Cross-validation failed (exit code {result.returncode})")
            else:
                # Run per-task
                cross_val_script = os.path.join(DIR, "arena-loop", "cross_validate.py")
                for task in cross_val_tasks:
                    print(f"\n{'=' * 70}")
                    print(f"  Running cross-validation ({task})...")
                    print(f"{'=' * 70}\n")
                    result = subprocess.run(
                        [sys.executable, cross_val_script, "--task", task],
                        cwd=os.path.join(DIR, "arena-loop"),
                    )
                    if result.returncode != 0:
                        print(f"\n  Cross-validation for {task} failed (exit code {result.returncode})")

        # Run analysis
        if not args.skip_analysis:
            print(f"\n{'=' * 70}")
            print(f"  Generating cross-level analysis...")
            print(f"{'=' * 70}\n")
            result = subprocess.run(
                [sys.executable, os.path.join(DIR, "analyze_results.py"),
                 "--run-id", run_id],
                cwd=DIR,
            )
            if result.returncode == 0:
                print(f"\n  Analysis written to: experiment-results.md")
                print(f"  Run analysis: results/analysis_{run_id}.md")
            else:
                print(f"\n  Analysis generation failed (exit code {result.returncode})")

        print(f"\n  Done. Run ID: {run_id}")

    finally:
        release_lock()


if __name__ == "__main__":
    main()
