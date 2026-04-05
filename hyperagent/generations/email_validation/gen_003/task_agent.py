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

    instruction = (
        f"Write an improved version. Consider factors like correctness, "
        f"efficiency, readability, and robustness."
    )

    # Heuristic to guide the LLM when an optimal primary metric is reached.
    # This addresses the REJECTED actions when the proposed_metric equals previous_metric.
    if metric_name == "accuracy" and best_metric == 1.0:
        instruction = (
            f"The current code achieves a perfect {metric_name} score of {best_metric:.3f}. "
            f"Focus on improving efficiency, readability, and robustness without "
            f"sacrificing correctness or the perfect {metric_name} score. "
            f"If no significant improvements are possible, you may suggest "
            f"the current code again or indicate that it's already optimal."
        )
        
        # Check for consecutive rejections at optimal score
        consecutive_rejections_at_optimal = 0
        for h in reversed(history):
            if h.get("action") == "REJECTED" and h.get("proposed_metric") == best_metric and h.get("previous_metric") == best_metric:
                consecutive_rejections_at_optimal += 1
            else:
                break # Stop counting if history breaks the pattern
        
        if consecutive_rejections_at_optimal >= 2: # Trigger more explicit guidance after 2+ rejections at optimal
            instruction += (
                f"\n\nNOTICE: The perfect score of {best_metric:.3f} has been reached, "
                f"and the last {consecutive_rejections_at_optimal} proposals also resulted "
                f"in the same metric, leading to rejections. "
                f"At this point, *only* make changes if they are significant and risk-free "
                f"improvements to readability or efficiency. If no such improvements are obvious, "
                f"return the *exact same code* as provided in CURRENT CODE. "
                f"This signals that the code is already optimal for the primary metric "
                f"and secondary improvements are not evident."
            )
    elif metric_name == "time_ms" and best_metric <= 0.001: # For very low time values
        instruction = (
            f"The current code is extremely fast ({best_metric:.3f} {metric_name}). "
            f"Focus on improving readability and robustness without "
            f"sacrificing correctness or speed. "
            f"If no significant improvements are possible, you may suggest "
            f"the current code again or indicate that it's already optimal."
        )

    prompt = (
        f"You are improving a Python function.\n\n"
        f"CURRENT CODE:\n{current_code}\n\n"
        f"Current {metric_name}: {best_metric:.3f}\n\n"
    )
    if history_text:
        prompt += f"RECENT HISTORY:\n{history_text}\n\n"
    prompt += instruction + " Return ONLY the function definition."
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
