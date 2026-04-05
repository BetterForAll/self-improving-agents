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
    seen_moves = set() # Use a set to efficiently track unique moves and maintain order

    # Helper function to add a move to the list if not already seen
    def add_move_if_new(move_dir_str):
        if move_dir_str and move_dir_str not in seen_moves:
            moves_to_try.append(move_dir_str)
            seen_moves.add(move_dir_str)
    
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
        horizontal_target = "LEFT" # Fixed typo: horizontal_col -> horizontal_target

    add_move_if_new(vertical_target)
    add_move_if_new(horizontal_target)

    # 2. Add perpendicular moves to primary targets as fallback options
    if vertical_target:
        for move in perpendicular_map[vertical_target]:
            add_move_if_new(move)
    if horizontal_target:
        for move in perpendicular_map[horizontal_target]:
            add_move_if_new(move)

    # 3. Add any remaining moves (e.g., the direct "backwards" move if all else fails)
    all_directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    for move in all_directions:
        add_move_if_new(move)

    # Iterate through prioritized moves and pick the first safe one
    for move_dir in moves_to_try:
        dr, dc = possible_moves_drdc[move_dir]
        next_head_row, next_head_col = head_row + dr, head_col + dc
        next_head_pos = (next_head_row, next_head_col)

        # Robust boundary checks for board dimensions
        is_in_bounds = (0 <= next_head_row < height) and \
                       (0 <= next_head_col < width)

        if not is_in_bounds:
            continue  # This move hits a wall, try the next prioritized move

        # Robust self-collision check for snake movements
        # A move causes self-collision if the next head position:
        # 1. Is any part of the snake's body *except* the current tail (snake[:-1] covers this).
        # 2. Is the current tail position (`snake[-1]`), AND the snake eats food there
        #    (meaning the tail won't move, leading to collision).
        #    If the snake doesn't eat food, the tail moves out of the way, so it's not a collision.
        is_self_collision = next_head_pos in snake[:-1] or \
                            (next_head_pos == snake[-1] and next_head_pos == food)

        if not is_self_collision:
            return move_dir

    # Fallback: If no safe move is found (meaning the snake is completely trapped,
    # either by walls or its own body in all directions), return the first move
    # in the prioritized list. This means the snake will die, but it's a deterministic
    # choice. `moves_to_try` will always contain all 4 directions.
    return moves_to_try[0]