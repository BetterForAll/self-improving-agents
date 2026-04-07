import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "."))
import llm


def propose(current_code, best_metric, history, metric_name="time_ms", higher_is_better=None):
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

    # Determine metric direction: higher or lower is better
    metric_direction_str = None
    if higher_is_better is not None:
        metric_direction_str = 'higher' if higher_is_better else 'lower'
    else:
        # Fallback to inference from history if higher_is_better is not explicitly provided
        for entry in reversed(recent):
            proposed = entry.get('proposed_metric')
            previous = entry.get('previous_metric')
            if proposed is not None and previous is not None:
                if entry.get('action') == 'ACCEPTED':
                    if proposed > previous:
                        metric_direction_str = 'higher'
                    elif proposed < previous:
                        metric_direction_str = 'lower'
                    break # Found a clear signal from acceptance
                elif entry.get('action') == 'REJECTED':
                    # For a rejected proposal, if we assume the proposed value was "worse" than previous in the desired direction:
                    # If proposed < previous was rejected, it implies higher is better.
                    # If proposed > previous was rejected, it implies lower is better.
                    if proposed < previous: # If agent proposed a lower value and it was rejected, then higher must be better.
                        metric_direction_str = 'higher'
                        break
                    elif proposed > previous: # If agent proposed a higher value and it was rejected, then lower must be better.
                        metric_direction_str = 'lower'
                        break

    prompt_intro = (
        f"You are improving a Python function to optimize for {metric_name}. "
    )
    if higher_is_better is not None:
        if higher_is_better:
            prompt_intro += f"Based on the problem definition, {metric_name} is considered better when its value is HIGHER. Your primary goal is to INCREASE this value above {best_metric:.3f}. Crucially, you MUST NOT propose changes that would DECREASE it."
        else:
            prompt_intro += f"Based on the problem definition, {metric_name} is considered better when its value is LOWER. Your primary goal is to DECREASE this value below {best_metric:.3f}. Crucially, you MUST NOT propose changes that would INCREASE it."
        prompt_intro += "\n\n" # Added newline for clarity
    else:
        # Fallback if higher_is_better is not explicitly provided.
        # Use metric_direction_str for guidance if it was inferred from history.
        if metric_direction_str == 'higher':
            prompt_intro += f"Based on historical data, {metric_name} is considered better when its value is HIGHER. Your primary goal is to INCREASE this value above {best_metric:.3f}. Crucially, you MUST NOT propose changes that would DECREASE it."
        elif metric_direction_str == 'lower':
            prompt_intro += f"Based on historical data, {metric_name} is considered better when its value is LOWER. Your primary goal is to DECREASE this value below {best_metric:.3f}. Crucially, you MUST NOT propose changes that would INCREASE it."
        else:
            prompt_intro += f"Analyze the recent history of accepted and rejected proposals to understand if higher or lower values of this metric are considered better. Your goal is to improve upon the current best of {best_metric:.3f}.\n\n"

    prompt = (
        prompt_intro +
        f"CURRENT CODE:\n{current_code}\n\n"
        f"Current {metric_name}: {best_metric:.3f}\n\n"
    )
    if history_text:
        prompt += f"RECENT HISTORY:\n{history_text}\n\n"

    # --- NEW LOGIC FOR LAST REJECTION WARNING ---
    if recent and recent[-1].get('action') == 'REJECTED':
        last_rejected_entry = recent[-1]
        proposed = last_rejected_entry.get('proposed_metric')
        previous = last_rejected_entry.get('previous_metric')

        # Check if higher_is_better is known to provide specific guidance
        if higher_is_better is not None and proposed is not None and previous is not None:
            is_degraded = (higher_is_better and proposed < previous) or \
                          (not higher_is_better and proposed > previous)
            if is_degraded:
                prompt += (
                    f"--- CRITICAL FEEDBACK ---\n"
                    f"Your VERY LAST proposal (iter {last_rejected_entry.get('step', '?')}) was REJECTED because it degraded the {metric_name} "
                    f"from {previous:.3f} to {proposed:.3f}. This is unacceptable. "
                    f"You MUST NOT propose solutions that worsen the metric. "
                    f"If you cannot find a safe improvement, propose the CURRENT CODE unchanged as a NO-OP. This is crucial for stability. "
                    f"Re-evaluate your approach, as consistently degrading performance is unacceptable.\n\n"
                )
            else: # Rejected but not due to degradation (e.g., no improvement, or minimal change not in the right direction)
                prompt += (
                    f"--- FEEDBACK ---\n"
                    f"Your VERY LAST proposal (iter {last_rejected_entry.get('step', '?')}) was REJECTED. It did not improve the {metric_name} "
                    f"from {previous:.3f}. Remember to propose ONLY changes that promise improvement. "
                    f"If you are unsure of an improvement, propose the CURRENT CODE unchanged as a NO-OP.\n\n"
                )
    # --- END NEW LOGIC FOR LAST REJECTION WARNING ---

    # --- NEW LOGIC FOR REJECTION GUIDANCE (original, moved after new specific feedback) ---
    consecutive_rejections = 0
    for h in reversed(recent):
        if h.get('action') == 'REJECTED':
            consecutive_rejections += 1
        else:
            # An ACCEPTED or ERROR breaks the streak of rejections
            break

    if consecutive_rejections >= 3: # A significant streak
        last_rejected = None
        for h in reversed(recent): # Find the absolute last rejected entry for specific feedback
            if h.get('action') == 'REJECTED':
                last_rejected = h
                break

        rejection_specific_guidance = ""
        if last_rejected and last_rejected.get('proposed_metric') is not None and last_rejected.get('previous_metric') is not None:
            prop = last_rejected['proposed_metric']
            prev = last_rejected['previous_metric']
            if higher_is_better is not None: # Only provide specific guidance if direction is known
                if (higher_is_better and prop < prev) or (not higher_is_better and prop > prev):
                    rejection_specific_guidance = (
                        f"Crucially, your last proposal resulted in a {metric_name} of {prop:.3f}, which was WORSE than the current best of {prev:.3f}. "
                        f"This is unacceptable. Your absolute top priority is to NOT degrade performance. "
                    )
                else: # Failed to improve but didn't actively make it worse (e.g., proposed same or very minor difference not in right direction)
                    rejection_specific_guidance = (
                        f"Your last proposal resulted in a {metric_name} of {prop:.3f}, which failed to improve upon the current best of {prev:.3f}. "
                    )

        prompt += (
            f"--- REJECTION WARNING ---\n"
            f"Your last {consecutive_rejections} proposals were REJECTED. {rejection_specific_guidance}"
            f"Carefully review the rejection details in the history. Focus on making very safe, highly targeted changes. "
            f"If previous successful strategies exist, try to adapt or refine them. Avoid any changes that might degrade performance at all costs.\n"
            f"Consider if your proposed changes are introducing new bugs or inefficiencies that are negatively impacting the metric.\n\n"
        )
    elif consecutive_rejections > 0: # A short streak (1 or 2)
        prompt += (
            f"--- REJECTION NOTE ---\n"
            f"Your last {consecutive_rejections} proposal(s) were REJECTED. Review the reasons and consider a fresh angle.\n\n"
        )
    # --- END NEW LOGIC ---

    prompt += (
        f"Write an improved version.\n\n"
        f"GUIDELINES:\n"
        f"- Return ONLY the complete Python function definition, starting with 'def' and including its entire body.\n"
        f"- The function name and its parameter list MUST remain unchanged. Do NOT alter the function signature.\n"
        f"- Ensure the proposed code is robust, handles potential errors gracefully, and maintains its intended functionality.\n"
        f"- Your primary goal is to improve the {metric_name} metric. However, proposals that significantly degrade performance will be rejected.\n"
        f"- Prefer small, targeted changes that are likely to yield incremental improvements over large, speculative overhauls.\n"
        f"- If you are unable to find a change that improves the metric, or if you are unsure, propose the CURRENT CODE unchanged as a NO-OP. This is preferable to degrading performance."
        f"\n"
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
