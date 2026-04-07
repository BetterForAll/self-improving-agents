"""
Generate rubric-based scoring for any LLM-as-judge task.

Works with any task that uses LLM-as-judge evaluation, regardless of the
output format (Q&A, code generation, summarization, classification, etc.).

The generator:
  1. Reads the task's test cases, config, benchmark, and any reference files
  2. Asks the LLM to analyze what kind of task this is
  3. Asks the LLM to extract boolean checks per test case
  4. Generates rubric_checks.json and rubric.py

Usage:
    python tasks/generate_rubric.py --task support
    python tasks/generate_rubric.py --task your_new_task
    python tasks/generate_rubric.py --task your_task --dry-run

Prerequisites:
  - Task folder in tasks/ with config.py and benchmark.py
  - Test cases: either test_cases.json or derivable from benchmark.py
  - config.py should have USES_LLM_JUDGE = True
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


def _ask_json(prompt, retries=2):
    """Ask LLM and parse JSON response, with retries on parse failure."""
    for attempt in range(retries + 1):
        response = llm.ask(prompt)
        text = response.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if attempt < retries:
                print(f"    (JSON parse error, retrying: {e})")
            else:
                raise


# -- Step 1: Load task context --

def load_task_context(task_name):
    """Load all available files from the task directory."""
    task_dir = os.path.join(DIR, task_name)
    context = {
        "task_name": task_name,
        "task_dir": task_dir,
        "test_cases": None,
        "knowledge_base": "",
        "config_source": "",
        "benchmark_source": "",
        "initial_solution_source": "",
    }

    # Test cases (various possible names)
    for name in ["test_cases.json", "initial_tests.json", "tests.json"]:
        path = os.path.join(task_dir, name)
        if os.path.exists(path):
            with open(path) as f:
                context["test_cases"] = json.load(f)
            context["test_cases_file"] = name
            break

    # Knowledge base (optional)
    for name in ["knowledge_base.txt", "knowledge_base.md", "reference.txt"]:
        path = os.path.join(task_dir, name)
        if os.path.exists(path):
            with open(path) as f:
                context["knowledge_base"] = f.read()
            break

    # Config source (helps LLM understand the task)
    config_path = os.path.join(task_dir, "config.py")
    if os.path.exists(config_path):
        with open(config_path) as f:
            context["config_source"] = f.read()

    # Benchmark source (shows how outputs are evaluated)
    bench_path = os.path.join(task_dir, "benchmark.py")
    if os.path.exists(bench_path):
        with open(bench_path) as f:
            context["benchmark_source"] = f.read()

    # Initial solution (shows what the solution looks like)
    sol_path = os.path.join(task_dir, "initial_solution.py")
    if os.path.exists(sol_path):
        with open(sol_path) as f:
            context["initial_solution_source"] = f.read()

    return context


# -- Step 2: Analyze the task --

TASK_ANALYSIS_PROMPT = """\
You are analyzing a software task to create a scoring rubric. Your rubric
must work for whatever type of task this is -- Q&A, code generation,
summarization, classification, or anything else.

Task name: {task_name}

Config.py:
{config_source}

Benchmark.py:
{benchmark_source}

{test_section}

{kb_section}

{solution_section}

Analyze this task and return a JSON object:

1. "task_type": describe what the task does (free text, be specific)
2. "input_field": the field name in test cases that contains the input
   (e.g. "question", "prompt", "email", "document"). null if no test cases.
3. "expected_field": the field name that contains the expected output
   (e.g. "expected", "valid", "answer", "category"). null if no test cases.
4. "output_type": what the solution produces -- "text" (free text answers),
   "code" (source code), "boolean" (true/false), "number" (numeric),
   "category" (classification label), or "structured" (JSON/dict)
5. "domain": brief description of the domain
6. "reference_material": "knowledge_base" if there is a KB the solution
   should use, "test_data" if expected outputs define correctness, or
   "open_ended" if quality is subjective
