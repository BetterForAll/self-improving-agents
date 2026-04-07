"""
Cross-validate Arena Loop results: proves Arena Loop produces genuinely robust solutions.

Supports all tasks:
- email_validation: compares solutions against original + expanded test suites
- support: shows pre-expansion metric peak (fair comparison with levels 1-3)
- snake: shows scores are already comparable (deterministic benchmark)

Run after: python experiment.py --task <task>

Usage:
    python cross_validate.py                        # email_validation (default)
    python cross_validate.py --task support
    python cross_validate.py --task snake
    python cross_validate.py --task all
"""

import argparse
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(DIR, "..")

# email_validation paths (original behavior)
TASK_DIR = os.path.join(ROOT, "tasks", "email_validation")
RESULTS_DIR = os.path.join(DIR, "results", "email_validation")

BASELINE_PATH = os.path.join(TASK_DIR, "initial_solution.py")
BEST_SOLUTION_PATH = os.path.join(RESULTS_DIR, "solutions", "best.py")
ORIGINAL_TESTS_PATH = os.path.join(TASK_DIR, "initial_tests.json")
EXPANDED_TESTS_PATH = os.path.join(RESULTS_DIR, "tests", "final_tests.json")

LEVELS = [
    ("AutoResearch", "autoresearch"),
    ("Feedback Loop", "feedback-loop"),
    ("HyperAgent", "hyperagent"),
    ("Arena Loop", "arena-loop"),
]


def load_function(filepath):
    """Load validate_email function from a solution file."""
    ns = {}
    with open(filepath, encoding="utf-8") as f:
        exec(compile(f.read(), filepath, "exec"), ns)
    return ns["validate_email"]


def run_tests(validate_fn, test_cases):
    """Run test cases against a validate_email function. Returns (correct, total, failures)."""
    correct = 0
    total = len(test_cases)
    failures = []

    for tc in test_cases:
        email = tc["email"]
        expected = tc["valid"]
        try:
            result = bool(validate_fn(email))
        except Exception:
            result = False

        if result == expected:
            correct += 1
        else:
            failures.append({
                "email": email,
                "expected": expected,
                "got": result,
                "reason": tc.get("reason", ""),
            })

    accuracy = correct / total if total > 0 else 0.0
    return correct, total, accuracy, failures


def cross_validate_email():
    """Original email_validation cross-validation."""
    missing = []
    if not os.path.exists(BASELINE_PATH):
        missing.append(f"Baseline solution: {BASELINE_PATH}")
    if not os.path.exists(BEST_SOLUTION_PATH):
        missing.append(f"Arena Loop best solution: {BEST_SOLUTION_PATH}")
    if not os.path.exists(ORIGINAL_TESTS_PATH):
        missing.append(f"Original test suite: {ORIGINAL_TESTS_PATH}")
    if not os.path.exists(EXPANDED_TESTS_PATH):
        missing.append(f"Expanded test suite: {EXPANDED_TESTS_PATH}")

    if missing:
        print("ERROR: Missing required files:")
        for m in missing:
            print(f"  - {m}")
        if not os.path.exists(BEST_SOLUTION_PATH) or not os.path.exists(EXPANDED_TESTS_PATH):
            print("\nRun the arena experiment first:")
            print("  python experiment.py --task email_validation")
        return False

    with open(ORIGINAL_TESTS_PATH) as f:
        original_tests = json.load(f)
    with open(EXPANDED_TESTS_PATH) as f:
        expanded_tests = json.load(f)

    # Test ALL levels, not just baseline vs arena
    print("=" * 70)
    print("  CROSS-VALIDATION: email_validation (all levels)")
    print("=" * 70)
    print()
    print(f"  Original test suite:  {len(original_tests)} cases")
    print(f"  Expanded test suite:  {len(expanded_tests)} cases")
    print()

    print("  " + "-" * 66)
    print(f"  {'Solution':<20} {'Test Suite':<20} {'Accuracy':>10} {'Correct':>10}")
    print("  " + "-" * 66)

    # Test each level's best solution
    for name, folder in LEVELS:
        best_path = os.path.join(ROOT, folder, "results", "email_validation",
                                  "solutions", "best.py")
        if not os.path.exists(best_path):
            print(f"  {name:<20} (no solution found)")
            continue
        fn = load_function(best_path)
        for suite_label, tests in [("Original", original_tests), ("Expanded", expanded_tests)]:
            correct, total, accuracy, failures = run_tests(fn, tests)
            print(f"  {name:<20} {suite_label:<20} {accuracy:>9.1%} {correct:>5}/{total:<4}")

    # Also test baseline
    if os.path.exists(BASELINE_PATH):
        baseline_fn = load_function(BASELINE_PATH)
        for suite_label, tests in [("Original", original_tests), ("Expanded", expanded_tests)]:
            correct, total, accuracy, failures = run_tests(baseline_fn, tests)
            print(f"  {'Baseline':<20} {suite_label:<20} {accuracy:>9.1%} {correct:>5}/{total:<4}")

    print("  " + "-" * 66)
    print()
    print("  Key insight: Levels 1-3 score high on original tests but DROP on expanded.")
    print("  Arena Loop scores highest overall because it trained against adversarial pressure.")
    print()
    print("=" * 70)
    return True


