#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, random, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

PACKAGE_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get('NIGHT_CURATOR_HOME', Path(__file__).resolve().parent / '.night-curator'))
RUNS = STATE_DIR / 'runs'
MUSEUMS = json.loads((PACKAGE_DIR / 'museums.json').read_text())
MUSEUM_IDEAS = [
    {'museum':'Louvre Museum','city':'Paris','country':'France','artifact':'Winged Victory of Samothrace','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'British Museum','city':'London','country':'United Kingdom','artifact':'Rosetta Stone','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Palace Museum','city':'Beijing','country':'China','artifact':'Nine Dragon motifs','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'The Metropolitan Museum of Art','city':'New York','country':'United States','artifact':'Temple of Dendur','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Grand Egyptian Museum','city':'Giza','country':'Egypt','artifact':'Tutankhamun treasures','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Vatican Museums','city':'Vatican City','country':'Vatican City','artifact':'Gallery of Maps','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Uffizi Gallery','city':'Florence','country':'Italy','artifact':'Primavera','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Rijksmuseum','city':'Amsterdam','country':'Netherlands','artifact':'The Night Watch','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Museo Nacional de Antropología','city':'Mexico City','country':'Mexico','artifact':'Aztec Sun Stone','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Acropolis Museum','city':'Athens','country':'Greece','artifact':'Parthenon sculptures','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'Pergamon Museum','city':'Berlin','country':'Germany','artifact':'Ishtar Gate','next':'tomorrow’s museum','nextArtifact':'a new clue'},
    {'museum':'National Museum of Korea','city':'Seoul','country':'South Korea','artifact':'Goryeo celadon','next':'tomorrow’s museum','nextArtifact':'a new clue'},
]
PROJECT_CONFIG_PATH = STATE_DIR / 'night-curator-config.json'
ASSETS = STATE_DIR / 'assets'
OPEN_ID = os.environ.get('NIGHT_CURATOR_LARK_OPEN_ID', '')
AIDP_API_KEY = os.environ.get('AIDP_IMAGE_API_KEY') or os.environ.get('BYTEDANCE_GPT_MIDDLEWARE_API_KEY') or os.environ.get('OPENAI_API_KEY') or ''
AIDP_HEADER_KEY = os.environ.get('AIDP_IMAGE_HEADER_KEY', '')
IMAGE_BASE_URL = 'https://aidp.bytedance.net/api/modelhub/online/v2/crawl/openai'
TEXT_BASE_URL = os.environ.get('NIGHT_CURATOR_TEXT_BASE_URL', 'http://127.0.0.1:4002/v1')
TZ = timezone(timedelta(hours=8))

def load_project_config():
    if PROJECT_CONFIG_PATH.exists():
        return json.loads(PROJECT_CONFIG_PATH.read_text())
    return {}

def configured_open_id():
    config = load_project_config()
    return os.environ.get('NIGHT_CURATOR_LARK_OPEN_ID') or config.get('lark', {}).get('open_id') or OPEN_ID

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)

def choose_dynamic_museum(day, seed='night-curator'):
    digest = hashlib.sha256(f'{seed}:{day}'.encode()).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    pool = list(MUSEUM_IDEAS)
    rng.shuffle(pool)
    return dict(pool[0])

def choose_museum(run_date=None):
    now = datetime.fromisoformat(run_date).replace(tzinfo=TZ) if run_date else datetime.now(TZ)
    start = datetime(2026, 6, 22, tzinfo=TZ)
    day = max(0, (now.date() - start.date()).days)
    config = load_project_config()
    seed = config.get('agent', {}).get('description') or 'night-curator'
    return day, choose_dynamic_museum(day, seed=seed), now

def llm_json(day, item):
    if OpenAI is None:
        raise RuntimeError('The openai package is required for live text generation. Use --dry-run or install openai.')
    client = OpenAI(api_key=os.environ.get('NIGHT_CURATOR_TEXT_API_KEY', 'dummy'), base_url=TEXT_BASE_URL)
    prompt = f'''
You are The Night Curator, an educational museum adventure agent.
Create today's interactive 3x3 museum adventure content in Chinese.
Day index: {day+1}
Museum: {item['museum']} ({item['city']}, {item['country']})
Featured artifact/theme: {item['artifact']}
Today is a spontaneous one-night museum stop, not part of a prewritten fixed route.
Do not imply the route was planned long ago. The agent chose this museum tonight because it felt an unusual midnight signal.
Next museum clue: keep it mysterious and open-ended; do not promise a fixed next museum.
Return strict JSON only with this shape:
{{"title":"...","subtitle":"...","panels":[{{"t":"短标题","m":"英文知识标签","story":"120-180 Chinese chars rich adventure plot","note":"150-240 Chinese chars detailed history/archaeology/culture knowledge","q":"indirect higher-order question in Chinese","choices":["A","B","C"],"a":0,"why":"explanation in Chinese"}}]}}
Need exactly 9 panels. Correct answer index must vary across panels. Questions must require reasoning from the knowledge, not direct lookup. Include real historical/cultural knowledge and avoid hallucinated precise facts when uncertain.
'''.strip()
    resp = client.chat.completions.create(
        model=os.environ.get('NIGHT_CURATOR_TEXT_MODEL', 'bytedance-gpt-5.4'),
        messages=[{'role':'user','content':prompt}],
        temperature=0.8,
        extra_headers={'api-key': AIDP_HEADER_KEY},
    )
    text = resp.choices[0].message.content.strip()
    if text.startswith('```'):
        text = text[text.find('{'):text.rfind('}')+1]
    data = json.loads(text)
    if len(data.get('panels', [])) != 9:
        raise ValueError('panel count is not 9')
    return data

