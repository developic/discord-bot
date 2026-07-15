import json
import os
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "ai_data.json"


def _load() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_system_prompt(default: str) -> str:
    return _load().get("system_prompt", default)


def set_system_prompt(prompt: str):
    data = _load()
    data["system_prompt"] = prompt
    _save(data)


def get_rules() -> list[str]:
    return _load().get("rules", [])


def set_rules(rules: list[str]):
    data = _load()
    data["rules"] = rules
    _save(data)


def add_rule(rule: str):
    rules = get_rules()
    rules.append(rule)
    set_rules(rules)


def remove_rule(index: int) -> str | None:
    rules = get_rules()
    if not rules or index < 0 or index >= len(rules):
        return None
    removed = rules.pop(index)
    set_rules(rules)
    return removed


def get_tools_enabled() -> bool:
    return _load().get("tools_enabled", False)


def set_tools_enabled(enabled: bool):
    data = _load()
    data["tools_enabled"] = enabled
    _save(data)
