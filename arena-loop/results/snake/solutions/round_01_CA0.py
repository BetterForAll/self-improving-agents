import collections

def next_move(snake, food, width, height):
    """Pick the next direction for the snake with look-ahead pathfinding.

    This strategy targets food but critically verifies a subsequent safe path
    to the snake's tail or an open area, preventing self-entrapment after eating.
    If no safe path to food exists, it prioritizes moves that maximize open space
    and maintain a safe path to the snake's tail (or the cell it will vacate).

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """

    # Helper function definitions (nested for self-containment)
    DIRECTIONS = {
        "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)
    }

    def get_next_pos(current_pos, direction_str):
        dr, dc = DIRECTIONS[direction_str]
        return (current_pos[0] + dr, current_pos[1] + dc)

    def is_valid(pos, obstacles, board_width, board_height):
        r, c = pos
        # Check boundaries
        if not (0 <= r < board_height and 0 <= c < board_width):
            return False
        # Check collision with obstacles
        if pos in obstacles:
            return False
        return True

    def bfs_path(start, target, obstacles, board_width, board_height):
        """Finds a path from start to target using BFS, avoiding obstacles."""
        queue = collections.deque([(start, [])]) # (current_pos, path_to_current_pos)
        visited = {start}

        while queue:
            current_pos, path = queue.popleft()

            if current_pos == target:
                return path # Path found (list of positions from start to target, exclusive of start)

            for dr, dc in DIRECTIONS.values():
                neighbor = (current_pos[0] + dr, current_pos[1] + dc)
                if is_valid(neighbor, obstacles, board_width, board_height) and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None # No path found

    def bfs_reachable_count(start, obstacles, board_width, board_height):
        """Counts the number of cells reachable from start using BFS, avoiding obstacles."""
        queue = collections.deque([start])
        visited = {start}
        count = 0

        while queue:
            current_pos = queue.popleft()
            count += 1

            for dr, dc in DIRECTIONS.values():
                neighbor = (current_pos[0] + dr, current_pos[1] + dc)
                if is_valid(neighbor, obstacles, board_width, board_height) and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return count

    # Main logic for next_move
    head = snake[0]
    tail = snake[-1]

    # Store potential moves with their calculated scores for prioritization
    # Score structure: (priority, secondary_metric, direction_str)
    # Priority: 3 for safe food path, 2 for safe non-food path.
    # Secondary Metric:
    #   - For priority 3 (food): Length of the path to the original tail after eating.
    #     A longer path implies more open space / less chance of immediate entrapment.
    #   - For priority 2 (non-food): Number of reachable cells (open space) after the move.
    #     Maximizing this keeps the snake in open areas.
    candidate_moves = []

    # Evaluate all four possible immediate directions
    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_pos = (head[0] + dr, head[1] + dc)

        # 1. Immediate Collision Check:
        # For a non-eating move, the snake's tail (snake[-1]) will move, so it's not an obstacle.
        current_obstacles_for_immediate_check = set(snake[:-1])
        if not is_valid(next_pos, current_obstacles_for_immediate_check, width, height):
            continue # This move is immediately invalid (hits wall or current body, excluding tail)

        # 2. Scenario: Move leads to Food
        if next_pos == food:
            # Simulate eating: the snake grows, so its tail remains occupied (does not move).
            simulated_snake_after_eat = [next_pos] + snake
            obstacles_after_eat = set(simulated_snake_after_eat)

            # Look-ahead Safety Check (A): After eating, can we find a path from the new head
            # to the original tail? Reaching the original tail (which is now just an internal
            # part of the extended body) implies there's an open path around the newly grown snake,
            # preventing immediate self-entrapment.
            path_after_eat_to_tail = bfs_path(next_pos, tail, obstacles_after_eat, width, height)
            
            if path_after_eat_to_tail is not None:
                # This is a high-priority, safe food move.
                # Secondary metric: Use the length of this escape path. A longer path means more space.
                candidate_moves.append((3, len(path_after_eat_to_tail), direction_str))

        # 3. Scenario: Move does NOT lead to Food (normal movement)
        else:
            # Simulate normal move: the head moves, and the tail segment (snake[-1]) is vacated.
            simulated_snake_after_move = [next_pos] + snake[:-1]
            obstacles_after_move = set(simulated_snake_after_move)

            # Look-ahead Safety Check (B): After a normal move, can we find a path from the new head
            # to the cell that was just vacated by the tail (`tail`)? This ensures the snake
            # doesn't trap itself by cutting off its own tail-following route.
            path_to_freed_tail = bfs_path(next_pos, tail, obstacles_after_move, width, height)
            
            if path_to_freed_tail is not None:
                # This is a medium-priority, safe non-food move.
                # Secondary metric: Maximize the amount of open space (reachable cells) after this move.
                reachable_count = bfs_reachable_count(next_pos, obstacles_after_move, width, height)
                candidate_moves.append((2, reachable_count, direction_str))

    # Decision Making: Select the best move from the qualified candidates
    if candidate_moves:
        # Sort candidates:
        # Primary sort key: Priority (3 > 2), descending. Food moves are preferred.
        # Secondary sort key: Secondary metric (path length or reachable count), descending. More space is preferred.
        candidate_moves.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidate_moves[0][2] # Return the direction string of the highest-ranked move

    # Fallback Strategy: If no "safe" moves (i.e., moves with a guaranteed escape path) were found.
    # This implies all look-ahead verified paths lead to entrapment. In this desperate situation,
    # the snake must make *any* move that doesn't immediately result in a crash (wall or self-collision)
    # and tries to maximize immediate open space, even if it leads to a future trap.
    
    max_desperate_reachable_count = -1
    desperate_move = None
    
    for direction_str, (dr, dc) in DIRECTIONS.items():
        next_pos = (head[0] + dr, head[1] + dc)
        
        # Immediate collision check (only against wall or current body, excluding tail).
        # This is the most basic safety.
        if is_valid(next_pos, set(snake[:-1]), width, height):
            # This move is immediately valid but might lead to a look-ahead trap.
            # Calculate reachable cells assuming a non-food move (tail frees up) to maximize immediate space.
            simulated_snake_after_desperate_move = [next_pos] + snake[:-1]
            obstacles_for_desperate_count = set(simulated_snake_after_desperate_move)
            
            reachable_count = bfs_reachable_count(next_pos, obstacles_for_desperate_count, width, height)
            
            if reachable_count > max_desperate_reachable_count:
                max_desperate_reachable_count = reachable_count
                desperate_move = direction_str
    
    if desperate_move:
        return desperate_move
    
    # Absolute last resort: If even desperate immediate moves are not found,
    # the snake is completely surrounded and will die. Return a default to avoid error.
    return "UP" # Should almost never be reached in a playable game.