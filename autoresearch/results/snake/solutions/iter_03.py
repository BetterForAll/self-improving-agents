import collections

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using a smarter strategy.

    The strategy prioritizes moves that:
    1. Lead to the food via the shortest path, *and* ensure the snake can
       reach its new tail position after eating (to avoid self-trapping).
    2. If food is not safely reachable, lead to the snake's current tail
       via the *longest* path, maximizing free movement space.
    3. As a last resort, any immediately safe move.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    head_row, head_col = snake[0]

    possible_moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # --- Helper function for checking position validity and obstacles ---
    def is_safe(pos, obstacles, board_width, board_height):
        """Checks if a position is within board bounds and not an obstacle."""
        row, col = pos
        # 1. Check for wall collision
        if not (0 <= row < board_height and 0 <= col < board_width):
            return False
        # 2. Check for collision with obstacles (snake body segments)
        if pos in obstacles:
            return False
        return True

    # --- Helper function for BFS pathfinding ---
    def find_path_bfs(start_pos, target_pos, simulated_snake_body_as_obstacles, board_width, board_height):
        """
        Finds the shortest path from start_pos to target_pos using BFS,
        avoiding positions in simulated_snake_body_as_obstacles.
        
        Args:
            start_pos (tuple): (row, col) starting point.
            target_pos (tuple): (row, col) target point.
            simulated_snake_body_as_obstacles (list): The list of (row, col) tuples representing 
                                                  the snake's body to avoid.
            board_width (int): Board width.
            board_height (int): Board height.
            
        Returns:
            list: A list of (row, col) tuples representing the path, including start and target,
                  or None if no path is found.
        """
        queue = collections.deque([(start_pos, [start_pos])])
        visited = {start_pos}

        # The actual obstacles for BFS are the simulated snake body segments,
        # but the target position itself should not be considered an obstacle.
        bfs_obstacles = set(simulated_snake_body_as_obstacles) - {target_pos}

        while queue:
            current_node, path = queue.popleft()

            if current_node == target_pos:
                return path

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # UP, DOWN, LEFT, RIGHT
                neighbor_pos = (current_node[0] + dr, current_node[1] + dc)

                if is_safe(neighbor_pos, bfs_obstacles, board_width, board_height) and neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    queue.append((neighbor_pos, path + [neighbor_pos]))
        return None # No path found

    # --- Step 1: Filter out immediately unsafe moves ---
    # A move is immediately unsafe if it hits a wall or the snake's body.
    # The snake's tail (snake[-1]) will move out of its current position when the snake
    # moves forward, making that spot safe. So, we avoid `snake[:-1]`.
    
    # Stores (direction, next_head_pos, simulated_snake_body_after_move) for valid initial moves
    candidate_moves_info = [] 

    # For efficient lookup, convert the snake's body parts (excluding tail) to a set of obstacles
    current_snake_body_obstacles = set(snake[:-1])

    for direction, (dr, dc) in possible_moves.items():
        next_head_pos = (head_row + dr, head_col + dc)

        # Check for immediate wall or self-collision
        if not is_safe(next_head_pos, current_snake_body_obstacles, width, height):
            continue
        
        # If the move is safe, simulate the snake's body *after* this move.
        # This simulated body will be used as obstacles for pathfinding within the BFS.
        # The head moves to next_head_pos, and the rest of the body shifts, the old tail vanishes.
        simulated_snake_body_after_move = [next_head_pos] + snake[:-1]
        
        candidate_moves_info.append((direction, next_head_pos, simulated_snake_body_after_move))

    # If no safe moves, the snake is trapped. Game over is imminent.
    # Return a default direction (e.g., "UP") as a fallback.
    if not candidate_moves_info:
        return "UP" 

    # --- Step 2: Prioritize moves that lead to food ---
    
    # Store (direction, path_length_to_food, path_to_food_actual_list) for moves that can reach food
    food_reachable_moves = [] 
    
    for direction, next_head_pos, simulated_snake_body_after_move in candidate_moves_info:
        # Use BFS to find a path from next_head_pos to food, avoiding simulated_snake_body_after_move as obstacles.
        path_to_food = find_path_bfs(next_head_pos, food, simulated_snake_body_after_move, width, height)
        if path_to_food:
            food_reachable_moves.append((direction, len(path_to_food), path_to_food))

    # If food is reachable via any safe move:
    if food_reachable_moves:
        # Sort by path length to food (shortest path first)
        food_reachable_moves.sort(key=lambda x: x[1])

        best_food_move_direction = None
        # Get the minimum path length to food
        min_food_path_length = food_reachable_moves[0][1] 

        # Filter for all moves that achieve this minimum path length to food
        shortest_food_paths_candidates = [m for m in food_reachable_moves if m[1] == min_food_path_length]

        # From these candidates, prioritize moves that also allow reaching the new tail *after eating*.
        # When food is eaten, the snake grows, meaning its tail does *not* move.
        # The new head position will be `food`, and the new tail position will be `snake[-1]` (the old tail).
        # The new body will be `[food] + snake` (old body, extended at the head).
        
        best_tail_path_len_after_eating = -1 # We want to maximize this (longest path to new tail)
        
        for direction, path_len_to_food, _ in shortest_food_paths_candidates:
            # The snake body *if food were eaten*: `[food]` (new head) + `snake` (old body)
            snake_body_if_food_eaten = [food] + snake
            
            # Find a path from the new head (food) to the new tail (snake[-1])
            path_to_new_tail = find_path_bfs(food, snake[-1], snake_body_if_food_eaten, width, height)
            
            if path_to_new_tail:
                # If a path to the new tail exists after eating, this is a safer move.
                # Prioritize longer paths to the new tail for more maneuvering room.
                if len(path_to_new_tail) > best_tail_path_len_after_eating:
                    best_tail_path_len_after_eating = len(path_to_new_tail)
                    best_food_move_direction = direction
            
        # If we found a move that leads to food AND allows safely reaching the new tail
        if best_food_move_direction:
            return best_food_move_direction
        else:
            # If no shortest path to food also has a path to the new tail,
            # just pick the absolute shortest path to food (the first one in the sorted list).
            # This is a less safe but still direct option.
            return shortest_food_paths_candidates[0][0]


    # --- Step 3: If food is not safely reachable, prioritize moves that lead to the snake's tail ---
    # This strategy helps the snake to keep moving in a safe loop, preventing it from trapping itself.
    # We want the *longest* path to the tail to keep as much open space as possible.

    tail_reachable_moves = []
    
    for direction, next_head_pos, simulated_snake_body_after_move in candidate_moves_info:
        # Target is the current tail position (snake[-1]), which will become free after the move.
        # Find a path from next_head_pos to snake[-1], avoiding simulated_snake_body_after_move as obstacles.
        path_to_tail = find_path_bfs(next_head_pos, snake[-1], simulated_snake_body_after_move, width, height)
        if path_to_tail:
            tail_reachable_moves.append((direction, len(path_to_tail))) # Store path length

    if tail_reachable_moves:
        # Sort by path length to tail (longest first) to maximize maneuverability and avoid traps
        tail_reachable_moves.sort(key=lambda x: x[1], reverse=True)
        return tail_reachable_moves[0][0]

    # --- Step 4: If neither food nor tail is reachable, pick any safe move ---
    # This is a last resort, meaning the snake is likely in a very tight spot
    # and all calculated paths lead to a dead end. Any of the `candidate_moves_info`
    # will technically lead to a valid next_head_pos without immediate collision.
    # The first one from the candidate list (based on original `possible_moves` order) is chosen.
    return candidate_moves_info[0][0]