import random

import llm
import code_agent
import test_agent


def tournament_code_agents(agents, test_cases, code_map, initial_code):
    scores = {}
    for agent in agents:
        code = code_map.get(agent.agent_id, initial_code)
        scores[agent.agent_id] = code_agent.benchmark(code, test_cases)

    ranked = sorted(agents, key=lambda a: scores[a.agent_id])
    cutoff = max(1, len(ranked) // 2)

    survivors = ranked[:cutoff]
    for s in survivors:
        s.wins += 1
        # Mutate the propose function of surviving agents
        old_source = s.propose_source
        try:
            s.mutate_propose()
        except Exception:
            s.propose_source = old_source  # revert on any error

    replacements = []
    for i in range(len(ranked) - cutoff):
        parent = random.choice(survivors)
        child = code_agent.CodeAgent(
            agent_id=f"CA{parent.agent_id}_{parent.generation + 1}",
            strategy=mutate_strategy(parent.strategy),
            generation=parent.generation + 1,
        )
        child.current_code = code_map.get(parent.agent_id, initial_code)
        child.propose_source = parent.propose_source
        replacements.append(child)

    return survivors + replacements, scores


def tournament_test_agents(agents, hardness_scores):
    """Rank test agents by pre-computed hardness scores. Higher = better.

    Args:
        agents: list of TestAgent
        hardness_scores: dict mapping agent_id -> score (higher = harder tests)
    """
    ranked = sorted(agents, key=lambda a: hardness_scores.get(a.agent_id, 0), reverse=True)
    cutoff = max(1, len(ranked) // 2)

    survivors = ranked[:cutoff]
    for s in survivors:
        s.wins += 1
        s.hardness_scores.append(hardness_scores.get(s.agent_id, 0))

    replacements = []
    for i in range(len(ranked) - cutoff):
        parent = random.choice(survivors)
        child = test_agent.TestAgent(
            agent_id=f"TA{parent.agent_id}_{parent.generation + 1}",
            strategy=parent.strategy,
            generation=parent.generation + 1,
        )
        replacements.append(child)

    return survivors + replacements


def mutate_strategy(strategy):
    prompt = (
        f"Here is a code improvement strategy:\n\n{strategy}\n\n"
        f"Write a slightly modified version that explores a different angle. "
        f"Keep it 1-2 sentences. Return ONLY the strategy text."
    )
    return llm.ask(prompt).strip()
