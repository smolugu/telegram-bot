import json
import os

CACHE_FILE = "state_cache.json"


def load_state():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(CACHE_FILE, "w") as f:
        json.dump(state, f)


def should_alert(stage_key: str):
    state = load_state()

    if state.get(stage_key):
        return False

    state[stage_key] = True
    save_state(state)
    return True


def reset_cycle():
    save_state({})
