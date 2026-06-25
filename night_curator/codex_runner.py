import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
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


def model_settings(config, kind):
    return (config or {}).get("models", {}).get(kind, {})


def join_url(base_url, suffix):
    return f"{str(base_url).rstrip('/')}/{suffix.lstrip('/')}"


def api_key(settings):
    env_name = settings.get("api_key_env") or "OPENAI_API_KEY"
    value = os.environ.get(env_name, "")
    if not value:
        raise RuntimeError(f"Missing model API key. Set environment variable {env_name} or update api_key_env in config.")
    return value


def post_json(url, payload, settings):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Authorization": f"Bearer {api_key(settings)}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=float(settings.get("timeout", 180))) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API failed with HTTP {exc.code}: {body}") from exc


def build_json_request(settings, prompt):
    payload = {
        "model": settings.get("model", "gpt-4.1-mini"),
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "night_curator_content",
                "schema": CONTENT_SCHEMA,
                "strict": True,
            }
        },
    }
    if "temperature" in settings:
        payload["temperature"] = settings["temperature"]
    return {"url": join_url(settings.get("base_url", "https://api.openai.com/v1"), "responses"), "payload": payload}


def build_image_request(settings, prompt):
    endpoint = settings.get("endpoint", "responses")
    base_url = settings.get("base_url", "https://api.openai.com/v1")
    if endpoint == "images":
        return {
            "url": join_url(base_url, "images/generations"),
            "payload": {"model": settings.get("model", "gpt-image-1"), "prompt": prompt, "size": settings.get("size", "1024x1024")},
        }
    return {
        "url": join_url(base_url, "responses"),
        "payload": {
            "model": settings.get("model", "gpt-image-1"),
            "input": prompt,
            "tools": [{"type": "image_generation", "size": settings.get("size", "1024x1024")}],
        },
    }


def response_text(response):
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    texts = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                texts.append(content["text"])
    if texts:
        return "\n".join(texts)
    raise RuntimeError("Model API response did not include text output")


def response_image_bytes(response):
    for item in response.get("data", []):
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
    for item in response.get("output", []):
        if item.get("type") == "image_generation_call" and item.get("result"):
            return base64.b64decode(item["result"])
        for content in item.get("content", []):
            if content.get("b64_json"):
                return base64.b64decode(content["b64_json"])
            if content.get("image_base64"):
                return base64.b64decode(content["image_base64"])
    raise RuntimeError("Model API response did not include base64 image data")


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


def image_prompt(item, content, image_path=None, agent_description=""):
    target = f" and save it exactly at:\n{image_path}\n" if image_path else "."
    return f"""Generate one square 3x3 comic image for The Night Curator{target}
Museum: {item['museum']} in {item['city']}
Artifact/theme: {item['artifact']}
Title: {content.get('title', 'The Night Curator')}
Recurring character: {agent_description or 'small non-human AI curator explorer with a satchel and glowing eyes'}

Style: dark cinematic graphic novel, midnight museum adventure, dramatic chiaroscuro, deep navy shadows, antique gold highlights, film grain, inked panel lines. Format: one square image, clear 3 by 3 comic grid, nine distinct panels, thin black gutters. No readable text, no speech bubbles, no logos, no watermark.
"""


def generate_content_with_api(item, out_dir, config):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    settings = model_settings(config, "text")
    request = build_json_request(settings, content_prompt(item))
    response = post_json(request["url"], request["payload"], settings)
    content = json.loads(response_text(response))
    (out_dir / "content-api-response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2))
    return content


def generate_image_with_api(item, content, out_dir, config):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / "comic.png"
    settings = model_settings(config, "image")
    agent_description = (config or {}).get("agent", {}).get("description", "")
    request = build_image_request(settings, image_prompt(item, content, None, agent_description))
    response = post_json(request["url"], request["payload"], settings)
    image_path.write_bytes(response_image_bytes(response))
    return image_path


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


def generate_content(item, out_dir, config):
    return generate_content_with_api(item, out_dir, config)


def generate_image(item, content, out_dir, config):
    return generate_image_with_api(item, content, out_dir, config)


if __name__ == "__main__":
    print("This module is used by night_curator.daily", file=sys.stderr)
