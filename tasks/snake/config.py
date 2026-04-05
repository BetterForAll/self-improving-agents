"""Configuration for the Snake AI optimization task."""

TASK_NAME = "snake"
METRIC_NAME = "score"
HIGHER_IS_BETTER = True
PERFECT_SCORE = None  # no theoretical max for snake score

PROMPT_TEMPLATE = (
    "Here is a Python function that controls a snake in a Snake game:\n\n"
    "{code}\n\n"
    "The snake moves on a 10x10 grid. The function receives:\n"
    "- snake: list of (row,col) tuples, snake[0] is head\n"
    "- food: (row,col) of the food\n"
    "- width, height: board dimensions\n\n"
    "Current average score: {metric:.1f} apples over 20 games.\n\n"
    "Write a smarter version that scores higher. The snake must avoid walls "
    "and its own body. Return ONLY the function definition."
)


def build_prompt(code, metric):
    return PROMPT_TEMPLATE.format(code=code, metric=metric)
