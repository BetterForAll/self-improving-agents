"""
Generate rubric-based scoring for any LLM-as-judge task.

Analyzes the task's test cases, expected answers, and knowledge base to
produce:
  1. rubric_checks.json -- per-question boolean fact checks with weights
  2. rubric.py -- scoring engine with task-appropriate quality checks

Usage:
    python tasks/generate_rubric.py --task support
    python tasks/generate_rubric.py --task your_new_task

Prerequisites:
  - Task must have config.py with USES_LLM_JUDGE = True
  - Task must have test_cases.json with question/expected pairs
  - Task should have a knowledge_base.txt (optional but recommended)

The generated rubric_checks.json should be reviewed and committed.
The generated rubric.py works out of the box but can be customized.
"""

import argparse
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DIR)

sys.path.insert(0, os.path.join(ROOT, "autoresearch"))
import llm


# -- Step 1: Analyze the task --

def load_task_context(task_name):
    """Load everything we need to understand the task."""
    task_dir = os.path.join(DIR, task_name)

    # Test cases
    test_path = os.path.join(task_dir, "test_cases.json")
    if not os.path.exists(test_path):
        print(f"ERROR: {test_path} not found.")
        print("The task needs test_cases.json with question/expected pairs.")
        sys.exit(1)
    with open(test_path) as f:
        test_cases = json.load(f)

    # Knowledge base (optional)
    kb_path = os.path.join(task_dir, "knowledge_base.txt")
    knowledge_base = ""
    if os.path.exists(kb_path):
        with open(kb_path) as f:
            knowledge_base = f.read()

    # Config
    config_path = os.path.join(task_dir, "config.py")
    if not os.path.exists(config_path):
        print(f"ERROR: {config_path} not found.")
        sys.exit(1)

    return {
        "task_name": task_name,
        "task_dir": task_dir,
        "test_cases": test_cases,
        "knowledge_base": knowledge_base,
    }


# -- Step 2: Understand what kind of task this is --

TASK_ANALYSIS_PROMPT = """\
You are analyzing a task to create a scoring rubric. The task has test cases
with questions and expected answers, and optionally a knowledge base.

Task name: {task_name}
Number of test cases: {n_cases}
Has knowledge base: {has_kb}

Sample test cases (first 3):
{sample_cases}

{kb_section}

Analyze this task and return a JSON object with:
1. "task_type": one of "qa" (question answering), "generation" (text generation),
   "classification" (categorization), or "other"
2. "domain": brief description of the domain (e.g. "customer support for a SaaS product")
3. "answer_source": "knowledge_base" if answers come from the KB, "general_knowledge"
   if they require world knowledge, or "reasoning" if they require logic
4. "quality_dimensions": list of quality aspects that matter for THIS task, each with:
   - "name": short name (e.g. "relevance", "accuracy", "tone")
   - "description": what it means for this task
   - "weight": 1 (minor), 2 (important), or -3 (penalty if violated)
   - "is_penalty": true if this is a negative check (violation = bad)
5. "contradiction_scope": what domain-specific claims should be flagged as contradictions
   (e.g. "claims about this product's pricing or features")

Return ONLY valid JSON. No markdown, no explanation.
"""


def analyze_task(context):
    """Use LLM to understand what kind of task this is."""
    sample = json.dumps(context["test_cases"][:3], indent=2)
    kb = context["knowledge_base"]
    kb_section = ""
    if kb:
        # Truncate for prompt
        kb_preview = kb[:1500] + ("..." if len(kb) > 1500 else "")
        kb_section = f"Knowledge base (first 1500 chars):\n{kb_preview}"

    prompt = TASK_ANALYSIS_PROMPT.format(
        task_name=context["task_name"],
        n_cases=len(context["test_cases"]),
        has_kb="yes" if kb else "no",
        sample_cases=sample,
        kb_section=kb_section,
    )

    return _ask_json(prompt)


