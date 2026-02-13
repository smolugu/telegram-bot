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


def update_active_window(window_key):
    state = load_state()

    if state.get("active_window") != window_key:
        # Reset all flags for new window
        state = {
            "active_window": window_key,
            "flags": {}
        }
        save_state(state)

    return state


def should_alert(stage_key):
    state = load_state()

    if stage_key in state.get("flags", {}):
        return False

    state["flags"][stage_key] = True
    save_state(state)
    return True
