import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import llm


def propose(current_code, best_metric, history, metric_name="time_ms"):
    recent = history[-3:] if history else []
    history_text = ""
    for h in recent:
        history_text += f"  iter {h.get('step', '?')}: {h.get('action', '?')}"
        if h.get("action") == "ACCEPTED":
            history_text += f" ({h.get('improvement_pct', 0):.1f}% better)"
        history_text += "\n"

    prompt = (
        f"You are improving a Python function to optimize for {metric_name}.\n\n"
        f"CURRENT CODE:\n{current_code}\n\n"
        f"Current {metric_name}: {best_metric:.3f}\n\n"
    )
    if history_text:
        prompt += f"RECENT HISTORY:\n{history_text}\n\n"
    prompt += (
        f"Write an improved version.\n\n"
        f"GUIDELINES:\n"
        f"- Return ONLY the complete Python function definition, starting with 'def' and including its entire body.\n"
        f"- The function name and its parameter list MUST remain unchanged. Do NOT alter the function signature.\n"
        f"- Ensure the proposed code is robust, handles potential errors gracefully, and maintains its intended functionality.\n"
        f"- Focus on improving the {metric_name} metric while strictly adhering to these guidelines.\n"
        f"\n"
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
