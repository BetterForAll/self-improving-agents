"""Generate progress charts from experiment logs for the README."""

import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


LEVELS = [
    ("autoresearch", "AutoResearch Loop"),
    ("feedback-loop", "Feedback Loop"),
    ("hyperagent", "HyperAgent Loop"),
    ("arena-loop", "Arena Loop"),
]

TASKS = [
    ("snake", "Snake Game AI", "Score (food eaten)", None),
    ("email_validation", "Email Validation", "Accuracy",
     "Levels 1-3: 10 fixed tests  |  Arena Loop: 50 adversarial tests"),
    ("support", "Customer Support", "Quality Score", None),
]

COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]
MARKERS = ["o", "s", "^", "D"]


def load_history(level_dir, task):
    path = os.path.join(level_dir, "results", task, "experiment-log.json")
    if not os.path.exists(path):
        return None, None
    with open(path) as f:
        data = json.load(f)
    baseline = data.get("baseline_metric", 0)
    history = data.get("history", [])
    # Build best-so-far series
    best = baseline
    higher = data.get("higher_is_better", True)
    points = [(0, baseline)]
    for entry in history:
        metric = entry.get("proposed_metric")
        if metric is None:
            continue
        action = entry.get("action", "")
        if action in ("ACCEPTED", "ROUND_COMPLETE"):
            if higher and metric > best:
                best = metric
            elif not higher and metric < best:
                best = metric
        points.append((entry["step"], best))
    return points, data


def generate_chart(task_name, task_label, y_label, output_path, subtitle=None):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    max_steps = 0
    for i, (level_dir, level_name) in enumerate(LEVELS):
        points, data = load_history(level_dir, task_name)
        if points is None:
            continue
        steps = [p[0] for p in points]
        values = [p[1] for p in points]
        max_steps = max(max_steps, max(steps))
        ax.plot(steps, values, color=COLORS[i], marker=MARKERS[i],
                label=level_name, linewidth=2, markersize=6, markeredgewidth=0)

    ax.set_xlabel("Iteration", fontsize=12, fontweight="bold")
    ax.set_ylabel(y_label, fontsize=12, fontweight="bold")
    if subtitle:
        ax.set_title(task_label + "\n" + subtitle,
                     fontsize=14, fontweight="bold", pad=12)
        ax.title.set_fontsize(14)
        # Make subtitle smaller
        ax.set_title(task_label, fontsize=14, fontweight="bold", pad=20)
        ax.text(0.5, 1.01, subtitle, transform=ax.transAxes,
                fontsize=9, ha="center", color="#666666", style="italic")
    else:
        ax.set_title(task_label, fontsize=14, fontweight="bold", pad=12)
    ax.legend(loc="best", framealpha=0.9, fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Start x-axis at 0
    ax.set_xlim(left=-0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  {output_path}")


def main():
    os.makedirs("assets", exist_ok=True)
    print("Generating charts:")
    for task_name, task_label, y_label, subtitle in TASKS:
        output = os.path.join("assets", f"chart_{task_name}.png")
        generate_chart(task_name, task_label, y_label, output, subtitle)
    print("Done.")


if __name__ == "__main__":
    main()
