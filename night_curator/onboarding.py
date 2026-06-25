#!/usr/bin/env python3
import argparse
import hashlib
import json
import random
from pathlib import Path

try:
    from .config import DEFAULT_AGENT, DEFAULT_CODEX, default_state_dir, save_config
except ImportError:
    from config import DEFAULT_AGENT, DEFAULT_CODEX, default_state_dir, save_config

PACKAGE_DIR = Path(__file__).resolve().parent
STATE_DIR = default_state_dir()


def save_project_config(config_path, *, first_stop_id, agent_description, reference_images=None, lark_open_id='', codex_bin='codex', codex_profile='', codex_model='', **_ignored):
    data = {
        'codex': {'bin': codex_bin, 'profile': codex_profile, 'model': codex_model},
        'agent': {'description': agent_description, 'reference_images': reference_images or [], 'anchor_image': DEFAULT_AGENT['anchor_image'], 'first_stop_id': first_stop_id},
        'lark': {'enabled': bool(lark_open_id), 'open_id': lark_open_id},
    }
    return save_config(config_path, data)


def choose_first_stop(museums, requested, seed=None):
    if not museums:
        raise ValueError('museum list is empty')
    requested_norm = (requested or '').strip().lower()
    for item in museums:
        if requested_norm in {str(item.get('id', '')).lower(), str(item.get('museum', '')).lower()}:
            return item
    rng_seed = seed if seed is not None else requested_norm or 'night-curator'
    digest = hashlib.sha256(rng_seed.encode()).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    return museums[rng.randrange(len(museums))]


def build_anchor_prompt(agent_description, has_reference=False):
    reference_policy = 'preserve the reference identity, silhouette, key colors, and distinctive accessories while adapting it to the requested style.' if has_reference else 'invent a consistent original identity from the description.'
    return f'''Create a character anchor sheet for The Night Curator agent.
User description: {agent_description}
Style: dark cinematic graphic novel, vintage museum explorer, antique gold accents, moon-white glowing eyes, deep navy shadows, elegant but adventurous.
Character requirements: small non-human AI curator explorer, readable full-body design, front view, side view, three-quarter view, expression/eye variants, satchel or curator bag, moon-key badge, small scanning lantern.
Reference policy: {reference_policy}
Output: one clean character anchor sheet, no random text, no logo, no watermark, neutral dark parchment background.'''.strip()


def load_museums(path):
    museums = json.loads(Path(path).read_text())
    for i, item in enumerate(museums):
        item.setdefault('id', item.get('museum', f'museum-{i}').lower().replace(' ', '-'))
    return museums


def main(argv=None):
    parser = argparse.ArgumentParser(description='Configure The Night Curator for Codex CLI generation.')
    parser.add_argument('--config', default=str(STATE_DIR / 'night-curator-config.json'))
    parser.add_argument('--museums', default=str(PACKAGE_DIR / 'museums.json'))
    parser.add_argument('--codex-bin', default=DEFAULT_CODEX['bin'])
    parser.add_argument('--codex-profile', default=DEFAULT_CODEX['profile'])
    parser.add_argument('--codex-model', default=DEFAULT_CODEX['model'])
    parser.add_argument('--first-stop', default='surprise me')
    parser.add_argument('--agent-description', default=DEFAULT_AGENT['description'])
    parser.add_argument('--reference-image', action='append', default=[])
    parser.add_argument('--lark-open-id', default='')
    args = parser.parse_args(argv)
    museums = load_museums(args.museums)
    stop = choose_first_stop(museums, args.first_stop, seed=args.agent_description)
    save_project_config(args.config, first_stop_id=stop['id'], agent_description=args.agent_description, reference_images=args.reference_image, lark_open_id=args.lark_open_id, codex_bin=args.codex_bin, codex_profile=args.codex_profile, codex_model=args.codex_model)
    print(json.dumps({'config': args.config, 'first_stop': stop}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
