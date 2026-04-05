import os
from dataclasses import dataclass, field

import llm

DIR = os.path.dirname(os.path.abspath(__file__))

FALLBACK_STRATEGIES = [
    "Focus on algorithmic complexity: replace O(n^2) with O(n log n).",
    "Focus on Python runtime: prefer built-ins and C-speed operations.",
    "Focus on memory: minimize allocations and list copies.",
    "Focus on worst-case inputs: handle adversarial patterns first.",
]


def generate_strategies(task_name, metric_name, n=4):
    prompt = (
        f"Generate {n} different short (1-2 sentence) code improvement strategies "
        f"for a Python function that solves '{task_name}'. "
        f"It is evaluated by '{metric_name}'. "
        f"Each strategy should take a completely different approach.\n\n"
        f"Return ONLY a JSON array of strings."
    )
    raw = llm.ask(prompt)
    try:
        result = llm.extract_json(raw)
        if isinstance(result, list) and len(result) >= n:
            return [str(s) for s in result[:n]]
    except (ValueError, TypeError):
        pass
    return FALLBACK_STRATEGIES[:n]


@dataclass
class CodeAgent:
    agent_id: str
    strategy: str
    generation: int = 0
    wins: int = 0
    current_code: str = ""
    fitness_history: list = field(default_factory=list)
    # The agent's proposal logic as Python source code.
    # The agent can rewrite this to change HOW it proposes improvements.
    # Empty string = use the default propose() function below.
    propose_source: str = ""

    def serialize(self):
        return {
            "agent_id": self.agent_id, "strategy": self.strategy,
            "generation": self.generation, "wins": self.wins,
            "current_code": self.current_code,
            "fitness_history": list(self.fitness_history),
            "propose_source": self.propose_source,
        }

    @staticmethod
    def deserialize(d):
        agent = CodeAgent(
            agent_id=d["agent_id"], strategy=d["strategy"],
            generation=d.get("generation", 0), wins=d.get("wins", 0),
            current_code=d.get("current_code", ""),
        )
        agent.fitness_history = d.get("fitness_history", [])
        agent.propose_source = d.get("propose_source", "")
        return agent

    def mutate_propose(self):
        if not self.propose_source:
            return
        prompt = (
            f"Here is a code proposal function:\n\n{self.propose_source}\n\n"
            f"It produced mixed results. Rewrite it to propose better code improvements.\n"
            f"Keep the same signature: propose(agent, test_failures='', metric_name='time_ms')\n"
            f"It should import and use 'llm' module (llm.ask(), llm.extract_code()).\n"
            f"Return ONLY the function code."
        )
        raw = llm.ask(prompt)
        new_source = llm.extract_code(raw)
        try:
            compile(new_source, "<mutated_propose>", "exec")
            self.propose_source = new_source
        except SyntaxError:
            pass  # keep old version


def propose(agent, test_failures="", metric_name="time_ms"):
    # If agent has a custom propose_source, try to use it
    if agent.propose_source:
        # Run the code string in an isolated namespace to extract functions from it
        ns = {"llm": llm}
        try:
            exec(compile(agent.propose_source, "<propose>", "exec"), ns)
            fn = ns.get("propose")
            if fn:
                return fn(agent, test_failures=test_failures, metric_name=metric_name)
        except Exception:
            pass  # fall through to default

    # Default implementation
    prompt = (
        f"You are a code improvement agent.\n\n"
        f"STRATEGY: {agent.strategy}\n\n"
        f"CURRENT CODE:\n{agent.current_code}\n\n"
    )
    if test_failures:
        prompt += f"RECENT TEST FAILURES:\n{test_failures}\n\n"
    prompt += (
        f"Write an improved version that gets a better {metric_name}. "
        f"Return ONLY the function definition."
    )
    raw = llm.ask(prompt)
    return llm.extract_code(raw)
