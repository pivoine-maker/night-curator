#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
from .onboarding import DEFAULT_BASE_URL, DEFAULT_MODEL, choose_first_stop, generate_anchor_image, load_museums, save_project_config

PACKAGE_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get('NIGHT_CURATOR_HOME', Path.home() / '.night-curator'))
CONFIG_PATH = STATE_DIR / 'night-curator-config.json'
ASSETS = STATE_DIR / 'assets'
PLIST = Path.home() / 'Library' / 'LaunchAgents' / 'com.night-curator.daily.plist'

def ask(prompt, default=''):
    suffix = f' [{default}]' if default else ''
    value = input(f'{prompt}{suffix}: ').strip()
    return value or default

def existing_model_defaults():
    return {
        'api_key_env': 'AIDP_IMAGE_API_KEY' if os.environ.get('AIDP_IMAGE_API_KEY') else ('BYTEDANCE_GPT_MIDDLEWARE_API_KEY' if os.environ.get('BYTEDANCE_GPT_MIDDLEWARE_API_KEY') else 'OPENAI_API_KEY'),
        'model': os.environ.get('NIGHT_CURATOR_IMAGE_MODEL', DEFAULT_MODEL),
        'base_url': os.environ.get('NIGHT_CURATOR_IMAGE_BASE_URL', DEFAULT_BASE_URL),
        'header_key_env': 'AIDP_IMAGE_HEADER_KEY',
    }

def lark_status():
    try:
        r = subprocess.run(['lark-cli', 'auth', 'status', '--json'], text=True, capture_output=True, check=False)
        return json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}
    except Exception:
        return {}

def install_launchd():
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    logs = STATE_DIR / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.night-curator.daily</string>
<key>ProgramArguments</key><array><string>{python}</string><string>-m</string><string>night_curator.daily</string></array>
<key>StartCalendarInterval</key><dict><key>Hour</key><integer>0</integer><key>Minute</key><integer>0</integer></dict>
<key>StandardOutPath</key><string>{logs / 'daily.out.log'}</string>
<key>StandardErrorPath</key><string>{logs / 'daily.err.log'}</string>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>{os.environ.get('PATH','')}</string><key>TZ</key><string>Asia/Shanghai</string><key>NIGHT_CURATOR_HOME</key><string>{STATE_DIR}</string></dict>
</dict></plist>
'''
    PLIST.write_text(plist)
    subprocess.run(['launchctl', 'unload', str(PLIST)], text=True, capture_output=True)
    subprocess.run(['launchctl', 'load', str(PLIST)], check=True)
    return PLIST

def main():
    print('✦ The Night Curator setup ✦')
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    museums = load_museums(PACKAGE_DIR / 'museums.json')
    defaults = existing_model_defaults()
    print('\nImage model configuration. If Codex already exposes an image model env var, keep the defaults.')
    api_key_env = ask('Image API key environment variable', defaults['api_key_env'])
    header_key_env = ask('Image extra header api-key environment variable', defaults['header_key_env'])
    model = ask('Image model name', defaults['model'])
    base_url = ask('Image OpenAI-compatible base URL', defaults['base_url'])
    print('\nFirst museum stop. Type an id/name, or press Enter for deterministic random.')
    for item in museums:
        print(f"- {item['id']}: {item['museum']} ({item['city']})")
    first_stop_input = ask('First stop', 'surprise me')
    first_stop = choose_first_stop(museums, first_stop_input, seed=first_stop_input)
    print(f"Selected first stop: {first_stop['museum']}")
    print('\nAgent identity. Describe the recurring agent character, or press Enter for a random-ish default.')
    agent_description = ask('Agent description', 'a tiny brass owl-like AI curator with moon-white glowing eyes, velvet cape, antique gold satchel, and a moon-key badge')
    reference_images = []
    while True:
        ref = ask('Optional reference image path (Enter to skip)', '')
        if not ref:
            break
        reference_images.append(ref)
    status = lark_status()
    default_open_id = status.get('identities', {}).get('user', {}).get('openId', '')
    print('\nLark/Feishu bot delivery. Make sure lark-cli is configured and bot identity is ready.')
    if status:
        print('lark-cli status detected. Bot:', status.get('identities', {}).get('bot', {}).get('status'))
    lark_open_id = ask('Your open_id for this Lark app', default_open_id)
    config = save_project_config(CONFIG_PATH, image_api_key_env=api_key_env, image_header_key_env=header_key_env, image_model=model, image_base_url=base_url, first_stop_id=first_stop['id'], agent_description=agent_description, reference_images=reference_images, lark_open_id=lark_open_id)
    print(f'Config saved: {CONFIG_PATH}')
    if ask('Generate agent anchor image now? y/n', 'y').lower().startswith('y'):
        out = generate_anchor_image(config, ASSETS)
        print(f'Agent anchor image: {out}')
    if ask('Install daily 00:00 UTC+8 launchd task? y/n', 'y').lower().startswith('y'):
        plist = install_launchd()
        print(f'LaunchAgent installed: {plist}')
    if ask('Run a dry-run now? y/n', 'y').lower().startswith('y'):
        subprocess.run([sys.executable, '-m', 'night_curator.daily', '--dry-run'], check=False)
    print('\nSetup complete. Daily results will be written under:', STATE_DIR / 'runs')

if __name__ == '__main__':
    main()
