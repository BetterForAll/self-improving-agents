import collections

def _find_path(start, target, obstacles_body_set, width, height, tail_safe=None):
    """
    Performs a Breadth-First Search (BFS) to find the shortest path from start to target.

    Args:
        start (tuple): (row, col) starting position for the pathfinding.
        target (tuple): (row, col) target position for the pathfinding.
        obstacles_body_set (set): A set of (row, col) tuples representing cells
                                  occupied by the snake's body that act as obstacles.
        width (int): Board width.
        height (int): Board height.
        tail_safe (tuple, optional): A specific (row, col) position that should be
                                     treated as safe to move into, even if it's
                                     initially listed in `obstacles_body_set`.
                                     This is typically the snake's tail position
                                     from the previous turn, which becomes free.

    Returns:
        int: The length of the shortest path, or float('inf') if no path is found.
    """
    queue = collections.deque([(start, 0)])  # (position, distance)
    visited = {start}  # Keep track of visited positions to avoid cycles

    # Create a mutable copy of obstacles and adjust for the start and safe tail
    current_obstacles = set(obstacles_body_set)
    current_obstacles.discard(start)  # The path starts FROM `start`, so `start` itself isn't an obstacle

    if tail_safe:
        current_obstacles.discard(tail_safe) # If the tail is safe to move into, remove it from obstacles

    while queue:
        (r, c), dist = queue.popleft()

        if (r, c) == target:
            return dist  # Target found

        # Explore neighbors (UP, DOWN, LEFT, RIGHT)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            next_pos = (nr, nc)

            # Check for wall collision
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            # Check if position has already been visited in this BFS
            if next_pos in visited:
                continue
            # Check if position is an obstacle (snake body segment)
            if next_pos in current_obstacles:
                continue

            visited.add(next_pos)
            queue.append((next_pos, dist + 1))

    return float('inf')  # No path found to the target

