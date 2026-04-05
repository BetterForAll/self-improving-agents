import collections

def next_move(snake, food, width, height):
    """Pick the next direction for the snake using a smarter strategy.

    The strategy prioritizes moves that:
    1. Lead to the food via the shortest path, *and* ensure the snake can
       reach its new tail position after eating (to avoid self-trapping),
       while also maximizing the free space available after eating.
    2. If food is not safely reachable, lead to a move that maximizes
       the overall free movement space, effectively preventing self-trapping.
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
    def is_safe(pos, obstacles_set, board_width, board_height):
        """Checks if a position is within board bounds and not an obstacle.
        Args:
            pos (tuple): (row, col) position to check.
            obstacles_set (set): A set of (row, col) tuples representing obstacles.
        """
        row, col = pos
        # 1. Check for wall collision
        if not (0 <= row < board_height and 0 <= col < board_width):
            return False
        # 2. Check for collision with obstacles (snake body segments)
        if pos in obstacles_set:
            return False
        return True

    # --- Helper function for BFS pathfinding ---
    def find_path_bfs(start_pos, target_pos, obstacles_list_or_set, board_width, board_height):
        """
        Finds the shortest path from start_pos to target_pos using BFS,
        avoiding positions in obstacles_list_or_set.
        
        Args:
            start_pos (tuple): (row, col) starting point.
            target_pos (tuple): (row, col) target point.
            obstacles_list_or_set: The list or set of (row, col) tuples representing 
                                   the snake's body to avoid.
            board_width (int): Board width.
            board_height (int): Board height.
            
        Returns:
            list: A list of (row, col) tuples representing the path, including start and target,
                  or None if no path is found.
        """
        queue = collections.deque([(start_pos, [start_pos])])
        visited = {start_pos}

        # Convert obstacles to a set if not already one, for efficient lookup.
        # The target position itself should not be considered an obstacle for pathfinding to it.
        bfs_obstacles_set = set(obstacles_list_or_set) - {target_pos}

        while queue:
            current_node, path = queue.popleft()

            if current_node == target_pos:
                return path

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # UP, DOWN, LEFT, RIGHT
                neighbor_pos = (current_node[0] + dr, current_node[1] + dc)

                if is_safe(neighbor_pos, bfs_obstacles_set, board_width, board_height) and neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    queue.append((neighbor_pos, path + [neighbor_pos]))
        return None # No path found

    # --- Helper function for counting reachable cells (flood fill) ---
    def count_reachable_cells(start_pos, obstacles_set, board_width, board_height):
        """
        Counts the number of reachable cells from start_pos, avoiding specified obstacles.
        Uses BFS (flood fill) to determine the size of the largest connected free area.
        """
        # The starting position must itself be safe to begin counting.
        if not is_safe(start_pos, obstacles_set, board_width, board_height):
            return 0

        queue = collections.deque([start_pos])
        visited = {start_pos}
        reachable_count = 0

        while queue:
            current_node = queue.popleft()
            reachable_count += 1 # Count current cell as reachable

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor_pos = (current_node[0] + dr, current_node[1] + dc)

                if is_safe(neighbor_pos, obstacles_set, board_width, board_height) and neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    queue.append(neighbor_pos)
        return reachable_count

    # --- Step 1: Filter out immediately unsafe moves ---
    # A move is immediately unsafe if it hits a wall or the snake's body.
    # The snake's tail (snake[-1]) will move out of its current position when the snake
    # moves forward, making that spot safe. So, we avoid `snake[:-1]`.
    
    # Stores (direction, next_head_pos, simulated_snake_body_after_move) for valid initial moves
    candidate_moves_info = [] 

    # For efficient lookup, convert the snake's body parts (excluding tail) to a set of obstacles
    current_snake_body_obstacles_set = set(snake[:-1])

    for direction, (dr, dc) in possible_moves.items():
        next_head_pos = (head_row + dr, head_col + dc)

        # Check for immediate wall or self-collision
        if not is_safe(next_head_pos, current_snake_body_obstacles_set, width, height):
            continue
        
        # If the move is safe, simulate the snake's body *after* this move.
        # This simulated body will be used as obstacles for pathfinding and area calculation.
        # The head moves to next_head_pos, and the rest of the body shifts, the old tail vanishes.
        simulated_snake_body_after_move_list = [next_head_pos] + snake[:-1]
        
        candidate_moves_info.append((direction, next_head_pos, simulated_snake_body_after_move_list))

    # If no safe moves, the snake is trapped. Game over is imminent.
    # Return a default direction (e.g., "UP") as a fallback.
    if not candidate_moves_info:
        return "UP" 

    # --- Step 2: Prioritize moves that lead to food (safely and smartly) ---
    
    # Store (direction, path_length_to_food, path_to_food_actual_list) for moves that can reach food
    food_reachable_moves = [] 
    
    for direction, next_head_pos, simulated_snake_body_after_move_list in candidate_moves_info:
        # Use BFS to find a path from next_head_pos to food, avoiding simulated_snake_body_after_move as obstacles.
        path_to_food = find_path_bfs(next_head_pos, food, simulated_snake_body_after_move_list, width, height)
        if path_to_food:
            food_reachable_moves.append((direction, len(path_to_food), path_to_food))

    # If food is reachable via any safe move:
    if food_reachable_moves:
        # Sort by path length to food (shortest path first)
        food_reachable_moves.sort(key=lambda x: x[1])

        best_food_move_direction = None
        min_food_path_length = food_reachable_moves[0][1] 

        # Filter for all moves that achieve this minimum path length to food
        shortest_food_paths_candidates = [m for m in food_reachable_moves if m[1] == min_food_path_length]

        max_free_area_after_eating = -1 # Maximize free area after eating food
        
        for direction, path_len_to_food, _ in shortest_food_paths_candidates:
            # The snake body *if food were eaten*: `[food]` (new head) + `snake` (old body)
            snake_body_if_food_eaten_list = [food] + snake
            snake_body_if_food_eaten_set = set(snake_body_if_food_eaten_list)
            
            # Find a path from the new head (food) to the new tail (snake[-1])
            # Obstacles for this path should exclude the target (snake[-1]).
            obstacles_for_tail_path = snake_body_if_food_eaten_set - {snake[-1]}
            path_to_new_tail = find_path_bfs(food, snake[-1], obstacles_for_tail_path, width, height)
            
            if path_to_new_tail:
                # If a path to the new tail exists after eating, this is a safer move.
                # Now, calculate the reachable area from the 'food' position,
                # with the *grown* snake as obstacles. This maximizes safety/maneuverability.
                area_after_eating = count_reachable_cells(food, snake_body_if_food_eaten_set, width, height)
                
                if area_after_eating > max_free_area_after_eating:
                    max_free_area_after_eating = area_after_eating
                    best_food_move_direction = direction
            
        # If we found a move that leads to food AND allows safely reaching the new tail
        # AND maximizes free area after eating
        if best_food_move_direction:
            return best_food_move_direction
        else:
            # If no shortest path to food also has a path to the new tail (and maximizes area),
            # just pick the absolute shortest path to food. This is a less safe but still direct option.
            # This 'else' block implies that reaching the tail after eating might not be possible
            # for any of the shortest food paths, but a path to food itself still exists.
            return food_reachable_moves[0][0]


    # --- Step 3: If food is not safely reachable, prioritize moves that maximize free space ---
    # This strategy helps the snake to keep moving in the largest possible open area,
    # preventing it from trapping itself as it grows or explores.
    
    best_area_move_direction = None
    max_reachable_area = -1
    
    for direction, next_head_pos, simulated_snake_body_after_move_list in candidate_moves_info:
        # Convert the simulated body to a set for efficient lookup in count_reachable_cells.
        simulated_snake_body_after_move_set = set(simulated_snake_body_after_move_list)
        
        # Calculate how much free space would be available after this move.
        area_size = count_reachable_cells(next_head_pos, simulated_snake_body_after_move_set, width, height)
        
        if area_size > max_reachable_area:
            max_reachable_area = area_size
            best_area_move_direction = direction
        
    # This branch will always be taken if `candidate_moves_info` is not empty (checked at start).
    if best_area_move_direction:
        return best_area_move_direction

    # --- Step 4: Fallback (should ideally not be reached given initial check) ---
    # This line is technically unreachable if `candidate_moves_info` is empty,
    # as the initial check `if not candidate_moves_info: return "UP"` covers it.
    # However, it's good practice to have a final default return.
    return "UP"