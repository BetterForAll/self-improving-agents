"""
Task Runner -- loads tasks from tasks/ folder, writes solutions, runs benchmarks.

Each level imports from here instead of embedding task logic locally.
"""

import importlib.util
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(ROOT, "tasks")


def load_task(task_name):
    """Load a task's config and initial code from tasks/{task_name}/."""
    task_dir = os.path.join(TASKS_DIR, task_name)

    # Load config.py as a Python module by file path (avoids needing __init__.py)
    spec = importlib.util.spec_from_file_location(
        f"tasks.{task_name}.config",
        os.path.join(task_dir, "config.py")
    )
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)

    # Attach initial code from real file
    with open(os.path.join(task_dir, "initial_solution.py")) as f:
        config.INITIAL_CODE = f.read()

    # Attach benchmark path
    config.BENCHMARK_PATH = os.path.join(task_dir, "benchmark.py")

    return config


def write_solution(code, solution_file):
    """Write code to the level's own solution.py. Just the code, no harness."""
    with open(solution_file, "w", encoding="utf-8") as f:
        f.write(code)


def run_solution(config, solution_file, llm_module=None, judge_runs=None):
    """Run benchmark.py with solution_file as argument. Parse output.

    For LLM-as-judge tasks (config.USES_LLM_JUDGE), requires llm_module.
    judge_runs: number of times to call the LLM judge and average (default: 1
    for backward compatibility, 3 recommended for stable scores).
    Returns (metric_value, error_string_or_None).
    """
    timeout = 60 if config.TASK_NAME == "snake" else 30
    try:
        result = subprocess.run(
            ["python", config.BENCHMARK_PATH, solution_file],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None, result.stderr[:500]
        output = result.stdout

        if getattr(config, "USES_LLM_JUDGE", False):
            if judge_runs is None:
                judge_runs = getattr(config, "JUDGE_RUNS", 1)
            return _run_llm_judge_averaged(config, output, llm_module, judge_runs)
        else:
            return _parse_metric(config, output)
    except subprocess.TimeoutExpired:
        return None, f"Timeout ({timeout}s)"
    except Exception as e:
        return None, str(e)


def _parse(output, key):
    for line in output.strip().splitlines():
        if line.startswith(key + ":"):
            return line.split(":", 1)[1]
    raise ValueError(f"Key '{key}' not found in output")


def _parse_metric(config, output):
    """Parse metric from benchmark output. Validate correctness if applicable."""
    metric = float(_parse(output, config.METRIC_NAME))
    try:
        correct = _parse(output, "correct")
        if correct == "False":
            return None, "Incorrect output"
    except ValueError:
        pass  # not all benchmarks have a "correct" field
    return metric, None


def _run_llm_judge(config, output, llm_module):
    """Parse answers JSON, call LLM judge, return score (single run)."""
    if llm_module is None:
        return None, "LLM-as-judge task requires llm_module"

    answers_line = None
    for line in output.strip().splitlines():
        if line.startswith("answers:"):
            answers_line = line.split(":", 1)[1]
            break
    if not answers_line:
        return None, "No answers output found"

    answers = json.loads(answers_line)
    qa_pairs = ""
    for i, (tc, ans) in enumerate(zip(config.TEST_CASES, answers)):
        qa_pairs += (
            f"\nQuestion {i+1}: {tc['question']}\n"
            f"Expected: {tc['expected']}\n"
            f"Actual: {ans['answer']}\n"
        )
    judge_prompt = config.JUDGE_PROMPT.format(qa_pairs=qa_pairs)
    judge_response = llm_module.ask(judge_prompt)
    score = _parse_judge_score(judge_response)
    return score, None


def _run_llm_judge_averaged(config, output, llm_module, runs=1):
    """Run LLM judge multiple times and average to reduce noise.

    With runs=1, behaves identically to _run_llm_judge (backward compatible).
    With runs=3, smooths out LLM judge variance significantly.
    """
    if runs <= 1:
        return _run_llm_judge(config, output, llm_module)

    scores = []
    last_error = None
    for _ in range(runs):
        score, err = _run_llm_judge(config, output, llm_module)
        if score is not None:
            scores.append(score)
        else:
            last_error = err

    if not scores:
        return None, last_error or "All judge runs failed"

    avg = sum(scores) / len(scores)
    return round(avg, 2), None


def _parse_judge_score(response):
    """Extract average score from LLM judge JSON response."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    try:
        data = json.loads(text)
        return float(data.get("average", 0))
    except (json.JSONDecodeError, ValueError):
        numbers = re.findall(r'\d+\.?\d*', text)
        return float(numbers[-1]) if numbers else 0.0
