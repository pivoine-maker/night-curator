#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from .config import DEFAULT_AGENT, DEFAULT_CODEX, DEFAULT_MODELS, default_state_dir, save_config
    from .onboarding import choose_first_stop, load_museums
except ImportError:
    from config import DEFAULT_AGENT, DEFAULT_CODEX, DEFAULT_MODELS, default_state_dir, save_config
    from onboarding import choose_first_stop, load_museums

PACKAGE_DIR = Path(__file__).resolve().parent
STATE_DIR = default_state_dir()
CONFIG_PATH = STATE_DIR / "night-curator-config.json"
AUTOMATION_PROMPT = PACKAGE_DIR / "codex-automation-prompt.md"


def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def lark_status():
    try:
        result = subprocess.run(["lark-cli", "auth", "status", "--json"], text=True, capture_output=True, check=False)
        return json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
    except Exception:
        return {}


def automation_prompt_text(config_path=None):
    state_dir = Path(config_path).expanduser().resolve().parent if config_path else default_state_dir()
    command = f"NIGHT_CURATOR_HOME={state_dir} {sys.executable} -m night_curator.daily --summary-json"
    if AUTOMATION_PROMPT.exists():
        return AUTOMATION_PROMPT.read_text().replace("{{PROJECT_DIR}}", str(PACKAGE_DIR)).replace("{{STATE_DIR}}", str(state_dir)).replace("{{DAILY_COMMAND}}", command)
    return f"# Codex Automation Prompt\n\nState directory: `{state_dir}`\nCommand: `{command}`\n"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Configure The Night Curator.")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--museums", default=str(PACKAGE_DIR / "museums.json"))
    parser.add_argument("--codex-bin", default=DEFAULT_CODEX["bin"])
    parser.add_argument("--codex-profile", default=DEFAULT_CODEX["profile"])
    parser.add_argument("--codex-model", default=DEFAULT_CODEX["model"])
    parser.add_argument("--text-base-url", default=DEFAULT_MODELS["text"]["base_url"])
    parser.add_argument("--text-api-key-env", default=DEFAULT_MODELS["text"]["api_key_env"])
    parser.add_argument("--text-model", default=DEFAULT_MODELS["text"]["model"])
    parser.add_argument("--image-base-url", default=DEFAULT_MODELS["image"]["base_url"])
    parser.add_argument("--image-api-key-env", default=DEFAULT_MODELS["image"]["api_key_env"])
    parser.add_argument("--image-model", default=DEFAULT_MODELS["image"]["model"])
    parser.add_argument("--image-size", default=DEFAULT_MODELS["image"]["size"])
    parser.add_argument("--image-endpoint", choices=["responses", "images"], default=DEFAULT_MODELS["image"]["endpoint"])
    parser.add_argument("--first-stop", default="surprise me")
    parser.add_argument("--agent-description", default=DEFAULT_AGENT["description"])
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument("--enable-lark", action="store_true")
    parser.add_argument("--lark-open-id", default="")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--skip-dry-run", action="store_true")
    parser.add_argument("--print-automation-prompt", action="store_true")
    return parser.parse_args(argv)


def apply_interactive(args):
    print("✦ The Night Curator setup ✦")
    args.text_base_url = ask("Text model API base URL", args.text_base_url)
    args.text_api_key_env = ask("Text model API key env var", args.text_api_key_env)
    args.text_model = ask("Text model", args.text_model)
    args.image_base_url = ask("Image model API base URL", args.image_base_url)
    args.image_api_key_env = ask("Image model API key env var", args.image_api_key_env)
    args.image_model = ask("Image model", args.image_model)
    args.image_size = ask("Image size", args.image_size)
    args.first_stop = ask("First museum stop id/name", args.first_stop)
    args.agent_description = ask("Agent description", args.agent_description)
    use_lark = ask("Enable Lark/Feishu delivery? yes/no", "no").lower() in {"y", "yes"}
    args.enable_lark = use_lark
    if use_lark:
        status = lark_status()
        default_open_id = status.get("identities", {}).get("user", {}).get("openId", args.lark_open_id)
        args.lark_open_id = ask("Your Lark/Feishu open_id", default_open_id)
    return args


def config_from_args(args, first_stop):
    return {
        "codex": {"bin": args.codex_bin, "profile": args.codex_profile, "model": args.codex_model},
        "models": {
            "text": {"base_url": args.text_base_url, "api_key_env": args.text_api_key_env, "model": args.text_model, "temperature": DEFAULT_MODELS["text"]["temperature"]},
            "image": {"base_url": args.image_base_url, "api_key_env": args.image_api_key_env, "model": args.image_model, "size": args.image_size, "endpoint": args.image_endpoint},
        },
        "agent": {"first_stop_id": first_stop["id"], "description": args.agent_description, "reference_images": args.reference_image, "anchor_image": DEFAULT_AGENT["anchor_image"]},
        "lark": {"enabled": bool(args.enable_lark), "open_id": args.lark_open_id if args.enable_lark else ""},
    }


def main(argv=None):
    args = parse_args(argv)
    if args.print_automation_prompt:
        print(automation_prompt_text(args.config))
        return 0
    if args.interactive:
        args = apply_interactive(args)

    state_dir = Path(args.config).resolve().parent
    state_dir.mkdir(parents=True, exist_ok=True)
    museums = load_museums(args.museums)
    first_stop = choose_first_stop(museums, args.first_stop, seed=args.agent_description)
    config = save_config(args.config, config_from_args(args, first_stop))
    print(json.dumps({"config": str(Path(args.config).resolve()), "state_dir": str(state_dir), "first_stop": first_stop}, ensure_ascii=False, indent=2))

    if not args.skip_dry_run:
        result = subprocess.run([sys.executable, "-m", "night_curator.daily", "--dry-run", "--no-send", "--summary-json"], text=True, capture_output=True, check=False, env={**os.environ, "NIGHT_CURATOR_HOME": str(state_dir)})
        print(result.stdout, end="")
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr, end="")
            return result.returncode

    print(f"Automation prompt ready: {AUTOMATION_PROMPT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
