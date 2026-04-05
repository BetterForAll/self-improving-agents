import llm


def propose(current_code, best_metric, metric_name="time_ms"):
    prompt = (
        f"Here is a Python function:\n\n{current_code}\n\n"
        f"Current {metric_name}: {best_metric:.3f}\n\n"
        f"Write an improved version. Return ONLY the function definition."
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw), raw
