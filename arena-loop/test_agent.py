import json
from dataclasses import dataclass, field

import llm

FALLBACK_STRATEGIES = [
    "Focus on worst-case inputs that expose algorithmic weaknesses.",
    "Focus on scale: large inputs to expose O(n^2) behavior.",
    "Focus on degenerate data: edge cases, duplicates, extremes.",
    "Focus on adversarial patterns that break common implementations.",
]


def generate_strategies(task_name, metric_name, n=4):
    prompt = (
        f"Generate {n} different short (1-2 sentence) adversarial testing strategies "
        f"for a Python function that solves '{task_name}'. "
        f"The goal is to generate inputs that expose weaknesses. "
        f"Each strategy should focus on a different type of edge case or attack.\n\n"
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
class TestAgent:
    agent_id: str
    strategy: str
    generation: int = 0
    wins: int = 0
    hardness_scores: list = field(default_factory=list)

    def serialize(self):
        return {
            "agent_id": self.agent_id, "strategy": self.strategy,
            "generation": self.generation, "wins": self.wins,
            "hardness_scores": list(self.hardness_scores),
        }

    @staticmethod
    def deserialize(d):
        agent = TestAgent(
            agent_id=d["agent_id"], strategy=d["strategy"],
            generation=d.get("generation", 0), wins=d.get("wins", 0),
        )
        agent.hardness_scores = d.get("hardness_scores", [])
        return agent


def propose_email_tests(agent, current_best_code):
    """Generate tricky email test cases to break the current validator."""
    prompt = (
        f"You are an adversarial tester for email validation.\n\n"
        f"STRATEGY: {agent.strategy}\n\n"
        f"CURRENT VALIDATOR:\n{current_best_code}\n\n"
        f"Generate 5 tricky email test cases that this function will likely "
        f"get wrong. Include both valid emails it might reject and invalid "
        f"emails it might accept.\n\n"
        f"Return ONLY a JSON array:\n"
        f'[{{"email": "...", "valid": true, "reason": "why this is tricky"}}]'
    )
    raw = llm.ask(prompt)
    return _parse_email_tests(raw, agent.agent_id)


def propose_support_tests(agent, current_best_code, knowledge_base):
    """Generate tricky customer support questions that the current best code struggles with."""
    prompt = (
        f"You are an adversarial tester for a customer support AI.\n\n"
        f"STRATEGY: {agent.strategy}\n\n"
        f"KNOWLEDGE BASE:\n{knowledge_base}\n\n"
        f"CURRENT SUPPORT FUNCTION:\n{current_best_code}\n\n"
        f"Generate 3 tricky customer questions that this function will likely "
        f"answer poorly. The questions should be answerable from the knowledge base "
        f"but require careful reading or combining multiple facts.\n\n"
        f"Return ONLY a JSON array:\n"
        f'[{{"question": "...", "expected": "the correct answer based on knowledge base"}}]'
    )
    raw = llm.ask(prompt)
    return _parse_support_tests(raw, agent.agent_id, knowledge_base)


def _parse_support_tests(raw, agent_id, knowledge_base=None):
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        tests = json.loads(text)
        if not isinstance(tests, list):
            tests = [tests]
        result = []
        for t in tests:
            if "question" in t and "expected" in t:
                fact_checks = []
                if knowledge_base:
                    fact_checks = _generate_fact_checks(
                        str(t["question"]), str(t["expected"]), knowledge_base)
                result.append({
                    "question": str(t["question"]),
                    "expected": str(t["expected"]),
                    "generated_by": agent_id,
                    "fact_checks": fact_checks,
                })
        return result if result else _fallback_support_tests(agent_id)
    except (json.JSONDecodeError, KeyError):
        return _fallback_support_tests(agent_id)


def _generate_fact_checks(question, expected, knowledge_base):
    prompt = (
        "You are creating boolean checks for scoring a customer support answer.\n\n"
        f"KNOWLEDGE BASE:\n{knowledge_base}\n\n"
        f"Question: {question}\n"
        f"Expected answer: {expected}\n\n"
        "Extract boolean checks that verify the actual answer is correct. Each check\n"
        "should be something an LLM can answer YES or NO about the actual output.\n\n"
        "For each check provide:\n"
        '- "description": a statement to verify (phrased for YES/NO evaluation)\n'
        '- "keywords": list of specific substrings that confirm this check.\n'
        '  Use numbers, technical terms, specific phrases. Lowercase. Empty list []\n'
        '  if keyword matching is unreliable.\n'
        '- "weight": 1 (supporting detail), 2 (key requirement), or 3 (critical)\n\n'
        "RULES:\n"
        "- Extract checks ONLY from the expected output. Do not invent extras.\n"
        "- Use weight 3 for at most 1-2 checks (the core requirement).\n"
        "- Keep keyword lists short (2-4 items).\n\n"
        "Return ONLY a JSON array. No markdown."
    )
    raw = llm.ask(prompt)
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        checks = json.loads(text)
        if not isinstance(checks, list):
            return []
        result = []
        for c in checks:
            if not isinstance(c, dict) or "description" not in c:
                continue
            result.append({
                "description": str(c["description"]),
                "keywords": [str(k) for k in c.get("keywords", [])],
                "weight": max(1, min(3, int(c.get("weight", 1)))),
            })
        return result
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return []


def _fallback_support_tests(agent_id):
    return [
        {"question": "If I'm on Personal and need to upload a 15GB file, what are my options?",
         "expected": "You would need to upgrade to Pro or Enterprise, as large files over 10GB are only supported on those plans.",
         "generated_by": agent_id,
         "fact_checks": [
             {"description": "Mentions upgrading to Pro or Enterprise",
              "keywords": ["pro", "enterprise"], "weight": 3},
             {"description": "Mentions the 10GB file size limit on Personal",
              "keywords": ["10gb", "10 gb"], "weight": 2},
         ]},
    ]


def _parse_email_tests(raw, agent_id):
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])
        tests = json.loads(text)
        if not isinstance(tests, list):
            tests = [tests]
        result = []
        for t in tests:
            if "email" in t and "valid" in t:
                result.append({
                    "email": str(t["email"]),
                    "valid": bool(t["valid"]),
                    "reason": t.get("reason", "adversarial"),
                    "generated_by": agent_id,
                })
        return result if result else _fallback_email_tests(agent_id)
    except (json.JSONDecodeError, KeyError):
        return _fallback_email_tests(agent_id)


def _fallback_email_tests(agent_id):
    return [
        {"email": "user@[127.0.0.1]", "valid": True, "reason": "IP literal", "generated_by": agent_id},
        {"email": "user@domain..com", "valid": False, "reason": "double dot", "generated_by": agent_id},
    ]


