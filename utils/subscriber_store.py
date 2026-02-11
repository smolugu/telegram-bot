import json
import os

SUBSCRIBERS_FILE = "subscribers.json"
UNSUBSCRIBED_FILE = "unsubscribed.json"


def _load(file_path: str) -> set:
    if not os.path.exists(file_path):
        return set()

    try:
        with open(file_path, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save(file_path: str, data: set):
    with open(file_path, "w") as f:
        json.dump(list(data), f, indent=2)


def load_subscribers() -> set:
    return _load(SUBSCRIBERS_FILE)


def save_subscribers(subscribers: set):
    _save(SUBSCRIBERS_FILE, subscribers)


def load_unsubscribed() -> set:
    return _load(UNSUBSCRIBED_FILE)


def save_unsubscribed(unsubscribed: set):
    _save(UNSUBSCRIBED_FILE, unsubscribed)