def fallback_content(day, item):
    panels=[]
    answers=[1,2,0,1,2,0,2,1,0]
    for i in range(9):
        panels.append({'t':f'第{i+1}格 · {item["artifact"]}','m':item['museum'],'story':f'今晚并没有预设路线。Agent 临时捕捉到来自{item["city"]}的午夜信号，于是抵达{item["museum"]}。第{i+1}个展厅里，{item["artifact"]}的影子开始移动，引导它寻找今晚的月光钥匙线索。','note':f'{item["museum"]}与{item["artifact"]}提供了理解当地历史、考古发现、收藏迁移和文化解释的入口。阅读时要关注地点、年代、材料、原始用途和今天的展示方式。','q':'哪一种阅读方式最接近博物馆学习？','choices':['只看画面是否好看','结合地点、用途、材料和展示语境理解文物','只记住英文名称'], 'a':answers[i], 'why':'正确。博物馆学习需要把文物放回历史和展示语境中。'})
    return {'title':f'The Night Curator · Day {day+1}: {item["museum"]}','subtitle':f'{item["city"]} · {item["artifact"]}', 'panels':panels}

def generate_image(day, item, content, out_dir):
    if OpenAI is None:
        raise RuntimeError('The openai package is required for live image generation. Use --dry-run/--no-send or install openai.')
    config = load_project_config()
    image_config = config.get('image', {})
    api_key_env = image_config.get('api_key_env', 'AIDP_IMAGE_API_KEY')
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f'Missing image API key. Set {api_key_env}.')
    base_url = image_config.get('base_url') or IMAGE_BASE_URL
    model = image_config.get('model') or 'gpt-image-2'
    header_key_env = image_config.get('header_key_env', 'AIDP_IMAGE_HEADER_KEY')
    header_key = os.environ.get(header_key_env, AIDP_HEADER_KEY)
    client = OpenAI(api_key=api_key, base_url=base_url)
    agent = config.get('agent', {})
    agent_description = agent.get('description', 'small nimble non-human AI agent explorer with satchel and tiny glowing eyes')
    anchor_path = ASSETS / agent.get('anchor_image', 'agent-anchor.png')
    anchor_hint = f' Use the established agent anchor image as identity reference: {anchor_path}.' if anchor_path.exists() else ''
    prompt = f"""Create one square 3x3 nine-panel comic page for The Night Curator. Museum: {item['museum']} in {item['city']}. Featured artifact/theme: {item['artifact']}. Style: dark cinematic graphic novel, midnight museum adventure, dramatic chiaroscuro, deep navy shadows, antique gold highlights, film grain, inked panel lines. Format: one square image, clear 3 by 3 comic grid, nine distinct panels, thin black gutters. No readable text, no speech bubbles, no logos, no watermark. Recurring character: {agent_description}.{anchor_hint}"""
    result = client.images.generate(model=model, prompt=prompt, size='1024x1024', quality='medium', extra_headers={'api-key': header_key})
    item0 = result.data[0]
    out = out_dir / 'comic.png'
    if getattr(item0, 'b64_json', None):
        out.write_bytes(base64.b64decode(item0.b64_json))
    elif getattr(item0, 'url', None):
        import urllib.request
        out.write_bytes(urllib.request.urlopen(item0.url, timeout=120).read())
    else:
        raise RuntimeError('No image payload')
    return out

