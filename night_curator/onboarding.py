#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, random
from pathlib import Path
from openai import OpenAI

DEFAULT_BASE_URL = 'https://aidp.bytedance.net/api/modelhub/online/v2/crawl/openai'
DEFAULT_MODEL = 'gpt-image-2'
DEFAULT_HEADER_KEY_ENV = 'AIDP_IMAGE_HEADER_KEY'
DEFAULT_API_KEY_ENV = 'AIDP_IMAGE_API_KEY'
DEFAULT_HEADER_KEY = ''
PACKAGE_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get('NIGHT_CURATOR_HOME', Path.home() / '.night-curator'))


def save_project_config(config_path, *, image_api_key_env, image_model, image_base_url, first_stop_id, agent_description, reference_images=None, image_header_key_env=DEFAULT_HEADER_KEY_ENV, lark_open_id=''):
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'image': {'api_key_env': image_api_key_env, 'header_key_env': image_header_key_env, 'model': image_model, 'base_url': image_base_url},
        'journey': {'first_stop_id': first_stop_id},
        'agent': {'description': agent_description, 'reference_images': reference_images or [], 'anchor_image': 'agent-anchor.png'},
        'lark': {'open_id': lark_open_id},
    }
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data


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

def _write_image_from_result(result, out_path):
    item = result.data[0]
    if getattr(item, 'b64_json', None):
        out_path.write_bytes(base64.b64decode(item.b64_json))
    elif getattr(item, 'url', None):
        import urllib.request
        out_path.write_bytes(urllib.request.urlopen(item.url, timeout=120).read())
    else:
        raise RuntimeError('No image payload')


def generate_anchor_image(config, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get(config['image']['api_key_env']) or os.environ.get('BYTEDANCE_GPT_MIDDLEWARE_API_KEY') or os.environ.get('OPENAI_API_KEY') or 'dummy'
    header_key = os.environ.get(config['image'].get('header_key_env', DEFAULT_HEADER_KEY_ENV), DEFAULT_HEADER_KEY)
    client = OpenAI(api_key=api_key, base_url=config['image']['base_url'])
    prompt = build_anchor_prompt(config['agent']['description'], bool(config['agent'].get('reference_images')))
    kwargs = {'model': config['image']['model'], 'prompt': prompt, 'size': '1024x1024', 'quality': 'medium', 'extra_headers': {'api-key': header_key}}
    result = client.images.generate(**kwargs)
    out = output_dir / config['agent'].get('anchor_image', 'agent-anchor.png')
    _write_image_from_result(result, out)
    (output_dir / 'agent-anchor-prompt.txt').write_text(prompt)
    return out


def load_museums(path):
    museums = json.loads(Path(path).read_text())
    for i, item in enumerate(museums):
        item.setdefault('id', item.get('museum', f'museum-{i}').lower().replace(' ', '-'))
    return museums


def main():
    parser = argparse.ArgumentParser(description='Configure The Night Curator and generate an Agent anchor image.')
    parser.add_argument('--config', default=str(STATE_DIR / 'night-curator-config.json'))
    parser.add_argument('--museums', default=str(PACKAGE_DIR / 'museums.json'))
    parser.add_argument('--output-dir', default=str(STATE_DIR / 'assets'))
    parser.add_argument('--image-api-key-env', default=DEFAULT_API_KEY_ENV)
    parser.add_argument('--image-header-key-env', default=DEFAULT_HEADER_KEY_ENV)
    parser.add_argument('--image-model', default=DEFAULT_MODEL)
    parser.add_argument('--image-base-url', default=DEFAULT_BASE_URL)
    parser.add_argument('--first-stop', default='surprise me')
    parser.add_argument('--agent-description', required=True)
    parser.add_argument('--reference-image', action='append', default=[])
    parser.add_argument('--lark-open-id', default='')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    museums = load_museums(args.museums)
    stop = choose_first_stop(museums, args.first_stop, seed=args.agent_description)
    config = save_project_config(args.config, image_api_key_env=args.image_api_key_env, image_header_key_env=args.image_header_key_env, image_model=args.image_model, image_base_url=args.image_base_url, first_stop_id=stop['id'], agent_description=args.agent_description, reference_images=args.reference_image, lark_open_id=args.lark_open_id)
    print(json.dumps({'config': args.config, 'first_stop': stop, 'dry_run': args.dry_run}, ensure_ascii=False, indent=2))
    if not args.dry_run:
        out = generate_anchor_image(config, args.output_dir)
        print(f'anchor_image={out}')

if __name__ == '__main__':
    main()
