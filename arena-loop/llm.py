import os
import re
import time
from google import genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

# Token tracking
_token_usage = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "calls": 0,
}


def get_token_usage():
    return dict(_token_usage)


def reset_token_usage():
    for key in _token_usage:
        _token_usage[key] = 0


def ask(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt)
            if not response.candidates:
                raise RuntimeError("Gemini returned no candidates (possibly blocked)")
            # Track tokens
            usage = response.usage_metadata
            if usage:
                _token_usage["prompt_tokens"] += usage.prompt_token_count or 0
                _token_usage["completion_tokens"] += usage.candidates_token_count or 0
                _token_usage["total_tokens"] += usage.total_token_count or 0
            _token_usage["calls"] += 1
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def extract_json(response_text):
    import json
    text = response_text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (```json or ```) and last line (```)
        text = "\n".join(lines[1:-1]).strip()
    return json.loads(text)


def extract_code(response_text):
    match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'```\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = response_text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("def "):
            return "\n".join(lines[i:]).strip()
    return response_text.strip()
