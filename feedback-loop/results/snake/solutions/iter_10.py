import collections

def next_move(snake, food, width, height):
    head_r, head_c = snake[0]

    # Define possible moves as (dr, dc) for (delta_row, delta_col)
    directions_map = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    # For deterministic ordering of moves if multiple paths have same length or score
    ordered_directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    # Assign numerical priority for tie-breaking: lower index means higher priority
    direction_priority = {dir_name: i for i, dir_name in enumerate(ordered_directions)}

    # Helper function to check if a position is within board boundaries
    def is_valid(r, c):
        return 0 <= r < height and 0 <= c < width

    # BFS pathfinding function
    # Returns the full path (list of direction strings) from start_node to target_node,
    # avoiding specified obstacles. Returns None if no path found.
    def find_path_bfs(start_node, target_node, obstacles_set):
        queue = collections.deque([(start_node, [])]) # (current_pos, path_to_current_pos)
        visited = {start_node} # Store visited (row, col) tuples

        while queue:
            (r, c), path = queue.popleft()

            for direction_name in ordered_directions:
                dr, dc = directions_map[direction_name]
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                # 1. Wall collision check
                if not is_valid(next_r, next_c):
                    continue
                
                # 2. Check if target is reached
                if next_pos == target_node:
                    return path + [direction_name]
                
                # 3. Body collision check:
                if next_pos in obstacles_set:
                    continue
                
                # 4. Already visited check
                if next_pos in visited:
                    continue

                # If safe and unvisited, add to queue
                visited.add(next_pos)
                queue.append((next_pos, path + [direction_name]))
        
        return None # No path found

    # Helper to count reachable cells from a starting point, avoiding obstacles
    def count_reachable_cells(start_node, obstacles_set):
        queue = collections.deque([start_node])
        visited = {start_node}
        count = 0

        while queue:
            r, c = queue.popleft()
            count += 1 # Count the current cell

            for direction_name in ordered_directions:
                dr, dc = directions_map[direction_name]
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                # Wall collision check
                if not is_valid(next_r, next_c):
                    continue
                # Obstacle check
                if next_pos in obstacles_set:
                    continue
                # Already visited check
                if next_pos in visited:
                    continue
                
                visited.add(next_pos)
                queue.append(next_pos)
        return count

    # List to store potential moves and their calculated scores
    # Each entry: (move_direction_string, score)
    move_candidates = []

    # --- Evaluate a potential food-eating move ---
    # When going for food, all current body segments (snake[1:]) are obstacles.
    food_obstacles = set(snake[1:]) 
    path_to_food = find_path_bfs(snake[0], food, food_obstacles)

    if path_to_food:
        # Simulate the snake's state after eating the food at the end of path_to_food
        simulated_snake_body_after_eating = [food] + list(snake)
        
        sim_head_after_eating = simulated_snake_body_after_eating[0] # This is 'food'
        sim_tail_after_eating = simulated_snake_body_after_eating[-1] # This is original snake's tail
        
        # Obstacles for checking reachability to new tail *after* eating:
        # These are all body segments except the new head (food) and the new tail (original tail).
        simulated_obstacles_after_eating_to_tail = set(simulated_snake_body_after_eating[1:-1])

        # Check if, after eating, the snake can still reach its new tail (safety check).
        path_after_eating_to_tail = find_path_bfs(sim_head_after_eating, sim_tail_after_eating, simulated_obstacles_after_eating_to_tail)
        
        # If a path to the new tail exists after eating, the food path is considered safe enough to evaluate.
        if path_after_eating_to_tail is not None:
            # Calculate 'freedom' after eating: how much open space is left.
            # Obstacles for freedom: all new body segments except the new head itself.
            simulated_obstacles_after_eating_for_freedom = set(simulated_snake_body_after_eating[1:])
            freedom_after_eating = count_reachable_cells(sim_head_after_eating, simulated_obstacles_after_eating_for_freedom)
            
            # Score for the food move: prioritize high freedom, penalize long paths to food.
            food_move_score = freedom_after_eating - len(path_to_food)
            move_candidates.append((path_to_food[0], food_move_score))

    # --- Evaluate survival moves (maximize freedom without eating) ---
    for direction_name in ordered_directions:
        dr, dc = directions_map[direction_name]
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        # When not eating, the tail moves. So, body segments from snake[1] to snake[-2] are fixed obstacles.
        current_step_obstacles = set(snake[1:-1]) if len(snake) > 1 else set()

        # Check for immediate collision (walls or body parts that don't move)
        if not is_valid(next_r, next_c) or next_pos in current_step_obstacles:
            continue # This move leads to immediate collision

        # Simulate the snake's state after this potential move (no food eaten).
        sim_snake_body = [next_pos] + list(snake[:-1])
        
        sim_head_after_move = sim_snake_body[0]
        
        # Obstacles for counting freedom: all body segments of the simulated snake, except its head.
        sim_freedom_obstacles = set(sim_snake_body[1:])

        # Calculate 'freedom' (number of reachable cells) from the new head.
        current_freedom = count_reachable_cells(sim_head_after_move, sim_freedom_obstacles)
        
        # Score for a survival move is just the freedom it offers.
        move_candidates.append((direction_name, current_freedom))
    
    # --- Decision Time: Select the best move from candidates ---
    if not move_candidates:
        # If no valid moves are found (snake is completely trapped)
        return "UP" 

    best_move = None
    best_score = -float('inf')
    best_dir_priority = float('inf') # Lower priority value means earlier in ordered_directions

    for move_dir, score in move_candidates:
        current_dir_priority = direction_priority[move_dir]
        if score > best_score:
            best_score = score
            best_move = move_dir
            best_dir_priority = current_dir_priority
        elif score == best_score:
            # If scores are equal, use the predefined direction order for tie-breaking
            if current_dir_priority < best_dir_priority:
                best_move = move_dir
                best_dir_priority = current_dir_priority
    
    return best_move