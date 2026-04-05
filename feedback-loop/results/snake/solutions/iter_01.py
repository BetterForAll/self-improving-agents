def next_move(snake, food, width, height):
    """Pick the next direction for the snake.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    head_r, head_c = snake[0]
    food_r, food_c = food

    # Define possible moves as (dr, dc) for (delta_row, delta_col)
    directions_map = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # Store potential next coordinates for each direction
    potential_next_coords = {}
    for direction_name, (dr, dc) in directions_map.items():
        next_r, next_c = head_r + dr, head_c + dc
        potential_next_coords[direction_name] = (next_r, next_c)

    # Determine safe moves
    safe_moves = []
    
    # The set of body coordinates currently occupied by the snake.
    # We exclude the head (snake[0]) as it's the current position, and we are evaluating moves *from* it.
    # We also exclude the very last segment (snake[-1]) if the snake is longer than 1,
    # because if no food is eaten, the tail will move, freeing that spot.
    # However, for simplicity and maximum safety against complex tail mechanics in general contest systems,
    # it's often safer to consider all of snake[1:] as occupied, as the tail *might* not move if food is eaten.
    # For this basic implementation, we'll consider `snake[1:]` as occupied by the body.
    # This means the head cannot move into any position currently occupied by any body segment.
    body_coords = set(snake[1:]) 

    # We iterate through directions in a consistent order to ensure deterministic behavior
    # if multiple safe moves exist and we need to pick one arbitrarily.
    ordered_directions = ["UP", "DOWN", "LEFT", "RIGHT"] 

    for direction_name in ordered_directions:
        next_r, next_c = potential_next_coords[direction_name]
        
        # 1. Wall collision check
        if not (0 <= next_r < height and 0 <= next_c < width):
            continue

        # 2. Body collision check
        if (next_r, next_c) in body_coords:
            continue
        
        safe_moves.append(direction_name)

    # Strategy:
    # 1. Prioritize moving horizontally towards the food if it's safe.
    # 2. If not possible, prioritize moving vertically towards the food if it's safe.
    # 3. If no direct path towards food is safe, pick any available safe move.
    # 4. If no safe moves at all, choose a default direction (this will likely lead to death).

    best_move = None

    # Try to move horizontally towards food
    if food_c < head_c and "LEFT" in safe_moves:
        best_move = "LEFT"
    elif food_c > head_c and "RIGHT" in safe_moves:
        best_move = "RIGHT"
    
    # If no horizontal food-seeking move, try vertical
    if best_move is None:
        if food_r < head_r and "UP" in safe_moves:
            best_move = "UP"
        elif food_r > head_r and "DOWN" in safe_moves:
            best_move = "DOWN"

    # If still no move found (e.g., food is unreachable or direct path blocked),
    # pick any available safe move.
    if best_move is None and safe_moves:
        # Pick the first safe move in the preferred order
        for direction in ordered_directions:
            if direction in safe_moves:
                best_move = direction
                break

    # Fallback: If absolutely no safe moves, return a default direction.
    # The snake is trapped and will die anyway.
    if best_move is None:
        return "UP" # Arbitrary choice; any direction will result in collision.
    
    return best_move