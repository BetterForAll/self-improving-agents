import heapq

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using A* search to reliably locate food and predict potential self-collisions.

    This improved version adds a robust survival strategy: if food is unreachable,
    the snake attempts to find a path to its own tail to maximize playable space
    and survive longer.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    # Helper A* function - defined locally to adhere to "return ONLY the function definition"
    def find_path_astar(start, goal, obstacles, current_width, current_height, heuristic_func):
        """
        Finds a path from start to goal using A* search.
        
        Args:
            start: (row, col) tuple, starting position.
            goal: (row, col) tuple, target position.
            obstacles: set of (row, col) tuples, positions to avoid.
            current_width: int, board width.
            current_height: int, board height.
            heuristic_func: function that takes (r, c) and returns heuristic value to goal.
            
        Returns:
            list of (row, col) tuples representing the path from start to goal (inclusive),
            or None if no path found.
        """
        
        MOVES_DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)] # UP, DOWN, LEFT, RIGHT

        open_set = []
        # (f_score, node) - f_score is g_score + heuristic
        heapq.heappush(open_set, (heuristic_func(start[0], start[1]), start)) 

        came_from = {} # To reconstruct path: maps node to its predecessor
        g_score = {start: 0} # Cost from start to current node
        f_score = {start: heuristic_func(start[0], start[1])} # Estimated total cost from start to goal

        while open_set:
            current_f_score, current_node = heapq.heappop(open_set)
            current_r, current_c = current_node

            # Optimization: If we've already found a shorter path to current_node, skip this one.
            # This can happen if a node was pushed multiple times with different f_scores.
            if current_node in f_score and current_f_score > f_score[current_node]:
                continue

            if current_node == goal:
                # Path to goal found, reconstruct it by tracing back
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                path.append(start) # Add the start node to complete the path
                path.reverse() # Path now goes from start to goal
                return path

            # Explore neighbors
            for dr, dc in MOVES_DELTAS:
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                # Check if the neighbor is within board boundaries
                if not (0 <= neighbor_r < current_height and 0 <= neighbor_c < current_width):
                    continue

                # Check for collision with obstacles
                if neighbor_node in obstacles:
                    continue

                # Calculate the cost to reach this neighbor from the start
                tentative_g_score = g_score[current_node] + 1

                # If this path to neighbor is better than any previous one, or it's a new node
                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic_func(neighbor_r, neighbor_c)
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
                    
        return None # No path found

    head_r, head_c = snake[0]
    head = (head_r, head_c)
    
    # Define possible moves and their deltas for easy lookup
    MOVES = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    REVERSE_MOVES = {
        (-1, 0): "UP",
        (1, 0): "DOWN",
        (0, -1): "LEFT",
        (0, 1): "RIGHT"
    }

    # --- 1. A* Pathfinding to Food ---
    # Obstacles for A* to food: All current snake body segments.
    # If the snake finds food, it will grow, so the tail position does NOT free up.
    a_star_obstacles_to_food = set(snake) 

    def heuristic_to_food(node_r, node_c):
        """Manhattan distance heuristic for A* to food."""
        return abs(node_r - food[0]) + abs(node_c - food[1])

    path_to_food = find_path_astar(head, food, a_star_obstacles_to_food, width, height, heuristic_to_food)

    if path_to_food and len(path_to_food) > 1:
        # If A* found a path to food (and the path is longer than just the head itself),
        # take the first step along that path.
        next_node_r, next_node_c = path_to_food[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]

    # --- 2. Fallback: A* to Tail (Survival Strategy) ---
    # If no path to food, try to chase the tail to stay alive and maximize space.
    # This strategy is only meaningful if the snake has a body (length > 1).
    if len(snake) > 1:
        target_tail = snake[-1]
        # Obstacles for A* to tail: All snake segments EXCEPT the tail itself (which is the target).
        # When moving without eating, the tail position will free up.
        a_star_obstacles_to_tail = set(snake[:-1])
        
        def heuristic_to_tail(node_r, node_c):
            """Manhattan distance heuristic for A* to the snake's tail."""
            return abs(node_r - target_tail[0]) + abs(node_c - target_tail[1])

        path_to_tail = find_path_astar(head, target_tail, a_star_obstacles_to_tail, width, height, heuristic_to_tail)

        if path_to_tail and len(path_to_tail) > 1:
            # If a path to the tail is found, take the first step along it.
            next_node_r, next_node_c = path_to_tail[1]
            delta_r = next_node_r - head_r
            delta_c = next_node_c - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]

    # --- 3. Last Resort: Any Immediately Safe Move ---
    # If no path to food, and no path to tail, the snake is likely in a very tight spot
    # (e.g., very short snake with no valid path to tail, or completely trapped).
    # Take any single safe step to prolong life as much as possible.
    
    # Obstacles for immediate safe move: All snake segments EXCEPT the tail (as it frees up).
    # If snake length is 1, snake[:-1] will be an empty list, and the set will be empty.
    fallback_obstacles_immediate = set(snake[:-1]) 
    
    safe_moves = []
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        is_safe = True
        # Check boundaries
        if not (0 <= next_r < height and 0 <= next_c < width):
            is_safe = False
        # Check collision with snake body (excluding the tail for non-food moves)
        if is_safe and next_pos in fallback_obstacles_immediate:
            is_safe = False
        
        if is_safe:
            safe_moves.append(move_name)

    if safe_moves:
        # If there are multiple safe moves, return the first one found.
        # This provides a deterministic behavior based on the iteration order of MOVES.
        return safe_moves[0]
    else:
        # If no safe move is found, the snake is completely trapped.
        # This will lead to game over. Returning "RIGHT" is an arbitrary default.
        return "RIGHT"