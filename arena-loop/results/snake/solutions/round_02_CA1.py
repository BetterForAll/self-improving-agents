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

    # Helper function to check if a potential position is immediately safe
    # (i.e., no boundary or self-collision at the next step).
    def _is_safe(pos, current_snake_body, board_width, board_height, is_eating=False):
        # Check for boundary collision
        if not (0 <= pos[0] < board_height and 0 <= pos[1] < board_width):
            return False
        
        # Check for self-collision
        if is_eating:
            # If the snake is eating, it grows, so the potential next_pos must not be any part of the *current* snake body.
            if pos in current_snake_body:
                return False
        else:
            # If the snake is not eating, its tail vacates its spot.
            # So, check against all body segments except the very last one (the current tail).
            if pos in current_snake_body[:-1]:
                return False
            
        return True

    # Helper function to calculate Manhattan distance, useful for heuristics.
    def _manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # BFS pathfinding function to check if a path exists from start_pos to target_pos,
    # avoiding specified obstacles. Returns True if a path exists, False otherwise.
    def _find_path_bfs(start_pos, target_pos, board_width, board_height, obstacles):
        queue = [start_pos]
        visited = {start_pos}

        # If start is already target, a path exists.
        if start_pos == target_pos:
            return True

        while queue:
            current_r, current_c = queue.pop(0)

            # Explore all four possible directions
            for dr, dc in moves.values():
                next_r, next_c = current_r + dr, current_c + dc
                next_p = (next_r, next_c)

                # Check boundaries
                if not (0 <= next_r < board_height and 0 <= next_c < board_width):
                    continue

                # Check collision with specified obstacles
                if next_p in obstacles:
                    continue

                # If next_p is visited, skip to avoid cycles and redundant checks
                if next_p not in visited:
                    # If target is found, a path exists
                    if next_p == target_pos:
                        return True
                    visited.add(next_p)
                    queue.append(next_p)
        return False # No path found

    safe_moves_data = [] # Stores (direction, next_pos, will_eat_food, dist_to_food, can_reach_tail_after_move)

    # Evaluate all four possible directions for the head's next move
    for direction, delta in moves.items():
        next_pos = _get_next_head_position(head, delta)
        will_eat_food = (next_pos == food)
        
        # First, check if the move is immediately safe (no boundary or self-collision)
        if _is_safe(next_pos, snake, width, height, is_eating=will_eat_food):
            # Simulate the snake's body after this potential move to perform advanced checks
            if will_eat_food:
                simulated_snake = [next_pos] + snake
            else:
                simulated_snake = [next_pos] + snake[:-1] # Tail disappears if not eating
            
            # Advanced Check: Can the snake reach its own tail after making this move?
            # This is crucial for avoiding traps and ensuring the snake has room to maneuver.
            can_reach_tail_after_move = False
            if len(simulated_snake) == 1:
                # If the simulated snake has only one segment, the head is the tail, so it's always reachable.
                can_reach_tail_after_move = True
            else:
                # The obstacles for pathfinding are all segments of the simulated snake EXCEPT the new head (next_pos).
                # This is because the new head is the starting point of our pathfinding, and it shouldn't block itself.
                obstacles_for_path = set(simulated_snake) - {next_pos}
                target_tail_pos = simulated_snake[-1] # The last segment of the simulated snake is the new tail.
                can_reach_tail_after_move = _find_path_bfs(next_pos, target_tail_pos, width, height, obstacles_for_path)

            safe_moves_data.append({
                "direction": direction,
                "next_pos": next_pos,
                "will_eat_food": will_eat_food,
                "dist_to_food": _manhattan_distance(next_pos, food),
                "can_reach_tail_after_move": can_reach_tail_after_move,
            })

    # If there are no immediately safe moves (e.g., completely surrounded), the snake is trapped.
    # Return "RIGHT" as a default, which will lead to game over.
    if not safe_moves_data:
        return "RIGHT"

    # --- Decision Making: Prioritize moves for a better score ---
    
    # 1. Prioritize moves that lead directly to the food AND ensure the snake does not trap itself
    # (i.e., can still reach its new tail after eating).
    eating_and_safe_moves = [
        move for move in safe_moves_data 
        if move["will_eat_food"] and move["can_reach_tail_after_move"]
    ]
    if eating_and_safe_moves:
        # If multiple such moves exist, any will lead to food safely.
        # We can pick the first one encountered for deterministic behavior.
        return eating_and_safe_moves[0]["direction"]

    # 2. If no safe eating moves, consider non-eating moves that ensure the snake does not trap itself.
    non_eating_and_safe_moves = [
        move for move in safe_moves_data
        if not move["will_eat_food"] and move["can_reach_tail_after_move"]
    ]

    if non_eating_and_safe_moves:
        # Among these safe non-eating moves, choose the one that gets closest to the food.
        best_move = None
        min_dist_to_food = float('inf')
        
        for move in non_eating_and_safe_moves:
            if move["dist_to_food"] < min_dist_to_food:
                min_dist_to_food = move["dist_to_food"]
                best_move = move
        
        # This condition should always be true if non_eating_and_safe_moves is not empty.
        if best_move: 
            return best_move["direction"]

    # 3. Fallback: If no moves guarantee reaching the tail (i.e., all immediate safe moves might lead to a future trap).
    # In this critical scenario, the snake is likely in a bad position but must still make a move.
    # As a last resort, pick any immediately safe move that gets closest to the food, similar to the original logic.
    # This might lead to death soon, but it's the "best" available option under poor circumstances.
    best_fallback_move_direction = None
    min_dist_to_food = float('inf')

    for move in safe_moves_data: # Iterate through all moves that were immediately safe.
        dist = move["dist_to_food"]
        if dist < min_dist_to_food:
            min_dist_to_food = dist
            best_fallback_move_direction = move["direction"]
            
    # This should always return a direction if safe_moves_data was not empty (handled by initial check).
    if best_fallback_move_direction:
        return best_fallback_move_direction

    # This line should ideally not be reached given the prior checks, but serves as a final safety measure.
    return "RIGHT"