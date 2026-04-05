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

    def heuristic(node_r, node_c, target_r, target_c):
        """Manhattan distance heuristic for A*."""
        return abs(node_r - target_r) + abs(node_c - target_c)

    def find_path(start, target, obstacles, target_is_tail=False):
        """
        A* search algorithm.
        Returns a list of (row, col) nodes representing the path from start to target (inclusive),
        or None if no path is found.
        
        Args:
            start: (row, col) tuple, the starting node.
            target: (row, col) tuple, the target node.
            obstacles: set of (row, col) tuples that are blocked.
            target_is_tail: bool, if True, the 'target' position itself is NOT considered
                            an obstacle, even if it's in the obstacles set (e.g., when
                            chasing the snake's tail, as the tail will move and free that space).
        """
        
        start_r, start_c = start
        target_r, target_c = target

        # open_set is a priority queue of (f_score, (row, col)) tuples
        open_set = []
        heapq.heappush(open_set, (heuristic(start_r, start_c, target_r, target_c), start))

        # came_from maps (row, col) to its predecessor (row, col) in the cheapest path found so far
        came_from = {}

        # g_score is the cost from the start node to the current node
        g_score = {start: 0}

        # f_score = g_score + h_score (estimated total cost)
        f_score = {start: heuristic(start_r, start_c, target_r, target_c)}

        while open_set:
            current_f_score, current_node = heapq.heappop(open_set)
            current_r, current_c = current_node

            # If we've already found a shorter path to current_node, skip this one.
            # This can happen if a node was pushed multiple times with different f_scores.
            if current_node in f_score and current_f_score > f_score[current_node]:
                continue
            
            # Target reached
            if current_node == target:
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                path.append(start) # Add the start node to complete the path
                path.reverse() # Path now goes from start to target
                return path

            # Explore neighbors
            for _, (dr, dc) in MOVES.items(): # Iterating MOVES is fine, order doesn't matter for A* correctness
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                # Check if the neighbor is within board boundaries
                if not (0 <= neighbor_r < height and 0 <= neighbor_c < width):
                    continue

                # Check for collision with obstacles.
                # If target_is_tail is True, the target itself is not an obstacle.
                is_obstacle = neighbor_node in obstacles
                if is_obstacle and not (target_is_tail and neighbor_node == target):
                    continue

                # Calculate the cost to reach this neighbor from the start
                tentative_g_score = g_score[current_node] + 1

                # If this path to neighbor is better than any previous one, or it's a new node
                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_r, neighbor_c, target_r, target_c)
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        return None # No path found

    # --- Strategy 1: Try to reach food safely ---
    
    # Obstacles for A* to food: All current snake body segments.
    # If the snake finds food, it will grow, so all body segments are considered obstacles.
    # The tail position does NOT free up when eating.
    obstacles_to_food = set(snake)
    path_to_food = find_path(snake[0], food, obstacles_to_food)

    if path_to_food and len(path_to_food) > 1:
        # We found a path to food. Now, check if taking this path is safe *after eating*.
        # Safety means the snake won't immediately trap itself after growing.
        
        next_pos_towards_food = path_to_food[1] # The immediate next step to take towards food
        
        # Simulate the snake's state after taking `next_pos_towards_food` and eating food.
        # The snake grows, so its length increases by 1.
        # new_snake = [next_pos, original_head, original_body1, ..., original_tail]
        simulated_snake_after_eating = [next_pos_towards_food] + list(snake)
        
        simulated_head = simulated_snake_after_eating[0]
        simulated_tail = simulated_snake_after_eating[-1] # The original tail segment is now the new tail.

        # To check safety, we need to ensure the simulated snake can still reach its new tail (or any open space).
        # We use pathfinding from the simulated head to the simulated tail.
        # Obstacles for this check: All segments of the *simulated* snake body, EXCEPT its *new* tail.
        # The 'new tail' (simulated_tail) is a valid target cell for pathfinding because it will move out.
        obstacles_for_tail_chase_after_eating = set(simulated_snake_after_eating[:-1]) # All but the last segment

        path_to_tail_after_eating = find_path(simulated_head, 
                                              simulated_tail, 
                                              obstacles_for_tail_chase_after_eating, 
                                              target_is_tail=True)
        
        if path_to_tail_after_eating:
            # If a path to food exists AND it guarantees the snake won't be trapped immediately after eating, take it.
            delta_r = next_pos_towards_food[0] - head_r
            delta_c = next_pos_towards_food[1] - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]

    # --- Strategy 2: Fallback: No safe path to food, try to survive by chasing tail ---
    
    # If no path to food was found, or the path found was deemed unsafe (would lead to self-entrapment),
    # the snake must prioritize survival. The best survival strategy is often to find a path to its own tail.
    # This ensures the snake always has a valid exit and avoids trapping itself.

    # Obstacles for survival moves: All snake segments EXCEPT the tail.
    # If the snake does not eat, its tail position will free up in the next move.
    obstacles_for_survival = set(snake[:-1])
    
    best_move = None
    best_path_length_to_tail = -1 # We want the longest path to the tail for more room

    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)

        # Check immediate safety of this potential move: boundaries and immediate body collision.
        if not (0 <= next_r < height and 0 <= next_c < width):
            continue
        if next_pos in obstacles_for_survival: # Cannot hit its own body (excluding tail)
            continue
        
        # This move is immediately safe. Now, evaluate its long-term safety by simulating
        # the snake's state and checking if it can reach its new tail.
        
        # Simulate snake state after taking this move (without eating).
        # new_snake = [next_pos, original_head, ..., original_body_k-1] (original_tail `snake[-1]` is freed)
        simulated_snake_for_survival = [next_pos] + list(snake[:-1])

        simulated_head_for_survival = simulated_snake_for_survival[0]
        # The target tail for survival is the position of the *original* tail, which will be freed.
        simulated_tail_for_survival = snake[-1] 
        
        # Obstacles for this tail chase: All segments of the *simulated* snake body, EXCEPT its new tail.
        # This is `simulated_snake_for_survival[:-1]`.
        obstacles_for_simulated_tail_chase = set(simulated_snake_for_survival[:-1])
        
        path_to_tail = find_path(simulated_head_for_survival, 
                                 simulated_tail_for_survival,
                                 obstacles_for_simulated_tail_chase,
                                 target_is_tail=True)
        
        if path_to_tail:
            # If a path to the tail exists, this is a good survival move.
            # Prioritize moves that lead to a longer path to the tail (more room to maneuver).
            current_path_length = len(path_to_tail)
            if current_path_length > best_path_length_to_tail:
                best_path_length_to_tail = current_path_length
                best_move = move_name
        
    if best_move:
        return best_move
    else:
        # --- Strategy 3: Desperate Fallback: No safe path to tail, take any immediately safe move ---
        # This means the snake is likely trapped or has very little space, and cannot reach its tail.
        # This is a last resort to extend the game, even if it leads to a dead-end eventually.
        
        immediately_safe_moves = []
        for move_name, (dr, dc) in MOVES.items():
            next_r, next_c = head_r + dr, head_c + dc
            next_pos = (next_r, next_c)

            is_safe = True
            if not (0 <= next_r < height and 0 <= next_c < width):
                is_safe = False
            if is_safe and next_pos in obstacles_for_survival:
                is_safe = False
            
            if is_safe:
                immediately_safe_moves.append(move_name)
        
        if immediately_safe_moves:
            # If multiple, just pick the first one found (deterministic).
            return immediately_safe_moves[0]
        else:
            # Completely trapped, no safe move at all. Game over.
            # Return "RIGHT" as a default, but this implies immediate game termination.
            return "RIGHT"