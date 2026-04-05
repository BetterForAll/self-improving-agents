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
    # For deterministic ordering of moves if multiple paths have same length
    ordered_directions = ["UP", "DOWN", "LEFT", "RIGHT"] 

    # Helper function to check if a position is within board boundaries
    def is_valid(r, c):
        return 0 <= r < height and 0 <= c < width

    # BFS pathfinding function
    # Returns the first move (direction string) from start_node to target_node,
    # avoiding specified obstacles.
    def find_path_bfs(start_node, target_node, obstacles_body):
        queue = collections.deque([(start_node, [])]) # (current_pos, path_to_current_pos)
        visited = {start_node} # Store visited (row, col) tuples to prevent cycles and redundant checks

        while queue:
            (r, c), path = queue.popleft()

            if (r, c) == target_node:
                # If the start_node is the target_node, no move is needed.
                # In next_move context, this would imply snake is already on target,
                # but we need a 'next move', so we return None.
                if not path: 
                    return None
                return path[0] # Return the first direction in the path

            for direction_name in ordered_directions:
                dr, dc = directions_map[direction_name]
                next_r, next_c = r + dr, c + dc
                next_pos = (next_r, next_c)

                # 1. Wall collision check
                if not is_valid(next_r, next_c):
                    continue

                # 2. Body collision check:
                # A cell is an obstacle if it's in obstacles_body AND it's not the target itself.
                # This ensures we can pathfind *to* the target, even if the target's current position
                # is included in the general 'obstacles_body' set (e.g., pathfinding to tail).
                if next_pos in obstacles_body and next_pos != target_node:
                    continue
                
                # 3. Already visited check
                if next_pos in visited:
                    continue

                # If safe and unvisited, add to queue
                visited.add(next_pos)
                queue.append((next_pos, path + [direction_name]))
        
        return None # No path found

    # Strategy 1: Find shortest path to food
    # When going for food, assume the snake grows. So, its current tail doesn't move.
    # Therefore, all existing body segments (snake[1:]) are considered obstacles.
    food_obstacles = set(snake[1:])
    path_to_food_move = find_path_bfs(snake[0], food, food_obstacles)
    if path_to_food_move:
        return path_to_food_move

    # Strategy 2: If no path to food, find shortest path to the tail (to stay alive)
    # This is done only if the snake has more than one segment.
    # When chasing the tail, assume the snake doesn't grow. So, its tail will move.
    # Therefore, the tail (snake[-1]) is NOT an obstacle; it's the target.
    # Only the body segments from snake[1] to snake[-2] (i.e., snake[1:-1]) are obstacles.
    path_to_tail_move = None
    if len(snake) > 1:
        tail_obstacles = set(snake[1:-1]) 
        path_to_tail_move = find_path_bfs(snake[0], snake[-1], tail_obstacles)

    if path_to_tail_move:
        return path_to_tail_move

    # Strategy 3: If no path to food or tail, try any single-step safe move.
    # This scenario typically means the snake is very trapped.
    # The obstacle definition is the same as for chasing the tail: only snake[1:-1] are obstacles.
    safe_moves_one_step = []
    
    # Determine obstacles for single-step lookahead (most permissive for survival)
    any_safe_move_obstacles = set(snake[1:-1]) if len(snake) > 1 else set()

    for direction_name in ordered_directions:
        dr, dc = directions_map[direction_name]
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)
        
        # Wall collision check
        if not is_valid(next_r, next_c):
            continue
        
        # Body collision check (using the most permissive obstacle set)
        if next_pos in any_safe_move_obstacles:
            continue
        
        safe_moves_one_step.append(direction_name)

    if safe_moves_one_step:
        # Pick the first safe move in the preferred order (e.g., UP, DOWN, LEFT, RIGHT)
        return safe_moves_one_step[0]

    # Strategy 4: Fallback - No safe moves at all. The snake is completely trapped.
    # Any move will result in collision. Return an arbitrary direction.
    return "UP"