def next_move(snake, food, width, height):
    """
    Pick the next direction for the snake using a smarter strategy based on BFS.
    Prioritizes reaching food while ensuring a path to the tail for survival.

    Args:
        snake: list of (row, col) tuples, snake[0] is the head
        food:  (row, col) tuple, position of the food
        width: int, board width
        height: int, board height

    Returns: one of "UP", "DOWN", "LEFT", "RIGHT"
    """
    head_row, head_col = snake[0]
    current_tail_pos = snake[-1] # Position of the snake's tail *before* the next move

    possible_moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    # Store evaluations for each immediately safe move:
    # (direction, next_head_pos, path_to_food_len, path_to_tail_len)
    move_evaluations = []

    for direction, (dr, dc) in possible_moves.items():
        next_head_pos = (head_row + dr, head_col + dc)

        # 1. Check for immediate wall collision
        if not (0 <= next_head_pos[0] < height and 0 <= next_head_pos[1] < width):
            continue

        # 2. Check for immediate self-collision
        # The snake's tail (snake[-1]) will move out of its current position IF NOT EATING.
        # So, we only need to avoid `snake[:-1]` (all body segments except the current tail).
        # This check is sufficient for determining if the move is immediately safe from self-collision.
        if next_head_pos in snake[:-1]:
            continue # This move hits an immediate body part (excluding tail)

        # --- This move is immediately safe, now evaluate long-term safety and goals ---
        path_to_food_len = float('inf')
        path_to_tail_len = float('inf')

        # Define the set of obstacles for pathfinding *from* `next_head_pos`.
        # These are the cells that will be occupied by the snake's body *after* the move.
        
        # Scenario A: The snake moves to a new cell and DOES NOT eat food.
        #   The snake's body effectively shifts forward, and its original tail `current_tail_pos` becomes free.
        #   Obstacles for pathfinding will be `[next_head_pos] + snake[1:-1]`.
        #   (`snake[1:-1]` means all segments between the original head and original tail).
        #   In this case, `current_tail_pos` is a safe cell that the snake can path to.
        if next_head_pos != food:
            # Body segments that remain occupied (excluding original head and tail, plus new head)
            body_parts_as_obstacles = set(snake[1:-1])
            body_parts_as_obstacles.add(next_head_pos) # The new head is also an obstacle for further pathfinding
            
            # Path to food: `current_tail_pos` will be free, so it's `tail_safe`.
            path_to_food_len = _find_path(next_head_pos, food, body_parts_as_obstacles, width, height, tail_safe=current_tail_pos)
            
            # Path to tail: The target is `current_tail_pos`, which is also safe.
            path_to_tail_len = _find_path(next_head_pos, current_tail_pos, body_parts_as_obstacles, width, height, tail_safe=current_tail_pos)

        # Scenario B: The snake moves to `food` and DOES eat it.
        #   The snake's body grows, and its original tail `current_tail_pos` remains occupied.
        #   Obstacles for pathfinding will be `[next_head_pos] + snake[1:]`.
        #   (`snake[1:]` means all original segments except the head, which is replaced by `next_head_pos`).
        #   In this case, `current_tail_pos` is *not* free for general pathfinding to empty cells,
        #   but we still want to confirm we can reach it if needed, by treating it as a target that can be entered.
        else: # next_head_pos == food
            # Body segments that remain occupied (excluding original head, plus new head)
            body_parts_as_obstacles = set(snake[1:])
            body_parts_as_obstacles.add(next_head_pos) # The new head is also an obstacle for further pathfinding

            # Path to food: The tail remains occupied, so no `tail_safe` argument.
            path_to_food_len = _find_path(next_head_pos, food, body_parts_as_obstacles, width, height)
            
            # Path to tail (the new tail, which is `current_tail_pos`):
            # We explicitly treat `current_tail_pos` as enterable to calculate a path to it.
            path_to_tail_len = _find_path(next_head_pos, current_tail_pos, body_parts_as_obstacles, width, height, tail_safe=current_tail_pos)

        move_evaluations.append((direction, next_head_pos, path_to_food_len, path_to_tail_len))

    # If there are no immediately safe moves (snake is completely trapped)
    if not move_evaluations:
        return "UP" # Fallback: game is likely over, return a default direction

    # --- Decision Making based on evaluated paths ---

    # Priority 1: Find moves that lead to food AND ensure the snake can still reach its tail afterwards.
    # This is the safest and most optimal strategy for getting food without trapping itself.
    best_food_and_tail_moves = [
        (d, f_len, t_len, pos) for d, pos, f_len, t_len in move_evaluations
        if f_len != float('inf') and t_len != float('inf')
    ]
    if best_food_and_tail_moves:
        # Sort by shortest path to food, then by shortest path to tail (tie-breaker)
        best_food_and_tail_moves.sort(key=lambda x: (x[1], x[2]))
        return best_food_and_tail_moves[0][0]

    # Priority 2: If no moves satisfy Priority 1, find moves that lead to food (even if it might trap the snake).
    # This is a greedy approach for food, used when the safer option isn't available.
    best_food_moves = [
        (d, f_len, pos) for d, pos, f_len, _ in move_evaluations
        if f_len != float('inf')
    ]
    if best_food_moves:
        # Sort by shortest path to food
        best_food_moves.sort(key=lambda x: x[1])
        return best_food_moves[0][0]

    # Priority 3: If food is unreachable or too risky, prioritize survival by moving towards the tail.
    # This keeps the snake in the largest open area and prevents it from trapping itself.
    best_tail_moves = [
        (d, t_len, pos) for d, pos, _, t_len in move_evaluations
        if t_len != float('inf')
    ]
    if best_tail_moves:
        # Sort by shortest path to tail
        best_tail_moves.sort(key=lambda x: x[1])
        return best_tail_moves[0][0]

    # Priority 4: All paths to food or tail are blocked.
    # This means the snake is likely going to die, but it must still make a move.
    # In this scenario, just pick any move that passed the initial immediate collision checks.
    # `move_evaluations` should not be empty here because the "if not move_evaluations" check handles it.
    # The selection order is determined by the iteration order of `possible_moves`.
    return move_evaluations[0][0]