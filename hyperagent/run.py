"""
HyperAgent Loop -- True Code-Rewriting Self-Improvement
=======================================================
The meta-agent rewrites its own source code (task_agent.py, meta_agent.py).
A fixed harness validates changes, reverts on crash, and versions every generation.

Inspired by Meta's DGM-H (HyperAgents, arxiv 2603.19461), simplified: no Docker,
folder-based versioning, subprocess isolation.

Uses Gemini 2.5 Flash. Set GEMINI_API_KEY in ../.env

Tasks:
  python run.py                  # default: snake
  python run.py --task support   # Customer support (LLM-as-judge)
  python run.py --task    # Sorting optimization
"""

import argparse
import importlib
import importlib.util
import inspect
import json
import os
import shutil
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(DIR, ".."))
from tasks.task_runner import load_task, write_solution, run_solution

import llm

SEED_DIR = os.path.join(DIR, "seed")
MODIFIABLE_FILES = ["task_agent.py", "meta_agent.py"]

# Python caches modules by name. We use a counter to force fresh imports
# each time, so modified agent code is actually loaded (not the cached version).
_module_counter = 0


# -- Path helpers: each task gets its own directories --

def _task_dirs(task_name):
    """Return (solution_file, agent_code_dir, generations_dir) for a task."""
    return (
        os.path.join(DIR, f"solution_{task_name}.py"),
        os.path.join(DIR, "agent_code", task_name),
        os.path.join(DIR, "generations", task_name),
    )


# -- Agent file management --

def initialize(agent_code_dir, generations_dir):
    gen_000 = os.path.join(generations_dir, "gen_000")
    if not os.path.exists(gen_000):
        os.makedirs(agent_code_dir, exist_ok=True)
        for fname in MODIFIABLE_FILES:
            shutil.copy2(os.path.join(SEED_DIR, fname), os.path.join(agent_code_dir, fname))
        save_generation(0, read_agent_files(agent_code_dir), generations_dir,
                        {"parent": None, "valid": True, "score": None,
                         "files_changed": [], "error": None})


def read_agent_files(agent_code_dir):
    files = {}
    for fname in MODIFIABLE_FILES:
        path = os.path.join(agent_code_dir, fname)
        if os.path.exists(path):
            with open(path, "r") as f:
                files[fname] = f.read()
    return files


def write_agent_files(agent_code_dir, modifications):
    for fname, source in modifications.items():
        path = os.path.join(agent_code_dir, fname)
        with open(path, "w") as f:
            f.write(source)


