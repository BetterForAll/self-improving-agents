"""
Benchmark harness for customer support task.

Runs solution.py (which must define answer_question), collects answers
to test questions, and outputs them as JSON for the LLM judge.

Usage: python benchmark.py <solution_file>
"""

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))

# Load knowledge base and test cases from files
with open(os.path.join(DIR, "knowledge_base.txt")) as f:
    KNOWLEDGE_BASE = f.read()

with open(os.path.join(DIR, "test_cases.json")) as f:
    TEST_CASES = json.load(f)


if __name__ == "__main__":
    solution_file = sys.argv[1] if len(sys.argv) > 1 else "solution.py"
    ns = {}
    with open(solution_file) as f:
        exec(compile(f.read(), solution_file, "exec"), ns)

    answer_question = ns["answer_question"]
    scores = []
    for tc in TEST_CASES:
        answer = answer_question(tc["question"], KNOWLEDGE_BASE)
        scores.append({"question": tc["question"], "answer": str(answer)})
    print("answers:" + json.dumps(scores))
