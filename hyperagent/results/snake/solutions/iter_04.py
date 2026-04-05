import collections

def next_move(snake, food, width, height):
    head = snake[0]

    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }

    # --- Helper function for BFS pathfinding to a target ---
    # This BFS finds the first move to reach a `target_pos` while avoiding `obstacles_set`.
    # It accounts for obstacles being static (not moving like a snake's tail).
    def _find_path_bfs(start_pos, target_pos, board_width, board_height, obstacles_set):
        queue = collections.deque([(start_pos, None)])
        visited = {start_pos}

        while queue:
            current_pos, first_dir_from_start = queue.popleft()

            for direction_str, (dr, dc) in DIRECTIONS.items():
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                
                # 1. Check boundaries
                if not (0 <= next_pos[0] < board_height and 0 <= next_pos[1] < board_width):
                    continue
                
                # 2. Check for target
                if next_pos == target_pos:
                    # If this is the very first step from the start_pos, return that direction.
                    if current_pos == start_pos:
                        return direction_str
                    # Otherwise, this path's first step was already determined earlier in the BFS.
                    return first_dir_from_start
                
                # 3. Check for collision with obstacles (if not the target)
                if next_pos in obstacles_set:
                    continue
                
                # If the `next_pos` is safe and hasn't been visited yet:
                if next_pos not in visited:
                    visited.add(next_pos)
                    
                    # If `current_pos` is the starting point, `direction_str` is the first move.
                    # Otherwise, inherit the `first_dir_from_start` from the parent.
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
    # Obstacles for pathfinding to food: the snake's body *excluding* its current tail,
    # as the tail will vacate its spot on the next move.
    food_path_obstacles = set(snake[:-1])
    path_first_move = _find_path_bfs(head, food, width, height, food_path_obstacles)

    if path_first_move:
        return path_first_move

    # ====================================================================
    # --- Strategy 2: If no path to food, try to survive ---
    #   Sub-strategy A: Find a move that allows reaching the *new* tail, tie-break by largest free space.
    #   Sub-strategy B: If no such move, find a move that leads to largest *immediate* free space.
    
    candidate_tail_moves = [] # Stores (reachable_count, move_dir) for moves that can reach tail

    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_head_potential = (head[0] + dr, head[1] + dc)

        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail)
        #    This is for the *current* snake.
        if next_head_potential in snake[:-1]:
            continue
            
        # 3. For survival mode, moving onto food is not considered 'safe' for finding free space.
        #    We are specifically looking for empty space to survive, not to eat.
        if next_head_potential == food:
            continue
        
        # --- Passed immediate safety checks for survival (not hitting wall/body/food) ---
        
        # Simulate the snake's state after this potential move
        simulated_snake = [next_head_potential] + snake[:-1]
        simulated_tail_pos = simulated_snake[-1]
        
        # Obstacles for pathfinding to the simulated tail:
        # All segments of the simulated snake *except* the target tail position.
        # The actual food position is also an obstacle when trying to find a path to the tail,
        # unless the food itself *is* the simulated tail position (unlikely, but handled).
        obstacles_for_tail_path_bfs = set(simulated_snake[:-1])
        if food != simulated_tail_pos: # Avoid adding food as an obstacle if it's our target (tail)
            obstacles_for_tail_path_bfs.add(food)

        # Check if a path exists from the new head to the new tail
        path_to_simulated_tail = _find_path_bfs(
            start_pos=next_head_potential, 
            target_pos=simulated_tail_pos, 
            board_width=width, 
            board_height=height, 
            obstacles_set=obstacles_for_tail_path_bfs
        )

        if path_to_simulated_tail:
            # If a path to the tail exists, this is a robust survival move.
            # Now, score it by the amount of free space it leads to.
            # Obstacles for free space count: new snake body (excluding its tail), and food.
            obstacles_for_free_space_bfs = set(simulated_snake[:-1])
            obstacles_for_free_space_bfs.add(food) # Food is always an obstacle when counting free cells

            reachable_cells = _count_reachable_cells_bfs(
                start_pos=next_head_potential,
                board_width=width,
                board_height=height,
                fixed_obstacles_set=obstacles_for_free_space_bfs
            )
            candidate_tail_moves.append((reachable_cells, direction_str))

    if candidate_tail_moves:
        # Sort by reachable_cells (descending) to pick the best move.
        # If reachable_cells are equal, the first encountered direction (based on DIRECTIONS dict order) wins.
        candidate_tail_moves.sort(key=lambda x: x[0], reverse=True)
        return candidate_tail_moves[0][1]

    # --- Fallback: If no move allows reaching the tail (very dangerous situation) ---
    # This means the snake is likely going to get trapped.
    # In this case, just go for the largest *immediate* free space,
    # without guaranteeing a path to the tail. This is equivalent to the original Strategy 2.
    
    best_fallback_move = None
    max_fallback_reachable_cells = -1

    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_head_potential = (head[0] + dr, head[1] + dc)
        
        # 1. Check boundaries
        if not (0 <= next_head_potential[0] < height and 0 <= next_head_potential[1] < width):
            continue
        
        # 2. Check collision with snake's body (excluding its current tail)
        if next_head_potential in snake[:-1]:
            continue
            
        # 3. Exclude food for free space calculation
        if next_head_potential == food:
            continue
            
        # This move is immediately safe, now count reachable cells from it.
        # Obstacles for this fallback BFS: current snake body (excluding its tail), and food.
        fallback_obstacles = set(snake[:-1])
        fallback_obstacles.add(food) # Food is always an obstacle when counting free cells
        
        reachable_count = _count_reachable_cells_bfs(
            next_head_potential, width, height, fallback_obstacles
        )

        if reachable_count > max_fallback_reachable_cells:
            max_fallback_reachable_cells = reachable_count
            best_fallback_move = direction_str

    if best_fallback_move:
        return best_fallback_move
    
    # Emergency fallback: If completely trapped (no safe moves at all), just return a default direction.
    # This scenario means the snake will die regardless, so the specific direction doesn't matter much.
    return "RIGHT"