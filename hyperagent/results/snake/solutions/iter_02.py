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
    def _find_path_to_food_bfs(start_pos, target_food_pos, board_width, board_height, current_snake_body):
        # The queue stores (current_position, first_direction_taken_from_start).
        # `first_direction_taken_from_start` is the actual move we'd make from the snake's head.
        queue = collections.deque([(start_pos, None)])
        visited = {start_pos} # Keep track of visited cells to avoid cycles and redundant processing

        while queue:
            current_pos, first_dir_from_start = queue.popleft()

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue # This move is out of bounds, try next direction
                
                # 2. Check for food collision (prioritized: moving onto food is always safe)
                if next_pos == target_food_pos:
                    # If this is the very first step from the snake's head to the food, return that direction.
                    if current_pos == start_pos:
                        return direction_str
                    # Otherwise, this path's first step was already determined earlier in the BFS.
                    return first_dir_from_start
                
                # 3. Check for self-collision (if not food)
                # If the snake doesn't eat, its tail (`current_snake_body[-1]`) vacates its position.
                # So, we only need to check against `current_snake_body[:-1]` (all segments except the tail).
                if next_pos in current_snake_body[:-1]:
                    continue # Collision with own body, try next direction
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    
                    # If `current_pos` is the starting point, `direction_str` is the first move.
                    # Otherwise, inherit the `first_dir_from_start` from the parent.
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    queue.append((next_pos, new_first_dir))
        
        return None # No safe path found to the food

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
    path_first_move = _find_path_to_food_bfs(head, food, width, height, snake)

    if path_first_move:
        return path_first_move

    # ====================================================================
    # --- Strategy 2: If no path to food, try to survive by maximizing free space ---
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
        # The `fixed_obstacles_for_free_space_bfs` correctly defines what's not free space.
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
    
    # Fallback in case of an unexpected scenario (should ideally not be reached).
    return "RIGHT"