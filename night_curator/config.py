import copy
import json
import os
from pathlib import Path

DEFAULT_CODEX = {
    "bin": "codex",
    "profile": "",
    "model": "",
}

DEFAULT_MODELS = {
    "text": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4.1-mini",
        "temperature": 0.7,
    },
    "image": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-image-1",
        "size": "1024x1024",
        "endpoint": "responses",
    },
}

DEFAULT_AGENT = {
    "description": "a tiny brass owl-like AI curator with moon-white glowing eyes, velvet cape, antique gold satchel, and a moon-key badge",
    "first_stop_id": "",
    "reference_images": [],
    "anchor_image": "agent-anchor.png",
}

DEFAULT_LARK = {
    "enabled": False,
    "open_id": "",
}

SECRET_KEYS = {"api_key", "header_key", "secret", "token", "password"}


def default_state_dir():
    return Path(os.environ.get("NIGHT_CURATOR_HOME", Path.home() / ".night-curator")).expanduser()


def default_config():
    return {
        "codex": copy.deepcopy(DEFAULT_CODEX),
        "models": copy.deepcopy(DEFAULT_MODELS),
        "agent": copy.deepcopy(DEFAULT_AGENT),
        "lark": copy.deepcopy(DEFAULT_LARK),
    }


def deep_merge(base, override):
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def scrub_secrets(value):
    if isinstance(value, dict):
        return {key: scrub_secrets(child) for key, child in value.items() if key not in SECRET_KEYS}
    if isinstance(value, list):
        return [scrub_secrets(item) for item in value]
    return value


def load_config(path=None):
    config_path = Path(path).expanduser() if path else default_state_dir() / "night-curator-config.json"
    if not config_path.exists():
        return default_config()
    return deep_merge(default_config(), json.loads(config_path.read_text()))


def save_config(path, config):
    config_path = Path(path).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    safe = deep_merge(default_config(), scrub_secrets(config))
    config_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n")
    return safe
