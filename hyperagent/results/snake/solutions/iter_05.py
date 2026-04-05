import collections

def next_move(snake, food, width, height):
    head = snake[0]

    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # --- Helper function for BFS pathfinding to a target (food or tail) ---
    # This BFS accounts for the snake's body movement (tail vacating its spot).
    # It takes the full snake body configuration as `current_snake_body_for_collision`.
    # The obstacles for the BFS are all segments of `current_snake_body_for_collision`
    # except its last element (which is the tail and vacates its spot).
    def _find_path_bfs(start_pos, target_pos, board_width, board_height, current_snake_body_for_collision):
        # The queue stores (current_position, first_direction_taken_from_start).
        queue = collections.deque([(start_pos, None)])
        visited = {start_pos} 

        # The obstacles for a pathfinding BFS are all body segments except the last one (tail vacates).
        # This set is calculated once based on the provided `current_snake_body_for_collision`.
        # Note: This is a static obstacle set for the duration of this BFS.
        # It's suitable for the simple "tail vacates" model.
        body_obstacles_set = set(current_snake_body_for_collision[:-1])

        while queue:
            current_pos, first_dir_from_start = queue.popleft()

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # 2. Check for target (food or tail)
                if next_pos == target_pos:
                    if current_pos == start_pos: # If it's the very first step from the initial head
                        return direction_str
                    return first_dir_from_start # Return the initial direction found earlier
                
                # 3. Check for collision with snake's body (excluding its current tail)
                if next_pos in body_obstacles_set:
                    continue 
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    # If current_pos is the starting point, direction_str is the first move.
                    # Otherwise, inherit the first_dir_from_start from the parent.
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    queue.append((next_pos, new_first_dir))
        
        return None # No safe path found to the target

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
    # --- Strategy 1: Find shortest path to food using BFS ---
    # Prioritize moving directly towards the food if a safe path exists.
    # `snake` is the current list of (row, col) tuples representing the snake's body.
    path_first_move_to_food = _find_path_bfs(head, food, width, height, snake)

    if path_first_move_to_food:
        # Simulate the snake's state *after* eating the food.
        # The new head is `food`. The new body is `[food] + original_snake_body`.
        simulated_snake_after_eating = [food] + snake

        # Now, check if there's a path from the new head (food position) to the new tail
        # (`simulated_snake_after_eating[-1]`). This prevents the snake from trapping itself
        # immediately after eating the food.
        path_to_tail_exists = _find_path_bfs(
            start_pos=food, 
            target_pos=simulated_snake_after_eating[-1], 
            board_width=width, 
            board_height=height, 
            current_snake_body_for_collision=simulated_snake_after_eating
        )
        
        if path_to_tail_exists:
            # If a path to food exists AND we can still reach our tail after eating,
            # then taking this food path is considered safe.
            return path_first_move_to_food
        # Else: Even if a path to food exists, it leads to a trap, so fall through to survival strategy.

    # ====================================================================
    # --- Strategy 2: If no safe path to food (or food leads to trap), try to survive by maximizing free space ---
    # First, identify all immediately safe moves from the current head position.
    # A move is "safe" for survival if it doesn't hit a wall or the snake's body (excluding its tail),
    # and it does NOT move onto the food (as we're looking for empty space for survival).
    immediately_safe_moves = []
    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_head_potential = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (if not food)
        # If the snake doesn't eat, its tail (`snake[-1]`) vacates its position.
        # So, we only need to check against `snake[:-1]` (all segments except the tail).
        if next_head_potential in snake[:-1]:
            continue
            
        # 3. For survival mode, moving onto food is not considered 'safe' for finding free space.
        # We want to count actual empty cells for maximum maneuverability.
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
    
    # Return the move that leads to the largest free area.
    # `best_move` should always be set here if `immediately_safe_moves` was not empty.
    if best_move:
        return best_move
    
    # Fallback in case of an unexpected scenario (should ideally not be reached if immediately_safe_moves is not empty).
    return "RIGHT"