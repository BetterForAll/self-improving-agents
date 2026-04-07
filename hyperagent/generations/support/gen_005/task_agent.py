import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "."))
import llm


def propose(current_code, best_metric, history, metric_name="time_ms"):
    # Increased history to 6 to give more context for successes, rejections, and failures
    recent = history[-6:] if history else []
    history_text = ""
    for h in recent:
        history_text += f"  iter {h.get('step', '?')}: {h.get('action', '?')}"
        if h.get('action') == "ACCEPTED":
            history_text += f" ({h.get('improvement_pct', 0):.1f}% better)"
        elif h.get('action') == "REJECTED":
            # Provide more detail for rejected proposals, showing the actual metrics
            proposed = h.get('proposed_metric')
            previous = h.get('previous_metric')
            if proposed is not None and previous is not None:
                history_text += f" (proposed {proposed:.3f} vs previous {previous:.3f})"
            else:
                history_text += " (metrics N/A)"
        elif h.get('action') == "ERROR":
            # Inform the agent that the code produced an error
            history_text += " (code produced an error during execution/evaluation)"
        history_text += "\n"

    metric_direction = None
    # Look for the latest ACCEPTED action in recent history to determine if higher or lower is better
    for entry in reversed(recent):
        if entry.get('action') == 'ACCEPTED':
            proposed = entry.get('proposed_metric')
            previous = entry.get('previous_metric')
            if proposed is not None and previous is not None:
                if proposed > previous:
                    metric_direction = 'higher'
                elif proposed < previous:
                    metric_direction = 'lower'
                break # Found a clear signal

    metric_guidance = ""
    if metric_direction:
        metric_guidance = f"A {metric_direction} value for {metric_name} is considered better."
    else:
        # Fallback if no clear ACCEPTED signal in recent history (e.g., all rejections, or very start)
        metric_guidance = f"Analyze the recent history of accepted and rejected proposals to understand if higher or lower values of this metric are considered better."

    prompt = (
        f"You are improving a Python function to optimize for {metric_name}. The current best score is {best_metric:.3f}. {metric_guidance}\n\n"
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
        f"- Your primary goal is to improve the {metric_name} metric. However, proposals that significantly degrade performance will be rejected.\n"
        f"- Prefer small, targeted changes that are likely to yield incremental improvements over large, speculative overhauls.\n"
        f"\n"
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