def _ask_json(prompt, retries=2):
    """Ask LLM and parse JSON response, with retries on parse failure."""
    for attempt in range(retries + 1):
        response = llm.ask(prompt)
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        # Fix common JSON issues: trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if attempt < retries:
                print(f"    (JSON parse error, retrying: {e})")
            else:
                raise


# -- Step 3: Generate fact checks per question --

FACT_EXTRACTION_PROMPT = """\
You are creating boolean fact checks for scoring an AI assistant's answer.

Task type: {task_type}
Domain: {domain}

Question: {question}
Expected answer: {expected}

{kb_context}

Extract every distinct verifiable fact from the expected answer as a boolean check.
For each fact, provide:
- "description": a statement to verify (phrased so an LLM can answer YES/NO)
- "keywords": list of specific substrings that would confirm this fact if found in
  the answer. Use dollar amounts, numbers, technical terms, proper nouns. Use
  lowercase for case-insensitive matching. Empty list [] if keyword matching is
  unreliable for this fact (e.g. negations, conditional statements).
- "weight": 1 (supporting detail), 2 (key fact), or 3 (the single most critical fact)

RULES:
- Only extract facts that are in the expected answer. Do not add extra facts from
  the knowledge base that the expected answer does not mention.
- Use weight 3 sparingly -- at most 1-2 per question for the core answer.
- Keep keyword lists short (2-4 items) with specific, unlikely-to-false-match strings.
- For yes/no questions, the first check should be whether the answer gives the
  correct yes/no.

Return ONLY a JSON array. No markdown, no explanation.
"""


