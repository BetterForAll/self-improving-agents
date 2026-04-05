"""
TaskEvaluator -- wraps task-specific benchmarking, test generation, and suite management.

One interface for all task types: deterministic, adversarial, LLM-as-judge.
"""

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(DIR, ".."))
from tasks.task_runner import write_solution, run_solution

import llm
import test_agent

class TaskEvaluator:
    """Wraps task-specific benchmarking, test generation, and suite management."""

    def __init__(self, task, task_name, solution_file=None):
        self.task = task
        self.task_name = task_name
        self.solution_file = solution_file or os.path.join(DIR, f"solution_{task_name}.py")
        self.adversarial = getattr(task, "ADVERSARIAL", False)
        self.llm_judge = getattr(task, "USES_LLM_JUDGE", False)
        self.kb = getattr(task, "KNOWLEDGE_BASE", "")

    def initial_suite(self):
        if self.adversarial:
            return list(self.task.INITIAL_TESTS)
        if self.llm_judge:
            return list(self.task.TEST_CASES)
        return []

    def benchmark(self, code, test_suite):
        if self.adversarial:
            return self._score_email_validation(code, test_suite)
        if self.llm_judge:
            return self._score_support_quality(code, test_suite)
        # Generic: use task_runner subprocess
        write_solution(code, self.solution_file)
        metric, err = run_solution(self.task, self.solution_file, llm_module=llm)
        if metric is None:
            hib = self.task.HIGHER_IS_BETTER
            return float("-inf") if hib else float("inf")
        return metric

    def propose_tests(self, agent, best_code):
        if self.adversarial:
            return test_agent.propose_email_tests(agent, best_code)
        if self.llm_judge:
            return test_agent.propose_support_tests(agent, best_code, self.kb)
        return test_agent.propose_email_tests(agent, best_code)

    def measure_hardness(self, best_code, proposed):
        if self.adversarial:
            return self._count_validation_failures(best_code, proposed)
        if self.llm_judge:
            scores = self._score_questions(best_code, proposed)
            return sum(100 - s for s in scores) if scores else 0
        return 0

    def add_to_suite(self, test_suite, best_tests, best_agent_id):
        test_suite.extend(best_tests)
        kind = "questions" if self.llm_judge else "tests"
        print(f"  [SUITE] Added {len(best_tests)} {kind} from {best_agent_id} "
              f"(suite now {len(test_suite)})")

    def format_hardness(self, hardness, proposed):
        count = len(proposed) if isinstance(proposed, list) else 1
        if self.llm_judge:
            return f"{count} questions, hardness={hardness:.0f}"
        return f"{count} tests, {hardness} break current best"

    def get_failures(self, code, test_suite):
        if not self.adversarial:
            return ""
        return self._get_failures_text(code, test_suite)

    def build_prompt(self, code, metric, test_suite):
        if self.adversarial:
            failures = self.get_failures(code, test_suite)
            return self.task.build_prompt(
                code, metric, failures=failures,
                correct=int(metric * len(test_suite)), total=len(test_suite))
        return None  # use default code_agent.propose

    # -- Private helpers --

    def _score_email_validation(self, code, test_suite):
        ns = {}
        # Run the code string in an isolated namespace to extract functions from it
        try:
            exec(compile(code, "<agent>", "exec"), ns)
        except Exception:
            return 0.0
        fn = ns.get("validate_email")
        if fn is None:
            return 0.0
        correct = 0
        for tc in test_suite:
            try:
                if bool(fn(tc["email"])) == tc["valid"]:
                    correct += 1
            except Exception:
                pass
        return correct / len(test_suite) if test_suite else 0.0

    def _score_support_quality(self, code, test_suite):
        ns = {}
        # Run the code string in an isolated namespace to extract functions from it
        try:
            exec(compile(code, "<agent>", "exec"), ns)
        except Exception:
            return 0.0
        fn = ns.get("answer_question")
        if fn is None:
            return 0.0
        qa_pairs = self._build_qa_pairs(fn, test_suite)
        raw = llm.ask(self._judge_prompt(qa_pairs))
        return self._parse_judge_avg(raw)

    def _score_questions(self, code, test_cases):
        ns = {}
        try:
            exec(compile(code, "<agent>", "exec"), ns)
        except Exception:
            return [0.0] * len(test_cases)
        fn = ns.get("answer_question")
        if fn is None:
            return [0.0] * len(test_cases)
        qa_pairs = self._build_qa_pairs(fn, test_cases)
        raw = llm.ask(self._judge_prompt(qa_pairs))
        return self._parse_judge_list(raw, len(test_cases))

    def _build_qa_pairs(self, fn, test_cases):
        parts = []
        for i, tc in enumerate(test_cases):
            try:
                answer = str(fn(tc["question"], self.kb))
            except Exception:
                answer = "ERROR: function crashed"
            parts.append(f"\nQuestion {i+1}: {tc['question']}\n"
                         f"Expected: {tc['expected']}\nActual: {answer}")
        return "".join(parts)

    def _judge_prompt(self, qa_pairs):
        return (
            "You are a quality judge for a customer support AI. Score each answer 0-100.\n\n"
            "Criteria: Accuracy (40%), Completeness (30%), Tone (15%), Conciseness (15%).\n\n"
            f"ANSWERS:{qa_pairs}\n\n"
            'Return ONLY JSON: {"scores": [score1, score2, ...], "average": average_score}')

    def _parse_judge_avg(self, response):
        import re
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        try:
            return float(json.loads(text).get("average", 0))
        except (json.JSONDecodeError, ValueError):
            numbers = re.findall(r'\d+\.?\d*', text)
            return float(numbers[-1]) if numbers else 0.0

    def _parse_judge_list(self, response, n):
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        try:
            return [float(s) for s in json.loads(text).get("scores", [])]
        except (json.JSONDecodeError, ValueError):
            return [50.0] * n

    def _count_validation_failures(self, code, test_cases):
        ns = {}
        try:
            exec(compile(code, "<agent>", "exec"), ns)
        except Exception:
            return len(test_cases)
        fn = ns.get("validate_email")
        if fn is None:
            return len(test_cases)
        wrong = 0
        for tc in test_cases:
            try:
                if bool(fn(tc["email"])) != tc["valid"]:
                    wrong += 1
            except Exception:
                wrong += 1
        return wrong

    def _get_failures_text(self, code, test_suite):
        ns = {}
        try:
            exec(compile(code, "<agent>", "exec"), ns)
        except Exception:
            return "Code doesn't compile"
        fn = ns.get("validate_email")
        if fn is None:
            return "No validate_email function"
        failures = []
        for tc in test_suite:
            try:
                result = bool(fn(tc["email"]))
                if result != tc["valid"]:
                    failures.append(f"  {tc['email']!r}: expected {tc['valid']}, got {result}")
            except Exception as e:
                failures.append(f"  {tc['email']!r}: crashed ({e})")
        return "\n".join(failures[:10]) if failures else "None"
