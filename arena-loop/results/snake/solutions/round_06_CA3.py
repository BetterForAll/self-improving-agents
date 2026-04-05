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
    food_r, food_c = food

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

    # Helper A* Pathfinding function
    def find_path_astar(start_node, target_node, obstacles):
        """
        Finds the shortest path from start_node to target_node using A* search.
        
        Args:
            start_node: (row, col) tuple, the starting point.
            target_node: (row, col) tuple, the goal point.
            obstacles: set of (row, col) tuples, positions that cannot be entered.
            
        Returns:
            A list of (row, col) tuples representing the path from start_node to target_node (inclusive),
            or None if no path is found.
        """
        start_r, start_c = start_node
        target_r, target_c = target_node

        def heuristic(node_r, node_c):
            """Manhattan distance heuristic for A*."""
            return abs(node_r - target_r) + abs(node_c - target_c)

        # open_set is a priority queue of (f_score, (row, col)) tuples
        open_set = []
        heapq.heappush(open_set, (heuristic(start_r, start_c), start_node))

        # came_from maps (row, col) to its predecessor (row, col) in the cheapest path found so far
        came_from = {}

        # g_score is the cost from the start node to the current node
        g_score = {start_node: 0}

        # f_score = g_score + h_score (estimated total cost)
        f_score = {start_node: heuristic(start_r, start_c)}

        while open_set:
            current_f_score, current_node = heapq.heappop(open_set)
            current_r, current_c = current_node

            # Optimization: If we've already found a shorter path to current_node, skip this one.
            # This can happen if a node was pushed multiple times with different f_scores.
            if current_node in f_score and current_f_score > f_score[current_node]:
                continue

            if current_node == target_node:
                # Path found, reconstruct it by tracing back from the target to the start
                path = []
                node = target_node
                while node != start_node:
                    path.append(node)
                    node = came_from[node]
                path.append(start_node) # Add the start node to complete the path
                path.reverse() # Path now goes from start to target
                return path

            # Explore neighbors
            for dr, dc in MOVES.values():
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                # Check if the neighbor is within board boundaries
                if not (0 <= neighbor_r < height and 0 <= neighbor_c < width):
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
                    f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_r, neighbor_c)
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        
        return None # No path found

    # --- Decision Making Strategy ---

    # 1. Primary Goal: Find a path to food
    # Obstacles: All current snake body segments.
    # If the snake finds food, it will grow, so the tail position does NOT free up.
    a_star_obstacles_food = set(snake) 
    path_to_food = find_path_astar((head_r, head_c), food, a_star_obstacles_food)

    if path_to_food and len(path_to_food) > 1:
        # If A* found a valid path to food (and the path is longer than just the head itself),
        # take the first step along that path.
        next_node_r, next_node_c = path_to_food[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]
    
    # 2. Fallback: If no path to food, try to find a path to the tail
    # This strategy helps the snake avoid trapping itself when food is unreachable,
    # by constantly moving towards the space that will become free.
    # If the snake doesn't eat, its tail position WILL free up.
    # Special handling for snake of length 1: in this case, tail is head,
    # and we don't need to path to ourselves. The "last resort" handles this naturally.
    if len(snake) > 1:
        tail_pos = snake[-1]
        # Obstacles: All snake segments EXCEPT the tail itself.
        a_star_obstacles_tail = set(snake[:-1]) 
        path_to_tail = find_path_astar((head_r, head_c), tail_pos, a_star_obstacles_tail)

        if path_to_tail and len(path_to_tail) > 1:
            # A valid path to the tail was found. Take the first step.
            next_node_r, next_node_c = path_to_tail[1]
            delta_r = next_node_r - head_r
            delta_c = next_node_c - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]

    # 3. Last Resort: If neither a path to food nor a path to tail is found,
    # find any immediately safe move to survive one more turn.
    # This covers cases where the snake is almost fully trapped or is a single segment.
    
    # Obstacles for this last resort are the same as for path to tail:
    # all body parts except the current tail (which will free up).
    # If snake length is 1, snake[:-1] is empty, which correctly means no body parts to collide with.
    fallback_obstacles = set(snake[:-1]) 
    safe_moves_list = []
    
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        is_safe = True
        # Check boundaries
        if not (0 <= next_r < height and 0 <= next_c < width):
            is_safe = False
        # Check collision with snake body (excluding the tail if len > 1, or empty set if len == 1)
        if is_safe and next_pos in fallback_obstacles:
            is_safe = False
        
        if is_safe:
            safe_moves_list.append(move_name)

    if safe_moves_list:
        # If multiple safe moves are available, simply pick the first one found.
        # A more advanced bot might try to evaluate which safe move maximizes future options
        # (e.g., by checking how much open space it leads to with a BFS/flood fill).
        return safe_moves_list[0]
    else:
        # The snake is completely trapped and cannot make any safe move.
        # This move will result in immediate collision/game over.
        # Returning "RIGHT" (or any default) is arbitrary here as the game is effectively lost.
        return "RIGHT"