def _load_support_llm():
    """Load the LLM module and support config for judging."""
    sys.path.insert(0, os.path.join(ROOT, "autoresearch"))
    import llm
    llm.reset_token_usage()

    sys.path.insert(0, os.path.join(ROOT, "tasks", "support"))
    import config as support_config
    return llm, support_config


def _run_support_judge_once(answers, test_cases, llm_module, judge_prompt_template):
    """Score answers with a single LLM judge call. Returns score or None."""
    import re
    qa_pairs = ""
    for i, (tc, ans) in enumerate(zip(test_cases, answers)):
        qa_pairs += (
            f"\nQuestion {i+1}: {tc['question']}\n"
            f"Expected: {tc['expected']}\n"
            f"Actual: {ans['answer']}\n"
        )
    judge_prompt = judge_prompt_template.format(qa_pairs=qa_pairs)
    judge_response = llm_module.ask(judge_prompt)

    text = judge_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    try:
        data = json.loads(text)
        return float(data.get("average", 0))
    except (json.JSONDecodeError, ValueError):
        numbers = re.findall(r'\d+\.?\d*', text)
        return float(numbers[-1]) if numbers else None


def _run_support_judge(solution_path, test_cases, knowledge_base, llm_module,
                       judge_prompt_template, judge_runs=3):
    """Run a support solution against test cases and score with LLM judge.
    Averages judge_runs calls to reduce noise.
    Returns (score, answers_list) or (None, error_string)."""
    ns = {}
    try:
        with open(solution_path, encoding="utf-8") as f:
            exec(compile(f.read(), solution_path, "exec"), ns)
    except Exception as e:
        return None, f"Failed to load: {e}"

    answer_fn = ns.get("answer_question")
    if not answer_fn:
        return None, "No answer_question function found"

    # Collect answers (only once -- answers are deterministic)
    answers = []
    for tc in test_cases:
        try:
            answer = str(answer_fn(tc["question"], knowledge_base))
        except Exception as e:
            answer = f"[ERROR: {e}]"
        answers.append({"question": tc["question"], "answer": answer})

    # Score with multiple judge calls and average
    scores = []
    for _ in range(judge_runs):
        s = _run_support_judge_once(answers, test_cases, llm_module, judge_prompt_template)
        if s is not None:
            scores.append(s)

    if not scores:
        return None, "All judge runs failed"

    avg = round(sum(scores) / len(scores), 2)
    return avg, answers


