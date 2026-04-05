import collections

def next_move(snake, food, width, height):
    head = snake[0]

    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # --- Generalized BFS pathfinding helper ---
    # Returns (path_coordinates_list, first_direction_string)
    # path_coordinates_list: list of positions from start_pos's immediate neighbor to target_pos (inclusive).
    #                        If start_pos == target_pos, this list will be empty.
    # first_direction_string: the direction to take from start_pos to begin the path.
    #                         Returns None if start_pos == target_pos or no path found.
    def _bfs_pathfinder(start_pos, target_pos, board_width, board_height, current_obstacles_set):
        # queue stores (current_position, path_coords_from_start, first_dir_from_start)
        # path_coords_from_start: list of (row, col) positions from the first step to current_position (exclusive of start_pos).
        queue = collections.deque([(start_pos, [], None)])
        visited = {start_pos}

        while queue:
            current_pos, path_coords_so_far, first_dir_from_start = queue.popleft()

            if current_pos == target_pos:
                return path_coords_so_far, first_dir_from_start

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # 2. Check collision with obstacles
                if next_pos in current_obstacles_set:
                    continue
                
                # If safe and not visited:
                if next_pos not in visited:
                    visited.add(next_pos)
                    
                    new_path_coords = path_coords_so_far + [next_pos]
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    
                    queue.append((next_pos, new_path_coords, new_first_dir))
        
        return None, None # No path found

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
    # --- Strategy 1: Find safe path to food (path to food AND then path to tail) ---
    # Convert snake list to set for faster lookups of obstacles.
    # Obstacles for path to food: current snake body *excluding its tail* (tail vacates its spot).
    snake_body_obstacles_for_food_path = set(snake[:-1])

    path_to_food_coords, first_move_to_food = _bfs_pathfinder(head, food, width, height, snake_body_obstacles_for_food_path)

    if path_to_food_coords and first_move_to_food:
        # We found a path to food. Now, simulate the snake's state *after* moving to food and eating,
        # then check if it can reach its new tail from the new head.
        
        # 1. Simulate the snake's body after moving along the path to food and eating.
        # Start with current snake's body.
        simulated_snake_body_after_eating = list(snake) 
        for i, path_segment_pos in enumerate(path_to_food_coords):
            simulated_snake_body_after_eating.insert(0, path_segment_pos) # New head moves to current path segment
            # If not the *very last* segment (which is the food itself), the tail moves up.
            # When snake eats, its tail does *not* move for that turn, so length increases.
            if i < len(path_to_food_coords) - 1: 
                simulated_snake_body_after_eating.pop()
        
        # At this point, `simulated_snake_body_after_eating[0]` is `food`.
        # Its length is `len(snake) + 1` (compared to original `snake`).
        
        sim_head_for_tail_path = simulated_snake_body_after_eating[0] # This is the food position
        sim_tail_for_tail_path = simulated_snake_body_after_eating[-1] # The new tail position

        # 2. Define obstacles for finding a path from the new head to the new tail.
        # These are all segments of the `simulated_snake_body_after_eating` *except* its own tail,
        # because the tail vacates its spot when the snake moves.
        sim_obstacles_for_tail_path = set(simulated_snake_body_after_eating[:-1])

        # 3. Find a path from the new head (food) to the new tail.
        path_to_tail_coords, _ = _bfs_pathfinder(
            sim_head_for_tail_path,
            sim_tail_for_tail_path,
            width, height,
            sim_obstacles_for_tail_path
        )
        
        if path_to_tail_coords:
            # If a path to food was found, and after eating, a path to its own tail exists,
            # then this is considered a "safe" move (it won't immediately trap itself).
            return first_move_to_food

    # ====================================================================
    # --- Strategy 2: If no safe path to food, try to survive by maximizing free space ---
    # Identify immediately safe moves from the current head position.
    # A move is "safe" for survival if it doesn't hit a wall or the snake's body (excluding its tail),
    # and it does NOT move onto the food (as we're looking for empty space for survival).
    immediately_safe_moves = []
    # Reuse `snake_body_obstacles_for_food_path` as obstacles for basic survival checks.
    
    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_head_potential = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail)
        if next_head_potential in snake_body_obstacles_for_food_path:
            continue
            
        # 3. For survival mode, moving onto food is not considered 'safe' for finding free space.
        # This prevents the snake from trying to eat food that might lead to a trap later (which the primary strategy already filtered).
        if next_head_potential == food:
            continue
            
        immediately_safe_moves.append(direction_str)

    if not immediately_safe_moves:
        # If no immediate safe move is found, the snake is completely trapped and will die.
        # Return a default direction, though it won't matter.
        return "RIGHT"

    best_move = None
    max_reachable_cells = -1

    # Define the set of `fixed_obstacles` for the `_count_reachable_cells_bfs`.
    # These are cells that are considered occupied and cannot be entered during the free space BFS.
    # - `snake[:-1]`: The body segments that remain occupied even after the head moves (tail vacates).
    # - `food`: The food position itself is an obstacle because we are counting *free* (empty) cells.
    fixed_obstacles_for_free_space_bfs = set(snake[:-1])
    fixed_obstacles_for_free_space_bfs.add(food)
    
    for move_dir in immediately_safe_moves:
        dr, dc = DIRECTIONS[move_dir]
        potential_next_head = (head[0] + dr, head[1] + dc)
        
        # Count how many free cells are reachable from this `potential_next_head` position.
        reachable_count = _count_reachable_cells_bfs(
            potential_next_head, width, height, fixed_obstacles_for_free_space_bfs
        )

        if reachable_count > max_reachable_cells:
            max_reachable_cells = reachable_count
            best_move = move_dir
        # If reachable_count is equal, the first encountered direction for that count will be chosen,
        # which is a reasonable tie-breaking strategy.

    # `best_move` should always be set here if `immediately_safe_moves` was not empty.
    return best_move if best_move else "RIGHT" # Fallback, just in case.