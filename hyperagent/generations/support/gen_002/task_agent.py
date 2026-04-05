import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import llm

# Helper function to determine if higher values are better for a given metric
def _is_higher_better(metric_name):
    # Common keywords indicating that LOWER values are better
    lower_is_better_keywords = ["time", "ms", "latency", "error", "loss", "cost", "memory", "bytes", "duration"]
    return not any(keyword in metric_name.lower() for keyword in lower_is_better_keywords)

def propose(current_code, best_metric, history, metric_name="time_ms"):
    recent = history[-3:] if history else []
    history_text = ""
    for h in recent:
        history_text += f"  iter {h.get('step', '?')}: {h.get('action', '?')}"
        if h.get("action") == "ACCEPTED":
            history_text += f" ({h.get('improvement_pct', 0):.1f}% better)"
        history_text += "\n"

    higher_is_better = _is_higher_better(metric_name)
    metric_goal_verb = "increase" if higher_is_better else "decrease"
    comparison_symbol = ">" if higher_is_better else "<"
    opposite_comparison_symbol = "<" if higher_is_better else ">"

    prompt = (
        f"You are improving a Python function.\n"
        f"Your primary goal is to {metric_goal_verb} the '{metric_name}'.\n\n"
        f"CURRENT CODE:\n{current_code}\n\n"
        f"Current best '{metric_name}': {best_metric:.3f}\n"
        f"You MUST propose code that aims for a '{metric_name}' {comparison_symbol} {best_metric:.3f}.\n"
        f"DO NOT propose solutions where the '{metric_name}' is {opposite_comparison_symbol} {best_metric:.3f}.\n\n"
    )

    if history_text:
        prompt += f"RECENT HISTORY:\n{history_text}\n"
        all_rejected = all(h.get('action') == 'REJECTED' for h in recent)
        any_error = any(h.get('action') == 'ERROR' for h in recent)

        if all_rejected:
            prompt += "The recent proposals have all been REJECTED. Consider a significantly different approach or a more fundamental change, rather than minor tweaks, to break out of this local optimum.\n\n"
        if any_error:
            prompt += "One or more recent proposals resulted in an ERROR. Ensure your proposed code is syntactically correct, handles edge cases, and is robust to prevent errors during execution.\n\n"
        
    prompt += (
        f"Write an improved version. Return ONLY the function definition."
        f"Ensure the proposed code is syntactically correct and runnable Python."
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