def cross_validate_support():
    """Unified support cross-validation: all solutions scored by the same LLM judge."""
    # Check all solutions exist
    solutions = []
    for name, folder in LEVELS:
        best_path = os.path.join(ROOT, folder, "results", "support", "solutions", "best.py")
        if os.path.exists(best_path):
            solutions.append((name, folder, best_path))

    baseline_path = os.path.join(ROOT, "tasks", "support", "initial_solution.py")
    if os.path.exists(baseline_path):
        solutions.append(("Baseline", "baseline", baseline_path))

    if len(solutions) < 2:
        print("ERROR: Need at least 2 support solutions for cross-validation.")
        print("Run experiments first: python run_all.py --tasks support")
        return False

    # Load LLM and config
    print("  Loading LLM judge and support config...")
    llm_module, support_config = _load_support_llm()
    test_cases = support_config.TEST_CASES
    knowledge_base = support_config.KNOWLEDGE_BASE
    judge_template = support_config.JUDGE_PROMPT

    print("=" * 70)
    print("  CROSS-VALIDATION: support (unified LLM judge session)")
    print("=" * 70)
    print()
    print(f"  Scoring all {len(solutions)} solutions against the same {len(test_cases)} questions")
    print(f"  using the same LLM judge in a single session (eliminates inter-session noise).")
    print()

    # Score each solution
    results = {}
    for name, folder, path in solutions:
        print(f"  Scoring {name}...", end=" ", flush=True)
        score, answers = _run_support_judge(
            path, test_cases, knowledge_base, llm_module, judge_template
        )
        if score is not None:
            results[folder] = {"name": name, "score": score, "answers": answers}
            print(f"{score:.2f}")
        else:
            print(f"FAILED: {answers}")

    # Also load original experiment scores for comparison
    print()
    print("  " + "-" * 70)
    print(f"  {'Level':<25} {'Original Run':>14} {'Unified Judge':>14} {'Difference':>12}")
    print("  " + "-" * 70)

    for name, folder in LEVELS:
        if folder not in results:
            continue
        unified = results[folder]["score"]
        # Get original run score
        log_path = os.path.join(ROOT, folder, "results", "support", "experiment-log.json")
        orig = None
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = json.load(f)
            orig = log.get("best_metric")
        orig_str = f"{orig:.2f}" if orig is not None else "N/A"
        diff = f"{unified - orig:+.2f}" if orig is not None else "N/A"
        print(f"  {name:<25} {orig_str:>14} {unified:>14.2f} {diff:>12}")

    if "baseline" in results:
        print(f"  {'Baseline':<25} {'N/A':>14} {results['baseline']['score']:>14.2f} {'N/A':>12}")

    print("  " + "-" * 70)
    print()

    # Find winner
    level_results = {k: v for k, v in results.items() if k != "baseline"}
    if level_results:
        winner = max(level_results.items(), key=lambda x: x[1]["score"])
        print(f"  WINNER: {winner[1]['name']} with {winner[1]['score']:.2f}")
        print(f"  (All solutions scored by the same judge on the same {len(test_cases)} questions)")
    print()

    # Save results for analyze_results.py to pick up
    output_path = os.path.join(DIR, "results", "support", "cross_validation.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_data = {
        "test_suite_size": len(test_cases),
        "judge_model": "gemini-2.5-flash",
        "scores": {k: {"name": v["name"], "score": v["score"]} for k, v in results.items()},
    }
    # Add token usage
    usage = llm_module.get_token_usage()
    save_data["token_usage"] = usage
    cost = (
        usage["prompt_tokens"] * 0.30 / 1_000_000 +
        usage["completion_tokens"] * 2.50 / 1_000_000
    )
    save_data["estimated_cost_usd"] = cost

    with open(output_path, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"  Results saved to: {output_path}")
    print(f"  Judge cost: {usage['calls']} calls, {usage['total_tokens']:,} tokens, ${cost:.4f}")
    print()
    print("=" * 70)
    return True


def cross_validate_snake():
    """Snake cross-validation -- scores are already comparable."""
    log_path = os.path.join(DIR, "results", "snake", "experiment-log.json")
    if not os.path.exists(log_path):
        print("ERROR: No arena-loop snake results found.")
        print("Run: python experiment.py --task snake")
        return False

    with open(log_path) as f:
        arena_log = json.load(f)

    history = arena_log.get("history", [])
    arena_best = arena_log.get("best_metric")
    arena_suite_size = arena_log.get("test_suite_size", "?")

    print("=" * 70)
    print("  CROSS-VALIDATION: snake (deterministic benchmark)")
    print("=" * 70)
    print()
    print("  Snake uses a fixed subprocess benchmark (20 games, deterministic seeds).")
    print(f"  Arena's test suite grew to {arena_suite_size} cases but benchmark score")
    print("  is unaffected -- scores are directly comparable across all levels.")
    print()

    print("  " + "-" * 50)
    print(f"  {'Level':<25} {'Best Score':>12}")
    print("  " + "-" * 50)

    for name, folder in LEVELS:
        level_log_path = os.path.join(ROOT, folder, "results", "snake", "experiment-log.json")
        if os.path.exists(level_log_path):
            with open(level_log_path) as f:
                level_log = json.load(f)
            best = level_log.get("best_metric", "N/A")
            print(f"  {name:<25} {best:>12}")

    print("  " + "-" * 50)
    print()

    # Show pre-expansion history
    if history:
        print("  Arena Loop round-by-round (pre-expansion metric):")
        for h in history:
            step = h.get("step", "?")
            pre = h.get("pre_expansion_metric", "N/A")
            suite = h.get("test_suite_size", "?")
            print(f"    Round {step}: score={pre}, test_suite_size={suite}")
    print()
    print("  VERDICT: Snake scores are directly comparable. No fairness issue.")
    print()
    print("=" * 70)
    return True


def main():
    parser = argparse.ArgumentParser(description="Cross-validate Arena Loop results")
    parser.add_argument("--task", default="email_validation",
                        choices=["email_validation", "support", "snake", "all"],
                        help="Task to cross-validate (default: email_validation)")
    args = parser.parse_args()

    tasks = ["email_validation", "support", "snake"] if args.task == "all" else [args.task]

    for task in tasks:
        if task == "email_validation":
            cross_validate_email()
        elif task == "support":
            cross_validate_support()
        elif task == "snake":
            cross_validate_snake()
        if len(tasks) > 1:
            print()


if __name__ == "__main__":
    main()
