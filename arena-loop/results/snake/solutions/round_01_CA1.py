def next_move(snake, food, width, height):
    head = snake[0]
    
    # Define possible moves and their deltas
    moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # Helper function to get the next head position for a given direction
    # This abstracts part of the snake's movement logic.
    def _get_next_head_position(current_head, delta):
        return (current_head[0] + delta[0], current_head[1] + delta[1])

    # Helper function to check if a potential position is safe
    # This encapsulates the collision detection logic.
    def _is_safe(pos, current_snake_body, board_width, board_height):
        # Check for boundary collision
        if not (0 <= pos[0] < board_height and 0 <= pos[1] < board_width):
            return False
        
        # Check for self-collision
        # The head will move, and if the snake doesn't eat, its tail will also move,
        # vacating its current spot. Therefore, we check against all body segments
        # except the very last one (the current tail).
        if pos in current_snake_body[:-1]:
            return False
            
        return True

    # Helper function to calculate Manhattan distance
    # Useful for heuristic decisions like finding the closest food.
    def _manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    safe_moves = []
    # Evaluate all four possible directions
    for direction, delta in moves.items():
        next_pos = _get_next_head_position(head, delta)
        # Check if the potential move is safe using the dedicated helper
        if _is_safe(next_pos, snake, width, height):
            safe_moves.append((direction, next_pos))

    # If there are no safe moves, the snake is trapped and will die.
    # In this scenario, any returned move will lead to game over.
    # We return "RIGHT" as a default, similar to the baseline.
    if not safe_moves:
        return "RIGHT"

    # Prioritize moves that directly lead to the food
    for direction, next_pos in safe_moves:
        if next_pos == food:
            return direction  # Found a direct path to food, take it!

    # If no direct path to food, choose the safe move that gets closest to the food
    best_move_direction = None
    min_dist_to_food = float('inf')

    # Iterate through the safe moves to find the one with the minimum Manhattan distance to food
    for direction, next_pos in safe_moves:
        dist = _manhattan_distance(next_pos, food)
        if dist < min_dist_to_food:
            min_dist_to_food = dist
            best_move_direction = direction
            
    # If multiple moves have the same minimum distance, the first one encountered will be chosen.
    return best_move_direction