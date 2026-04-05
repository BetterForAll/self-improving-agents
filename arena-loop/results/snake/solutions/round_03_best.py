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

    # --- A* Pathfinding to Food ---
    
    # Obstacles for A* to food: All current snake body segments.
    # If the snake finds food, it will grow, so the tail position does NOT free up.
    # Therefore, any part of the current snake body is considered an obstacle.
    a_star_obstacles = set(snake) 

    def heuristic(node_r, node_c):
        """Manhattan distance heuristic for A*."""
        return abs(node_r - food_r) + abs(node_c - food_c)

    # open_set is a priority queue of (f_score, (row, col)) tuples
    open_set = []
    heapq.heappush(open_set, (heuristic(head_r, head_c), (head_r, head_c)))

    # came_from maps (row, col) to its predecessor (row, col) in the cheapest path found so far
    came_from = {}

    # g_score is the cost from the start node (snake's head) to the current node
    g_score = {(head_r, head_c): 0}

    # f_score = g_score + h_score (estimated total cost)
    f_score = {(head_r, head_c): heuristic(head_r, head_c)}

    path_to_food = None

    while open_set:
        current_f_score, current_node = heapq.heappop(open_set)
        current_r, current_c = current_node

        # Optimization: If we've already found a shorter path to current_node, skip this one.
        # This can happen if a node was pushed multiple times with different f_scores.
        if current_node in f_score and current_f_score > f_score[current_node]:
            continue

        if current_node == food:
            # Path to food found, reconstruct it by tracing back from the food to the head
            path_to_food = []
            while current_node in came_from:
                path_to_food.append(current_node)
                current_node = came_from[current_node]
            path_to_food.append((head_r, head_c)) # Add the head to complete the path
            path_to_food.reverse() # Path now goes from head to food
            break # Exit the A* loop as a path has been found

        # Explore neighbors
        for move_name, (dr, dc) in MOVES.items():
            neighbor_r, neighbor_c = current_r + dr, current_c + dc
            neighbor_node = (neighbor_r, neighbor_c)

            # Check if the neighbor is within board boundaries
            if not (0 <= neighbor_r < height and 0 <= neighbor_c < width):
                continue

            # Check for collision with snake's body (using a_star_obstacles set)
            if neighbor_node in a_star_obstacles:
                continue

            # Calculate the cost to reach this neighbor from the start
            tentative_g_score = g_score[current_node] + 1

            # If this path to neighbor is better than any previous one, or it's a new node
            if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                came_from[neighbor_node] = current_node
                g_score[neighbor_node] = tentative_g_score
                f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_r, neighbor_c)
                heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))

    # --- Decision Making ---

    if path_to_food and len(path_to_food) > 1:
        # If A* found a path to food (and the path is longer than just the head itself),
        # take the first step along that path.
        next_node_r, next_node_c = path_to_food[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]
    else:
        # If no path to food was found (e.g., snake is trapped, or food is unreachable),
        # or if food is exactly on the head (path_to_food length 1),
        # use a fallback strategy: find any immediately safe move to stay alive.
        
        # Obstacles for fallback: All snake segments EXCEPT the tail.
        # If the snake doesn't eat, its tail position will free up in the next move.
        # If the snake has only a head, this set will be empty.
        fallback_obstacles = set(snake[:-1]) 
        
        safe_moves = []
        for move_name, (dr, dc) in MOVES.items():
            next_r, next_c = head_r + dr, head_c + dc
            next_pos = (next_r, next_c)

            is_safe = True
            # Check boundaries
            if not (0 <= next_r < height and 0 <= next_c < width):
                is_safe = False
            # Check collision with snake body (excluding the tail for non-food moves)
            if is_safe and next_pos in fallback_obstacles:
                is_safe = False
            
            if is_safe:
                safe_moves.append(move_name) # Store the direction string if it's safe

        if safe_moves:
            # If there are multiple safe moves, return the first one found.
            # This provides a deterministic behavior based on the iteration order of MOVES.
            # More advanced survival strategies could involve finding the longest safe path
            # or a path that leads towards the snake's tail.
            return safe_moves[0]
        else:
            # If no safe move is found, the snake is completely trapped,
            # and the game should effectively be over. Returning "RIGHT" here is a default,
            # but in a real game, this would typically lead to immediate termination.
            return "RIGHT"