def load_agent_module(agent_code_dir, module_name):
    global _module_counter
    _module_counter += 1
    unique_name = f"_agent_{module_name}_{_module_counter}"
    path = os.path.join(agent_code_dir, module_name + ".py")
    spec = importlib.util.spec_from_file_location(unique_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# -- Validation --

def validate_modifications(agent_code_dir, modifications):
    # Stage 0: all required files must be present and non-empty
    for fname in MODIFIABLE_FILES:
        if fname not in modifications:
            return False, f"Missing required file {fname}"
        if not modifications[fname] or not modifications[fname].strip():
            return False, f"Empty content for {fname}"

    # Stage 1: compile check
    for fname, source in modifications.items():
        try:
            compile(source, fname, "exec")
        except SyntaxError as e:
            return False, f"Compile error in {fname}: {e}"

    # Stage 2: write and import check
    backup = read_agent_files(agent_code_dir)
    write_agent_files(agent_code_dir, modifications)
    try:
        task_mod = load_agent_module(agent_code_dir, "task_agent")
        meta_mod = load_agent_module(agent_code_dir, "meta_agent")
    except Exception as e:
        write_agent_files(agent_code_dir, backup)
        return False, f"Import error: {e}"

    # Stage 3: signature check
    if not hasattr(task_mod, "propose") or not callable(task_mod.propose):
        write_agent_files(agent_code_dir, backup)
        return False, "task_agent.py missing propose() function"
    if not hasattr(meta_mod, "propose_modifications") or not callable(meta_mod.propose_modifications):
        write_agent_files(agent_code_dir, backup)
        return False, "meta_agent.py missing propose_modifications() function"

    try:
        sig = inspect.signature(task_mod.propose)
        if len(sig.parameters) < 3:
            write_agent_files(agent_code_dir, backup)
            return False, f"task_agent.propose() needs >=3 params, has {len(sig.parameters)}"
    except (ValueError, TypeError):
        pass

    try:
        sig = inspect.signature(meta_mod.propose_modifications)
        if len(sig.parameters) < 3:
            write_agent_files(agent_code_dir, backup)
            return False, f"meta_agent.propose_modifications() needs >=3 params, has {len(sig.parameters)}"
    except (ValueError, TypeError):
        pass

    return True, None


# -- Generation management --

def save_generation(gen_id, agent_files, generations_dir, metadata):
    gen_dir = os.path.join(generations_dir, f"gen_{gen_id:03d}")
    os.makedirs(gen_dir, exist_ok=True)
    for fname, source in agent_files.items():
        with open(os.path.join(gen_dir, fname), "w") as f:
            f.write(source)
    metadata["gen_id"] = gen_id
    metadata["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(gen_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)


def revert_to(gen_id, generations_dir, agent_code_dir):
    gen_dir = os.path.join(generations_dir, f"gen_{gen_id:03d}")
    for fname in MODIFIABLE_FILES:
        src = os.path.join(gen_dir, fname)
        dst = os.path.join(agent_code_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)


def find_last_valid_gen(generations_dir):
    if not os.path.exists(generations_dir):
        return 0
    gen_dirs = sorted([d for d in os.listdir(generations_dir) if d.startswith("gen_")])
    for gen_dir in reversed(gen_dirs):
        meta_path = os.path.join(generations_dir, gen_dir, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            if meta.get("valid", False):
                return meta["gen_id"]
    return 0


# -- Inner loop --

def run_inner_loop(task, n_iters, history, best_metric, current_code, higher_is_better,
                   metric_name, agent_code_dir, solution_file, on_step=None, step_offset=0):
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

    for i in range(n_iters):
        step_num = step_offset + i + 1
        print(f"    [TASK] Iteration {i + 1}/{n_iters}...")

        try:
            task_mod = load_agent_module(agent_code_dir, "task_agent")
            proposed_code, raw_response = task_mod.propose(
                current_code, best_metric, history, metric_name=metric_name
            )
        except Exception as e:
            print(f"    [TASK] Agent error: {e}")
            step = {"type": "task_step", "step": step_num, "action": "ERROR", "error": str(e)}
            history.append(step)
            if on_step:
                on_step(step)
            continue

        write_solution(proposed_code, solution_file)
        new_metric, err = run_solution(task, solution_file, llm_module=llm)

        if err or new_metric is None:
            print(f"    [TASK] Benchmark error: {err or 'No metric'}")
            write_solution(current_code, solution_file)
            step = {"type": "task_step", "step": step_num, "action": "ERROR", "error": str(err)}
            history.append(step)
            if on_step:
                on_step(step)
            continue

        if is_better(new_metric, best_metric):
            imp = improvement_pct(new_metric, best_metric)
            print(f"    [TASK] + ACCEPTED  {best_metric:.3f} -> {new_metric:.3f}  ({imp:.1f}% better)")
            step = {
                "type": "task_step", "step": step_num, "action": "ACCEPTED",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "improvement_pct": round(imp, 1),
                "code": proposed_code, "llm_response": raw_response,
            }
            history.append(step)
            current_code = proposed_code
            best_metric = new_metric
        else:
            print(f"    [TASK] x REJECTED  {new_metric:.3f} (best: {best_metric:.3f})")
            write_solution(current_code, solution_file)
            step = {
                "type": "task_step", "step": step_num, "action": "REJECTED",
                "proposed_metric": round(new_metric, 4),
                "previous_metric": round(best_metric, 4),
                "code": proposed_code, "llm_response": raw_response,
            }
            history.append(step)

        if on_step:
            on_step(step)

        if is_perfect(best_metric):
            print(f"    [TASK] PERFECT SCORE ({best_metric:.3f}). Stopping inner loop.")
            break

    return current_code, best_metric, history


# -- Main generation loop --

def run(total_generations=6, inner_iters=3, task_name="snake",
        on_step=None, start_from=0, resume_state=None):
    # on_step: called by experiment.py to save checkpoints. None when running directly.
    task = load_task(task_name)
    higher_is_better = task.HIGHER_IS_BETTER
    metric_name = task.METRIC_NAME

    # Each task gets isolated directories so parallel runs don't conflict
    solution_file, agent_code_dir, generations_dir = _task_dirs(task_name)

    print("=" * 65)
    print(f"  HyperAgent Loop -- {task.TASK_NAME} (Real LLM)")
    print("=" * 65)
    print(f"  Generations: {total_generations}  |  Inner iterations: {inner_iters}")
    print(f"  Agent code: {agent_code_dir}")
    print()

    if resume_state:
        current_code = resume_state["current_code"]
        best_metric = resume_state["best_metric"]
        baseline_metric = resume_state["baseline_metric"]
        history = resume_state["history"]
        last_valid_gen = resume_state.get("last_valid_gen", find_last_valid_gen(generations_dir))
        generation_log = resume_state.get("generation_log", [])
        print(f"[RESUME] Resuming from generation {start_from + 1}, best: {best_metric:.3f}\n")
    else:
        initialize(agent_code_dir, generations_dir)
        current_code = task.INITIAL_CODE
        write_solution(current_code, solution_file)
        best_metric, err = run_solution(task, solution_file, llm_module=llm)
        if err:
            print(f"Baseline failed: {err}")
            return None
        baseline_metric = best_metric
        history = []
        generation_log = []
        last_valid_gen = 0

        save_generation(0, read_agent_files(agent_code_dir), generations_dir, {
            "parent": None, "valid": True, "score": round(best_metric, 4),
            "files_changed": [], "error": None
        })
        print(f"[INIT] Baseline {metric_name}: {best_metric:.3f}")
        print(f"[INIT] Agent code initialized from seed/\n")

    for gen in range(start_from, total_generations):
        gen_id = gen + 1
        print(f"== Generation {gen_id}/{total_generations} " + "=" * 40)

        # -- Inner loop: task agent proposes solutions --
        print(f"  [INNER LOOP] Running {inner_iters} iterations with current agent code...")
        step_offset = gen * inner_iters
        current_code, best_metric, history = run_inner_loop(
            task, inner_iters, history, best_metric, current_code,
            higher_is_better, metric_name, agent_code_dir, solution_file,
            on_step=on_step, step_offset=step_offset
        )

        # -- Meta-agent proposes code modifications --
        print(f"\n  [META] Asking meta-agent to modify agent code...")
        agent_files = read_agent_files(agent_code_dir)

        task_steps = [h for h in history if h.get("type") == "task_step"]
        recent_evals = []
        for h in task_steps[-6:]:
            recent_evals.append({
                "step": h.get("step"), "action": h.get("action"),
                "proposed_metric": h.get("proposed_metric"),
                "previous_metric": h.get("previous_metric"),
                "improvement_pct": h.get("improvement_pct"),
            })

        task_info = {
            "task_name": task_name,
            "metric_name": metric_name,
            "higher_is_better": higher_is_better,
            "best_metric": best_metric,
        }

        try:
            meta_mod = load_agent_module(agent_code_dir, "meta_agent")
            modifications = meta_mod.propose_modifications(agent_files, recent_evals, task_info)
        except Exception as e:
            print(f"  [META] Error calling meta-agent: {e}")
            gen_meta = {
                "parent": last_valid_gen, "valid": False,
                "score": round(best_metric, 4),
                "files_changed": [], "error": str(e),
            }
            save_generation(gen_id, agent_files, generations_dir, gen_meta)
            generation_log.append(gen_meta)
            if on_step:
                on_step({"type": "generation", "gen_id": gen_id, "valid": False,
                         "error": str(e), "best_metric": round(best_metric, 4)})
            continue

        if not modifications:
            print(f"  [META] No modifications proposed")
            gen_meta = {
                "parent": last_valid_gen, "valid": True,
                "score": round(best_metric, 4),
                "files_changed": [], "error": None,
            }
            save_generation(gen_id, agent_files, generations_dir, gen_meta)
            generation_log.append(gen_meta)
            if on_step:
                on_step({"type": "generation", "gen_id": gen_id, "valid": True,
                         "files_changed": [], "best_metric": round(best_metric, 4)})
            continue

        changed = list(modifications.keys())
        print(f"  [META] Proposed changes to: {changed}")

        # Merge: start with current files, overlay modifications
        merged = dict(agent_files)
        merged.update(modifications)

        valid, error = validate_modifications(agent_code_dir, merged)
        if not valid:
            print(f"  [META] x INVALID: {error}")
            print(f"  [META] Reverting to gen {last_valid_gen}")
            revert_to(last_valid_gen, generations_dir, agent_code_dir)
            gen_meta = {
                "parent": last_valid_gen, "valid": False,
                "score": round(best_metric, 4),
                "files_changed": changed, "error": error,
            }
            save_generation(gen_id, merged, generations_dir, gen_meta)
            generation_log.append(gen_meta)
            if on_step:
                on_step({"type": "generation", "gen_id": gen_id, "valid": False,
                         "error": error, "files_changed": changed,
                         "best_metric": round(best_metric, 4)})
            continue

        # Valid -- files already written by validate_modifications
        print(f"  [META] + VALID -- agent code updated")
        for fname in changed:
            old_lines = agent_files.get(fname, "").count("\n")
            new_lines = modifications[fname].count("\n")
            print(f"    {fname}: {old_lines} -> {new_lines} lines")

        gen_meta = {
            "parent": last_valid_gen, "valid": True,
            "score": round(best_metric, 4),
            "files_changed": changed, "error": None,
        }
        save_generation(gen_id, read_agent_files(agent_code_dir), generations_dir, gen_meta)
        last_valid_gen = gen_id
        generation_log.append(gen_meta)

        if on_step:
            on_step({"type": "generation", "gen_id": gen_id, "valid": True,
                     "files_changed": changed, "best_metric": round(best_metric, 4)})

        print()

    # -- Summary --
    print("\n" + "=" * 65)
    print("  FINAL RESULTS")
    print("=" * 65)
    task_steps = [h for h in history if h.get("type") == "task_step"]
    accepted = [h for h in task_steps if h.get("action") == "ACCEPTED"]
    valid_gens = [g for g in generation_log if g.get("valid")]
    code_changing_gens = [g for g in generation_log if g.get("files_changed")]

    print(f"  Baseline {metric_name}      : {baseline_metric:.3f}")
    print(f"  Final best {metric_name}    : {best_metric:.3f}")
    print(f"  Code improvements      : {len(accepted)} / {len(task_steps)} accepted")
    print(f"  Generations            : {len(generation_log)} total, {len(valid_gens)} valid")
    print(f"  Agent code modified    : {len(code_changing_gens)} times")

    print(f"\n  Generation history:")
    for i, g in enumerate(generation_log):
        status = "VALID" if g.get("valid") else "FAILED"
        changed = g.get("files_changed", [])
        files_str = ", ".join(changed) if changed else "no changes"
        err_str = f" -- {g['error']}" if g.get("error") else ""
        print(f"    gen {i + 1}: [{status:6}] {files_str}{err_str}")

    return {
        "task": task_name,
        "metric_name": metric_name,
        "higher_is_better": higher_is_better,
        "baseline_metric": baseline_metric,
        "best_metric": best_metric,
        "final_code": current_code,
        "history": history,
        "generation_log": generation_log,
        "total_generations": total_generations,
        "last_valid_gen": last_valid_gen,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="snake",
                        help="Task to optimize: snake, support, email_validation")
    parser.add_argument("--gens", type=int, default=6, help="Number of generations")
    parser.add_argument("--inner", type=int, default=3, help="Inner iterations per generation")
    args = parser.parse_args()
    run(total_generations=args.gens, inner_iters=args.inner, task_name=args.task)
