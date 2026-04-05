"""
Visual Snake Game Player
========================
Watch the AI play Snake in your terminal.

Usage:
    python play.py                        # play with initial (dumb) AI
    python play.py path/to/solution.py    # play with a specific AI
    python play.py --speed 0.1            # slower (default 0.05s per step)
"""

import argparse
import os
import random
import sys
import time

DIRECTIONS = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
WIDTH, HEIGHT = 10, 10


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def render(snake, food, width, height, score, step):
    clear_screen()
    print(f"  Snake AI  |  Score: {score}  |  Step: {step}")
    print("  " + "-" * (width * 2 + 1))
    for r in range(height):
        row = " |"
        for c in range(width):
            pos = (r, c)
            if pos == snake[0]:
                row += "@@"  # head
            elif pos in snake:
                row += "##"  # body
            elif pos == food:
                row += "<>"  # food
            else:
                row += "  "  # empty
        row += "|"
        print(row)
    print("  " + "-" * (width * 2 + 1))


def play_visual(move_fn, seed=0, speed=0.05):
    random.seed(seed)
    snake = [(HEIGHT // 2, WIDTH // 2)]
    food = _place_food(snake)
    score = 0
    step = 0
    max_steps = WIDTH * HEIGHT * 3

    while step < max_steps:
        render(snake, food, WIDTH, HEIGHT, score, step)
        time.sleep(speed)

        try:
            direction = move_fn(list(snake), food, WIDTH, HEIGHT)
        except Exception as e:
            print(f"\n  AI crashed: {e}")
            break
        if direction not in DIRECTIONS:
            print(f"\n  AI returned invalid direction: {direction}")
            break

        dr, dc = DIRECTIONS[direction]
        new_head = (snake[0][0] + dr, snake[0][1] + dc)

        if not (0 <= new_head[0] < HEIGHT and 0 <= new_head[1] < WIDTH):
            render(snake, food, WIDTH, HEIGHT, score, step)
            print(f"\n  GAME OVER -- hit wall! Final score: {score}")
            break

        if new_head in snake:
            render(snake, food, WIDTH, HEIGHT, score, step)
            print(f"\n  GAME OVER -- hit self! Final score: {score}")
            break

        snake.insert(0, new_head)

        if new_head == food:
            score += 1
            if len(snake) >= WIDTH * HEIGHT:
                render(snake, food, WIDTH, HEIGHT, score, step)
                print(f"\n  YOU WIN! Snake filled the board! Score: {score}")
                break
            food = _place_food(snake)
        else:
            snake.pop()

        step += 1
    else:
        render(snake, food, WIDTH, HEIGHT, score, step)
        print(f"\n  Time's up! Final score: {score}")

    return score


def _place_food(snake):
    while True:
        pos = (random.randint(0, HEIGHT - 1), random.randint(0, WIDTH - 1))
        if pos not in snake:
            return pos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watch Snake AI play")
    parser.add_argument("solution", nargs="?", default=None,
                        help="Path to solution.py (default: initial_solution.py)")
    parser.add_argument("--speed", type=float, default=0.05,
                        help="Seconds per step (default: 0.05)")
    parser.add_argument("--seed", type=int, default=0,
                        help="Random seed for the game")
    args = parser.parse_args()

    # Load the AI
    if args.solution:
        solution_file = args.solution
    else:
        solution_file = os.path.join(os.path.dirname(__file__), "initial_solution.py")

    ns = {}
    with open(solution_file) as f:
        exec(compile(f.read(), solution_file, "exec"), ns)

    print(f"  Loading AI from: {solution_file}")
    time.sleep(1)

    score = play_visual(ns["next_move"], seed=args.seed, speed=args.speed)
