import collections

def next_move(snake, food, width, height):
    head = snake[0]
    tail = snake[-1]

    # Define possible moves as (dr, dc) tuples and their string names
    MOVES = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

    def is_valid_cell(r, c):
        """Check if a cell is within board boundaries."""
        return 0 <= r < height and 0 <= c < width

    def get_snake_obstacles(current_snake_body, ignore_last_segment=False):
        """
        Generates a set of obstacle cells from the snake's body.
        If ignore_last_segment is True, the very last segment (tail) is excluded,
        as it's considered free for the snake to move into.
        """
        obstacles = set(current_snake_body)
        if ignore_last_segment and len(current_snake_body) > 0:
            obstacles.discard(current_snake_body[-1])
        return obstacles

    def bfs(start_pos, target_pos, current_obstacles, return_path=True):
        """
        Performs a Breadth-First Search to find a path from start_pos to target_pos.
        
        Args:
            start_pos (tuple): (row, col) of the starting cell.
            target_pos (tuple): (row, col) of the target cell.
            current_obstacles (set): A set of (row, col) tuples that are blocked.
            return_path (bool): If True, returns the list of moves (e.g., ["UP", "RIGHT"]).
                                If False, returns True if a path exists, False otherwise.
        
        Returns:
            list or bool: The path (if return_path=True and path found), True (if return_path=False and path found),
                          None (if return_path=True and no path), False (if return_path=False and no path).
        """
        queue = collections.deque([(start_pos, [])]) # (current_cell, path_to_current_cell_moves)
        visited = {start_pos}

        # If start_pos is already the target, an empty path (or True for reachability) is valid.
        if start_pos == target_pos:
            return [] if return_path else True

        while queue:
            (r, c), path = queue.popleft()

            for move_name, (dr, dc) in MOVES.items():
                nr, nc = r + dr, c + dc
                next_pos = (nr, nc)

                if not is_valid_cell(nr, nc):
                    continue

                # If the next position is the target
                if next_pos == target_pos:
                    if return_path:
                        return path + [move_name]
                    else:
                        return True

                # If the next position is safe (not an obstacle and not visited)
                if next_pos not in current_obstacles and next_pos not in visited:
                    visited.add(next_pos)
                    new_path = path + [move_name]
                    queue.append((next_pos, new_path))
        
        return None if return_path else False

    # Helper to calculate min distance to any wall
    def get_min_dist_to_wall(r, c):
        return min(r, c, height - 1 - r, width - 1 - c)

    # --- Phase 1: Attempt to find a path to food that also allows for a safe escape ---
    # This phase evaluates each possible immediate first move. For each move, it checks:
    # 1. If that move leads to a path to food.
    # 2. If, after eating the food, there's a path to the original tail (as a safe escape).
    # It prioritizes moves that maximize the escape path length, secondarily minimizes the food path length,
    # and as a tie-breaker, maximizes the distance to the nearest wall.
    
    best_food_move = None
    min_food_path_len = float('inf')
    max_escape_path_len_after_food = -1
    max_min_dist_to_wall_food_phase = -1 # Tie-breaker: max distance from wall for `first_step_pos`

    # When pathfinding to food, the current snake's tail is considered free to move into.
    obstacles_for_food_bfs_from_head = get_snake_obstacles(snake, ignore_last_segment=True)

    # Consider each immediate potential move from the head.
    for first_move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head[0] + dr, head[1] + dc
        first_step_pos = (next_r, next_c)

        # 1. Check if the first step itself is valid (within bounds and not hitting current snake body,
        # where the tail is ignored).
        if not is_valid_cell(next_r, next_c) or first_step_pos in obstacles_for_food_bfs_from_head:
            continue

        # Simulate the snake having made this first step.
        # Its new head is `first_step_pos`. The new body segments are `[first_step_pos] + snake[:-1]`.
        # When finding a path to food *from this new head*, these new body segments become obstacles.
        # The tail of this *simulated* snake (which is `snake[-1]`) is considered free.
        simulated_snake_after_first_step = [first_step_pos] + snake[:-1]
        
        obstacles_to_reach_food_from_first_step = get_snake_obstacles(simulated_snake_after_first_step, ignore_last_segment=True)
        
        # 2. Find a path from `first_step_pos` to `food`.
        path_to_food_from_first_step = bfs(first_step_pos, food, obstacles_to_reach_food_from_first_step, return_path=True)

        if path_to_food_from_first_step is None:
            # This first move does not lead to a path to food.
            continue
        
        # We found a viable path to food. Now, check if eating it allows for a safe escape.
        current_food_path_len = 1 + len(path_to_food_from_first_step) # 1 for first_move + path_len from first_step

        # 3. Simulate the snake's state *after* eating the food.
        # Its body will be `[food] + original_snake`. It's one segment longer because the tail doesn't disappear.
        simulated_snake_body_after_eating = [food] + snake
        
        # Obstacles for the escape path: the entire *longer* simulated snake body.
        # The target for the escape path is the original tail position. It must be free for pathfinding.
        obstacles_for_escape = get_snake_obstacles(simulated_snake_body_after_eating, ignore_last_segment=False)
        if tail in obstacles_for_escape: # The original tail is the eventual target, so it's not an obstacle itself.
            obstacles_for_escape.discard(tail)
        
        # Find a path from the new head (food) to the original tail.
        path_from_food_to_tail = bfs(food, tail, obstacles_for_escape, return_path=True)
        
        current_escape_path_len = -1 # Default if no escape path is found
        if path_from_food_to_tail is not None:
            current_escape_path_len = len(path_from_food_to_tail)
        
        current_min_dist_to_wall = get_min_dist_to_wall(first_step_pos[0], first_step_pos[1])

        # Evaluate this candidate move based on the prioritized strategy:
        # 1. Maximise escape path length (longer path to tail means more open space for survival after eating).
        # 2. Minimise food path length (efficiency).
        # 3. Maximise distance from nearest wall (tie-breaker for robustness).
        is_better = False
        if current_escape_path_len > max_escape_path_len_after_food:
            is_better = True
        elif current_escape_path_len == max_escape_path_len_after_food:
            if current_food_path_len < min_food_path_len:
                is_better = True
            elif current_food_path_len == min_food_path_len:
                if current_min_dist_to_wall > max_min_dist_to_wall_food_phase:
                    is_better = True

        if is_better:
            max_escape_path_len_after_food = current_escape_path_len
            min_food_path_len = current_food_path_len
            max_min_dist_to_wall_food_phase = current_min_dist_to_wall
            best_food_move = first_move_name

    if best_food_move:
        return best_food_move

    # --- Phase 2: No safe path to food. Prioritize survival by finding the safest move. ---
    # Find a move that keeps the snake from immediately dying and ideally allows
    # it to eventually reach its current tail to avoid self-entrapment.
    # Prioritizes moves that lead to a longer path to the tail, and as a tie-breaker,
    # maximizes the distance to the nearest wall.
    
    best_survival_move = None
    longest_path_to_tail_found = -1
    max_min_dist_to_wall_survival_phase = -1 # Tie-breaker: max distance from wall for `next_pos`

    # For survival moves, the current tail is still considered free as the snake will move.
    obstacles_for_current_moves = get_snake_obstacles(snake, ignore_last_segment=True)

    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head[0] + dr, head[1] + dc
        next_pos = (next_r, next_c)

        # Check if the immediate potential move is valid (within bounds and not hitting its own body,
        # where the tail is considered free).
        if is_valid_cell(next_r, next_c) and next_pos not in obstacles_for_current_moves:
            # Simulate the snake moving one step for this potential survival move.
            # The new head is `next_pos`. The new body is `[next_pos] + snake[:-1]`.
            simulated_body_after_move = [next_pos] + snake[:-1]
            
            # Obstacles for checking future tail reachability: the full simulated body.
            obstacles_for_tail_reachability = get_snake_obstacles(simulated_body_after_move, ignore_last_segment=False)
            
            # The target for this pathfinding is the *original* tail position, as this cell
            # will become free. Ensure it's not in the obstacles set.
            if tail in obstacles_for_tail_reachability:
                obstacles_for_tail_reachability.discard(tail)
            
            # Check if, after making this move, the snake can still reach its tail.
            # This ensures it doesn't immediately trap itself.
            path_to_tail = bfs(next_pos, tail, obstacles_for_tail_reachability, return_path=True)

            if path_to_tail is not None: # A path to the tail exists
                current_path_to_tail_len = len(path_to_tail)
                current_min_dist_to_wall = get_min_dist_to_wall(next_r, next_c)

                # Prioritize moves that result in a longer path to the tail,
                # as this generally indicates more open space for maneuverability.
                # As a tie-breaker, maximize distance from walls.
                is_better_survival = False
                if current_path_to_tail_len > longest_path_to_tail_found:
                    is_better_survival = True
                elif current_path_to_tail_len == longest_path_to_tail_found:
                    if current_min_dist_to_wall > max_min_dist_to_wall_survival_phase:
                        is_better_survival = True
                
                if is_better_survival:
                    longest_path_to_tail_found = current_path_to_tail_len
                    max_min_dist_to_wall_survival_phase = current_min_dist_to_wall
                    best_survival_move = move_name

    if best_survival_move:
        return best_survival_move
    
    # --- Phase 3: Fallback - All paths lead to immediate death or guaranteed entrapment. ---
    # If even the survival moves lead to guaranteed entrapment, try any immediately valid move
    # just to continue for one more turn, even if fatal.
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head[0] + dr, head[1] + dc
        next_pos = (next_r, next_c)
        # Here we only check for immediate collisions (walls or non-moving body parts).
        # The `obstacles_for_current_moves` already considers the tail as free.
        if is_valid_cell(next_r, next_c) and next_pos not in obstacles_for_current_moves:
            return move_name

    # If no valid move is found (e.g., completely surrounded), the snake is doomed.
    # Return a default move; it will hit something.
    return "UP"