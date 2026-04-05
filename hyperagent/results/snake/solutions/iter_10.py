import collections

# Global constant for directions to avoid re-creation on every function call
_DIRECTIONS = {
    "UP":    (-1, 0),
    "DOWN":  (1, 0),
    "LEFT":  (0, -1),
    "RIGHT": (0, 1)
}

def next_move(snake, food, width, height):
    head = snake[0]

    # --- Helper function for BFS pathfinding ---
    # This generalized BFS accounts for dynamic snake body obstacles based on whether the snake grows or not.
    def _find_path_bfs(start_pos, target_pos, board_width, board_height, current_snake_body, snake_grows_on_target):
        # The queue stores (current_position, first_direction_taken_from_start, path_length).
        queue = collections.deque([(start_pos, None, 0)])
        visited = {start_pos} # Keep track of visited cells to avoid cycles and redundant processing

        while queue:
            current_pos, first_dir_from_start, path_len = queue.popleft()

            for direction_str, (dr, dc) in _DIRECTIONS.items(): # Use global _DIRECTIONS
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                new_path_len = path_len + 1

                # 2. Check for target collision (prioritized: moving onto target is always safe if it's the target)
                if next_pos == target_pos:
                    if current_pos == start_pos: # If target is reached in 1 step
                        return direction_str, new_path_len
                    # Otherwise, this path's first step was already determined earlier in the BFS.
                    return first_dir_from_start, new_path_len
                
                # 3. Check for self-collision (if not target)
                is_collision = False
                
                # Determine which parts of the snake body are obstacles for the current pathfinding.
                if snake_grows_on_target:
                    # If the snake eats and grows, its tail does NOT vacate.
                    # Therefore, all segments of the *current_snake_body* (excluding the head, which moves)
                    # are considered fixed obstacles.
                    # The `current_snake_body[1:]` represents all segments except the head `current_snake_body[0]`.
                    if next_pos in current_snake_body[1:]:
                        is_collision = True
                else: # Snake does not grow (e.g., pathfinding to tail, or a safety path after eating)
                    # Obstacles are the body segments that will *still be occupied* after `new_path_len` moves.
                    # These are `current_snake_body[:-new_path_len]`.
                    # If `new_path_len` is greater than or equal to `len(current_snake_body)`,
                    # the entire original snake body would have vacated, so no self-collision from it.
                    if new_path_len < len(current_snake_body) and next_pos in current_snake_body[:-new_path_len]:
                        is_collision = True
                
                if is_collision:
                    continue # Collision with own body, try next direction
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    # If `current_pos` is the starting point, `direction_str` is the first move.
                    # Otherwise, inherit the `first_dir_from_start` from the parent.
                    new_first_dir = direction_str if current_pos == start_pos else first_dir_from_start
                    queue.append((next_pos, new_first_dir, new_path_len))
        
        return None, None # No safe path found

    # --- Helper function for BFS to count reachable free cells ---
    # This BFS is used for 'survival mode' to find the largest open space.
    # It considers specified cells as fixed obstacles.
    def _count_reachable_cells_bfs(start_pos, board_width, board_height, fixed_obstacles_set):
        queue = collections.deque([start_pos])
        visited_cells = {start_pos} # Keeps track of cells visited in *this* BFS
        
        while queue:
            r, c = queue.popleft()

            for dr, dc in _DIRECTIONS.values(): # Use global _DIRECTIONS
                next_p = (r + dr, c + dc)

                # Check boundaries, if cell is not visited, and if it's not a fixed obstacle
                if (0 <= next_p[0] < board_height and 0 <= next_p[1] < board_width and
                    next_p not in visited_cells and next_p not in fixed_obstacles_set):
                    visited_cells.add(next_p)
                    queue.append(next_p)
        return len(visited_cells)

    # ====================================================================
    # --- Strategy 1: Find shortest path to food, with a safety check ---
    # Prioritize moving directly towards the food if a safe path exists.
    # When finding a path to food, the snake *will grow*, so use `snake_grows_on_target=True`.
    food_path_move, food_path_len = _find_path_bfs(head, food, width, height, snake, snake_grows_on_target=True)

    if food_path_move:
        # If a path to food is found, simulate eating the food and check if the snake
        # can still reach its (new, longer) tail. This prevents self-trapping after eating.

        # Calculate the potential next head position after making the first move towards food.
        dr, dc = _DIRECTIONS[food_path_move] # Use global _DIRECTIONS
        potential_next_head = (head[0] + dr, head[1] + dc)
        
        # Simulate the snake's body *after* taking the first step and eating the food.
        # The snake grows, so its new body is the `potential_next_head` followed by the *entire original snake body*.
        # For example, if snake = [s0, s1, s2], new_head = F. Simulated snake = [F, s0, s1, s2].
        simulated_snake_after_eating = [potential_next_head] + snake 
        
        # Now, check if there's a path from this `new_head` to the `new_tail`
        # (which is the last segment of `simulated_snake_after_eating`).
        # This pathfinding does *not* involve growth (`snake_grows_on_target=False`).
        safety_path_to_tail_move, _ = _find_path_bfs(
            simulated_snake_after_eating[0],       # The new head of the simulated snake
            simulated_snake_after_eating[-1],      # The new tail of the simulated snake
            width, height,
            simulated_snake_after_eating,
            snake_grows_on_target=False            # Snake does not grow further during this safety check
        )
        
        if safety_path_to_tail_move: # If a safe path to the new tail exists, the food path is good.
            return food_path_move

    # ====================================================================
    # --- Strategy 2: If no safe path to food, try to chase own tail ---
    # This strategy helps the snake stay in open areas and avoids getting trapped.
    # When pathfinding to the tail, the snake does *not* grow.
    # The `_find_path_bfs` with `snake_grows_on_target=False` handles the tail vacating correctly.
    tail_path_move, _ = _find_path_bfs(head, snake[-1], width, height, snake, snake_grows_on_target=False)
    
    if tail_path_move:
        return tail_path_move

    # ====================================================================
    # --- Strategy 3: If no path to food or tail, try to survive by maximizing free space ---
    # This is a fallback to prevent immediate death by moving into the largest available open area.
    immediately_safe_moves = []
    for direction_str, (dr, dc) in _DIRECTIONS.items(): # Use global _DIRECTIONS
        next_head_potential = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail)
        # For an immediate single step, snake[:-1] is considered occupied.
        # This is consistent with how the `_find_path_bfs` treats non-growing snake movement.
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
    # - `snake[:-1]`: The body segments that remain occupied (tail vacates).
    # - `food`: The food position itself is an obstacle because we are counting *free* (empty) cells.
    fixed_obstacles_for_free_space_bfs = set(snake[:-1])
    fixed_obstacles_for_free_space_bfs.add(food)
    
    for move_dir in immediately_safe_moves:
        dr, dc = _DIRECTIONS[move_dir] # Use global _DIRECTIONS
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
    
    # Fallback in case of an unexpected scenario (should ideally not be reached).
    return "RIGHT"