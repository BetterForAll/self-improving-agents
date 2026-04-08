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

    def manhattan_distance(pos1, pos2):
        """Calculates Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # --- Phase 1: Attempt to find a path to food that also allows for an escape ---

    # Calculate obstacles for pathfinding to food. The snake's tail is considered free
    # because it will move out of the way.
    obstacles_for_food_path = get_snake_obstacles(snake, ignore_last_segment=True)
    path_to_food = bfs(head, food, obstacles_for_food_path, return_path=True)

    if path_to_food:
        # If a path to food is found, simulate eating and check for an escape route.
        # The simulated snake after eating includes the food cell as the new head,
        # and its body is effectively one segment longer (the old tail does NOT disappear yet for this check).
        simulated_snake_body_after_eating = [food] + snake
        
        # Obstacles for finding an escape path: the entire *longer* simulated snake body.
        obstacles_for_escape = get_snake_obstacles(simulated_snake_body_after_eating, ignore_last_segment=False)
        
        # The target for the escape path is the original tail position, as this is the cell
        # that would eventually become free. This cell must not be considered an obstacle itself.
        if tail in obstacles_for_escape:
            obstacles_for_escape.discard(tail)
        
        # Check if there is a path from the new head (food) to the old tail.
        has_escape_path = bfs(food, tail, obstacles_for_escape, return_path=False)

        if has_escape_path:
            # If a safe path to food and an escape path exist, take the first step towards food.
            return path_to_food[0]

    # --- Phase 2: No safe path to food. Prioritize survival by finding the safest move. ---
    # Find a move that keeps the snake from immediately dying and ideally allows
    # it to eventually reach its current tail (to avoid self-entrapment).
    
    best_survival_move = None
    longest_path_to_tail_found = -1
    min_dist_to_food_for_best_move = float('inf') # Added for tie-breaking: prefer closer to food

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
            # For checking reachability to the tail, this new body forms the obstacles.
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
                current_path_len = len(path_to_tail)
                dist_to_food_after_move = manhattan_distance(next_pos, food)

                # Prioritize moves that result in a longer path to the tail,
                # as this generally indicates more open space for maneuverability.
                if current_path_len > longest_path_to_tail_found:
                    longest_path_to_tail_found = current_path_len
                    min_dist_to_food_for_best_move = dist_to_food_after_move # Reset tie-breaker
                    best_survival_move = move_name
                # If path length is equal, use distance to food as a tie-breaker (prefer closer food).
                elif current_path_len == longest_path_to_tail_found:
                    if dist_to_food_after_move < min_dist_to_food_for_best_move:
                        min_dist_to_food_for_best_move = dist_to_food_after_move
                        best_survival_move = move_name

    if best_survival_move:
        return best_survival_move
    
    # --- Phase 3: Fallback - All paths lead to immediate death or guaranteed entrapment. ---
    # This scenario means the snake is completely trapped and will die.
    # Just return any immediately valid move if possible, or a default.
    # This ensures the game can continue for one more turn, even if fatal.
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head[0] + dr, head[1] + dc
        next_pos = (next_r, next_c)
        # Here we only check for immediate collisions (walls or non-moving body parts)
        # The `obstacles_for_current_moves` already considers the tail as free.
        if is_valid_cell(next_r, next_c) and next_pos not in obstacles_for_current_moves:
            return move_name

    # If even the most basic immediate safe move isn't possible (fully surrounded),
    # the snake is definitely doomed. Return a default, it will hit something.
    return "UP"