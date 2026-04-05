import heapq

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using A* search to reliably locate food and predict potential self-collisions.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    head_r, head_c = snake[0]

    # Define possible moves and their deltas
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

    # Helper function for A* search
    def a_star_search(start_node, target_node, obstacles):
        """
        Performs an A* search from start_node to target_node.
        Args:
            start_node: (row, col)
            target_node: (row, col)
            obstacles: set of (row, col) nodes that are blocked.
        Returns:
            list of (row, col) tuples representing the path, or None if no path found.
        """
        
        target_r, target_c = target_node

        def heuristic(node_r, node_c):
            """Manhattan distance heuristic."""
            return abs(node_r - target_r) + abs(node_c - target_c)

        open_set = []
        heapq.heappush(open_set, (heuristic(start_node[0], start_node[1]), start_node))

        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: heuristic(start_node[0], start_node[1])}

        while open_set:
            current_f, current_node = heapq.heappop(open_set)
            current_r, current_c = current_node

            # Optimization: If we've already found a shorter path to current_node, skip this one.
            # This can happen if a node was pushed multiple times with different f_scores.
            if current_node in f_score and current_f > f_score[current_node]:
                continue

            if current_node == target_node:
                # Path to target found, reconstruct it by tracing back
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                path.append(start_node) # Add the start node to complete the path
                path.reverse() # Path now goes from start to target
                return path

            # Explore neighbors
            for _, (dr, dc) in MOVES.items():
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                # Check if the neighbor is within board boundaries
                if not (0 <= neighbor_r < height and 0 <= neighbor_c < width):
                    continue

                # Check for collision with obstacles
                if neighbor_node in obstacles:
                    continue

                # Calculate the cost to reach this neighbor from the start
                tentative_g_score = g_score.get(current_node, float('inf')) + 1

                # If this path to neighbor is better than any previous one, or it's a new node
                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_r, neighbor_c)
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        return None

    # --- 1. Primary Goal: A* Pathfinding to Food ---
    # Obstacles for A* to food: All current snake body segments.
    # If the snake eats food, it grows, so its current tail position does NOT free up.
    # Thus, the entire current snake body (including tail) is an obstacle.
    food_obstacles = set(snake) 
    path_to_food = a_star_search(snake[0], food, food_obstacles)

    if path_to_food and len(path_to_food) > 1: # path_to_food length 1 means head is already on food
        # If A* found a path to food, take the first step along that path.
        next_node_r, next_node_c = path_to_food[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]
    else:
        # --- 2. Secondary Goal: A* Pathfinding to Tail for Survival ---
        # If no path to food was found (or if food is on the head),
        # try to find a path to the tail to stay alive in open space.
        # Obstacles for A* to tail: All snake segments EXCEPT the tail.
        # If the snake doesn't eat, its tail position WILL free up in the next move.
        tail_obstacles = set(snake[:-1]) if len(snake) > 1 else set()
        
        # We target the current tail position. If the snake has only one segment,
        # its 'tail' is its head. In this case, path_to_tail will likely be a path
        # of length 1 (start_node == target_node), leading to the next fallback.
        path_to_tail = a_star_search(snake[0], snake[-1], tail_obstacles)

        # We only want to move if the path is actually "somewhere else" (longer than just the head).
        if path_to_tail and len(path_to_tail) > 1:
            # Found a path to the tail, take the first step.
            next_node_r, next_node_c = path_to_tail[1]
            delta_r = next_node_r - head_r
            delta_c = next_node_c - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]
        else:
            # --- 3. Tertiary Goal: Find Any Immediately Safe Move ---
            # If no path to food AND no path to tail was found (e.g., completely trapped,
            # or snake is length 1 with no food and no meaningful path to 'tail' i.e. itself).
            # Fallback to finding any immediately safe move to stay alive one more turn.
            
            # Obstacles for immediate safe moves: All snake segments EXCEPT the tail.
            # (This is the same set as `tail_obstacles`.)
            fallback_obstacles = set(snake[:-1]) 
            
            safe_moves = []
            for move_name, (dr, dc) in MOVES.items():
                next_r, next_c = head_r + dr, head_c + dc
                next_pos = (next_r, next_c)

                is_safe = True
                # Check boundaries
                if not (0 <= next_r < height and 0 <= next_c < width):
                    is_safe = False
                # Check collision with snake body (excluding the tail, as it will move)
                if is_safe and next_pos in fallback_obstacles:
                    is_safe = False
                
                if is_safe:
                    safe_moves.append(move_name)

            if safe_moves:
                # If there are multiple safe moves, return the first one found.
                # This provides a deterministic behavior based on the iteration order of MOVES.
                return safe_moves[0]
            else:
                # If no safe move is found, the snake is completely trapped.
                # The game should effectively be over. Returning "RIGHT" here is a default.
                return "RIGHT"