import collections

# Define DIRECTIONS outside the function for efficiency, as it's constant.
DIRECTIONS = {
    "UP":    (-1, 0),
    "DOWN":  (1, 0),
    "LEFT":  (0, -1),
    "RIGHT": (0, 1)
}

def next_move(snake, food, width, height):
    head = snake[0]

    # --- Helper function for BFS pathfinding to the food (returns first_move and full_path) ---
    def _find_path_to_food_bfs_with_path(start_pos, target_food_pos, board_width, board_height, current_snake_body):
        # The queue stores (current_position, first_direction_taken_from_start, full_path_to_current_pos).
        # `full_path_to_current_pos` is a list of (row, col) tuples from start_pos to current_position.
        queue = collections.deque([(start_pos, None, [start_pos])])
        visited = {start_pos}

        while queue:
            current_pos, first_dir_from_start, current_path = queue.popleft()

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue # This move is out of bounds, try next direction
                
                # 2. Check for food collision (prioritized: moving onto food is always safe for the path itself)
                if next_pos == target_food_pos:
                    # If this is the very first step from the snake's head, return that direction.
                    if current_pos == start_pos:
                        return (direction_str, current_path + [next_pos])
                    # Otherwise, this path's first step was already determined earlier in the BFS.
                    return (first_dir_from_start, current_path + [next_pos])
                
                # 3. Check for self-collision (if not food)
                # When pathfinding to an empty cell, the snake's tail (`current_snake_body[-1]`) vacates its position.
                # So, we only need to check against `current_snake_body[:-1]` (all segments except the tail).
                if next_pos in current_snake_body[:-1]:
                    continue # Collision with own body, try next direction
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    
                    # If `current_pos` is the starting point, `direction_str` is the first move.
                    # Otherwise, inherit the `first_dir_from_start` from the parent.
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    queue.append((next_pos, new_first_dir, current_path + [next_pos]))
        
        return None # No safe path found to the food

    # --- Helper function for BFS to check if the snake can reach its (original) tail ---
    def _is_path_to_tail_safe(start_pos, target_tail_pos, board_width, board_height, current_obstacles_body):
        # This BFS checks if a path exists from `start_pos` to `target_tail_pos`.
        # `current_obstacles_body` represents the full snake body configuration, including its head.
        # Segments in `current_obstacles_body` that are not `start_pos` or `target_tail_pos` are considered obstacles.
        
        queue = collections.deque([start_pos])
        visited = {start_pos}
        
        # All segments of the simulated snake body (except the start position and the target tail position)
        # are considered fixed obstacles for this pathfinding.
        obstacles_set = set(current_obstacles_body) - {start_pos, target_tail_pos}

        while queue:
            current_pos = queue.popleft()

            # If we reached the target tail position, a path is found.
            if current_pos == target_tail_pos:
                return True

            for dr, dc in DIRECTIONS.values():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)

                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # 2. Check collision with actual obstacles (body segments not start/target)
                if next_pos in obstacles_set:
                    continue
                
                # 3. Avoid revisiting cells
                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append(next_pos)
        
        return False # No safe path found to the tail

    # --- Helper function for BFS to count reachable free cells ---
    # This BFS is used for 'survival mode' to find the largest open space.
    # It considers specified cells as fixed obstacles.
    def _count_reachable_cells_bfs(start_pos, board_width, board_height, fixed_obstacles_set):
        queue = collections.deque([start_pos])
        visited_cells = {start_pos} # Keeps track of cells visited in *this* BFS
        
        while queue:
            r, c = queue.popleft()

            for dr, dc in DIRECTIONS.values():
                next_p = (r + dr, c + dc)

                # Check boundaries, if cell is not visited, and if it's not a fixed obstacle
                if (0 <= next_p[0] < board_height and 0 <= next_p[1] < board_width and
                    next_p not in visited_cells and next_p not in fixed_obstacles_set):
                    visited_cells.add(next_p)
                    queue.append(next_p)
        return len(visited_cells)

    # ====================================================================
    # --- Strategy 1: Find shortest path to food, checking for post-eating trap ---
    food_path_info = _find_path_to_food_bfs_with_path(head, food, width, height, snake)

    if food_path_info:
        first_move_to_food, full_path_to_food = food_path_info
        
        # Simulate the snake's body after eating the food along this path.
        # The new snake body consists of the path segments (reversed, as the head is at the end of path),
        # followed by the remaining original snake body segments (if any) after the path.
        # Example: snake = [H,B1,B2,T], food at F, path = [H,X,F] (length 3)
        # full_path_to_food = [(H),(X),(F)]
        # full_path_to_food[::-1] = [(F),(X),(H)]
        # snake[len(full_path_to_food):] = snake[3:] = [(B2),(T)]
        # simulated_snake_body_after_eating = [(F),(X),(H),(B2),(T)]
        simulated_snake_body_after_eating = full_path_to_food[::-1] + snake[len(full_path_to_food):]

        # Check if, after eating, the snake can still find a path to its (original) tail.
        # This prevents the snake from trapping itself in a dead-end immediately after eating.
        new_head_pos_after_eating = simulated_snake_body_after_eating[0] # This is `food`
        original_tail_pos = snake[-1] # The original tail is the target for reachability.
        
        if _is_path_to_tail_safe(new_head_pos_after_eating, original_tail_pos, width, height, simulated_snake_body_after_eating):
            return first_move_to_food # This path to food is considered safe.

    # ====================================================================
    # --- Strategy 2: If no *safe* path to food, prioritize survival by maximizing free space and keeping tail reachable ---
    
    candidate_survival_moves_details = [] # Stores (direction, reachable_count, is_tail_reachable)

    for direction_str, (dr, dc) in DIRECTIONS.items():
        potential_next_head = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= potential_next_head[0] < height and 0 <= potential_next_head[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail, as it vacates)
        if potential_next_head in snake[:-1]:
            continue
            
        # 3. For survival mode, moving onto food is not considered 'safe' for finding free space.
        if potential_next_head == food:
            continue
        
        # Simulate the snake body if this move is taken (snake does NOT eat)
        # Its length remains the same, and the original tail vacates its spot.
        simulated_snake_body_no_eating = [potential_next_head] + snake[:-1]
        
        # Define obstacles for the free space BFS: the simulated snake body (no eating) and the food.
        obstacles_for_free_space_bfs = set(simulated_snake_body_no_eating)
        obstacles_for_free_space_bfs.add(food) # Food is also an obstacle for free space calculation.

        reachable_count = _count_reachable_cells_bfs(
            potential_next_head, width, height, obstacles_for_free_space_bfs
        )
        
        # Check if this survival move still allows a path to the new tail.
        # The new head is `potential_next_head`. The new tail is `snake[-1]` (the original tail).
        # `simulated_snake_body_no_eating` acts as the body obstacles for this check.
        tail_reachable = _is_path_to_tail_safe(potential_next_head, snake[-1], width, height, simulated_snake_body_no_eating)
        
        candidate_survival_moves_details.append((direction_str, reachable_count, tail_reachable))

    # Filter for moves that keep the tail reachable first.
    # `move[2]` is the `is_tail_reachable` boolean.
    safe_to_tail_survival_moves = [move for move in candidate_survival_moves_details if move[2]]
    
    # If there are moves that keep the tail reachable, we prioritize those.
    # Otherwise, we consider all candidate moves (even those that might trap the snake later, for a desperate attempt to survive longer).
    selected_moves = safe_to_tail_survival_moves if safe_to_tail_survival_moves else candidate_survival_moves_details

    if not selected_moves:
        # If no immediate safe move is found (even without considering tail reachability),
        # the snake is completely trapped and will die. Return a default direction, though it won't matter.
        return "RIGHT"

    # From the selected moves, pick the one that leads to the largest area of free space.
    best_move = None
    max_reachable_cells = -1

    for move_dir, reachable_count, _ in selected_moves:
        if reachable_count > max_reachable_cells:
            max_reachable_cells = reachable_count
            best_move = move_dir
    
    return best_move