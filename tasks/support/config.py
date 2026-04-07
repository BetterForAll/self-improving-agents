"""Configuration for the customer support optimization task (rubric-based scoring)."""

import json
import os

TASK_NAME = "support"
METRIC_NAME = "quality_score"
HIGHER_IS_BETTER = True
PERFECT_SCORE = 100.0  # stop early when quality reaches 100/100
USES_LLM_JUDGE = True
USES_RUBRIC = True  # use boolean rubric (keyword + LLM YES/NO) instead of open-ended 0-100
JUDGE_RUNS = 3  # only used when USES_RUBRIC is False

DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIR, "knowledge_base.txt")) as f:
    KNOWLEDGE_BASE = f.read()

with open(os.path.join(DIR, "test_cases.json")) as f:
    TEST_CASES = json.load(f)

JUDGE_PROMPT = """\
You are a quality judge for a customer support AI. Score each answer on a 0-100 scale.

Scoring criteria:
- Accuracy (40%): Does the answer match the expected answer factually?
- Completeness (30%): Does it include all relevant information?
- Tone (15%): Is it helpful, professional, and natural?
- Conciseness (15%): Is it appropriately brief without omitting key info?

EXPECTED ANSWERS AND ACTUAL ANSWERS:
{qa_pairs}

Return ONLY a JSON object:
{{"scores": [score1, score2, ...], "average": average_score}}
"""

PROMPT_TEMPLATE = (
    "You are writing a Python function that answers customer questions about CloudSync Pro.\n\n"
    "KNOWLEDGE BASE (the function receives this as the knowledge_base parameter):\n"
    "{kb}\n\n"
    "CURRENT FUNCTION:\n{code}\n\n"
    "Current quality score: {metric:.1f}/100 (judged by LLM on 10 test questions).\n\n"
    "Write an improved version that gives more accurate, complete, and helpful answers. "
    "The function should parse the knowledge_base string to find relevant info for each question. "
    "Return ONLY the function definition."
)


def build_prompt(code, metric):
    return PROMPT_TEMPLATE.format(code=code, metric=metric, kb=KNOWLEDGE_BASE[:500] + "...")
