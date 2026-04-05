import heapq

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using A* search with enhanced safety and survival strategies.

    The strategy involves:
    1. Finding the shortest path to food using A*.
    2. Crucially, before committing to the food path, it simulates the snake eating the food
       and checks if the snake can then reach its own tail (using A* again). This ensures
       the snake doesn't trap itself after growing.
    3. If no safe path to food is found, it falls back to a survival strategy: finding a path
       to its own tail (which will free up if no food is eaten) to stay alive.
    4. As a last resort, if no path to food or tail is found, it picks an immediately safe
       move that leads to the largest open area, maximizing survival chances.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    head_r, head_c = snake[0]
    food_r, food_c = food

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

    # Helper function for A* pathfinding
    def find_path_astar(start_node, target_node, obstacles, board_width, board_height):
        """
        Finds the shortest path from start_node to target_node avoiding obstacles.
        obstacles: a set of (r, c) tuples that are blocked.
        The target_node itself should not be in obstacles if a path to it is desired.
        """
        def heuristic(node_r, node_c):
            return abs(node_r - target_node[0]) + abs(node_c - target_node[1])

        open_set = []
        heapq.heappush(open_set, (heuristic(start_node[0], start_node[1]), start_node))

        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: heuristic(start_node[0], start_node[1])}

        while open_set:
            current_f_score, current_node = heapq.heappop(open_set)

            if current_node in f_score and current_f_score > f_score[current_node]:
                continue
            
            if current_node == target_node:
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                path.append(start_node)
                return list(reversed(path))

            for dr, dc in MOVES.values():
                neighbor_r, neighbor_c = current_node[0] + dr, current_node[1] + dc
                neighbor_node = (neighbor_r, neighbor_c)

                if not (0 <= neighbor_r < board_height and 0 <= neighbor_c < board_width):
                    continue
                if neighbor_node in obstacles:
                    continue

                tentative_g_score = g_score[current_node] + 1

                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic(neighbor_r, neighbor_c)
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        return None

    # Helper function to count reachable cells using BFS
    def count_reachable_cells(start_node, forbidden_nodes, board_width, board_height):
        """
        Counts the number of cells reachable from start_node, avoiding forbidden_nodes.
        """
        q = [start_node]
        visited = {start_node}
        count = 0

        while q:
            current_node = q.pop(0)
            count += 1

            for dr, dc in MOVES.values():
                neighbor_r, neighbor_c = current_node[0] + dr, current_node[1] + dc
                neighbor_node = (neighbor_r, neighbor_c)

                if not (0 <= neighbor_r < board_height and 0 <= neighbor_c < board_width):
                    continue
                if neighbor_node in forbidden_nodes:
                    continue
                if neighbor_node in visited:
                    continue
                
                visited.add(neighbor_node)
                q.append(neighbor_node)
        return count

    # --- Step 1: Find a safe path to food ---

    # Obstacles for A* to food: All current snake body segments.
    # If the snake finds food, it will grow, so the tail position does NOT free up.
    obstacles_to_food = set(snake)
    path_to_food = find_path_astar(snake[0], food, obstacles_to_food, width, height)

    if path_to_food and len(path_to_food) > 1:
        # Simulate the snake's state after taking *all* steps of `path_to_food` and eating.
        simulated_snake_after_eating = list(snake) # Start with current snake
        for i in range(1, len(path_to_food)):
            next_step_on_path = path_to_food[i]
            simulated_snake_after_eating.insert(0, next_step_on_path) # New head
            
            # If we are at the food (the last step on the path), the snake grows.
            # Otherwise (intermediate step), the tail moves, so pop the old tail.
            if next_step_on_path != food:
                simulated_snake_after_eating.pop()
        
        new_head_after_eating = simulated_snake_after_eating[0] # Should be 'food'
        new_tail_after_eating = simulated_snake_after_eating[-1]
        
        # Obstacles for "food to tail" path: All segments of `simulated_snake_after_eating`
        # EXCEPT the new tail (which is the target).
        obstacles_for_tail_path_after_eating = set(simulated_snake_after_eating[:-1]) if len(simulated_snake_after_eating) > 1 else set()
        
        # Check if the snake can reach its new tail from the food position.
        # This confirms it won't get trapped after eating.
        path_food_to_tail = find_path_astar(new_head_after_eating, new_tail_after_eating, 
                                            obstacles_for_tail_path_after_eating, width, height)
        
        if path_food_to_tail:
            # A safe path to food was found. Take the first step towards food.
            next_node_r, next_node_c = path_to_food[1]
            delta_r = next_node_r - head_r
            delta_c = next_node_c - head_c
            return REVERSE_MOVES[(delta_r, delta_c)]

    # --- Step 2: Fallback to Survival (find path to own tail) ---

    # If no safe path to food, try to survive by moving towards the current tail.
    # The tail position will free up if the snake doesn't eat.
    if len(snake) == 1:
        tail_pos = snake[0] # Head and tail are the same
        obstacles_to_tail = set() # No body obstacles for a single-segment snake
    else:
        tail_pos = snake[-1]
        obstacles_to_tail = set(snake[:-1]) # All body parts except the current tail

    path_to_tail = find_path_astar(snake[0], tail_pos, obstacles_to_tail, width, height)

    if path_to_tail and len(path_to_tail) > 1:
        # Found a path to the tail (survival path). Take the first step.
        next_node_r, next_node_c = path_to_tail[1]
        delta_r = next_node_r - head_r
        delta_c = next_node_c - head_c
        return REVERSE_MOVES[(delta_r, delta_c)]
    else:
        # --- Step 3: Last Resort (find any safe move that maximizes open space) ---

        # If no safe path to food and no path to its own tail, the snake is in a tight spot.
        # Find any immediately safe move and choose the one that offers the most open space.
        
        potential_moves_info = [] # Stores (move_name, next_pos) for safe moves
        
        for move_name, (dr, dc) in MOVES.items():
            next_r, next_c = head_r + dr, head_c + dc
            next_pos = (next_r, next_c)

            # Check boundaries
            if not (0 <= next_r < height and 0 <= next_c < width):
                continue

            # Check collision with snake body. The current tail frees up, so it's not an obstacle.
            if next_pos in set(snake[:-1]): 
                continue

            potential_moves_info.append((move_name, next_pos))

        if potential_moves_info:
            best_move = None
            max_reachable_cells = -1

            for move_name, next_pos in potential_moves_info:
                # Simulate snake taking this move (without eating).
                # New head is `next_pos`, new tail is `snake[-2]` (if snake length > 1).
                simulated_snake_onestep = list(snake)
                simulated_snake_onestep.insert(0, next_pos)
                simulated_snake_onestep.pop() # Tail frees up because no food eaten
                
                # Obstacles for BFS from `next_pos`: all segments of `simulated_snake_onestep` except its tail.
                bfs_obstacles = set(simulated_snake_onestep[:-1]) if len(simulated_snake_onestep) > 1 else set()
                
                # Count reachable cells from `next_pos` in the simulated state.
                reachable_count = count_reachable_cells(next_pos, bfs_obstacles, width, height)
                
                if reachable_count > max_reachable_cells:
                    max_reachable_cells = reachable_count
                    best_move = move_name
            
            if best_move:
                return best_move
            
        # If absolutely no safe immediate move is found (e.g., completely surrounded).
        # This scenario should be rare if previous strategies are robust.
        # As a last resort, just pick a default direction, which will likely result in a collision.
        return "RIGHT"