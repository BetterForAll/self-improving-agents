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
                neighbor_pos = (current_node[0] + dr, current_col + dc)

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
        return "UP" # This state should ideally lead to game over

    # --- Step 2: Prioritize moves that lead to food SAFELY ---
    # A move is safe if it leads to food AND after eating, the snake can still reach its new tail.
    
    # Store (direction, path_len_to_food, path_len_to_new_tail_after_eating) for moves that can safely reach food
    truly_safe_food_moves = [] 
    
    for direction, next_head_pos, simulated_snake_body_after_move in candidate_moves_info:
        # 1. Find a path from next_head_pos to food, avoiding the snake's body *after this move*.
        path_to_food = find_path_bfs(next_head_pos, food, simulated_snake_body_after_move, width, height)
        
        if path_to_food:
            # 2. If a path to food exists, now check if it's safe *after eating*.
            #    When food is eaten, the snake's head is at 'food', and its body is 'snake' (old body).
            #    The new tail will be the same as the old tail (snake[-1]).
            snake_body_if_food_eaten = [food] + snake # New head at 'food', old 'snake' body follows
            
            # Find a path from the new head (food) to the new tail (snake[-1])
            path_to_new_tail_after_eating = find_path_bfs(food, snake[-1], snake_body_if_food_eaten, width, height)
            
            if path_to_new_tail_after_eating:
                # This move is truly safe: it reaches food AND avoids self-trapping after eating.
                truly_safe_food_moves.append((direction, len(path_to_food), len(path_to_new_tail_after_eating)))

    if truly_safe_food_moves:
        # Sort by:
        # 1. Shortest path to food (primary key, ascending)
        # 2. Longest path to new tail after eating (secondary key, descending, hence -x[2])
        truly_safe_food_moves.sort(key=lambda x: (x[1], -x[2]))
        return truly_safe_food_moves[0][0]

    # --- Step 3: If no truly safe food path, prioritize moves that lead to the snake's current tail ---
    # This strategy helps the snake to keep moving in a safe loop, preventing it from trapping itself.
    # We want the *longest* of the shortest paths to the tail to maximize free movement space.

    tail_reachable_moves = []
    
    for direction, next_head_pos, simulated_snake_body_after_move in candidate_moves_info:
        # Target is the current tail position (snake[-1]), which will become free after the move.
        # Find a path from next_head_pos to snake[-1], avoiding simulated_snake_body_after_move as obstacles.
        path_to_tail = find_path_bfs(next_head_pos, snake[-1], simulated_snake_body_after_move, width, height)
        if path_to_tail:
            tail_reachable_moves.append((direction, len(path_to_tail))) # Store path length

    if tail_reachable_moves:
        # Sort by path length to tail (longest of the shortest paths first)
        tail_reachable_moves.sort(key=lambda x: x[1], reverse=True)
        return tail_reachable_moves[0][0]

    # --- Step 4: If neither truly safe food path nor tail path is reachable, pick any safe move ---
    # This is a last resort, meaning the snake is likely in a very tight spot
    # and all calculated paths lead to a dead end. Any of the `candidate_moves_info`
    # will technically lead to a valid next_head_pos without immediate collision.
    # The first one from the candidate list (based on original `possible_moves` order) is chosen.
    return candidate_moves_info[0][0]