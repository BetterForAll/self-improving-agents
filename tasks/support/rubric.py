"""
Rubric-based scoring for the customer support task.

Scores answers using boolean fact checks (keyword + LLM fallback) and
quality checks. Much more stable than open-ended LLM-as-judge scoring.

Usage:
    from tasks.support.rubric import score_answer, score_all

    # Score a single answer
    result = score_answer(question_rubric, answer, llm_module)

    # Score all 10 answers
    results = score_all(answers, llm_module)
"""

import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIR, "rubric_checks.json")) as f:
    RUBRIC = json.load(f)

with open(os.path.join(DIR, "knowledge_base.txt")) as f:
    KNOWLEDGE_BASE = f.read()


# -- Quality checks (same for every question) --

QUALITY_CHECKS = [
    {
        "id": "relevance",
        "description": "Directly addresses the question asked",
        "prompt": (
            "The customer asked: \"{question}\"\n"
            "The agent answered: \"{answer}\"\n\n"
            "Does the answer directly address the customer's question? "
            "Answer YES if it attempts to answer what was asked (even if "
            "incomplete). Answer NO if it returns unrelated information, "
            "a generic error message, or says it cannot find an answer "
            "when the knowledge base contains the information.\n"
            "Answer YES or NO only."
        ),
        "weight": 2,
    },
    {
        "id": "contradiction",
        "description": "Does NOT contradict the knowledge base about this product",
        "prompt": (
            "Knowledge base:\n{knowledge_base}\n\n"
            "The agent answered: \"{answer}\"\n\n"
            "Does the answer make any specific claims about THIS PRODUCT "
            "(CloudSync Pro) that CONTRADICT the knowledge base above? "
            "General knowledge and helpful context are fine -- only flag "
            "claims about this specific product's features, pricing, or "
            "policies that are factually wrong.\n"
            "Answer YES if there is a contradiction, NO if there is not.\n"
            "Answer YES or NO only."
        ),
        "weight": -3,
        "invert": True,
    },
    {
        "id": "tone",
        "description": "Professional and helpful tone",
        "prompt": (
            "The agent answered: \"{answer}\"\n\n"
            "Is this answer professional and helpful in tone? "
            "Answer NO only if it is a raw error message, a raw data dump "
            "with no formatting or greeting, or rude/dismissive.\n"
            "Answer YES or NO only."
        ),
        "weight": 1,
    },
]


def _keyword_match(answer, keywords):
    """Check if ANY keyword substring is found in the answer (case-insensitive)."""
    answer_lower = answer.lower()
    for kw in keywords:
        if kw.lower() in answer_lower:
            return True
    return False


def _llm_bool(prompt, llm_module):
    """Ask LLM a YES/NO question. Returns True for YES, False for NO."""
    response = llm_module.ask(prompt)
    text = response.strip().upper()
    # Extract first YES or NO from response
    if "YES" in text.split()[0] if text else False:
        return True
    if "NO" in text.split()[0] if text else False:
        return False
    # Fallback: look anywhere in first line
    first_line = text.split("\n")[0] if text else ""
    return "YES" in first_line


def _check_complete(answer):
    """Deterministic check: answer is not cut off mid-sentence."""
    if not answer or len(answer.strip()) < 5:
        return False
    last_char = answer.strip()[-1]
    return last_char in ".!?)\""


def score_answer(rubric_entry, answer, llm_module):
    """Score a single answer against its rubric.

    Returns dict with:
        score: 0-100 normalized score
        max_possible: total possible weight
        earned: earned weight
        checks: list of {check, passed, weight, method}
    """
    checks_log = []
    earned = 0
    max_possible = 0
    penalties = 0

    question = rubric_entry["question"]

    # -- Fact checks --
    for fc in rubric_entry["fact_checks"]:
        weight = fc["weight"]
        max_possible += weight

        keywords = fc.get("keywords", [])
        description = fc["description"]

        # Step 1: try keyword match
        if keywords and _keyword_match(answer, keywords):
            passed = True
            method = "keyword"
        else:
            # Step 2: LLM fallback
            prompt = (
                f"The customer asked: \"{question}\"\n"
                f"The agent answered: \"{answer}\"\n\n"
                f"Check: {description}\n"
                f"Answer YES or NO only."
            )
            passed = _llm_bool(prompt, llm_module)
            method = "llm"

        if passed:
            earned += weight
        checks_log.append({
            "check": description,
            "passed": passed,
            "weight": weight,
            "method": method,
        })

    # -- Quality checks --
    for qc in QUALITY_CHECKS:
        weight = qc["weight"]
        is_penalty = weight < 0
        invert = qc.get("invert", False)

        if not is_penalty:
            max_possible += weight

        prompt = qc["prompt"].format(
            question=question,
            answer=answer,
            knowledge_base=KNOWLEDGE_BASE,
        )
        raw_result = _llm_bool(prompt, llm_module)

        # For "contradiction" check: YES means there IS a contradiction (bad)
        if invert:
            passed = not raw_result  # no contradiction = good
        else:
            passed = raw_result

        if passed and not is_penalty:
            earned += weight
        elif not passed and is_penalty:
            penalties += abs(weight)

        checks_log.append({
            "check": qc["description"],
            "passed": passed,
            "weight": weight,
            "method": "llm",
            "quality_check": True,
        })

    # -- Completeness (deterministic) --
    complete_weight = 1
    max_possible += complete_weight
    is_complete = _check_complete(answer)
    if is_complete:
        earned += complete_weight
    checks_log.append({
        "check": "Answer is complete (not cut off mid-sentence)",
        "passed": is_complete,
        "weight": complete_weight,
        "method": "deterministic",
        "quality_check": True,
    })

    # -- Final score --
    raw_score = max(0, earned - penalties)
    score = (raw_score / max_possible * 100) if max_possible > 0 else 0

    return {
        "score": round(score, 2),
        "max_possible": max_possible,
        "earned": earned,
        "penalties": penalties,
        "checks": checks_log,
    }


def score_all(answers, llm_module, verbose=False):
    """Score all answers against the rubric.

    answers: list of {"question": str, "answer": str} dicts
    Returns dict with:
        average_score: 0-100
        per_question: list of score_answer results
    """
    if len(answers) != len(RUBRIC):
        raise ValueError(
            f"Expected {len(RUBRIC)} answers, got {len(answers)}"
        )

    results = []
    for rubric_entry, ans in zip(RUBRIC, answers):
        result = score_answer(rubric_entry, ans["answer"], llm_module)
        if verbose:
            q = rubric_entry["question"][:50]
            print(f"  Q: {q:<50s} score={result['score']:5.1f}")
        results.append(result)

    avg = sum(r["score"] for r in results) / len(results) if results else 0

    return {
        "average_score": round(avg, 2),
        "per_question": results,
    }
