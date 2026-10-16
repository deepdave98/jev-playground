"""Render Jev questions for Claude and normalize its answers for shared scoring."""

from common.jev import levels


def render(questions):
    lines = []
    for name, q in questions.items():
        if q["type"] == "noul":
            lines.append(f"{name}: a probability from 0 to 1. {q['instructions']}")
            for side in ("true", "false"):
                if q.get("criteria", {}).get(side):
                    lines.append(f"  {side} when: {q['criteria'][side]}")
        elif q["type"] == "choice":
            lines.append(f"{name}: one of {', '.join(q['criteria'])}. {q['instructions']}")
            lines += [f"  {k}: {v}" for k, v in q["criteria"].items()]
        else:
            lines.append(f"{name}: one of {', '.join(levels(q))}. {q['instructions']}")
            lines += [f"  {c}" for c in q["criteria"]]
        lines.append("")
    return "\n".join(lines).rstrip()


def answer_shape(questions):
    """The JSON Claude is asked to return, one key per question."""
    keys = [f'"{n}": 0.0' if q["type"] == "noul" else f'"{n}": "..."' for n, q in questions.items()]
    return "{" + ", ".join(keys) + "}"


def pick(value, allowed):
    """Normalize label formatting; reject missing or unknown answers."""
    if not isinstance(value, str):
        raise ValueError("label must be a string")
    v = value.strip().lower().replace(" ", "_").replace("-", "_")
    if not v or v not in allowed:
        raise ValueError(f"unknown label: {value!r}")
    return v


def read(obj, questions):
    out = {}
    for name, q in questions.items():
        v = obj.get(name)
        if q["type"] == "noul":
            out[name] = float(v)
        elif q["type"] == "choice":
            out[name] = pick(v, list(q["criteria"]))
        else:
            out[name] = pick(v, levels(q))
    return out
