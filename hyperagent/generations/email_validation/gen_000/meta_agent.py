import sys
import os
import json

# Add repo root to Python path so we can import from tasks/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import llm


MODIFIABLE_FILES = ["task_agent.py", "meta_agent.py"]


def propose_modifications(agent_files, eval_results, task_info):
    files_text = ""
    for fname, code in agent_files.items():
        files_text += f"\n--- {fname} ---\n{code}\n"

    results_text = json.dumps(eval_results[-6:], indent=2)

    prompt = (
        f"You are a meta-agent that improves its own code.\n\n"
        f"CURRENT AGENT SOURCE CODE:\n{files_text}\n\n"
        f"RECENT EVALUATION RESULTS:\n{results_text}\n\n"
        f"TASK: {task_info['task_name']}\n"
        f"METRIC: {task_info['metric_name']} "
        f"({'higher' if task_info['higher_is_better'] else 'lower'} is better)\n"
        f"BEST SCORE: {task_info['best_metric']}\n\n"
        f"Analyze the results and modify the agent code to improve performance.\n"
        f"You may modify task_agent.py (how solutions are proposed) and/or "
        f"meta_agent.py (how improvements are proposed -- your own code).\n\n"
        f"RULES:\n"
        f"- task_agent.py MUST export: propose(current_code, best_metric, history, metric_name)\n"
        f"  which returns (proposed_code_string, raw_llm_response)\n"
        f"- meta_agent.py MUST export: propose_modifications(agent_files, eval_results, task_info)\n"
        f"  which returns a dict of {{filename: new_source_or_None}}\n"
        f"- Both files may import 'llm' (Gemini wrapper with ask(), extract_code(), extract_json())\n"
        f"- Keep the sys.path.insert and import llm lines at the top\n\n"
        f"Return a JSON object where keys are filenames and values are the "
        f"complete new file contents. Use null for files you do not want to change.\n"
        f'Example: {{"task_agent.py": "import sys\\nimport os\\n...", "meta_agent.py": null}}\n'
        f"Return ONLY the JSON object."
    )
    raw = llm.ask(prompt)
    return _parse_modifications(raw)


def _parse_modifications(response):
    data = llm.extract_json(response)
    return {k: v for k, v in data.items() if v is not None and k in MODIFIABLE_FILES}
