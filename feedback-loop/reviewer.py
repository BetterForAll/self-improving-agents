import json
import re

import llm

REVIEW_PROMPT = '''\
You are a code reviewer with access to the FULL history of this optimization session.

CURRENT BEST CODE:
{current_code}

PROPOSED CODE:
{proposed_code}

PROPOSED METRIC: {new_metric:.3f}
CURRENT BEST METRIC: {best_metric:.3f}

FULL HISTORY (all previous steps and your previous feedback):
{history_json}

Analyze the proposal considering the full history. Return a JSON object with exactly these fields:
{{
    "issue_type": "performance" or "correctness" or "architecture" or "ok",
    "severity": "critical" or "major" or "minor" or "ok",
    "fix_suggestion": "concrete, actionable suggestion",
    "confidence": 0.0 to 1.0,
    "pattern_detected": "name of cross-step pattern" or null
}}

Return ONLY the JSON, nothing else.
'''


def review(current_code, proposed_code, new_metric, best_metric, history):
    prompt = REVIEW_PROMPT.format(
        current_code=current_code,
        proposed_code=proposed_code,
        new_metric=new_metric,
        best_metric=best_metric,
        history_json=json.dumps(history, indent=2, default=str),
    )
    raw = llm.ask(prompt)
    return _parse_feedback(raw)


def _parse_feedback(raw):
    try:
        text = raw.strip()
        match = re.search(r'```(?:json)?\n(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {
            "issue_type": "unknown",
            "severity": "minor",
            "fix_suggestion": f"Could not parse reviewer response: {raw[:200]}",
            "confidence": 0.0,
            "pattern_detected": None,
        }
