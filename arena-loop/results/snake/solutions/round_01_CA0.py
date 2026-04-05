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

    # Directions mapping
    moves = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # Helper function to check if a position is valid (within bounds and not self-colliding)
    def is_valid_move(r, c):
        # Check boundaries
        if not (0 <= r < height and 0 <= c < width):
            return False
        
        # Check self-collision:
        # A move is safe if the target cell is not occupied by any part of the snake
        # that will remain occupied after the move.
        # snake[:-1] refers to all segments except the very last one (the tail).
        # When the snake moves (and doesn't grow), its tail vacates its current spot.
        # So, the head can move into the current tail's position without collision.
        # This is a common heuristic for a greedy snake AI.
        if (r, c) in snake[:-1]:
            return False
            
        return True

    target_r, target_c = food
    
    possible_moves = []
    
    # Evaluate each possible direction
    for direction, (dr, dc) in moves.items():
        next_r, next_c = head_r + dr, head_c + dc
        
        if is_valid_move(next_r, next_c):
            # Calculate Manhattan distance to food for this potential move
            dist_to_food = abs(next_r - target_r) + abs(next_c - target_c)
            possible_moves.append((dist_to_food, direction))

    # Sort valid moves by their distance to food (ascending).
    # This prioritizes moves that get the snake closer to the food.
    possible_moves.sort()

    if possible_moves:
        # Pick the move that minimizes distance to food
        return possible_moves[0][1]
    
    # Fallback: If no valid moves are found (e.g., snake is completely trapped),
    # it means the snake will crash regardless of the move. Return "RIGHT" as a default.
    return "RIGHT"