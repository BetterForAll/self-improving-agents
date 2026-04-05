import collections

def next_move(snake, food, width, height):
    head = snake[0]

    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # --- Helper function for BFS pathfinding to the food ---
    # This BFS correctly accounts for the snake's body movement (tail vacating its spot).
    # Returns (first_move_direction_string, path_length_int) or (None, None) if no path.
    def _find_path_to_food_bfs(start_pos, target_food_pos, board_width, board_height, current_snake_body):
        # The queue stores (current_position, first_direction_taken_from_start, path_length).
        queue = collections.deque([(start_pos, None, 0)])
        visited = {start_pos} 

        while queue:
            current_pos, first_dir_from_start, path_len = queue.popleft()

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # 2. Check for food collision (prioritized: moving onto food is always safe)
                if next_pos == target_food_pos:
                    if current_pos == start_pos:
                        return direction_str, path_len + 1
                    return first_dir_from_start, path_len + 1
                
                # 3. Check for self-collision (if not food)
                # If the snake doesn't eat, its tail (`current_snake_body[-1]`) vacates its position.
                # So, we only need to check against `current_snake_body[:-1]` (all segments except the tail).
                if next_pos in current_snake_body[:-1]:
                    continue
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    queue.append((next_pos, new_first_dir, path_len + 1))
        
        return None, None # No safe path found to the food

    # --- Helper function for BFS pathfinding to any target with fixed obstacles ---
    # This BFS is used for trap detection (can new head reach new tail).
    # Returns True if a path exists, False otherwise.
    def _find_path_to_target_fixed_obstacles_bfs(start_pos, target_pos, board_width, board_height, obstacles_set):
        queue = collections.deque([start_pos])
        visited = {start_pos}

        while queue:
            current_pos = queue.popleft()

            if current_pos == target_pos:
                return True # Path found!
            
            for dr, dc in DIRECTIONS.values():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # Check collision with fixed obstacles
                if next_pos in obstacles_set:
                    continue
                
                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append(next_pos)
        
        return False # No path found

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
    # --- Strategy 1: Find shortest path to food and check for traps ---
    # Prioritize moving directly towards the food if a safe path exists.
    # `snake` is the current list of (row, col) tuples representing the snake's body.
    path_first_move_dir, path_len_to_food = _find_path_to_food_bfs(head, food, width, height, snake)

    if path_first_move_dir:
        # Simulate the snake's state *after* taking `path_first_move_dir` (one step) and potentially eating.
        dr, dc = DIRECTIONS[path_first_move_dir]
        potential_next_head_pos = (head[0] + dr, head[1] + dc)

        simulated_snake_body = [potential_next_head_pos] + list(snake)
        if potential_next_head_pos == food:
            # Snake eats, its length increases, the old tail `snake[-1]` remains.
            pass 
        else:
            # Snake moves without eating, its length remains the same, the old tail `snake[-1]` vacates.
            simulated_snake_body.pop() 
        
        # Determine the new tail position after this simulated move.
        simulated_new_tail_pos = simulated_snake_body[-1]

        # Define obstacles for the "can reach tail" check.
        # These are all segments of the `simulated_snake_body` *except* the new tail itself
        # (because the tail's spot will vacate if the head reaches it).
        simulated_obstacles_for_tail_reach = set(simulated_snake_body[:-1]) 

        # Check if the simulated new head can reach the simulated new tail without self-colliding.
        is_safe_to_eat = _find_path_to_target_fixed_obstacles_bfs(
            potential_next_head_pos, simulated_new_tail_pos, width, height, simulated_obstacles_for_tail_reach
        )

        if is_safe_to_eat:
            return path_first_move_dir
        # If not safe (leads to a trap), fall through to survival strategy.

    # ====================================================================
    # --- Strategy 2: If no safe path to food, try to survive by maximizing free space ---
    # First, identify all immediately safe moves from the current head position.
    # A move is "safe" for survival if it doesn't hit a wall or the snake's body (excluding its tail),
    # and it does NOT move onto the food (as we're looking for empty space for survival).
    immediately_safe_moves = []
    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_head_potential = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail)
        # For survival, we assume the tail vacates.
        if next_head_potential in snake[:-1]:
            continue
            
        # 3. For survival mode, moving onto food is not considered 'safe' for finding free space.
        if next_head_potential == food:
            continue
            
        immediately_safe_moves.append(direction_str)

    if not immediately_safe_moves:
        # If no immediate safe move is found, the snake is completely trapped and will die.
        # Return a default direction, though it won't matter.
        return "RIGHT"

    # From the immediately safe moves, pick the one that leads to the largest area of free space.
    best_move = None
    max_reachable_cells = -1
    
    for move_dir in immediately_safe_moves:
        dr, dc = DIRECTIONS[move_dir]
        potential_next_head = (head[0] + dr, head[1] + dc)
        
        # Simulate the snake's body after taking this move (without eating).
        # This will be `[potential_next_head] + snake[:-1]`.
        temp_snake_body_after_move = [potential_next_head] + snake[:-1]
        
        # Define the set of `fixed_obstacles_set` for the `_count_reachable_cells_bfs`.
        # These are cells that are considered occupied and cannot be entered during the free space BFS.
        # - `temp_snake_body_after_move[1:]`: The body segments behind the *new* head.
        # - `food`: The food position itself is an obstacle because we are counting *free* (empty) cells.
        current_obstacles_for_free_space_bfs = set(temp_snake_body_after_move[1:])
        current_obstacles_for_free_space_bfs.add(food)
        
        # Count how many free cells are reachable from this `potential_next_head` position.
        reachable_count = _count_reachable_cells_bfs(
            potential_next_head, width, height, current_obstacles_for_free_space_bfs
        )

        if reachable_count > max_reachable_cells:
            max_reachable_cells = reachable_count
            best_move = move_dir
    
    # Return the move that leads to the largest free area.
    if best_move:
        return best_move
    
    # Fallback in case of an unexpected scenario (should ideally not be reached if immediately_safe_moves is not empty).
    return "RIGHT"