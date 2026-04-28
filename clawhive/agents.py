"""The four specialized agents. Each is a function that takes structured input and
returns structured output. The orchestrator wires them together.

Keep these functions narrow. The "specialist beats generalist" claim only holds when
each agent has a tight role.
"""
import json
import re
from dataclasses import dataclass, field

from client import ModelSpec, chat, planner_spec, coder_spec, critic_spec, estimate_cost


@dataclass
class Step:
    n: int
    description: str
    output: str = ""
    passed: bool = False
    feedback: str = ""
    retries: int = 0


@dataclass
class Plan:
    task: str
    steps: list[Step]
    total_cost_usd: float = 0.0
    spec_log: list[tuple[str, str, dict]] = field(default_factory=list)  # (role, label, usage)

    def record(self, role: str, spec: ModelSpec, usage: dict):
        self.spec_log.append((role, spec.label, usage))
        self.total_cost_usd += estimate_cost(spec, usage)


# ---------- planner ----------

PLANNER_SYSTEM = """You are a planning agent. Given a high-level task, break it into 3-7
concrete, ordered steps. Each step should be small enough that a focused coder can implement
it without further decomposition.

Output JSON only, in this format:
{"steps": ["step 1 description", "step 2 description", ...]}

Do not number the steps in the strings. Do not include code in the plan."""


def plan(task: str, plan_obj: Plan) -> list[Step]:
    spec = planner_spec()
    msgs = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": task},
    ]
    content, usage = chat(spec, msgs, temperature=0.0)
    plan_obj.record("planner", spec, usage)
    data = _parse_json(content)
    steps_raw = data.get("steps", []) if data else []
    return [Step(n=i + 1, description=s) for i, s in enumerate(steps_raw)]


# ---------- coder ----------

CODER_SYSTEM = """You are a focused coding agent. Implement exactly what the step asks,
nothing more. Output Python code in a single ```python block. No explanation outside the
code. Include only the code needed for THIS step — assume earlier steps have been done."""


def code(task: str, step: Step, prior_steps: list[Step], plan_obj: Plan) -> str:
    spec = coder_spec()
    context = "\n\n".join(f"Step {s.n} produced:\n```python\n{s.output}\n```"
                          for s in prior_steps if s.output)
    user = f"Overall task: {task}\n\n{context}\n\nNow implement step {step.n}: {step.description}"
    if step.feedback:
        user += f"\n\nPrior attempt was rejected. Critic feedback:\n{step.feedback}\nFix it."
    msgs = [
        {"role": "system", "content": CODER_SYSTEM},
        {"role": "user", "content": user},
    ]
    content, usage = chat(spec, msgs, temperature=0.2)
    plan_obj.record("coder", spec, usage)
    return _extract_code(content)


# ---------- critic ----------

CRITIC_SYSTEM = """You are a strict code reviewer. Given a step description and an
implementation, decide if the implementation actually does what the step asks.

Output JSON only:
{"verdict": "PASS"} or {"verdict": "FAIL", "reason": "one short sentence"}

Be brief. PASS for working code that does the step. FAIL for missing logic, wrong logic,
or code that doesn't match the step."""


def critique(step: Step, plan_obj: Plan) -> tuple[bool, str]:
    spec = critic_spec()
    user = f"Step: {step.description}\n\nImplementation:\n```python\n{step.output}\n```"
    msgs = [
        {"role": "system", "content": CRITIC_SYSTEM},
        {"role": "user", "content": user},
    ]
    content, usage = chat(spec, msgs, temperature=0.0)
    plan_obj.record("critic", spec, usage)
    data = _parse_json(content)
    if not data:
        return True, "(critic returned no JSON; passing by default)"
    verdict = data.get("verdict", "PASS").upper()
    return verdict == "PASS", data.get("reason", "")


# ---------- helpers ----------

def _parse_json(text: str) -> dict | None:
    fence = re.search(r"```(?:json)?\s*\n(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()
