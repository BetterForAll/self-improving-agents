import heapq
import math

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using a strategic AI that prioritizes
    maximizing future traversable empty space and maintaining viable escape routes,
    in addition to reaching food.

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

    def is_valid_coord(r, c):
        return 0 <= r < height and 0 <= c < width

    def heuristic_manhattan(node_r, node_c, target_r, target_c):
        return abs(node_r - target_r) + abs(node_c - target_c)

    def a_star_search(start, goal, obstacles):
        """
        Finds the shortest path length from start to goal avoiding obstacles using A* search.
        Returns path length or math.inf if no path.
        """
        if start == goal:
            return 0 # Path length 0 if already at goal

        # If start or goal is an obstacle, no path.
        if start in obstacles or goal in obstacles:
            return math.inf

        open_set = []
        heapq.heappush(open_set, (0, start)) # (f_score, node)

        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic_manhattan(start[0], start[1], goal[0], goal[1])}

        while open_set:
            current_f, current_node = heapq.heappop(open_set)

            # Optimization: If we've already found a shorter path to current_node, skip this one.
            if current_node in f_score and current_f > f_score[current_node]:
                continue

            if current_node == goal:
                # Reconstruct path length
                path_length = 0
                temp_node = goal
                while temp_node != start:
                    path_length += 1
                    temp_node = came_from[temp_node]
                return path_length

            current_r, current_c = current_node
            for dr, dc in MOVES.values():
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                if not is_valid_coord(neighbor_r, neighbor_c) or neighbor_node in obstacles:
                    continue

                tentative_g_score = g_score[current_node] + 1

                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + heuristic_manhattan(neighbor_r, neighbor_c, goal[0], goal[1])
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        return math.inf # No path found

    def count_reachable_cells(start, obstacles):
        """
        Counts the number of reachable cells from start using BFS, avoiding obstacles.
        """
        if start in obstacles or not is_valid_coord(start[0], start[1]):
            return 0 # If start is an obstacle or invalid, no cells are reachable from it

        q = [start]
        visited = {start}
        count = 0

        while q:
            r, c = q.pop(0)
            count += 1

            for dr, dc in MOVES.values():
                nr, nc = r + dr, c + dc
                neighbor = (nr, nc)

                if is_valid_coord(nr, nc) and neighbor not in obstacles and neighbor not in visited:
                    visited.add(neighbor)
                    q.append(neighbor)
        return count

    def find_path_bfs(start, target, obstacles):
        """
        Finds if a path exists from start to target using BFS, avoiding obstacles.
        Returns True if path exists, False otherwise.
        """
        if start == target:
            return True
        # If start or target is an obstacle, or start is invalid, no path.
        if start in obstacles or target in obstacles or not is_valid_coord(start[0], start[1]):
            return False 

        q = [start]
        visited = {start}

        while q:
            r, c = q.pop(0)

            for dr, dc in MOVES.values():
                nr, nc = r + dr, c + dc
                neighbor = (nr, nc)

                if neighbor == target:
                    return True # Path found to target

                if is_valid_coord(nr, nc) and neighbor not in obstacles and neighbor not in visited:
                    visited.add(neighbor)
                    q.append(neighbor)
        return False

    # Initialize best move and its score
    best_move = None
    best_score = -math.inf # We want to maximize the score

    possible_moves_with_pos = []
    for move_name, (dr, dc) in MOVES.items():
        next_r, next_c = head_r + dr, head_c + dc
        next_pos = (next_r, next_c)
        possible_moves_with_pos.append((move_name, next_pos))

    # Evaluate each possible move
    for move_name, next_pos in possible_moves_with_pos:
        current_score = 0

        # --- Basic collision checks for the proposed move ---
        if not is_valid_coord(next_pos[0], next_pos[1]):
            continue # Out of bounds, this move is impossible

        # Simulate the snake's body *after* this proposed move
        simulated_snake_body_list = []
        if next_pos == food:
            # If we eat, the snake grows. The new head is next_pos, current body shifts.
            simulated_snake_body_list = [next_pos] + snake
        else:
            # If we don't eat, the tail frees up. The new head is next_pos, body shifts, tail removed.
            simulated_snake_body_list = [next_pos] + snake[:-1]
        
        simulated_snake_body_set = set(simulated_snake_body_list)

        # Check for immediate self-collision *with the simulated body*
        # (excluding the head itself, which is next_pos, as it's the target of the move)
        # The body segments start from index 1 of simulated_snake_body_list
        if next_pos in set(simulated_snake_body_list[1:]):
            continue # Collides with the new body, impossible move

        # --- Evaluate the state resulting from this move ---

        # 1. Food Reachability (from next_pos to food)
        # Obstacles for food search: The entire simulated_snake_body
        food_path_length = a_star_search(next_pos, food, simulated_snake_body_set)

        if food_path_length == math.inf:
            # Food becomes unreachable. This is generally a very bad move.
            current_score -= 100000 
        else:
            # Food is reachable. Prioritize eating by giving a bonus based on path length.
            # Shorter path to food is better, but this will be balanced by safety/space.
            current_score += (10000 / (1 + food_path_length)) # Gives a high bonus for reachable food, diminishing with distance
            
            if next_pos == food:
                current_score += 1000000 # Massive bonus for actually eating!

        # 2. Safety / Tail Reachability (from next_pos)
        # Check if the snake can reach its own tail *after* the proposed move, ensuring an escape route.

        true_tail_pos = None
        if next_pos == food:
            # If eating, original tail remains
            true_tail_pos = snake[-1] 
        elif len(snake) > 1:
            # If not eating, old second-to-last becomes new tail
            true_tail_pos = snake[-2] 
        # If len(snake) == 1 and not eating, there's no "tail" to follow, the whole board is effectively open.
        # `true_tail_pos` will remain None, and `can_reach_tail` will implicitly be True.

        can_reach_tail = True
        if true_tail_pos: 
            # Obstacles for tail path: simulated body, *excluding* the true_tail_pos itself as it's the target.
            tail_path_obstacles = simulated_snake_body_set - {true_tail_pos}
            can_reach_tail = find_path_bfs(next_pos, true_tail_pos, tail_path_obstacles)

        if not can_reach_tail:
            # This move leads to entrapment (cannot reach its own tail). Very bad.
            current_score -= 50000
        else:
            current_score += 1000 # Small bonus for being able to reach tail

        # 3. Maximizing Free Space
        # Count reachable cells from next_pos, avoiding the *simulated body*.
        free_cells_count = count_reachable_cells(next_pos, simulated_snake_body_set)
        current_score += free_cells_count * 10 # Scale up free space importance


        # Update best move if current_score is better
        if current_score > best_score:
            best_score = current_score
            best_move = move_name
        # For tie-breaking, the first move with the best score is chosen.

    # --- Fallback Strategy ---
    # If no "good" move was found (all evaluated moves led to extreme penalties
    # such that best_score is still -math.inf, or no moves were valid),
    # revert to a simple "find any immediately safe move" strategy.
    # A score of -50000 or less implies either food is unreachable OR snake is trapped.
    if best_move is None or best_score <= -50000: 
        safe_moves = []
        for move_name, (dr, dc) in MOVES.items():
            next_r, next_c = head_r + dr, head_c + dc
            next_pos = (next_r, next_c)

            is_safe = True
            # Check boundaries
            if not is_valid_coord(next_r, next_c):
                is_safe = False
            # Check collision with snake body (excluding the tail for non-food moves)
            # This is the original fallback logic: only collide with body that won't free up.
            if is_safe and next_pos in set(snake[:-1]):
                is_safe = False
            
            if is_safe:
                safe_moves.append(move_name)

        if safe_moves:
            # In fallback, try to move closer to food if possible, otherwise pick the first safe one.
            best_fallback_move = safe_moves[0]
            min_fallback_dist = heuristic_manhattan(head_r, head_c, food[0], food[1])
            for move in safe_moves:
                dr, dc = MOVES[move]
                temp_pos = (head_r + dr, head_c + dc)
                dist = heuristic_manhattan(temp_pos[0], temp_pos[1], food[0], food[1])
                if dist < min_fallback_dist:
                    min_fallback_dist = dist
                    best_fallback_move = move
            return best_fallback_move
        else:
            # If no safe move is found even with fallback, the snake is completely trapped.
            # Game over. Returning "RIGHT" is a default.
            return "RIGHT" 

    return best_move