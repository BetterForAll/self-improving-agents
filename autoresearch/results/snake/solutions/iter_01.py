def next_move(snake, food, width, height):
    """Pick the next direction for the snake.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    head_row, head_col = snake[0]

    # Define possible moves and their corresponding coordinate changes
    # The order here can influence tie-breaking if multiple moves lead to the same min_distance_to_food.
    # For instance, if UP and LEFT both lead to the same minimum distance, the one listed first will be preferred.
    possible_moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # Store information about safe moves: (direction, next_position, distance_to_food)
    safe_moves_info = []

    for direction, (dr, dc) in possible_moves.items():
        next_row, next_col = head_row + dr, head_col + dc
        next_pos = (next_row, next_col)

        # 1. Check for wall collision
        if not (0 <= next_row < height and 0 <= next_col < width):
            continue  # This move hits a wall, so it's unsafe

        # 2. Check for self-collision (hitting the snake's own body)
        # The snake's tail (snake[-1]) will move out of its current position
        # when the snake moves forward, making that spot safe.
        # So, we only need to avoid the head and the body segments up to, but not including, the tail.
        # `snake[:-1]` includes all segments except the last one (the tail).
        # For a snake of length 1, snake[:-1] is an empty list, so it can't hit itself.
        # For a snake of length 2, snake[:-1] is `[snake[0]]` (the head). `next_pos` will never be `snake[0]`
        # because it's always one step away from the head.
        # This check is robust for all snake lengths.
        if next_pos in snake[:-1]:
            continue  # This move hits the snake's body, so it's unsafe

        # If the move is safe (no wall or body collision), calculate its Manhattan distance to the food
        distance_to_food = abs(next_row - food[0]) + abs(next_col - food[1])
        safe_moves_info.append((direction, next_pos, distance_to_food))

    # If there are no safe moves, the snake is trapped.
    # In this scenario, the game is likely over soon. We return a default direction.
    # This scenario should be rare if the game hasn't ended.
    if not safe_moves_info:
        # Fallback: if completely trapped, just pick a direction. Game over is imminent.
        return "UP"

    # Find the safest move that minimizes the distance to the food
    best_move_direction = None
    min_distance = float('inf') # Initialize with a very large distance

    for direction, _, dist in safe_moves_info:
        if dist < min_distance:
            min_distance = dist
            best_move_direction = direction
        # If there are multiple moves with the same minimum distance to food,
        # the first one encountered (based on `possible_moves` iteration order) will be chosen.

    return best_move_direction