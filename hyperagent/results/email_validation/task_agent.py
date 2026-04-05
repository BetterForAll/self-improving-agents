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

    # Check for consecutive rejections at an optimal primary metric first
    consecutive_rejections_at_optimal = 0
    is_current_metric_optimal = False
    if metric_name == "accuracy" and best_metric == 1.0:
        is_current_metric_optimal = True
    elif metric_name == "time_ms" and best_metric <= 0.001:
        is_current_metric_optimal = True
        
    if is_current_metric_optimal:
        for h in reversed(history):
            # Check if the historical action was a rejection where metrics were also optimal
            was_rejected_at_optimal = (
                h.get("action") == "REJECTED" and
                (
                    (metric_name == "accuracy" and h.get("proposed_metric") == 1.0 and h.get("previous_metric") == 1.0) or
                    (metric_name == "time_ms" and h.get("proposed_metric") <= 0.001 and h.get("previous_metric") <= 0.001)
                )
            )
            if was_rejected_at_optimal:
                consecutive_rejections_at_optimal += 1
            else:
                break # Stop counting if history breaks the pattern
    
    # If two or more consecutive rejections occurred while the metric was already optimal,
    # explicitly return the current code to signal stability/optimality and avoid redundant LLM calls.
    if consecutive_rejections_at_optimal >= 2:
        # Construct a specific prompt for the LLM to provide context if it's called (e.g., for logging),
        # but the agent itself will directly return the current code.
        prompt_for_logging = (
            f"NOTICE: The current code has reached the optimal {metric_name} score of {best_metric:.3f}. "
            f"The last {consecutive_rejections_at_optimal} proposals also resulted "
            f"in the same optimal metric, leading to rejections. "
            f"At this point, no further improvements are needed or possible for the primary metric. "
            f"You are instructed to return the *exact same code* as provided in CURRENT CODE. "
            f"This signals that the code is already optimal and avoids unnecessary further attempts to modify it. "
            f"\n\nCURRENT CODE:\n{current_code}\n"
            f"\nReturn ONLY the function definition, precisely as given in CURRENT CODE."
        )
        # Call LLM for interaction logging, but its output is explicitly discarded for the proposed code.
        _ = llm.ask(prompt_for_logging) 
        
        # Explicitly return the current code. This will be processed as a 'REJECTED' action
        # by the evaluation loop, indicating that no improvement was found.
        return current_code, f"Agent determined code is optimal after {consecutive_rejections_at_optimal} consecutive rejections at optimal metric ({best_metric:.3f}). Explicitly returning current_code."


    instruction = (
        f"Write an improved version. Consider factors like correctness, "
        f"efficiency, readability, and robustness."
    )

    # Heuristic to guide the LLM when an optimal primary metric is reached.
    # The explicit handling for consecutive rejections is now done upfront.
    if metric_name == "accuracy" and best_metric == 1.0:
        instruction = (
            f"The current code achieves a perfect {metric_name} score of {best_metric:.3f}. "
            f"Focus on improving efficiency, readability, and robustness without "
            f"sacrificing correctness or the perfect {metric_name} score. "
            f"If no significant improvements are possible, you may suggest "
            f"the current code again or indicate that it's already optimal."
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
