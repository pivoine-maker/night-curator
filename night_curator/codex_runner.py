import json
import subprocess
import sys
from pathlib import Path

CONTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "subtitle", "panels"],
    "properties": {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "panels": {
            "type": "array",
            "minItems": 9,
            "maxItems": 9,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["t", "m", "story", "note", "q", "choices", "a", "why"],
                "properties": {
                    "t": {"type": "string"},
                    "m": {"type": "string"},
                    "story": {"type": "string"},
                    "note": {"type": "string"},
                    "q": {"type": "string"},
                    "choices": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "string"}},
                    "a": {"type": "integer", "minimum": 0, "maximum": 2},
                    "why": {"type": "string"},
                },
            },
        },
    },
}


def codex_settings(config):
    return (config or {}).get("codex", {})


def build_codex_command(prompt, output_last_message=None, output_schema=None, codex_bin="codex", profile="", model="", cwd=None):
    command = [codex_bin, "exec", "--sandbox", "workspace-write", "--ask-for-approval", "never"]
    if cwd:
        command.extend(["--cd", str(cwd)])
    if profile:
        command.extend(["--profile", profile])
    if model:
        command.extend(["--model", model])
    if output_schema:
        command.extend(["--output-schema", str(output_schema)])
    if output_last_message:
        command.extend(["--output-last-message", str(output_last_message)])
    command.append(prompt)
    return command


def run_codex(prompt, out_dir, config, output_last_message=None, output_schema=None):
    settings = codex_settings(config)
    command = build_codex_command(
        prompt=prompt,
        output_last_message=output_last_message,
        output_schema=output_schema,
        codex_bin=settings.get("bin", "codex"),
        profile=settings.get("profile", ""),
        model=settings.get("model", ""),
        cwd=out_dir,
    )
    result = subprocess.run(command, text=True, capture_output=True, check=False, cwd=out_dir)
    if result.returncode != 0:
        raise RuntimeError(f"Codex CLI failed with exit {result.returncode}: {result.stderr or result.stdout}")
    return result


def content_prompt(item):
    return f"""Create today's Night Curator museum adventure as strict JSON only.
Museum: {item['museum']}
City: {item['city']}
Artifact/theme: {item['artifact']}

Return exactly 9 panels. Each panel must include:
- t: short Chinese title
- m: English knowledge label
- story: 120-180 Chinese characters of adventure plot
- note: 150-240 Chinese characters of real historical/cultural knowledge
- q: indirect reasoning question in Chinese
- choices: exactly 3 answer choices
- a: correct answer index 0, 1, or 2
- why: Chinese explanation

Use real museum/culture knowledge and avoid unsupported precise claims.
Output JSON only, no Markdown fences.
"""


def image_prompt(item, content, image_path, agent_description=""):
    return f"""Generate one square 3x3 comic image for The Night Curator and save it exactly at:
{image_path}

Museum: {item['museum']} in {item['city']}
Artifact/theme: {item['artifact']}
Title: {content.get('title', 'The Night Curator')}
Recurring character: {agent_description or 'small non-human AI curator explorer with a satchel and glowing eyes'}

Style: dark cinematic graphic novel, midnight museum adventure, dramatic chiaroscuro, deep navy shadows, antique gold highlights, film grain, inked panel lines. Format: one square image, clear 3 by 3 comic grid, nine distinct panels, thin black gutters. No readable text, no speech bubbles, no logos, no watermark.

You must create the image file. Do not only describe it.
"""


def generate_content_with_codex(item, out_dir, config):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    schema_path = out_dir / "content.schema.json"
    message_path = out_dir / "codex-content-message.txt"
    schema_path.write_text(json.dumps(CONTENT_SCHEMA, ensure_ascii=False, indent=2))
    run_codex(content_prompt(item), out_dir, config, output_last_message=message_path, output_schema=schema_path)
    return json.loads(message_path.read_text())


def generate_image_with_codex(item, content, out_dir, config):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / "comic.png"
    message_path = out_dir / "codex-image-message.txt"
    agent_description = (config or {}).get("agent", {}).get("description", "")
    run_codex(image_prompt(item, content, image_path, agent_description), out_dir, config, output_last_message=message_path)
    if not image_path.exists() or image_path.stat().st_size == 0:
        raise RuntimeError(f"Codex CLI did not create image file: {image_path}")
    return image_path
