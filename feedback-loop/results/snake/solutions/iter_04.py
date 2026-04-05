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
    # Returns the path (list of direction strings) from start_node to target_node,
    # avoiding specified obstacles. Returns None if no path found.
    def find_path_bfs(start_node, target_node, obstacles_set):
        queue = collections.deque([(start_node, [])]) # (current_pos, path_to_current_pos)
        visited = {start_node} # Store visited (row, col) tuples

        while queue:
            (r, c), path = queue.popleft()

            if (r, c) == target_node:
                return path # Return the sequence of directions

            for direction_name in ordered_directions:
                dr, dc = directions_map[direction_name]
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                # 1. Wall collision check
                if not is_valid(next_r, next_c):
                    continue

                # 2. Body collision check:
                # A cell is an obstacle if it's in obstacles_set AND it's not the target itself.
                # This allows pathfinding *to* the target, even if the target is within the general obstacle set.
                if next_pos in obstacles_set and next_pos != target_node:
                    continue
                
                # 3. Already visited check
                if next_pos in visited:
                    continue

                # If safe and unvisited, add to queue
                visited.add(next_pos)
                queue.append((next_pos, path + [direction_name]))
        
        return None # No path found

    # Helper function to count reachable cells (freedom) from a start_node
    # This is a flood fill algorithm.
    def count_reachable_cells(start_node, obstacles_set_for_freedom):
        queue = collections.deque([start_node])
        visited = {start_node}
        count = 0

        while queue:
            r, c = queue.popleft()
            count += 1 # This cell is reachable

            for dr, dc in directions_map.values(): # All 4 directions
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                if not is_valid(next_r, next_c):
                    continue
                
                if next_pos in obstacles_set_for_freedom:
                    continue
                
                if next_pos in visited:
                    continue

                visited.add(next_pos)
                queue.append(next_pos)
        
        return count

    # Helper function to determine if a potential move leads to a "safe" state
    # A move is safe if, after making the move, the snake can still reach its (new virtual) tail.
    def is_move_safe(potential_next_head, current_snake_body, is_eating_food):
        if len(current_snake_body) == 0:
            return True # Should not happen in a typical snake game, but for robustness

        target_tail_for_bfs = None
        obstacles_for_bfs = set()

        if is_eating_food:
            # When eating, the snake grows. The current tail (current_snake_body[-1]) becomes part of the body.
            # The 'target tail' for safety check is the *current* tail (current_snake_body[-1]),
            # as this is the furthest part of its new, longer body it must be able to reach.
            target_tail_for_bfs = current_snake_body[-1]
            # Obstacles are all segments of the *current* snake body, as they will remain on the board.
            # The BFS itself ensures start_node (potential_next_head) is not an obstacle.
            obstacles_for_bfs = set(current_snake_body) 
        else:
            # Snake moves, tail shifts. The current tail (current_snake_body[-1]) vacates its spot.
            # The new tail will be the second to last segment of the *current* snake body (current_snake_body[-2]).
            if len(current_snake_body) <= 1:
                return True # A very short snake (length 0 or 1) cannot self-trap by moving into empty space.
            
            target_tail_for_bfs = current_snake_body[-2] # This will be the new tail after the move
            # Obstacles are the body segments of the *virtual* snake, excluding its head and new tail.
            # This effectively corresponds to current_snake_body[1:-1]
            obstacles_for_bfs = set(current_snake_body[1:-1])

        # Check if a path exists from the potential_next_head to the new virtual tail
        path_to_virtual_tail = find_path_bfs(potential_next_head, target_tail_for_bfs, obstacles_for_bfs)
        
        return path_to_virtual_tail is not None

    # Store candidate moves and their evaluations
    # Tuple format: (direction_name, is_eating_food, is_safe_after_move, reachable_cells_count_if_not_eating_food)
    candidate_moves = [] 

    for direction_name in ordered_directions:
        dr, dc = directions_map[direction_name]
        next_r, next_c = head_r + dr, head_c + dc
        potential_next_head = (next_r, next_c)

        # 1. Wall collision check
        if not is_valid(next_r, next_c):
            continue
        
        # 2. Immediate body collision check (excluding the tail, which will move)
        # `snake[1:-1]` represents all body segments excluding the head and the current tail.
        # Moving into these segments is always a collision.
        if potential_next_head in set(snake[1:-1]):
            continue

        # At this point, `potential_next_head` is either:
        #  - An empty cell
        #  - The food cell
        #  - The current tail cell (snake[-1]) - which is allowed as it will vacate.

        is_eating_food = (potential_next_head == food)
        
        # Now, evaluate the "safety" of this potential move by checking if the snake can
        # reach its new virtual tail from `potential_next_head`.
        is_safe_after_move = is_move_safe(potential_next_head, snake, is_eating_food)
        
        if is_safe_after_move:
            reachable_cells_count = 0
            if not is_eating_food:
                # Calculate freedom only for non-food moves. Food moves are prioritized
                # if they are safe, and don't need additional freedom metrics for tie-breaking
                # unless there are multiple safe food moves.
                
                # The virtual body for freedom calculation: [potential_next_head] + snake[:-1]
                # Obstacles for freedom calculation are these virtual body segments themselves.
                virtual_body_for_freedom = set([potential_next_head] + list(snake[:-1]))
                reachable_cells_count = count_reachable_cells(potential_next_head, virtual_body_for_freedom)
            
            candidate_moves.append((direction_name, is_eating_food, True, reachable_cells_count))

    # Prioritize candidate moves:
    # 1. Safe moves that lead to food (is_eating_food == True).
    # 2. Among safe non-food moves, those that provide the most "freedom" (max reachable_cells_count).
    # 3. If multiple moves are tied, the `ordered_directions` implicitly breaks ties
    #    because `candidate_moves` are appended in that order, and `sort` is stable for equal keys.

    if candidate_moves:
        # Sort primarily by `is_eating_food` (True first, so `reverse=True`)
        # Then by `reachable_cells_count` (descending, so more freedom first, `reverse=True`)
        candidate_moves.sort(key=lambda x: (x[1], x[3]), reverse=True)
        return candidate_moves[0][0] # Return the direction of the best move

    # Fallback: No safe moves found. The snake is completely trapped.
    # Any move will result in collision. Return an arbitrary direction.
    return ordered_directions[0] # Return "UP"