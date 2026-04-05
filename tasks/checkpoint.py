"""
Checkpoint/resume module -- atomic writes, sequence-numbered, deterministic restore.

Shared by all 4 levels. Saves state as JSON + code files as .py alongside.
"""

import glob
import json
import os


def save_checkpoint(results_dir, step_num, state, code_files=None):
    """Save checkpoint atomically.

    Args:
        results_dir: path like "autoresearch/results/snake"
        step_num: integer step/iteration/generation number
        state: dict of everything needed to resume (JSON-serializable)
        code_files: dict of {filename: code_string} to save alongside

    Writes checkpoint_NNN.json atomically + code files.
    Keeps only last 3 checkpoints, deletes older ones.
    """
    os.makedirs(results_dir, exist_ok=True)

    tag = f"{step_num:03d}"  # e.g. step 5 -> "005" for consistent sorting
    checkpoint_path = os.path.join(results_dir, f"checkpoint_{tag}.json")
    tmp_path = checkpoint_path + ".tmp"

    # Save state JSON atomically
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, checkpoint_path)

    # Save code files alongside
    if code_files:
        for filename, code in code_files.items():
            code_path = os.path.join(results_dir, filename)
            code_tmp = code_path + ".tmp"
            with open(code_tmp, "w", encoding="utf-8") as f:
                f.write(code)
            os.replace(code_tmp, code_path)

    # Keep only last 3 checkpoints
    _cleanup_old_checkpoints(results_dir, keep=3)


def load_latest_checkpoint(results_dir):
    """Find and load the highest-numbered checkpoint.

    Returns (step_num, state, code_files) or None if no checkpoints exist.
    code_files is a dict of {filename: content} read from .py files saved alongside.
    Validates JSON is parseable before returning.
    """
    pattern = os.path.join(results_dir, "checkpoint_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None

    # Try from highest-numbered down in case latest is corrupted
    for path in reversed(files):
        basename = os.path.basename(path)
        # Extract step number from checkpoint_NNN.json
        num_str = basename.replace("checkpoint_", "").replace(".json", "")
        try:
            step_num = int(num_str)
        except ValueError:
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Load .py files in the same directory
        code_files = {}
        for py_path in glob.glob(os.path.join(results_dir, "*.py")):
            filename = os.path.basename(py_path)
            with open(py_path, "r", encoding="utf-8") as f:
                code_files[filename] = f.read()

        return (step_num, state, code_files)

    return None


def save_final(results_dir, final_log):
    """Atomic write of final experiment-log.json. Marks experiment as completed."""
    os.makedirs(results_dir, exist_ok=True)

    path = os.path.join(results_dir, "experiment-log.json")
    tmp_path = path + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(final_log, f, indent=2)
    os.replace(tmp_path, path)


def is_in_progress(results_dir):
    """Returns True if there are checkpoints but no completed experiment-log.json."""
    log_path = os.path.join(results_dir, "experiment-log.json")
    if os.path.exists(log_path):
        return False

    pattern = os.path.join(results_dir, "checkpoint_*.json")
    return len(glob.glob(pattern)) > 0


def clean_results(results_dir):
    """Delete all checkpoints, logs, and code files in results_dir for a fresh start."""
    import shutil
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
    os.makedirs(results_dir, exist_ok=True)


def describe_progress(results_dir):
    """Return a human-readable string describing checkpoint progress, or None."""
    if not is_in_progress(results_dir):
        return None
    loaded = load_latest_checkpoint(results_dir)
    if not loaded:
        return None
    step_num, state, _ = loaded
    return f"stopped at step {step_num}"


def _cleanup_old_checkpoints(results_dir, keep=3):
    pattern = os.path.join(results_dir, "checkpoint_*.json")
    files = sorted(glob.glob(pattern))
    if len(files) <= keep:
        return

    for old in files[:-keep]:
        try:
            os.remove(old)
        except OSError:
            pass