7. "quality_dimensions": list of quality aspects that matter for THIS
   specific task. Each with:
   - "name": short name
   - "description": what it means, phrased as a YES/NO question an LLM
     can answer about the output (e.g. "Does the output address the input
     directly?"). Be specific to this task.
   - "weight": 1 (minor), 2 (important)
   - "is_penalty": true if this is a negative check (weight will be -3)
   Include dimensions that apply to THIS task, not generic ones. Think about
   what makes a good output for this specific domain.
8. "contradiction_scope": what domain-specific false claims to watch for

Return ONLY valid JSON. No markdown.
"""


def analyze_task(context):
    """Use LLM to understand what kind of task this is."""
    tc = context["test_cases"]
    test_section = ""
    if tc:
        sample = json.dumps(tc[:3], indent=2)
        test_section = f"Test cases ({len(tc)} total, first 3 shown):\n{sample}"
    else:
        test_section = "No test_cases.json found."

    kb = context["knowledge_base"]
    kb_section = ""
    if kb:
        kb_preview = kb[:1500] + ("..." if len(kb) > 1500 else "")
        kb_section = f"Knowledge base:\n{kb_preview}"

    sol = context["initial_solution_source"]
    solution_section = ""
    if sol:
        sol_preview = sol[:1000] + ("..." if len(sol) > 1000 else "")
        solution_section = f"Initial solution (what the code looks like):\n{sol_preview}"

    prompt = TASK_ANALYSIS_PROMPT.format(
        task_name=context["task_name"],
        config_source=context["config_source"][:1000] or "(not found)",
        benchmark_source=context["benchmark_source"][:1500] or "(not found)",
        test_section=test_section,
        kb_section=kb_section,
        solution_section=solution_section,
    )

    return _ask_json(prompt)


# -- Step 3: Generate checks per test case --

CHECK_EXTRACTION_PROMPT = """\
You are creating boolean checks for scoring the output of an AI system.

Task: {task_type}
Domain: {domain}
Output type: {output_type}

Input ({input_field}): {input_value}
Expected output ({expected_field}): {expected_value}

{reference_section}

Extract boolean checks that verify the output is correct. Each check should
be something an LLM can answer YES or NO about the actual output.

For each check provide:
- "description": a statement to verify (phrased for YES/NO evaluation,
  e.g. "Does the output mention X?", "Does the code handle Y?",
  "Is the classification Z?")
- "keywords": list of specific substrings that would confirm this check
  if found in the output. Use numbers, technical terms, proper nouns,
  specific phrases. Lowercase for case-insensitive matching. Empty list []
  if keyword matching is unreliable (e.g. negations, logic checks,
  code structure).
- "weight": 1 (supporting detail), 2 (key requirement), or 3 (critical --
  the output is wrong without this)

RULES:
- Extract checks ONLY from the expected output. Do not invent extra checks.
- Use weight 3 for at most 1-2 checks per test case (the core requirement).
- Keep keyword lists short (2-4 items) with specific strings.
- Adapt checks to the output type: for code, check function behavior and
  edge cases; for text, check content and facts; for classification, check
  the label.

Return ONLY a JSON array. No markdown.
"""


def generate_checks(context, analysis):
    """Generate checks for all test cases."""
    tc = context["test_cases"]
    if not tc:
        print("  ERROR: No test cases found. Cannot generate checks.")
        return []

    input_field = analysis.get("input_field", "question")
    expected_field = analysis.get("expected_field", "expected")
    all_checks = []

    for i, case in enumerate(tc):
        input_val = case.get(input_field, str(case))
        expected_val = case.get(expected_field, str(case))
        label = str(input_val)[:50]
        print(f"  {i+1}/{len(tc)}: {label}...", flush=True)

        ref_section = ""
        if context["knowledge_base"]:
            ref_section = (
                "Reference material (knowledge base):\n"
                + context["knowledge_base"][:2000]
            )

        prompt = CHECK_EXTRACTION_PROMPT.format(
            task_type=analysis["task_type"],
            domain=analysis["domain"],
            output_type=analysis.get("output_type", "text"),
            input_field=input_field,
            expected_field=expected_field,
            input_value=str(input_val),
            expected_value=str(expected_val),
            reference_section=ref_section,
        )

        checks = _ask_json(prompt)

        cleaned = []
        for c in checks:
            if not isinstance(c, dict) or "description" not in c:
                continue
            c.setdefault("keywords", [])
            c.setdefault("weight", 1)
            c["weight"] = max(1, min(3, int(c["weight"])))
            cleaned.append(c)

        expected_words = len(str(expected_val).split())
        if len(cleaned) > max(5, expected_words // 8):
            print(f"    WARNING: {len(cleaned)} checks for a {expected_words}-word "
                  f"expected output -- may need trimming")

        all_checks.append({
            input_field: input_val,
            expected_field: expected_val,
            "fact_checks": cleaned,
        })

    return all_checks


# -- Step 4: Build quality checks from analysis --

def build_quality_checks(analysis, has_kb):
    """Build quality check prompts from the LLM's analysis."""
    checks = []
    input_field = analysis.get("input_field", "question")

    for dim in analysis.get("quality_dimensions", []):
        name = dim["name"]
        desc = dim["description"]
        weight = dim.get("weight", 1)
        is_penalty = dim.get("is_penalty", False)

        if is_penalty:
            weight = -abs(weight) if abs(weight) > 1 else -3

        # The description should already be phrased as a YES/NO question
        # (we asked for that in the analysis prompt). Wrap it in a prompt.
        if is_penalty:
            prompt = (
                'The input was: "{' + input_field + '}"\n'
                'The output was: "{answer}"\n\n'
                + desc + '\n'
                'Answer YES or NO only.'
            )
            if has_kb:
                prompt = (
                    'Knowledge base:\n{knowledge_base}\n\n'
                    + prompt
                )
            checks.append({
                "id": name.lower().replace(" ", "_"),
                "description": desc,
                "prompt": prompt,
                "weight": weight,
                "invert": True,
            })
        else:
            prompt = (
                'The input was: "{' + input_field + '}"\n'
                'The output was: "{answer}"\n\n'
                + desc + '\n'
                'Answer YES or NO only.'
            )
            checks.append({
                "id": name.lower().replace(" ", "_"),
                "description": desc,
                "prompt": prompt,
                "weight": weight,
            })

    return checks


# -- Step 5: Generate rubric.py --

def generate_rubric_py(task_name, quality_checks, has_kb, input_field):
    """Generate rubric.py as a list of lines."""
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
    lines.append(f'INPUT_FIELD = {json.dumps(input_field)}')
    lines.append('')
    qc_str = json.dumps(quality_checks, indent=4)
    qc_str = qc_str.replace(': true', ': True').replace(': false', ': False')
    lines.append('QUALITY_CHECKS = ' + qc_str)
    lines.append('')
    lines.append('')
    lines.append('def _keyword_match(output, keywords):')
    lines.append('    output_lower = output.lower()')
    lines.append('    for kw in keywords:')
    lines.append('        if kw.lower() in output_lower:')
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
    lines.append('def _check_complete(output):')
    lines.append('    if not output or len(output.strip()) < 5:')
    lines.append('        return False')
    lines.append('    return output.strip()[-1] in ".!?)\'"')
    lines.append('')
    lines.append('')
    lines.append('def score_answer(rubric_entry, answer, llm_module):')
    lines.append('    """Score a single output against its rubric entry."""')
    lines.append('    checks_log = []')
    lines.append('    earned = 0')
    lines.append('    max_possible = 0')
    lines.append('    penalties = 0')
    lines.append('    input_val = rubric_entry.get(INPUT_FIELD, "")')
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
    lines.append('                f\'The input was: "{input_val}"\\n\'')
    lines.append('                f\'The output was: "{answer}"\\n\\n\'')
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
    lines.append('        fmt = {INPUT_FIELD: input_val, "answer": answer}')
    lines.append('        if KNOWLEDGE_BASE is not None:')
    lines.append('            fmt["knowledge_base"] = KNOWLEDGE_BASE')
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
    lines.append('    checks_log.append({"check": "Output is complete", "passed": is_complete,')
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
    lines.append('    """Score all outputs. answers = list of {"question": ..., "answer": ...}."""')
    lines.append('    if len(answers) != len(RUBRIC):')
    lines.append('        raise ValueError(f"Expected {len(RUBRIC)} answers, got {len(answers)}")')
    lines.append('    results = []')
    lines.append('    for rubric_entry, ans in zip(RUBRIC, answers):')
    lines.append('        result = score_answer(rubric_entry, ans["answer"], llm_module)')
    lines.append('        if verbose:')
    lines.append('            label = str(rubric_entry.get(INPUT_FIELD, ""))[:50]')
    lines.append("            print(f'  {label:<50s} score={result[\"score\"]:5.1f}')")
    lines.append('        results.append(result)')
    lines.append('    avg = sum(r["score"] for r in results) / len(results) if results else 0')
    lines.append('    return {"average_score": round(avg, 2), "per_question": results}')
    lines.append('')

    return "\n".join(lines)


# -- Main --

def main():
    parser = argparse.ArgumentParser(
        description="Generate rubric-based scoring for any LLM-as-judge task"
    )
    parser.add_argument("--task", required=True, help="Task name (folder in tasks/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print analysis without generating files")
    args = parser.parse_args()

    task_dir = os.path.join(DIR, args.task)
    if not os.path.isdir(task_dir):
        print(f"ERROR: Task directory not found: {task_dir}")
        sys.exit(1)

    print(f"Generating rubric for task: {args.task}")
    print()

    # Step 1: Load context
    context = load_task_context(args.task)
    if context["test_cases"]:
        print(f"  Test cases: {len(context['test_cases'])} loaded")
    else:
        print("  WARNING: No test cases found")
    if context["knowledge_base"]:
        print(f"  Knowledge base: {len(context['knowledge_base'])} chars")
    if context["benchmark_source"]:
        print(f"  Benchmark: found")
    if context["initial_solution_source"]:
        print(f"  Initial solution: found")
    print()

    # Step 2: Analyze the task
    print("Analyzing task...")
    analysis = analyze_task(context)
    print(f"  Type: {analysis.get('task_type', '?')}")
    print(f"  Domain: {analysis.get('domain', '?')}")
    print(f"  Output type: {analysis.get('output_type', '?')}")
    print(f"  Input field: {analysis.get('input_field', '?')}")
    print(f"  Expected field: {analysis.get('expected_field', '?')}")
    print(f"  Quality dimensions: {len(analysis.get('quality_dimensions', []))}")
    for dim in analysis.get("quality_dimensions", []):
        prefix = "PENALTY" if dim.get("is_penalty") else f"weight={dim.get('weight', 1)}"
        print(f"    - {dim['name']}: {dim['description'][:60]}... [{prefix}]")
    print()

    if args.dry_run:
        print("DRY RUN -- stopping here.")
        print(json.dumps(analysis, indent=2))
        return

    if not context["test_cases"]:
        print("ERROR: Cannot generate checks without test cases.")
        sys.exit(1)

    # Step 3: Generate checks per test case
    print("Generating checks per test case...")
    all_checks = generate_checks(context, analysis)
    total = sum(len(c["fact_checks"]) for c in all_checks)
    print(f"  Generated {total} checks across {len(all_checks)} test cases")
    print()

    # Step 4: Build quality checks
    has_kb = bool(context["knowledge_base"])
    quality_checks = build_quality_checks(analysis, has_kb)
    print(f"Quality checks: {len(quality_checks)}")
    for qc in quality_checks:
        print(f"  - {qc['id']}: weight={qc['weight']}")
    print()

    # Step 5: Write rubric_checks.json
    checks_path = os.path.join(task_dir, "rubric_checks.json")
    with open(checks_path, "w", encoding="utf-8") as f:
        json.dump(all_checks, f, indent=2)
    print(f"Written: {checks_path}")

    # Step 6: Write rubric.py
    input_field = analysis.get("input_field", "question")
    rubric_content = generate_rubric_py(
        context["task_name"], quality_checks, has_kb, input_field
    )
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
    print(f"  3. Test: python tasks/generate_rubric.py --task {args.task} --dry-run")
    print(f"  4. Run experiment: python autoresearch/experiment.py --task {args.task}")


if __name__ == "__main__":
    main()
