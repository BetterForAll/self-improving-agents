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
    food_row, food_col = food

    possible_moves_drdc = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }

    # Define perpendicular moves mapping for ordering fallbacks
    perpendicular_map = {
        "UP": ["LEFT", "RIGHT"],
        "DOWN": ["LEFT", "RIGHT"],
        "LEFT": ["UP", "DOWN"],
        "RIGHT": ["UP", "DOWN"],
    }

    # Build a prioritized list of moves to try
    moves_to_try = []
    
    # 1. Primary target moves towards food (vertical then horizontal)
    vertical_target = ""
    if head_row < food_row:
        vertical_target = "DOWN"
    elif head_row > food_row:
        vertical_target = "UP"

    horizontal_target = ""
    if head_col < food_col:
        horizontal_target = "RIGHT"
    elif head_col > food_col:
        horizontal_target = "LEFT"

    if vertical_target:
        moves_to_try.append(vertical_target)
    if horizontal_target and horizontal_target != vertical_target:
        moves_to_try.append(horizontal_target)

    # Use a set to efficiently track unique moves and maintain order
    unique_moves_tried = set(moves_to_try)

    # 2. Add perpendicular moves to primary targets as fallback options
    if vertical_target:
        for move in perpendicular_map[vertical_target]:
            if move not in unique_moves_tried:
                moves_to_try.append(move)
                unique_moves_tried.add(move)
    if horizontal_target:
        for move in perpendicular_map[horizontal_target]:
            if move not in unique_moves_tried:
                moves_to_try.append(move)
                unique_moves_tried.add(move)

    # 3. Add any remaining moves (e.g., the direct "backwards" move if all else fails)
    all_directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    for move in all_directions:
        if move not in unique_moves_tried:
            moves_to_try.append(move)
            unique_moves_tried.add(move)

    # Iterate through prioritized moves and pick the first safe one
    for move_dir in moves_to_try:
        dr, dc = possible_moves_drdc[move_dir]
        next_head_row, next_head_col = head_row + dr, head_col + dc
        next_head_pos = (next_head_row, next_head_col)

        # Implement robust boundary checks for board dimensions
        is_in_bounds = (0 <= next_head_row < height) and \
                       (0 <= next_head_col < width)

        if not is_in_bounds:
            continue  # This move hits a wall, try the next prioritized move

        # Implement robust input validation (self-collision check) for snake movements
        # The set of dangerous positions includes the entire snake body if food is eaten (tail doesn't move),
        # otherwise, it includes all body segments except the current tail (which moves out of the way).
        # We convert to a set for efficient O(1) average time lookups.
        dangerous_positions = set(snake) if next_head_pos == food else set(snake[:-1])
        
        # Check for self-collision
        if next_head_pos in dangerous_positions:
            is_self_collision = True
        else:
            is_self_collision = False

        if not is_self_collision:
            return move_dir

    # Fallback: If no safe move is found (meaning the snake is completely trapped,
    # either by walls or its own body in all directions), return the first move
    # in the prioritized list. `moves_to_try` will always contain all 4 directions.
    # This implies the snake will die, but it's a deterministic choice.
    return moves_to_try[0]