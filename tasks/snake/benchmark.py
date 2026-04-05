"""
Benchmark harness for Snake AI task.

Runs solution.py (which must define next_move), plays 20 games
with different seeds, and reports average score.

Usage: python benchmark.py <solution_file>
"""

import random
import sys

DIRECTIONS = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
WIDTH, HEIGHT = 10, 10
NUM_GAMES = 20


def play_game(move_fn, seed):
    random.seed(seed)
    snake = [(HEIGHT // 2, WIDTH // 2)]
    food = _place_food(snake)
    score = 0
    steps = 0
    max_steps = WIDTH * HEIGHT * 3

    while steps < max_steps:
        try:
            direction = move_fn(list(snake), food, WIDTH, HEIGHT)
        except Exception:
            break
        if direction not in DIRECTIONS:
            break

        dr, dc = DIRECTIONS[direction]
        new_head = (snake[0][0] + dr, snake[0][1] + dc)

        if not (0 <= new_head[0] < HEIGHT and 0 <= new_head[1] < WIDTH):
            break

        if new_head in snake:
            break

        snake.insert(0, new_head)

        if new_head == food:
            score += 1
            if len(snake) >= WIDTH * HEIGHT:
                break
            food = _place_food(snake)
        else:
            snake.pop()

        steps += 1

    return score


def _place_food(snake):
    while True:
        pos = (random.randint(0, HEIGHT - 1), random.randint(0, WIDTH - 1))
        if pos not in snake:
            return pos


if __name__ == "__main__":
    solution_file = sys.argv[1] if len(sys.argv) > 1 else "solution.py"
    ns = {}
    with open(solution_file) as f:
        exec(compile(f.read(), solution_file, "exec"), ns)

    next_move = ns["next_move"]
    total_score = 0
    for seed in range(NUM_GAMES):
        total_score += play_game(next_move, seed)
    avg_score = total_score / NUM_GAMES
    print(f"score:{avg_score:.2f}")
    print(f"games:{NUM_GAMES}")
