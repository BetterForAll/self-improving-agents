def next_move(snake, food, width, height):
    """Pick the next direction for the snake using a reactive decision-making algorithm.

    Prioritizes immediate collision avoidance using a short-term look-ahead while always
    favoring movement towards the food's general direction. This provides a faster,
    more agile snake that excels in confined spaces without complex global pathfinding.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    head_r, head_c = snake[0]
    food_r, food_c = food

    # Define possible moves and their deltas.
    # A fixed priority is assigned for deterministic tie-breaking.
    MOVES = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    MOVE_PRIORITY = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3} # Lower value means higher priority in ties

    # Helper function to get the sign of a number (for direction comparison)
    def sign(x):
        return 1 if x > 0 else (-1 if x < 0 else 0)

    # List to store potential safe moves and their scores
    # Each entry will be: (food_distance, -alignment_score, move_priority_idx, move_name)
    scored_moves = []

    # Determine base obstacles: All snake segments except the current tail.
    # The tail (snake[-1]) is considered 'free' if the snake doesn't eat and moves.
    # This ensures it can move into its own tail if no other path is available.
    obstacles_base = set(snake[:-1]) if len(snake) > 0 else set()

    # Evaluate each possible direction
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        is_safe = True

        # 1. Boundary check: Is the next position within the board?
        if not (0 <= next_r < height and 0 <= next_c < width):
            is_safe = False

        # 2. Self-collision check:
        if is_safe:
            # Create a dynamic set of obstacles for this specific move consideration.
            # Start with the base obstacles (body segments excluding the tail).
            current_obstacles = set(obstacles_base)
            
            # SPECIAL CASE: If the snake moves onto the food, it will grow.
            # In this scenario, the current tail position does NOT free up,
            # and effectively becomes part of the new, longer snake's body.
            # Therefore, the current tail segment must also be considered an obstacle.
            if next_pos == food:
                if len(snake) > 0:
                    current_obstacles.add(snake[-1])
            
            # Check if the next position collides with any of the determined obstacles
            if next_pos in current_obstacles:
                is_safe = False
        
        # If the move is safe, calculate its score
        if is_safe:
            # Calculate Manhattan distance to food (prioritized for movement towards food)
            food_dist = abs(next_r - food_r) + abs(next_c - food_c)

            # Calculate an "alignment score" to favor moves that are in the general direction of food
            alignment_score = 0
            delta_r_food = food_r - head_r
            delta_c_food = food_c - head_c

            # Check if the move's vertical component aligns with food's vertical direction
            if sign(dr) == sign(delta_r_food) and dr != 0:
                alignment_score += 1
            # Check if the move's horizontal component aligns with food's horizontal direction
            if sign(dc) == sign(delta_c_food) and dc != 0:
                alignment_score += 1
            
            # Add this move to the list of scored moves.
            # The tuple is designed for sorting:
            # 1. `food_dist`: Primary sort key, minimize distance to food.
            # 2. `-alignment_score`: Secondary sort key, maximize alignment score (hence negative for min-sort).
            # 3. `MOVE_PRIORITY[move_name]`: Tertiary sort key, for consistent tie-breaking between moves with equal food_dist and alignment.
            # 4. `move_name`: The actual direction string to return.
            scored_moves.append((food_dist, -alignment_score, MOVE_PRIORITY[move_name], move_name))

    # If no safe moves were found, the snake is trapped. Return a default move
    # (this typically leads to game over, but a move must be returned).
    if not scored_moves:
        return "RIGHT"

    # Sort the safe moves based on the defined scoring criteria
    scored_moves.sort()

    # Return the name of the best move (the one with the lowest score after sorting)
    return scored_moves[0][3]