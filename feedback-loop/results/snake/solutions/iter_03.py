import collections

def next_move(snake, food, width, height):
    head_r, head_c = snake[0]

    directions_map = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    # For deterministic ordering of moves if multiple paths have same length/score
    ordered_directions = ["UP", "DOWN", "LEFT", "RIGHT"]

    # Helper function to check if a position is within board boundaries
    def is_valid(r, c):
        return 0 <= r < height and 0 <= c < width

    # Helper function to get the snake's body coordinates after a potential move
    # next_head_pos: the (r, c) of the snake's head after the move
    # current_snake: the current snake body (list of (r, c) tuples)
    # ate_food: boolean, true if the snake eats food with this move
    # Returns a list of (r, c) tuples representing the virtual snake body
    def get_future_snake_body(next_head_pos, current_snake, ate_food):
        if ate_food:
            return [next_head_pos] + current_snake
        else:
            return [next_head_pos] + current_snake[:-1]

    # BFS pathfinding function
    # Returns the first move (direction string) from start_node to target_node,
    # avoiding specified obstacles. Returns None if no path found or if start_node is target_node.
    def get_path_bfs(start_node, target_node, obstacles_set):
        queue = collections.deque([(start_node, [])]) # (current_pos, path_to_current_pos)
        visited = {start_node} # Store visited (row, col) tuples to prevent cycles and redundant checks

        while queue:
            (r, c), path = queue.popleft()

            if (r, c) == target_node:
                # If the start_node is the target_node, no *initial* move is needed.
                # In next_move context, we need a 'next move', so we return the first step of the path.
                # If path is empty, it means we are already at the target, so no move.
                return path[0] if path else None 

            for direction_name in ordered_directions:
                dr, dc = directions_map[direction_name]
                next_r, next_c = r + dr, head_c + dc if direction_name in ["UP", "DOWN"] else c + dc # Fixed bug: used head_c instead of c for vertical moves
                next_pos = (next_r, next_c)

                # 1. Wall collision check
                if not is_valid(next_r, next_c):
                    continue

                # 2. Body collision check:
                # A cell is an obstacle if it's in obstacles_set AND it's not the target itself.
                # This ensures we can pathfind *to* the target, even if the target's current position
                # is included in the general 'obstacles_set' (e.g., pathfinding to tail).
                if next_pos in obstacles_set and next_pos != target_node:
                    continue
                
                # 3. Already visited check
                if next_pos in visited:
                    continue

                # If safe and unvisited, add to queue
                visited.add(next_pos)
                queue.append((next_pos, path + [direction_name]))
        
        return None # No path found

    # Counts reachable empty cells from start_node, avoiding specified obstacles.
    # Returns the total count of reachable cells.
    def count_reachable_cells(start_node, obstacles_set):
        queue = collections.deque([start_node])
        visited = {start_node}
        count = 0

        while queue:
            r, c = queue.popleft()
            count += 1

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # UP, DOWN, LEFT, RIGHT
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                if not is_valid(next_r, next_c):
                    continue
                if next_pos in obstacles_set: # Any obstacle means it's not "empty" space
                    continue
                if next_pos in visited:
                    continue
                
                visited.add(next_pos)
                queue.append(next_pos)
        return count

    # --- Strategy 1: Find a safe path to food ---
    # Obstacles for path to food: current snake body segments, excluding head.
    # The tail (snake[-1]) is an obstacle because eating food means the tail doesn't move.
    food_path_obstacles = set(snake[1:])
    path_to_food_move = get_path_bfs(snake[0], food, food_path_obstacles)

    if path_to_food_move:
        # Calculate the head position if we take this food move
        dr, dc = directions_map[path_to_food_move]
        next_head_r, next_head_c = head_r + dr, head_c + dc
        next_head_pos = (next_head_r, next_head_c)

        # Simulate the snake's state *after* eating the food
        # The snake grows, so its tail stays in its current position.
        virtual_snake_after_eat = get_future_snake_body(next_head_pos, snake, ate_food=True)
        
        # Obstacles for the safety check (can we reach the new tail after eating?).
        # All parts of the new snake body are obstacles, EXCEPT the new tail itself.
        # virtual_snake_after_eat[1:-1] correctly excludes the new head and the new tail.
        safety_check_obstacles = set(virtual_snake_after_eat[1:-1]) 

        # Check if, after eating, the snake can still reach its new tail.
        # This prevents trapping itself after eating.
        can_reach_new_tail = get_path_bfs(next_head_pos, virtual_snake_after_eat[-1], safety_check_obstacles)
        
        if can_reach_new_tail:
            return path_to_food_move

    # --- Strategy 2: Find a safe survival move (maximize empty space) ---
    # If no safe path to food, or if the food path is unsafe, try to survive by
    # moving to the area that offers the most free space.
    best_survival_move = None
    max_reachable_space = -1

    for direction_name in ordered_directions:
        dr, dc = directions_map[direction_name]
        next_r, next_c = head_r + dr, head_c + dc
        next_head_pos = (next_r, next_c)

        # 1. Immediate wall collision check
        if not is_valid(next_r, next_c):
            continue

        # 2. Check for immediate self-collision (hitting the *current* snake body, excluding tail)
        # The tail (snake[-1]) is guaranteed to move, so it's not an obstacle for the *next* head position.
        # snake[:-1] correctly represents all segments from head up to the second-to-last segment.
        if next_head_pos in snake[:-1]:
            continue

        # Simulate snake's state *without* eating food (tail moves)
        virtual_snake_after_move = get_future_snake_body(next_head_pos, snake, ate_food=False)
        
        # Obstacles for counting reachable space: the entire virtual snake body AND the food.
        # We want to count cells that are truly empty and not occupied by the snake or food.
        obstacles_for_space_count = set(virtual_snake_after_move)
        obstacles_for_space_count.add(food) # Food is not considered "empty space" for survival pathfinding

        # Calculate reachable empty cells from this potential next_head_pos
        current_reachable_space = count_reachable_cells(next_head_pos, obstacles_for_space_count)

        # Prioritize moves that lead to more reachable space
        if current_reachable_space > max_reachable_space:
            max_reachable_space = current_reachable_space
            best_survival_move = direction_name
        
    if best_survival_move:
        return best_survival_move

    # --- Strategy 3: Fallback (should ideally not be reached in typical games) ---
    # If no safe move found via above strategies (e.g., completely trapped and board is full).
    # This scenario implies all possible moves lead to immediate death or no reachable space.
    # Return an arbitrary direction.
    return "UP"