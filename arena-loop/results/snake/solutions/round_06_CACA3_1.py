def next_move(snake, food, width, height):
    """Pick the next direction for the snake using a reactive decision-making algorithm.

    This strategy prioritizes immediate collision avoidance using a short-term look-ahead
    while always favoring movement towards the food's general direction.
    It does not use complex global pathfinding.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    head_r, head_c = snake[0]
    food_r, food_c = food

    MOVES = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # Pre-calculate obstacle sets for precise collision checking.
    # 1. If the snake moves onto the food, it grows. All current body segments
    #    (including the tail) remain occupied in the next state.
    #    The new head cannot collide with any of these.
    #    `set(snake)` correctly represents all segments of the current snake.
    occupied_if_eating = set(snake)

    # 2. If the snake moves to a non-food cell, it does not grow.
    #    Its tail position (`snake[-1]`) will be freed up.
    #    Obstacles are all segments *except* the tail.
    #    `set(snake[:-1])` correctly represents all segments from the head to the second-to-last.
    #    If `len(snake)` is 1, `snake[:-1]` is an empty list, and `set()` is empty, which is correct.
    occupied_if_not_eating = set(snake[:-1])

    best_move = None
    min_dist_to_food = float('inf')
    any_safe_move = None # Fallback: Stores any safe move if no food-seeking move is found

    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        is_safe = True

        # 1. Boundary check: Ensure the next position is within the board
        if not (0 <= next_r < height and 0 <= next_c < width):
            is_safe = False
        
        # 2. Collision with snake body: Varies based on whether the move lands on food
        if is_safe: # Only perform body collision check if within bounds
            if next_pos == food:
                # If moving to food, the snake will grow. The entire current body
                # (including the tail) would remain occupied.
                # `next_pos` must not be any part of the *current* snake.
                if next_pos in occupied_if_eating:
                    is_safe = False
            else:
                # If moving to a non-food position, the snake does not grow.
                # Its tail (`snake[-1]`) will move and free up its current spot.
                # `next_pos` must not be any part of the snake *except* its current tail.
                if next_pos in occupied_if_not_eating:
                    is_safe = False

        # If the move is safe, evaluate its desirability
        if is_safe:
            # Store this as a potential fallback move. The last safe move found will be used if no better move is identified.
            any_safe_move = move_name 

            # Calculate Manhattan distance to food from this potential next position
            current_dist = abs(next_r - food_r) + abs(next_c - food_c)
            
            # Prioritize moves that minimize the distance to food.
            # If multiple moves result in the same minimum distance, the first one encountered
            # in the MOVES dictionary iteration order will be chosen.
            if current_dist < min_dist_to_food:
                min_dist_to_food = current_dist
                best_move = move_name

    # Decision Making:
    if best_move:
        # If a safe move that minimized the distance to food was found, take it.
        return best_move
    elif any_safe_move:
        # If no move strictly reduced the distance to food (e.g., all safe moves increased or
        # maintained distance), but at least one safe move was found, take any safe move
        # (the last one encountered in the loop). This ensures survival if direct food path is blocked.
        return any_safe_move
    else:
        # If no safe moves are available (snake is trapped), return a default direction.
        # This will typically lead to an immediate collision and game over.
        return "UP"