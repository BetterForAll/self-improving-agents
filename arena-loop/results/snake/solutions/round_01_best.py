def next_move(snake, food, width, height):
    """Pick the next direction for the snake.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    # Baseline: always go right (very dumb)
    return "RIGHT"
