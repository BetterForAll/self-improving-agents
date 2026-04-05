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

    # Helper function to check if a position is within board boundaries
    def is_valid(r, c):
        return 0 <= r < height and 0 <= c < width

    # BFS pathfinding function
    # Returns the full path (list of direction strings) from start_node to target_node,
    # avoiding specified obstacles. Returns None if no path found.
    # IMPORTANT: The target_node should generally NOT be included in obstacles_set,
    # as the BFS naturally handles reaching the target even if it's currently occupied
    # by something that will move or be eaten.
    def find_path_bfs(start_node, target_node, obstacles_set):
        queue = collections.deque([(start_node, [])]) # (current_pos, path_to_current_pos)
        visited = {start_node} # Store visited (row, col) tuples to prevent cycles and re-exploring

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
                
                # 3. Body/Obstacle collision check:
                # If next_pos is in obstacles_set, it's blocked.
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
            count += 1 # Count the current cell as reachable

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

    # --- Strategy 1: Find shortest path to food with safety check ---
    # When going for food, the snake's length increases by one.
    # Therefore, all current body segments (snake[1:]) are considered obstacles,
    # as the tail will not move. The food itself is the target and not an obstacle.
    food_obstacles = set(snake[1:]) 
    path_to_food = find_path_bfs(snake[0], food, food_obstacles)

    if path_to_food:
        # Simulate the snake's state after eating the food at the end of path_to_food.
        # The new head will be 'food', and the body will be the original snake's body,
        # increasing its length by 1.
        simulated_snake_body_after_eating = [food] + list(snake)
        
        sim_head_after_eating = simulated_snake_body_after_eating[0] # This is 'food'
        sim_tail_after_eating = simulated_snake_body_after_eating[-1] # This is original snake's tail
        
        # Obstacles for checking reachability to the new tail *after* eating:
        # These are all body segments of the *simulated grown snake*,
        # excluding its head (food) and its new tail (original tail).
        # The slice [1:-1] correctly handles short snakes as well (e.g., for 1 or 2 segments, it's empty).
        simulated_obstacles_after_eating = set(simulated_snake_body_after_eating[1:-1])

        # Check if, after eating, the snake can still reach its new tail.
        # This is a crucial proxy for "not being trapped immediately after eating".
        # If the tail is reachable, the snake can follow itself and avoid self-collision.
        path_after_eating_to_tail = find_path_bfs(
            sim_head_after_eating, 
            sim_tail_after_eating, 
            simulated_obstacles_after_eating
        )
        
        # If a path to the new tail exists after eating, then the food path is considered safe.
        if path_after_eating_to_tail is not None:
            return path_to_food[0] # Return the first move of the path to food

    # --- Strategy 2: Find the safest path to move without eating (maximize freedom) ---
    # This strategy is used if a safe path to food is not found.
    # It aims to keep the snake alive and in open space by choosing a move
    # that leads to the most 'freedom', measured by the number of reachable cells
    # from the new head position.
    best_survival_move = None
    max_freedom = -1 # Initialize with a low value to ensure any valid move is picked

    for direction_name in ordered_directions:
        dr, dc = directions_map[direction_name]
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        # Check for immediate collision (walls or body parts that DON'T move).
        # When not eating, the snake's tail moves. So, only body segments
        # from snake[1] to snake[-2] are considered obstacles for the next move.
        # For a snake of length 1 or 2, this set (snake[1:-1]) will be empty, which is correct.
        current_step_obstacles = set(snake[1:-1]) if len(snake) > 1 else set()

        if not is_valid(next_r, next_c) or next_pos in current_step_obstacles:
            continue # This move leads to immediate collision, so it's not a valid survival move.

        # Simulate the snake's state after this potential move (no food eaten).
        # The head moves to next_pos, and the tail segment is removed, maintaining length.
        # Since snake always has length >= 1, snake[:-1] is always valid.
        sim_snake_body = [next_pos] + list(snake[:-1])
        
        sim_head_after_move = sim_snake_body[0]
        
        # Obstacles for counting 'freedom': all body segments of the simulated snake,
        # except its new head. These are the parts that block movement.
        sim_freedom_obstacles = set(sim_snake_body[1:])

        # Calculate 'freedom' (number of reachable cells) from the new head position.
        current_freedom = count_reachable_cells(sim_head_after_move, sim_freedom_obstacles)
        
        # Prefer moves that offer more freedom. If freedom is equal, the ordering of
        # 'ordered_directions' ensures deterministic behavior (first one encountered wins).
        if current_freedom > max_freedom:
            max_freedom = current_freedom
            best_survival_move = direction_name
        
    if best_survival_move:
        return best_survival_move

    # --- Strategy 3: Fallback - No safe moves found at all ---
    # This scenario is reached if even single-step safe moves (maximizing freedom)
    # are not possible. It implies the snake is completely trapped, and any move
    # will result in collision or death.
    # In such a case, we return an arbitrary direction, as the game is effectively over.
    return "UP"