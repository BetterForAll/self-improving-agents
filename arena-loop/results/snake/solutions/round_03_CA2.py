def next_move(snake, food, width, height):
    """Pick the next direction for the snake.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    # Robust Input Validation (Implicit): Assumes 'snake' is not empty and contains valid (row, col) tuples.
    # If snake could be empty, an explicit check like 'if not snake: raise ValueError("Snake cannot be empty")'
    # would be added here to prevent IndexError for snake[0].
    head_row, head_col = snake[0]
    food_row, food_col = food

    possible_moves_drdc = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }

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
        # BUG FIX: Corrected duplicated inner loop for adding perpendicular moves.
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

    # For robust and efficient self-collision checking:
    # Create a set of the snake's body segments that are 'fixed obstacles'.
    # These are all segments except the current head (which moves) and the tail (which moves if no food is eaten).
    # Using a set provides O(1) average time complexity for lookups, improving performance for long snakes.
    # For snakes with length 1 or 2, snake[1:-1] correctly evaluates to an empty list,
    # resulting in an empty set, as these snakes have no 'mid-body' fixed obstacles.
    fixed_body_segments = set(snake[1:-1])

    # Iterate through prioritized moves and pick the first safe one
    for move_dir in moves_to_try:
        dr, dc = possible_moves_drdc[move_dir]
        next_head_row, next_head_col = head_row + dr, head_col + dc
        next_head_pos = (next_head_row, next_head_col)

        # Robust Boundary Check: Prevents IndexError by ensuring next_head_pos is within board limits.
        is_out_of_bounds = not (0 <= next_head_row < height and \
                               0 <= next_head_col < width)
        if is_out_of_bounds:
            continue  # This move hits a wall, try the next prioritized move

        # Robust Self-Collision Check: Prevents unexpected behavior by validating snake movements.
        # A snake of length 1 cannot collide with itself, so no self-collision check is needed for it.
        is_self_collision = False
        if len(snake) > 1: 
            # Check collision with the 'fixed' body segments (all segments excluding head and tail).
            if next_head_pos in fixed_body_segments:
                is_self_collision = True
            # Special case for the tail segment (snake[-1]):
            # Collision occurs only if the snake attempts to move into its current tail position
            # AND the food is also at that tail position. In this scenario, the snake eats the food
            # and its tail does not move, leading to a self-collision.
            # Otherwise, if food is NOT at the tail, the tail moves out of the way, so it's not a collision.
            elif next_head_pos == snake[-1] and next_head_pos == food:
                is_self_collision = True

        if not is_self_collision:
            return move_dir

    # Fallback: If no safe move is found (meaning the snake is completely trapped,
    # either by walls or its own body in all directions), return the first move
    # in the prioritized list. This ensures a deterministic choice, even if it leads
    # to the snake's demise. `moves_to_try` will always contain all 4 directions if
    # no targets were initially valid, making this fallback safe.
    return moves_to_try[0]