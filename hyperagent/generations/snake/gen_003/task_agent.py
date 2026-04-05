import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import llm


def propose(current_code, best_metric, history, metric_name="time_ms"):
    # Determine the number of consecutive rejections from the end of history
    consecutive_rejections = 0
    # Look back up to 5 steps to detect a rejection streak
    for h in reversed(history[-5:]):
        if h.get("action") == "REJECTED":
            consecutive_rejections += 1
        else:
            break # Stop counting if an ACCEPTED proposal is found

    # Calculate last successful improvement percentage from all history
    last_successful_improvement_pct = 0
    for h in reversed(history):
        if h.get("action") == "ACCEPTED":
            last_successful_improvement_pct = h.get("improvement_pct", 0)
            break

    # Show last 5 entries in prompt for better context, aligning with rejection lookback
    recent = history[-5:] if history else []
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
    
    prompt += f"Analyze the recent history to understand what worked and what didn't.\n"

    if consecutive_rejections >= 3:
        # Add a specific instruction if the agent is stuck in a plateau
        prompt += f"You have had {consecutive_rejections} consecutive rejected proposals. " \
                  f"It's time to try a significantly different approach or explore new strategies " \
                  f"to break out of the current plateau. Avoid minor tweaks.\n"
    elif last_successful_improvement_pct >= 50:
        # If not in a rejection streak, but a significant improvement recently occurred,
        # prompt the agent to build on that success.
        prompt += f"A recent proposal led to a significant {last_successful_improvement_pct:.1f}% improvement. " \
                  f"Carefully analyze that successful change and try to build upon its strategy " \
                  f"or extrapolate its principles to find further gains.\n"
    
    prompt += f"Write an improved version. Return ONLY the function definition."
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
