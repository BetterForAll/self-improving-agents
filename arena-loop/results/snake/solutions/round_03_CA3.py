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

    # --- A* Pathfinding to Food (Primary Goal) ---
    
    # Obstacles for A* to food: All current snake body segments.
    # If the snake finds food, it will grow, so the tail position does NOT free up.
    # Therefore, any part of the current snake body is considered an obstacle.
    a_star_obstacles_for_food = set(snake) 

    def heuristic_to_food(node_r, node_c):
        """Manhattan distance heuristic for A* to food."""
        return abs(node_r - food_r) + abs(node_c - food_c)

    # open_set is a priority queue of (f_score, (row, col)) tuples
    open_set_food = []
    heapq.heappush(open_set_food, (heuristic_to_food(head_r, head_c), (head_r, head_c)))

    # came_from maps (row, col) to its predecessor (row, col) in the cheapest path found so far
    came_from_food = {}

    # g_score is the cost from the start node (snake's head) to the current node
    g_score_food = {(head_r, head_c): 0}

    # f_score = g_score + h_score (estimated total cost)
    f_score_food = {(head_r, head_c): heuristic_to_food(head_r, head_c)}

    path_to_food = None

    while open_set_food:
        current_f_score, current_node = heapq.heappop(open_set_food)
        current_r, current_c = current_node

        # Optimization: If we've already found a shorter path to current_node, skip this one.
        if current_node in f_score_food and current_f_score > f_score_food[current_node]:
            continue

        if current_node == food:
            # Path to food found, reconstruct it by tracing back from the food to the head
            path_to_food = []
            while current_node in came_from_food:
                path_to_food.append(current_node)
                current_node = came_from_food[current_node]
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

            # Check for collision with snake's body (using a_star_obstacles_for_food set)
            if neighbor_node in a_star_obstacles_for_food:
                continue

            # Calculate the cost to reach this neighbor from the start
            tentative_g_score = g_score_food[current_node] + 1

            # If this path to neighbor is better than any previous one, or it's a new node
            if neighbor_node not in g_score_food or tentative_g_score < g_score_food[neighbor_node]:
                came_from_food[neighbor_node] = current_node
                g_score_food[neighbor_node] = tentative_g_score
                f_score_food[neighbor_node] = tentative_g_score + heuristic_to_food(neighbor_r, neighbor_c)
                heapq.heappush(open_set_food, (f_score_food[neighbor_node], neighbor_node))

    # --- Decision Making ---

    if path_to_food and len(path_to_food) > 1:
        # If A* found a valid path to food (more than just the head itself),
        # take the first step along that path.
        next_node_r, next_node_c = path_to_food[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]
    else:
        # --- Fallback Strategy: Food is unreachable or already on head's cell.
        # Try to find a path to the snake's tail to survive longer.
        tail_r, tail_c = snake[-1]

        # Obstacles for A* to tail: All snake segments EXCEPT the tail.
        # If the snake doesn't eat, its tail position will free up.
        a_star_obstacles_for_tail = set(snake[:-1]) 
        # Note: If snake length is 1, snake[:-1] is an empty list, so set() is correct.
        
        def heuristic_to_tail(node_r, node_c):
            """Manhattan distance heuristic for A* to the snake's tail."""
            return abs(node_r - tail_r) + abs(node_c - tail_c)

        # Reinitialize A* data structures for tail search
        open_set_tail = []
        heapq.heappush(open_set_tail, (heuristic_to_tail(head_r, head_c), (head_r, head_c)))
        came_from_tail = {}
        g_score_tail = {(head_r, head_c): 0}
        f_score_tail = {(head_r, head_c): heuristic_to_tail(head_r, head_c)}

        path_to_tail = None

        while open_set_tail:
            current_f_score, current_node = heapq.heappop(open_set_tail)
            current_r, current_c = current_node

            if current_node in f_score_tail and current_f_score > f_score_tail[current_node]:
                continue

            if current_node == (tail_r, tail_c):
                # Path to tail found, reconstruct it.
                path_to_tail = []
                while current_node in came_from_tail:
                    path_to_tail.append(current_node)
                    current_node = came_from_tail[current_node]
                path_to_tail.append((head_r, head_c)) 
                path_to_tail.reverse()
                break

            for move_name, (dr, dc) in MOVES.items():
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                if not (0 <= neighbor_r < height and 0 <= neighbor_c < width):
                    continue

                if neighbor_node in a_star_obstacles_for_tail:
                    continue

                tentative_g_score = g_score_tail[current_node] + 1
                if neighbor_node not in g_score_tail or tentative_g_score < g_score_tail[neighbor_node]:
                    came_from_tail[neighbor_node] = current_node
                    g_score_tail[neighbor_node] = tentative_g_score
                    f_score_tail[neighbor_node] = tentative_g_score + heuristic_to_tail(neighbor_r, neighbor_c)
                    heapq.heappush(open_set_tail, (f_score_tail[neighbor_node], neighbor_node))

        if path_to_tail and len(path_to_tail) > 1:
            # Found a path to the tail, take the first step along this path to survive.
            next_node_r, next_node_c = path_to_tail[1]
            delta_r = next_node_r - head_r
            delta_c = next_node_c - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]
        else:
            # --- Last Resort Fallback: No path to food AND no path to tail found.
            # This means the snake is likely highly constrained or trapped.
            # Find any immediately safe move to avoid immediate collision.
            
            # Obstacles for this last resort: All snake segments EXCEPT the tail.
            # This is the same set as `a_star_obstacles_for_tail`.
            last_resort_obstacles = set(snake[:-1]) 
            
            safe_moves = []
            for move_name, (dr, dc) in MOVES.items():
                next_r, next_c = head_r + dr, head_c + dc
                next_pos = (next_r, next_c)

                is_safe = True
                # Check boundaries
                if not (0 <= next_r < height and 0 <= next_c < width):
                    is_safe = False
                # Check collision with snake body (excluding the tail for non-food moves)
                if is_safe and next_pos in last_resort_obstacles:
                    is_safe = False
                
                if is_safe:
                    safe_moves.append(move_name) 

            if safe_moves:
                # If there are multiple safe moves, return the first one found.
                # In highly constrained scenarios, any safe move is better than none.
                return safe_moves[0]
            else:
                # If no safe move is found, the snake is completely trapped.
                # Returning "RIGHT" will likely result in immediate collision/game over.
                return "RIGHT"