def write_html(content, out_dir, day, item):
    (out_dir / 'data.js').write_text('const panels = ' + json.dumps(content['panels'], ensure_ascii=False, indent=2) + ';\n')
    title = content.get('title', f'The Night Curator · Day {day+1}')
    subtitle = content.get('subtitle', '点击九宫格图片进入今日博物馆探险。')
    day_label = f'Day {day+1} · {item["museum"]}'
    template = (PACKAGE_DIR / 'vintage-template.html').read_text()
    html = (template
        .replace('{{TITLE}}', title)
        .replace('{{SUBTITLE}}', subtitle)
        .replace('{{DAY_LABEL}}', day_label))
    (out_dir / 'index.html').write_text(html)
    return out_dir / 'index.html'

def push_lark(content, out_dir, image_path, html_path, dry_run=False):
    md = f"""🌙 **The Night Curator 今日已出发**

**{content['title']}**

{content.get('subtitle','')}

- 漫画：`{image_path}`
- 交互 HTML：`{html_path}`

请在电脑上打开 HTML 体验九宫格闯关。"""
    if dry_run:
        print(md)
        return None
    rel_img = image_path.name
    rel_html = html_path.name
    open_id = configured_open_id()
    if not open_id:
        raise RuntimeError('Missing Lark open_id. Run night-curator-setup first.')
    r1 = run(['lark-cli','im','+messages-send','--as','bot','--user-id',open_id,'--markdown',md,'--json'], cwd=out_dir)
    print(r1.stdout or r1.stderr)
    r2 = run(['lark-cli','im','+messages-send','--as','bot','--user-id',open_id,'--image',rel_img,'--json'], cwd=out_dir)
    print(r2.stdout or r2.stderr)
    r3 = run(['lark-cli','im','+messages-send','--as','bot','--user-id',open_id,'--file',rel_html,'--json'], cwd=out_dir)
    print(r3.stdout or r3.stderr)


def load_content_json(path):
    data = json.loads(Path(path).read_text())
    panels = data.get('panels')
    if not isinstance(panels, list) or len(panels) != 9:
        raise ValueError('content JSON must contain exactly 9 panels')
    required = {'t', 'm', 'story', 'note', 'q', 'choices', 'a', 'why'}
    for index, panel in enumerate(panels, 1):
        missing = sorted(required - set(panel))
        if missing:
            raise ValueError(f'panel {index} missing fields: {", ".join(missing)}')
        if not isinstance(panel.get('choices'), list) or len(panel['choices']) != 3:
            raise ValueError(f'panel {index} choices must contain exactly 3 items')
        if panel.get('a') not in (0, 1, 2):
            raise ValueError(f'panel {index} answer index must be 0, 1, or 2')
    data.setdefault('title', 'The Night Curator')
    data.setdefault('subtitle', 'Codex-generated museum adventure')
    return data

def parse_args():
    parser = argparse.ArgumentParser(description='Run The Night Curator daily adventure.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--no-send', action='store_true')
    parser.add_argument('--summary-json', action='store_true')
    parser.add_argument('--date', default='')
    parser.add_argument('--content-json', default='', help='Path to Codex-generated content JSON to render instead of calling a model.')
    return parser.parse_args()


def main():
    args = parse_args()
    day, item, now = choose_museum(args.date or None)
    out_dir = RUNS / now.strftime('%Y-%m-%d')
    out_dir.mkdir(parents=True, exist_ok=True)
    force_fallback = os.environ.get('NIGHT_CURATOR_FORCE_FALLBACK') == '1'
    content_source = 'codex_json' if args.content_json else ('fallback' if force_fallback or args.dry_run else 'model')
    try:
        if args.content_json:
            content = load_content_json(args.content_json)
        else:
            content = fallback_content(day, item) if force_fallback or args.dry_run else llm_json(day, item)
    except Exception as e:
        if args.content_json:
            raise
        print('LLM content failed, fallback:', repr(e), file=sys.stderr)
        content = fallback_content(day, item)
        content_source = 'fallback'
    (out_dir / 'content.json').write_text(json.dumps(content, ensure_ascii=False, indent=2))
    image_path = out_dir / 'comic.png'
    image_source = 'placeholder'
    if args.dry_run or force_fallback:
        image_path.write_bytes(b'')
    else:
        image_path = generate_image(day, item, content, out_dir)
        image_source = 'python_image_api'
    html_path = write_html(content, out_dir, day, item)
    sent = False
    if not args.no_send:
        push_lark(content, out_dir, image_path, html_path, dry_run=args.dry_run)
        sent = not args.dry_run
    summary = {
        'date': now.strftime('%Y-%m-%d'),
        'day': day + 1,
        'museum': item['museum'],
        'title': content['title'],
        'output_dir': str(out_dir),
        'image_path': str(image_path),
        'html_path': str(html_path),
        'dry_run': args.dry_run,
        'sent': sent,
        'content_source': content_source,
        'image_source': image_source,
    }
    if args.summary_json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"DONE {out_dir}")

if __name__ == '__main__':
    main()
