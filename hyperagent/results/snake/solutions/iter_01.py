def next_move(snake, food, width, height):
    """Pick the next direction for the snake.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    head = snake[0]

    def is_safe(next_pos, current_snake, current_food, board_width, board_height):
        next_row, next_col = next_pos
        
        # 1. Check boundaries
        if not (0 <= next_row < board_height and 0 <= next_col < board_width):
            return False
        
        # 2. Check self-collision
        # If the next_pos is the food, it's always safe. The snake will grow, 
        # but the head moves into the food's position, and the old tail position 
        # (which would have been occupied by `current_snake[-1]`) becomes occupied by the new tail.
        # This implies that moving into current_snake[-1] while also moving to food is *not* a collision.
        # So, if `next_pos == current_food`, it's safe.
        if next_pos == current_food:
            return True
        
        # If next_pos is not the food:
        # It is unsafe if it collides with any segment of the snake *except* the current tail.
        # The tail (`current_snake[-1]`) will vacate its position if the snake is not growing.
        # Therefore, we only need to check against `current_snake[:-1]` (all segments except the tail).
        if next_pos in current_snake[:-1]:
            return False
            
        return True

    # Define possible moves and their deltas (row_change, col_change)
    possible_moves_deltas = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # Calculate desired movement towards food
    dy = food[0] - head[0] # Vertical distance
    dx = food[1] - head[1] # Horizontal distance

    # Order of candidate moves: prioritize directions that reduce distance to food,
    # then include all other directions as fallbacks.
    candidate_moves_order = [] 
    
    # Determine primary preferred directions based on largest distance
    # and their opposite directions for fallbacks.
    primary_vertical_dir = "UP" if dy < 0 else "DOWN"
    primary_horizontal_dir = "LEFT" if dx < 0 else "RIGHT"
    
    # Prioritize reducing the largest absolute distance first
    if abs(dy) > abs(dx): # Vertical distance is greater or equal (if dx=0)
        candidate_moves_order.append(primary_vertical_dir)
        candidate_moves_order.append(primary_horizontal_dir)
    else: # Horizontal distance is greater or equal (if dy=0)
        candidate_moves_order.append(primary_horizontal_dir)
        candidate_moves_order.append(primary_vertical_dir)

    # Ensure all four directions are in the list, to provide fallbacks.
    # This covers cases where food is on the same row/column, or when primary/secondary directions are blocked.
    all_directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    for d in all_directions:
        if d not in candidate_moves_order:
            candidate_moves_order.append(d)

    # Iterate through ordered candidate moves and pick the first safe one
    for direction_str in candidate_moves_order:
        dr, dc = possible_moves_deltas[direction_str]
        next_head = (head[0] + dr, head[1] + dc)
        if is_safe(next_head, snake, food, width, height):
            return direction_str

    # If no safe move is found (snake is completely trapped),
    # return a default direction (e.g., "RIGHT"). The snake will die anyway.
    return "RIGHT"