def generate_fact_checks(context, task_analysis):
    """Generate fact checks for all test cases."""
    all_checks = []

    for i, tc in enumerate(context["test_cases"]):
        print(f"  Q{i+1}/{len(context['test_cases'])}: {tc['question'][:50]}...", flush=True)

        kb_context = ""
        if context["knowledge_base"]:
            kb_context = (
                "The answer should be based on this knowledge base:\n"
                + context["knowledge_base"][:2000]
            )

        prompt = FACT_EXTRACTION_PROMPT.format(
            task_type=task_analysis["task_type"],
            domain=task_analysis["domain"],
            question=tc["question"],
            expected=tc["expected"],
            kb_context=kb_context,
        )

        checks = _ask_json(prompt)

        # Validate and clean
        cleaned = []
        for c in checks:
            if not isinstance(c, dict):
                continue
            if "description" not in c:
                continue
            c.setdefault("keywords", [])
            c.setdefault("weight", 1)
            c["weight"] = max(1, min(3, int(c["weight"])))
            cleaned.append(c)

        # Warn if too many checks (sign of over-extraction)
        expected_words = len(tc["expected"].split())
        if len(cleaned) > max(5, expected_words // 8):
            print(f"    WARNING: {len(cleaned)} checks for a {expected_words}-word answer "
                  f"-- may need manual trimming")

        all_checks.append({
            "question": tc["question"],
            "expected": tc["expected"],
            "fact_checks": cleaned,
        })

    return all_checks


# -- Step 4: Generate the rubric.py scoring engine --


def generate_rubric_py(task_name, quality_checks, has_kb):
    """Generate a rubric.py file as a list of lines. No string templates."""
    lines = []
    lines.append('"""')
    lines.append(f'Rubric-based scoring for the {task_name} task.')
    lines.append('')
    lines.append(f'Generated by: python tasks/generate_rubric.py --task {task_name}')
    lines.append('Review rubric_checks.json and adjust weights before committing.')
    lines.append('"""')
    lines.append('')
    lines.append('import json')
    lines.append('import os')
    lines.append('')
    lines.append('DIR = os.path.dirname(os.path.abspath(__file__))')
    lines.append('')
    lines.append('with open(os.path.join(DIR, "rubric_checks.json")) as f:')
    lines.append('    RUBRIC = json.load(f)')
    lines.append('')
    if has_kb:
        lines.append('with open(os.path.join(DIR, "knowledge_base.txt")) as f:')
        lines.append('    KNOWLEDGE_BASE = f.read()')
    else:
        lines.append('KNOWLEDGE_BASE = None')
    lines.append('')
    lines.append('')
    # json.dumps produces true/false; need Python True/False
    qc_str = json.dumps(quality_checks, indent=4)
    qc_str = qc_str.replace(': true', ': True').replace(': false', ': False')
    lines.append('QUALITY_CHECKS = ' + qc_str)
    lines.append('')
    lines.append('')
    # Helper functions -- written as literal strings, no escaping issues
    lines.append('def _keyword_match(answer, keywords):')
    lines.append('    answer_lower = answer.lower()')
    lines.append('    for kw in keywords:')
    lines.append('        if kw.lower() in answer_lower:')
    lines.append('            return True')
    lines.append('    return False')
    lines.append('')
    lines.append('')
    lines.append('def _llm_bool(prompt, llm_module):')
    lines.append('    response = llm_module.ask(prompt)')
    lines.append('    text = response.strip().upper()')
    lines.append('    words = text.split()')
    lines.append('    if words and "YES" in words[0]:')
    lines.append('        return True')
    lines.append('    if words and "NO" in words[0]:')
    lines.append('        return False')
    lines.append('    first_line = text.split("\\n")[0] if text else ""')
    lines.append('    return "YES" in first_line')
    lines.append('')
    lines.append('')
    lines.append('def _check_complete(answer):')
    lines.append('    if not answer or len(answer.strip()) < 5:')
    lines.append('        return False')
    lines.append('    return answer.strip()[-1] in ".!?)"')
    lines.append('')
    lines.append('')
    lines.append('def score_answer(rubric_entry, answer, llm_module):')
    lines.append('    checks_log = []')
    lines.append('    earned = 0')
    lines.append('    max_possible = 0')
    lines.append('    penalties = 0')
    lines.append('    question = rubric_entry["question"]')
    lines.append('')
    lines.append('    for fc in rubric_entry["fact_checks"]:')
    lines.append('        weight = fc["weight"]')
    lines.append('        max_possible += weight')
    lines.append('        keywords = fc.get("keywords", [])')
    lines.append('        description = fc["description"]')
    lines.append('        if keywords and _keyword_match(answer, keywords):')
    lines.append('            passed, method = True, "keyword"')
    lines.append('        else:')
    lines.append('            prompt = (')
    lines.append('                f\'The question was: "{question}"\\n\'')
    lines.append('                f\'The answer was: "{answer}"\\n\\n\'')
    lines.append('                f\'Check: {description}\\n\'')
    lines.append('                f\'Answer YES or NO only.\'')
    lines.append('            )')
    lines.append('            passed, method = _llm_bool(prompt, llm_module), "llm"')
    lines.append('        if passed:')
    lines.append('            earned += weight')
    lines.append('        checks_log.append({"check": description, "passed": passed,')
    lines.append('                           "weight": weight, "method": method})')
    lines.append('')
    lines.append('    for qc in QUALITY_CHECKS:')
    lines.append('        weight = qc["weight"]')
    lines.append('        is_penalty = weight < 0')
    lines.append('        invert = qc.get("invert", False)')
    lines.append('        if not is_penalty:')
    lines.append('            max_possible += weight')
    lines.append('        fmt = {"question": question, "answer": answer}')
    if has_kb:
        lines.append('        fmt["knowledge_base"] = KNOWLEDGE_BASE')
    lines.append('        prompt = qc["prompt"].format(**fmt)')
    lines.append('        raw_result = _llm_bool(prompt, llm_module)')
    lines.append('        passed = (not raw_result) if invert else raw_result')
    lines.append('        if passed and not is_penalty:')
    lines.append('            earned += weight')
    lines.append('        elif not passed and is_penalty:')
    lines.append('            penalties += abs(weight)')
    lines.append('        checks_log.append({"check": qc["description"], "passed": passed,')
    lines.append('                           "weight": weight, "method": "llm",')
    lines.append('                           "quality_check": True})')
    lines.append('')
    lines.append('    max_possible += 1')
    lines.append('    is_complete = _check_complete(answer)')
    lines.append('    if is_complete:')
    lines.append('        earned += 1')
    lines.append('    checks_log.append({"check": "Answer is complete", "passed": is_complete,')
    lines.append('                       "weight": 1, "method": "deterministic",')
    lines.append('                       "quality_check": True})')
    lines.append('')
    lines.append('    raw_score = max(0, earned - penalties)')
    lines.append('    score = (raw_score / max_possible * 100) if max_possible > 0 else 0')
    lines.append('    return {"score": round(score, 2), "max_possible": max_possible,')
    lines.append('            "earned": earned, "penalties": penalties, "checks": checks_log}')
    lines.append('')
    lines.append('')
    lines.append('def score_all(answers, llm_module, verbose=False):')
    lines.append('    if len(answers) != len(RUBRIC):')
    lines.append('        raise ValueError(f"Expected {len(RUBRIC)} answers, got {len(answers)}")')
    lines.append('    results = []')
    lines.append('    for rubric_entry, ans in zip(RUBRIC, answers):')
    lines.append('        result = score_answer(rubric_entry, ans["answer"], llm_module)')
    lines.append('        if verbose:')
    lines.append('            q = rubric_entry["question"][:50]')
    lines.append("            print(f'  Q: {q:<50s} score={result[\"score\"]:5.1f}')")
    lines.append('        results.append(result)')
    lines.append('    avg = sum(r["score"] for r in results) / len(results) if results else 0')
    lines.append('    return {"average_score": round(avg, 2), "per_question": results}')
    lines.append('')

    return "\n".join(lines)


def build_quality_checks(task_analysis, has_kb):
    """Build quality checks list from task analysis."""
    checks = []

    for dim in task_analysis.get("quality_dimensions", []):
        name = dim["name"]
        desc = dim["description"]
        weight = dim.get("weight", 1)
        is_penalty = dim.get("is_penalty", False)

        if is_penalty:
            weight = -abs(weight)

        # Build the prompt based on dimension type
        if name.lower() in ("relevance", "relevant"):
            prompt = (
                'The question was: "{question}"\n'
                'The answer was: "{answer}"\n\n'
                f'{desc} '
                'Answer YES if it attempts to answer what was asked (even if incomplete). '
                'Answer NO if it returns unrelated information or a generic error message.\n'
                'Answer YES or NO only.'
            )
        elif name.lower() in ("contradiction", "accuracy", "factual"):
            scope = task_analysis.get("contradiction_scope", "the topic")
            if has_kb:
                prompt = (
                    'Knowledge base:\n{knowledge_base}\n\n'
                    'The answer was: "{answer}"\n\n'
                    f'Does the answer make specific claims about {scope} that CONTRADICT '
                    'the knowledge base? General knowledge is fine -- only flag claims '
                    'that are factually wrong about the specific subject.\n'
                    'Answer YES if there is a contradiction, NO if there is not.\n'
                    'Answer YES or NO only.'
                )
            else:
                prompt = (
                    'The question was: "{question}"\n'
                    'The answer was: "{answer}"\n\n'
                    'Does the answer contain obviously false or fabricated information? '
                    'Answer YES if it does, NO if it does not.\n'
                    'Answer YES or NO only.'
                )
            checks.append({
                "id": name.lower(),
                "description": desc,
                "prompt": prompt,
                "weight": weight if weight < 0 else -3,
                "invert": True,
            })
            continue  # skip the default append below
        elif name.lower() in ("tone", "professional", "helpful"):
            prompt = (
                'The answer was: "{answer}"\n\n'
                f'{desc} '
                'Answer NO only if it is a raw error message, a data dump with '
                'no formatting, or rude/dismissive.\n'
                'Answer YES or NO only.'
            )
        else:
            # Generic quality dimension
            prompt = (
                'The question was: "{question}"\n'
                'The answer was: "{answer}"\n\n'
                f'{desc}\n'
                'Answer YES or NO only.'
            )

        checks.append({
            "id": name.lower().replace(" ", "_"),
            "description": desc,
            "prompt": prompt,
            "weight": weight,
        })

    # Ensure we always have at least relevance
    ids = [c["id"] for c in checks]
    if "relevance" not in ids and "relevant" not in ids:
        checks.insert(0, {
            "id": "relevance",
            "description": "Directly addresses the question asked",
            "prompt": (
                'The question was: "{question}"\n'
                'The answer was: "{answer}"\n\n'
                'Does the answer directly address the question? '
                'Answer YES or NO only.'
            ),
            "weight": 2,
        })

    return checks


# -- Main --

def main():
    parser = argparse.ArgumentParser(
        description="Generate rubric-based scoring for an LLM-as-judge task"
    )
    parser.add_argument("--task", required=True, help="Task name (folder in tasks/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print analysis without writing files")
    args = parser.parse_args()

    task_dir = os.path.join(DIR, args.task)
    if not os.path.isdir(task_dir):
        print(f"ERROR: Task directory not found: {task_dir}")
        sys.exit(1)

    print(f"Generating rubric for task: {args.task}")
    print()

    # Step 1: Load context
    context = load_task_context(args.task)
    print(f"  Loaded {len(context['test_cases'])} test cases")
    if context["knowledge_base"]:
        print(f"  Knowledge base: {len(context['knowledge_base'])} chars")
    print()

    # Step 2: Analyze the task
    print("Analyzing task type...")
    analysis = analyze_task(context)
    print(f"  Type: {analysis['task_type']}")
    print(f"  Domain: {analysis['domain']}")
    print(f"  Answer source: {analysis['answer_source']}")
    print(f"  Quality dimensions: {len(analysis.get('quality_dimensions', []))}")
    for dim in analysis.get("quality_dimensions", []):
        prefix = "PENALTY" if dim.get("is_penalty") else f"weight={dim.get('weight', 1)}"
        print(f"    - {dim['name']}: {dim['description']} [{prefix}]")
    print()

    if args.dry_run:
        print("DRY RUN -- stopping here.")
        print(json.dumps(analysis, indent=2))
        return

    # Step 3: Generate fact checks
    print("Generating fact checks per question...")
    fact_checks = generate_fact_checks(context, analysis)
    total_checks = sum(len(q["fact_checks"]) for q in fact_checks)
    print(f"  Generated {total_checks} checks across {len(fact_checks)} questions")
    print()

    # Step 4: Build quality checks
    quality_checks = build_quality_checks(analysis, bool(context["knowledge_base"]))
    print(f"Quality checks: {len(quality_checks)}")
    for qc in quality_checks:
        print(f"  - {qc['id']}: weight={qc['weight']}")
    print()

    # Step 5: Write rubric_checks.json
    checks_path = os.path.join(task_dir, "rubric_checks.json")
    with open(checks_path, "w", encoding="utf-8") as f:
        json.dump(fact_checks, f, indent=2)
    print(f"Written: {checks_path}")

    # Step 6: Write rubric.py
    has_kb = bool(context["knowledge_base"])
    rubric_content = generate_rubric_py(context["task_name"], quality_checks, has_kb)
    rubric_path = os.path.join(task_dir, "rubric.py")
    with open(rubric_path, "w", encoding="utf-8") as f:
        f.write(rubric_content)
    print(f"Written: {rubric_path}")

    # Summary
    usage = llm.get_token_usage()
    cost = (
        usage["prompt_tokens"] * 0.30 / 1_000_000 +
        usage["completion_tokens"] * 2.50 / 1_000_000
    )
    print(f"\nLLM usage: {usage['calls']} calls, {usage['total_tokens']:,} tokens, ${cost:.4f}")

    print(f"\nNext steps:")
    print(f"  1. Review {checks_path} -- trim over-extracted checks, adjust weights")
    print(f"  2. Add USES_RUBRIC = True to {args.task}/config.py")
    print(f"  3. Test: python -c \"from tasks.{args.task}.rubric import score_all\"")
    print(f"  4. Run experiment: python autoresearch/experiment.py --task {args.task}")


if __name__ == "__main__":
    main()
