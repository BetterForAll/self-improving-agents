import heapq
from collections import deque

def next_move(snake, food, width, height):
    """Pick the next direction for the snake, prioritizing moves that maximize
    future traversable empty space and maintain viable escape routes.

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

    # Helper function to check if a position is within board boundaries
    def is_valid_pos(r, c):
        return 0 <= r < height and 0 <= c < width

    # Generic A* pathfinding function
    # Returns (path_length, path_nodes) or (float('inf'), None) if no path
    def find_path_astar(start, target, obstacles_set):
        if start == target:
            return 0, [start] # Already at target

        # If start or target are initially considered obstacles, path is impossible
        if start in obstacles_set or target in obstacles_set:
            return float('inf'), None

        open_set = []
        heapq.heappush(open_set, (0, start)) # (f_score, node)

        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(start[0] - target[0]) + abs(start[1] - target[1])} # Manhattan heuristic

        while open_set:
            current_f, current_node = heapq.heappop(open_set)

            if current_node == target:
                path = []
                while current_node in came_from:
                    path.append(current_node)
                    current_node = came_from[current_node]
                path.append(start)
                path.reverse()
                return len(path) - 1, path # Return length of path (number of steps) and path nodes

            # Optimization: If we've already found a shorter path to current_node, skip this one.
            if current_node in f_score and current_f > f_score[current_node]:
                continue

            current_r, current_c = current_node
            for dr, dc in MOVES.values():
                neighbor_r, neighbor_c = current_r + dr, current_c + dc
                neighbor_node = (neighbor_r, neighbor_c)

                if not is_valid_pos(neighbor_r, neighbor_c) or neighbor_node in obstacles_set:
                    continue

                tentative_g_score = g_score[current_node] + 1
                if neighbor_node not in g_score or tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = tentative_g_score + (abs(neighbor_r - target[0]) + abs(neighbor_c - target[1]))
                    heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))
        
        return float('inf'), None # No path found

    # BFS to count reachable empty cells (flood fill)
    def count_reachable_cells(start, obstacles_set):
        if start in obstacles_set or not is_valid_pos(start[0], start[1]):
            return 0

        queue = deque([start])
        visited = {start}
        count = 0

        while queue:
            r, c = queue.popleft()
            count += 1

            for dr, dc in MOVES.values():
                nr, nc = r + dr, c + dc
                neighbor_node = (nr, nc)

                if is_valid_pos(nr, nc) and neighbor_node not in obstacles_set and neighbor_node not in visited:
                    visited.add(neighbor_node)
                    queue.append(neighbor_node)
        return count

    # --- Evaluate each possible first move ---
    candidate_moves = {} # Stores evaluated data for each valid initial move

    for move_name, (dr, dc) in MOVES.items():
        next_head_r, next_head_c = head_r + dr, head_c + dc
        next_head = (next_head_r, next_head_c)

        # 1. Basic Collision Check (Wall collision)
        if not is_valid_pos(next_head_r, next_head_c):
            continue

        # Simulate snake state after this move
        simulated_snake_full = [] # The full snake body after the move
        simulated_tail = None     # The position of the new tail

        if next_head == food:
            # Snake eats, grows. Original tail (snake[-1]) remains occupied.
            simulated_snake_full = [next_head] + snake
            simulated_tail = snake[-1] 
        else:
            # Snake moves, doesn't eat. Original tail (snake[-1]) frees up.
            simulated_snake_full = [next_head] + snake[:-1]
            simulated_tail = simulated_snake_full[-1] # The new last segment

        # Immediate self-collision check: Is the next_head hitting a part of the simulated body
        # that would be occupied in the next state and is not the current head itself?
        # This covers hitting a permanent body segment (if eating) or a moving segment (if not eating).
        obstacles_excluding_head = set(simulated_snake_full[1:])
        if next_head in obstacles_excluding_head:
            continue # This move immediately collides with the snake's own body.

        # --- Path to food after this first move ---
        # Obstacles for A* to food: all segments of simulated_snake_full *except* the new head.
        food_path_obstacles = obstacles_excluding_head
        food_path_len, food_path = find_path_astar(next_head, food, food_path_obstacles)

        # --- Path to tail after this first move (safety check) ---
        # Obstacles for A* to tail: all segments of simulated_snake_full *except* the new head AND the new tail (which is the target).
        tail_path_obstacles = set(simulated_snake_full[1:-1])
        
        tail_reachable = False
        # If the snake is just a head (length 1), it can always "reach its tail" (itself)
        if len(simulated_snake_full) == 1:
            tail_reachable = True 
        else:
            tail_path_len, _ = find_path_astar(next_head, simulated_tail, tail_path_obstacles)
            tail_reachable = tail_path_len != float('inf')

        # --- Count free space after this first move ---
        # Obstacles for flood fill: all segments of simulated_snake_full (including the head itself, as it's occupied).
        free_space_obstacles = set(simulated_snake_full)
        free_space = count_reachable_cells(next_head, free_space_obstacles)

        candidate_moves[move_name] = {
            'next_head': next_head,
            'sim_snake_full': simulated_snake_full,
            'food_path_len': food_path_len,
            'food_path': food_path,
            'tail_reachable': tail_reachable,
            'free_space': free_space,
        }

    # --- Decision Making Logic ---

    # 1. Prioritize moves that lead to food AND maintain tail reachability (safety).
    # Among these, prefer the one that leaves the most free space.
    safe_food_moves = []
    for move_name, data in candidate_moves.items():
        if data['food_path_len'] != float('inf') and data['tail_reachable']:
            safe_food_moves.append((move_name, data))
    
    if safe_food_moves:
        # Sort by free_space (maximize), then by food_path_len (minimize)
        safe_food_moves.sort(key=lambda x: (x[1]['free_space'], -x[1]['food_path_len']), reverse=True)
        return safe_food_moves[0][0]

    # 2. If no safe path to food, prioritize moves that are safe (maintain tail reachability)
    # but don't lead directly to food (e.g., waiting for an opening).
    # Among these, prefer the one that leaves the most free space.
    safe_non_food_moves = []
    for move_name, data in candidate_moves.items():
        # This condition implicitly means food_path_len is infinity, as safe_food_moves would have caught it otherwise.
        if data['tail_reachable']: 
            safe_non_food_moves.append((move_name, data))
            
    if safe_non_food_moves:
        safe_non_food_moves.sort(key=lambda x: x[1]['free_space'], reverse=True) # Max free space
        return safe_non_food_moves[0][0]

    # 3. Desperate situation: No move is safe (cannot guarantee tail reachability).
    # Try to find a path to food even if it traps the snake.
    # Among these, prioritize max free space (to delay death) and shortest path to food.
    unsafe_food_moves = []
    for move_name, data in candidate_moves.items():
        if data['food_path_len'] != float('inf'): # Doesn't matter if tail_reachable is False
            unsafe_food_moves.append((move_name, data))
            
    if unsafe_food_moves:
        unsafe_food_moves.sort(key=lambda x: (x[1]['free_space'], -x[1]['food_path_len']), reverse=True) # Max free space, then shortest path to food
        return unsafe_food_moves[0][0]

    # 4. Extremely desperate: No path to food at all, and no move keeps tail reachable.
    # Take *any* move that doesn't immediately crash into a wall or current snake body.
    # Prioritize by max free space to survive as long as possible.
    any_valid_moves = [] # candidate_moves already contains only initially valid moves
    for move_name, data in candidate_moves.items():
        any_valid_moves.append((move_name, data))

    if any_valid_moves:
        any_valid_moves.sort(key=lambda x: x[1]['free_space'], reverse=True) # Max free space
        return any_valid_moves[0][0]
    
    # If absolutely no moves are possible (e.g., fully trapped and all paths lead to immediate death).
    # This scenario should be caught by previous checks, but as a last resort return.
    return "RIGHT" # Default, game is likely over.