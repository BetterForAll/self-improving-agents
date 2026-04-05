"""
Arena Loop -- Adversarial Self-Improving Arena
==============================================
Code agents compete to write better code.
Test agents compete to write harder tests.
Tournament selection evolves strategies over generations.

All tasks supported: deterministic (snake), adversarial (email_validation),
and LLM-as-judge (support). Test agents generate harder inputs regardless of
evaluation type.

Uses Gemini 2.5 Flash. Set GEMINI_API_KEY in ../.env
"""

import argparse
import os
import sys
import random

DIR = os.path.dirname(os.path.abspath(__file__))
# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(DIR, ".."))
from tasks.task_runner import load_task, write_solution, run_solution

import llm
import code_agent
import test_agent
import arena
from evaluator import TaskEvaluator

random.seed(42)



# -- Main arena loop --

def run_arena(n_code=4, n_test=4, n_rounds=6, tournament_every=2,
              on_step=None, on_agent_step=None, start_from=0, resume_state=None,
              task_name="snake"):
    task = load_task(task_name)
    solution_file = os.path.join(DIR, f"solution_{task_name}.py")
    # ev handles all task-specific scoring and test generation (see evaluator.py)
    ev = TaskEvaluator(task, task_name, solution_file)

    higher_is_better = task.HIGHER_IS_BETTER
    metric_name = task.METRIC_NAME
    initial_code = task.INITIAL_CODE
    perfect_score = getattr(task, "PERFECT_SCORE", None)

    def is_better(new, old):
        return new > old if higher_is_better else new < old

    def is_perfect(score):
        if perfect_score is None:
            return False
        return score >= perfect_score if higher_is_better else score <= perfect_score

    print("=" * 70)
    print(f"  Arena Loop -- {task.TASK_NAME} (Real LLM)")
    print("=" * 70)
    print(f"  Code agents: {n_code}  |  Test agents: {n_test}")
    print(f"  Rounds: {n_rounds}  |  Tournament every {tournament_every} rounds\n")

    # -- Init or resume --
    if resume_state:
        raw_code = resume_state["code_agents"]
        if raw_code and isinstance(raw_code[0], dict):
            code_agents = [code_agent.CodeAgent.deserialize(d) for d in raw_code]
        else:
            code_agents = raw_code
        raw_test = resume_state["test_agents"]
        if raw_test and isinstance(raw_test[0], dict):
            test_agents_list = [test_agent.TestAgent.deserialize(d) for d in raw_test]
        else:
            test_agents_list = raw_test
        code_map = resume_state["code_map"]
        test_suite = resume_state.get("test_suite", [])
        global_best_code = resume_state["global_best_code"]
        global_best_metric = resume_state.get("global_best_metric", 0)
        baseline_metric = resume_state.get("baseline_metric", global_best_metric)
        print(f"[RESUME] Resuming from round {start_from + 1}\n")
    else:
        print(f"[INIT] Generating strategies for '{task_name}'...")
        ca_strategies = code_agent.generate_strategies(task_name, metric_name, n=n_code)
        code_agents = [code_agent.CodeAgent(f"CA{i}", ca_strategies[i]) for i in range(n_code)]

        ta_strategies = test_agent.generate_strategies(task_name, metric_name, n=n_test)
        test_agents_list = [test_agent.TestAgent(f"TA{i}", ta_strategies[i]) for i in range(n_test)]

        code_map = {a.agent_id: initial_code for a in code_agents}
        for a in code_agents:
            a.current_code = initial_code

        test_suite = ev.initial_suite()
        global_best_metric = ev.benchmark(initial_code, test_suite)
        global_best_code = initial_code
        baseline_metric = global_best_metric
        print(f"[INIT] Baseline {metric_name}: {global_best_metric:.2f}\n")

    round_history = []

    # -- Round loop --
    for round_num in range(start_from + 1, n_rounds + 1):
        prev_round_metric = global_best_metric
        print(f"-- Round {round_num}/{n_rounds} " + "-" * 50)

        # -- Code agents propose improvements --
        print("  [CODE AGENTS]")
        for agent in code_agents:
            print(f"    {agent.agent_id}: asking LLM...")
            try:
                custom_prompt = ev.build_prompt(agent.current_code, global_best_metric, test_suite)
                if custom_prompt:
                    raw = llm.ask(custom_prompt)
                    proposed = llm.extract_code(raw)
                else:
                    proposed = code_agent.propose(agent, metric_name=metric_name)
            except Exception as e:
                print(f"    {agent.agent_id}: LLM ERROR: {e}")
                bad = float("inf") if not higher_is_better else float("-inf")
                agent.fitness_history.append(bad)
                continue

            new_metric = ev.benchmark(proposed, test_suite)
            old_metric = ev.benchmark(agent.current_code, test_suite)

            direction = "^ better" if is_better(new_metric, old_metric) else "v worse"
            print(f"    {agent.agent_id}: {old_metric:.2f} -> {new_metric:.2f} {metric_name}  {direction}")

            if is_better(new_metric, old_metric):
                agent.current_code = proposed
                code_map[agent.agent_id] = proposed
                if is_better(new_metric, global_best_metric):
                    global_best_metric = new_metric
                    global_best_code = proposed

            agent.fitness_history.append(new_metric)

            if on_agent_step:
                on_agent_step({
                    "round": round_num, "agent_id": agent.agent_id,
                    "action": "ACCEPTED" if is_better(new_metric, old_metric) else "REJECTED",
                    "old_metric": round(old_metric, 4),
                    "new_metric": round(new_metric, 4),
                    "code": proposed,
                })

        # -- Capture metric before test expansion --
        pre_expansion_metric = ev.benchmark(global_best_code, test_suite)

        # -- Test agents generate harder tests --
        proposed_tests = {}
        hardness_map = {}
        print("  [TEST AGENTS]")
        for agent in test_agents_list:
            print(f"    {agent.agent_id}: generating tests...")
            try:
                new_tests = ev.propose_tests(agent, global_best_code)
                hardness = ev.measure_hardness(global_best_code, new_tests)
                proposed_tests[agent.agent_id] = new_tests
                hardness_map[agent.agent_id] = hardness
                print(f"    {agent.agent_id}: {ev.format_hardness(hardness, new_tests)}")
            except Exception as e:
                print(f"    {agent.agent_id}: LLM ERROR: {e}")

        # -- Add hardest tests to suite --
        if proposed_tests:
            best_ta = max(hardness_map, key=hardness_map.get)
            ev.add_to_suite(test_suite, proposed_tests[best_ta], best_ta)

        # -- Re-benchmark against expanded suite --
        if proposed_tests:
            new_best = ev.benchmark(global_best_code, test_suite)
            if is_better(global_best_metric, new_best):
                print(f"  [ARMS RACE] Best code dropped: "
                      f"{global_best_metric:.2f} -> {new_best:.2f} "
                      f"(new tests exposed weaknesses)")
            global_best_metric = new_best

        # -- Tournament --
        if round_num % tournament_every == 0:
            print(f"\n  [TOURNAMENT -- round {round_num}]")
            scores = {a.agent_id: ev.benchmark(
                code_map.get(a.agent_id, initial_code), test_suite
            ) for a in code_agents}
            ranked = sorted(code_agents, key=lambda a: scores[a.agent_id],
                            reverse=higher_is_better)

            cutoff = max(1, len(ranked) // 2)
            survivors = ranked[:cutoff]
            for s in survivors:
                s.wins += 1
                old_source = s.propose_source
                try:
                    s.mutate_propose()
                except Exception:
                    s.propose_source = old_source

            replacements = []
            for i in range(len(ranked) - cutoff):
                parent = random.choice(survivors)
                child = code_agent.CodeAgent(
                    agent_id=f"CA{parent.agent_id}_{parent.generation + 1}",
                    strategy=arena.mutate_strategy(parent.strategy),
                    generation=parent.generation + 1,
                )
                child.current_code = code_map.get(parent.agent_id, initial_code)
                child.propose_source = parent.propose_source
                replacements.append(child)
            code_agents = survivors + replacements

            for a in code_agents:
                if a.agent_id not in code_map:
                    code_map[a.agent_id] = global_best_code
                    a.current_code = global_best_code
            live_ids = {a.agent_id for a in code_agents}
            code_map = {k: v for k, v in code_map.items() if k in live_ids}

            test_agents_list = arena.tournament_test_agents(test_agents_list, hardness_map)

            print(f"  Code survivors: {[a.agent_id for a in code_agents[:cutoff]]}")
            print(f"  Test survivors: {[a.agent_id for a in test_agents_list[:n_test // 2]]}")
            print(f"  Test suite: {len(test_suite)} cases\n")

        # -- Step callback --
        step = {
            "step": round_num,
            "action": "ROUND_COMPLETE",
            "proposed_metric": round(global_best_metric, 4),
            "previous_metric": round(prev_round_metric, 4) if round_num > start_from + 1 else round(baseline_metric, 4),
            "pre_expansion_metric": round(pre_expansion_metric, 4),
            "global_best_code": global_best_code,
            "test_suite": list(test_suite) if ev.adversarial else None,
            "test_suite_size": len(test_suite),
            "tournament": round_num % tournament_every == 0,
            "code_agents": [{"id": a.agent_id, "wins": a.wins, "gen": a.generation}
                            for a in code_agents],
            "test_agents": [{"id": a.agent_id, "wins": a.wins, "gen": a.generation}
                            for a in test_agents_list],
            "code_agents_full": [a.serialize() for a in code_agents],
            "test_agents_full": [a.serialize() for a in test_agents_list],
            "code_map": code_map,
            "baseline_metric": baseline_metric,
        }
        round_history.append(step)
        if on_step:
            on_step(step)

        if is_perfect(global_best_metric):
            print(f"\n  PERFECT SCORE reached. Stopping early.")
            break

    # -- Summary --
    print("=" * 70)
    print("  ARENA FINAL RESULTS")
    print("=" * 70)
    print(f"  Best {metric_name:14}: {global_best_metric:.3f}")
    print(f"  Test suite size  : {len(test_suite)}")

    print(f"\n  Code agents:")
    for a in sorted(code_agents, key=lambda a: -a.wins):
        print(f"    {a.agent_id:8}  wins={a.wins}  gen={a.generation}"
              f"  strat={a.strategy[:50]}...")

    print(f"\n  Test agents:")
    for a in sorted(test_agents_list, key=lambda a: -a.wins):
        print(f"    {a.agent_id:8}  wins={a.wins}  gen={a.generation}"
              f"  strat={a.strategy[:50]}...")

    return {
        "best_metric": global_best_metric,
        "baseline_metric": baseline_metric,
        "best_code": global_best_code,
        "final_code": global_best_code,
        "test_suite_size": len(test_suite),
        "code_agents": [{"id": a.agent_id, "wins": a.wins, "gen": a.generation,
                         "strategy": a.strategy} for a in code_agents],
        "test_agents": [{"id": a.agent_id, "wins": a.wins, "gen": a.generation,
                         "strategy": a.strategy} for a in test_agents_list],
        "rounds": n_rounds,
        "task": task_name,
        "metric_name": metric_name,
        "higher_is_better": higher_is_better,
        "history": round_history,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="snake",
                        help="Task: snake, email_validation, support")
    parser.add_argument("--code", type=int, default=4, help="Number of code agents")
    parser.add_argument("--test", type=int, default=4, help="Number of test agents")
    parser.add_argument("--rounds", type=int, default=6, help="Number of rounds")
    args = parser.parse_args()
    run_arena(n_code=args.code, n_test=args.test, n_rounds=args.rounds,
              task_name=args.task)
