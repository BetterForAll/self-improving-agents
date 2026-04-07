import sys
import os

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "."))
import llm


def propose(current_code, best_metric, history, metric_name="time_ms", higher_is_better=None):
    recent = history[-6:] if history else []
    history_text = ""
    for h in recent:
        history_text += f"  iter {h.get('step', '?')}: {h.get('action', '?')}"
        if h.get('action') == "ACCEPTED":
            history_text += f" ({h.get('improvement_pct', 0):.1f}% better)"
        elif h.get('action') == "REJECTED":
            proposed = h.get('proposed_metric')
            previous = h.get('previous_metric')
            if proposed is not None and previous is not None:
                history_text += f" (proposed {proposed:.3f} vs previous {previous:.3f})"
            else:
                history_text += " (metrics N/A)"
        elif h.get('action') == "ERROR":
            history_text += " (code produced an error during execution/evaluation)"
        history_text += "\n"

    metric_direction_str = None
    if higher_is_better is not None:
        metric_direction_str = 'higher' if higher_is_better else 'lower'
    else:
        for entry in reversed(recent):
            proposed = entry.get('proposed_metric')
            previous = entry.get('previous_metric')
            if proposed is not None and previous is not None:
                if entry.get('action') == 'ACCEPTED':
                    if proposed > previous:
                        metric_direction_str = 'higher'
                    elif proposed < previous:
                        metric_direction_str = 'lower'
                    break
                elif entry.get('action') == 'REJECTED':
                    if proposed < previous:
                        metric_direction_str = 'higher'
                        break
                    elif proposed > previous:
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
        prompt_intro += "\n\n"
    else:
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

    # --- NEW LOGIC: DETECT AND PRIORITIZE DEGRADATION ---
    degradation_detected_last_step = False
    last_rejected_entry = None
    if recent and recent[-1].get('action') == 'REJECTED':
        last_rejected_entry = recent[-1]
        proposed = last_rejected_entry.get('proposed_metric')
        previous = last_rejected_entry.get('previous_metric')

        if higher_is_better is not None and proposed is not None and previous is not None:
            is_degraded = (higher_is_better and proposed < previous) or \
                          (not higher_is_better and proposed > previous)
            if is_degraded:
                degradation_detected_last_step = True
                prompt += (
                    f"--- URGENT ACTION REQUIRED: PERFORMANCE DEGRADATION ---\n"
                    f"Your VERY LAST proposal (iter {last_rejected_entry.get('step', '?')}) was REJECTED because it DEGRADED the {metric_name} "
                    f"from {previous:.3f} to {proposed:.3f}. THIS IS UNACCEPTABLE AND HAS HAPPENED REPEATEDLY.\n"
                    f"You have consistently proposed solutions that worsen the metric. THIS MUST STOP.\n\n"
                    f"**IMMEDIATE DIRECTIVE:**\n"
                    f"1. **STABILIZE PERFORMANCE:** Your absolute top priority is to ensure the metric does NOT degrade further.\n"
                    f"2. **PROPOSE NO-OP:** If you cannot find a change that GUARANTEES an improvement, you MUST propose the CURRENT CODE unchanged. THIS IS PREFERABLE TO DEGRADATION.\n"
                    f"3. **AVOID SPECULATION:** Do not guess. Only propose changes you are highly confident will improve the metric or, failing that, will maintain it.\n\n"
                )
            else: # Rejected but not due to degradation (e.g., no improvement, or minimal change not in the right direction)
                prompt += (
                    f"--- FEEDBACK: PROPOSAL REJECTED (NO IMPROVEMENT) ---\n"
                    f"Your VERY LAST proposal (iter {last_rejected_entry.get('step', '?')}) was REJECTED. It did not improve the {metric_name} "
                    f"from {previous:.3f}. Remember to propose ONLY changes that promise improvement. "
                    f"If you are unsure of an improvement, propose the CURRENT CODE unchanged as a NO-OP.\n\n"
                )

    # --- REJECTION WARNING (Consecutive Failures) ---
    consecutive_rejections = 0
    for h in reversed(recent):
        if h.get('action') == 'REJECTED':
            consecutive_rejections += 1
        else:
            break

    # This guidance is supplementary to the URGENT ACTION, so don't repeat the NO-OP if it was already explicitly given
    if consecutive_rejections >= 3 and not degradation_detected_last_step: # Only add if not already given the degradation warning
        # Determine if any of the consecutive rejections were due to degradation
        degradation_in_streak = False
        for h in recent[-consecutive_rejections:]:
            if h.get('action') == 'REJECTED':
                prop = h.get('proposed_metric')
                prev = h.get('previous_metric')
                if higher_is_better is not None and prop is not None and prev is not None:
                    if (higher_is_better and prop < prev) or (not higher_is_better and prop > prev):
                        degradation_in_streak = True
                        break

        rejection_specific_guidance = ""
        if degradation_in_streak:
            rejection_specific_guidance = (
                f"Multiple proposals in this streak resulted in a degraded {metric_name}. "
                f"This is unacceptable. "
            )
        else:
            rejection_specific_guidance = (
                f"All proposals in this streak failed to improve the {metric_name}. "
            )

        prompt += (
            f"--- REJECTION WARNING (Consecutive Failures) ---\n"
            f"Your last {consecutive_rejections} proposals were REJECTED. {rejection_specific_guidance}"
            f"Review the rejection details. Focus on making very safe, highly targeted changes. "
            f"If previous successful strategies exist, adapt them. Avoid any changes that might degrade performance at all costs.\n"
            f"Consider if your proposed changes are introducing new bugs or inefficiencies.\n\n"
        )
    elif consecutive_rejections > 0 and not degradation_detected_last_step: # Short streak, no degradation in last step
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
        f"- Your primary goal is to improve the {metric_name} metric. However, proposals that significantly degrade performance WILL BE REJECTED.\n"
        f"- Prefer small, targeted changes that are likely to yield incremental improvements over large, speculative overhauls.\n"
        f"- **CRITICAL:** If you are unable to find a change that improves the metric, or if you are unsure, propose the CURRENT CODE unchanged as a NO-OP. This is ALWAYS preferable to degrading performance. ESPECIALLY if you have recently degraded.\n"
        f"\n"
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
