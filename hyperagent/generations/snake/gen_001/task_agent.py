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
        elif h.get("action") == "REJECTED":
            # For rejected proposals, provide more detail on why it was rejected
            proposed_val = h.get('proposed_metric', '?')
            previous_val = h.get('previous_metric', '?')
            # Check if values are numeric before formatting
            if isinstance(proposed_val, (int, float)) and isinstance(previous_val, (int, float)):
                history_text += f" (proposed {proposed_val:.3f}, best was {previous_val:.3f})"
            else:
                history_text += f" (proposed {proposed_val}, best was {previous_val})"
        history_text += "\n"

    prompt = (
        f"You are improving a Python function.\n\n"
        f"CURRENT CODE:\n{current_code}\n\n"
        f"Current {metric_name}: {best_metric:.3f}\n\n"
    )
    if history_text:
        prompt += f"RECENT HISTORY:\n{history_text}\n\n"
    prompt += (
        f"Analyze the recent history to understand what worked and what didn't.\n"
        f"Write an improved version. Return ONLY the function definition."
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
