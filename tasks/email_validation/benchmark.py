"""
Benchmark harness for email validation task.

Runs solution.py (which must define validate_email) against test cases.
Reports accuracy as fraction of correctly classified emails.

Usage: python benchmark.py <solution_file> [test_file]
"""

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TESTS = os.path.join(DIR, "initial_tests.json")


if __name__ == "__main__":
    solution_file = sys.argv[1] if len(sys.argv) > 1 else "solution.py"
    test_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TESTS

    # Load solution
    ns = {}
    with open(solution_file) as f:
        exec(compile(f.read(), solution_file, "exec"), ns)
    validate_email = ns["validate_email"]

    # Load test cases
    with open(test_file) as f:
        tests = json.load(f)

    # Run tests
    correct = 0
    total = len(tests)
    failures = []

    for tc in tests:
        email = tc["email"]
        expected = tc["valid"]
        try:
            result = bool(validate_email(email))
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

    print(f"accuracy:{accuracy:.4f}")
    print(f"correct:{correct}")
    print(f"total:{total}")
    print(f"failures:{json.dumps(failures)}")
