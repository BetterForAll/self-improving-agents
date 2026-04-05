"""Configuration for the email validation task (adversarial arena)."""

import json
import os

TASK_NAME = "email_validation"
METRIC_NAME = "accuracy"
HIGHER_IS_BETTER = True
PERFECT_SCORE = 1.0  # stop early when accuracy reaches 100%

# For the adversarial arena: test agents generate new test cases
# that get added to the test suite. This flag tells the arena
# to use the test agent system.
ADVERSARIAL = True

DIR = os.path.dirname(os.path.abspath(__file__))
INITIAL_TESTS_PATH = os.path.join(DIR, "initial_tests.json")

with open(INITIAL_TESTS_PATH) as f:
    INITIAL_TESTS = json.load(f)

CODE_PROMPT_TEMPLATE = (
    "Here is a Python function that validates email addresses:\n\n"
    "{code}\n\n"
    "Current accuracy: {metric:.0%} ({correct}/{total} test cases correct).\n\n"
    "These test cases FAILED:\n{failures}\n\n"
    "Write an improved version that handles these edge cases correctly. "
    "Return ONLY the function definition. Keep the name validate_email."
)

TEST_PROMPT_TEMPLATE = (
    "You are an adversarial tester. Your goal is to find email addresses "
    "that will break this validation function:\n\n"
    "{code}\n\n"
    "Current accuracy: {metric:.0%} on {total} test cases.\n\n"
    "Generate 5 tricky email test cases that this function will likely "
    "get wrong. Include both valid emails it might reject and invalid "
    "emails it might accept.\n\n"
    "Return ONLY a JSON array:\n"
    '[{{"email": "...", "valid": true/false, "reason": "why this is tricky"}}]'
)


def build_prompt(code, metric, failures="", correct=0, total=0):
    return CODE_PROMPT_TEMPLATE.format(
        code=code, metric=metric, failures=failures,
        correct=correct, total=total
    )


def build_test_prompt(code, metric, total):
    return TEST_PROMPT_TEMPLATE.format(
        code=code, metric=metric, total=total
    )
