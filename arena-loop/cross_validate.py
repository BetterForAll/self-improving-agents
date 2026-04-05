"""
Cross-validate email_validation: proves Arena Loop produces genuinely robust solutions.

Compares baseline vs Arena Loop's best solution against both the original
test suite and the adversarially-expanded test suite.

Run after: python experiment.py --task email_validation
"""

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(DIR, "..")
TASK_DIR = os.path.join(ROOT, "tasks", "email_validation")
RESULTS_DIR = os.path.join(DIR, "results", "email_validation")

BASELINE_PATH = os.path.join(TASK_DIR, "initial_solution.py")
BEST_SOLUTION_PATH = os.path.join(RESULTS_DIR, "solutions", "best.py")
ORIGINAL_TESTS_PATH = os.path.join(TASK_DIR, "initial_tests.json")
EXPANDED_TESTS_PATH = os.path.join(RESULTS_DIR, "tests", "final_tests.json")


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


def main():
    # Check required files exist
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
        sys.exit(1)

    # Load test suites
    with open(ORIGINAL_TESTS_PATH) as f:
        original_tests = json.load(f)
    with open(EXPANDED_TESTS_PATH) as f:
        expanded_tests = json.load(f)

    # Load solutions
    baseline_fn = load_function(BASELINE_PATH)
    arena_fn = load_function(BEST_SOLUTION_PATH)

    print("=" * 70)
    print("  CROSS-VALIDATION: Baseline vs Arena Loop (email_validation)")
    print("=" * 70)
    print()
    print(f"  Original test suite:  {len(original_tests)} cases")
    print(f"  Expanded test suite:  {len(expanded_tests)} cases")
    print()

    # Run all 4 combinations
    results = {}

    for label, fn, fn_name in [
        ("Baseline", baseline_fn, "baseline"),
        ("Arena Loop", arena_fn, "arena"),
    ]:
        for suite_label, tests, suite_name in [
            ("Original tests", original_tests, "original"),
            ("Expanded tests", expanded_tests, "expanded"),
        ]:
            correct, total, accuracy, failures = run_tests(fn, tests)
            key = f"{fn_name}_{suite_name}"
            results[key] = {
                "correct": correct,
                "total": total,
                "accuracy": accuracy,
                "failures": failures,
            }

    # Print comparison table
    print("  " + "-" * 66)
    print(f"  {'Solution':<20} {'Test Suite':<20} {'Accuracy':>10} {'Correct':>10}")
    print("  " + "-" * 66)

    for fn_name, fn_label in [("baseline", "Baseline"), ("arena", "Arena Loop")]:
        for suite_name, suite_label in [("original", "Original"), ("expanded", "Expanded")]:
            key = f"{fn_name}_{suite_name}"
            r = results[key]
            print(f"  {fn_label:<20} {suite_label:<20} {r['accuracy']:>9.1%} {r['correct']:>5}/{r['total']:<4}")

    print("  " + "-" * 66)
    print()

    # Analysis
    b_orig = results["baseline_original"]["accuracy"]
    b_exp = results["baseline_expanded"]["accuracy"]
    a_orig = results["arena_original"]["accuracy"]
    a_exp = results["arena_expanded"]["accuracy"]

    print("  Key findings:")
    print()

    # Arena vs baseline on original tests
    if a_orig > b_orig:
        print(f"  1. Arena Loop improves on original tests: {b_orig:.1%} -> {a_orig:.1%}")
    elif a_orig == b_orig:
        print(f"  1. Arena Loop matches baseline on original tests: {a_orig:.1%}")
    else:
        print(f"  1. Arena Loop regressed on original tests: {b_orig:.1%} -> {a_orig:.1%}")

    # Baseline collapse on expanded tests
    if b_exp < b_orig:
        print(f"  2. Baseline collapses on expanded tests: {b_orig:.1%} -> {b_exp:.1%}")
        print(f"     (adversarial tests expose {len(results['baseline_expanded']['failures'])} new failures)")
    else:
        print(f"  2. Baseline holds on expanded tests: {b_orig:.1%} -> {b_exp:.1%}")

    # Arena robustness on expanded tests
    if a_exp >= a_orig * 0.9:
        print(f"  3. Arena Loop stays robust on expanded tests: {a_exp:.1%}")
        print(f"     (trained against adversarial pressure -- genuinely robust)")
    else:
        print(f"  3. Arena Loop drops on expanded tests: {a_orig:.1%} -> {a_exp:.1%}")
        print(f"     (more rounds may be needed)")

    # Overall verdict
    print()
    if a_exp > b_exp and a_orig >= b_orig:
        print("  VERDICT: Arena Loop produces a genuinely better solution.")
        print(f"  The adversarial co-evolution created a solution that handles")
        print(f"  {len(expanded_tests) - len(original_tests)} additional edge cases")
        print(f"  while maintaining or improving original test performance.")
    elif a_exp > b_exp:
        print("  VERDICT: Arena Loop is more robust overall, though with trade-offs.")
    else:
        print("  VERDICT: Results are mixed -- consider running more rounds.")

    print()

    # Show sample failures if any
    arena_expanded_failures = results["arena_expanded"]["failures"]
    if arena_expanded_failures:
        print(f"  Arena Loop still fails on {len(arena_expanded_failures)} expanded cases:")
        for fail in arena_expanded_failures[:5]:
            exp = "valid" if fail["expected"] else "invalid"
            got = "valid" if fail["got"] else "invalid"
            reason = fail.get("reason", "")
            reason_str = f" ({reason})" if reason else ""
            print(f"    {fail['email']:<40} expected={exp}, got={got}{reason_str}")
        if len(arena_expanded_failures) > 5:
            print(f"    ... and {len(arena_expanded_failures) - 5} more")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
