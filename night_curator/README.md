# The Night Curator

The Night Curator is a **daily scheduled museum night-adventure generator** powered by configurable text and image model APIs. Every night it picks a world-class museum, turns the visit into a playful night-at-the-museum quest, teaches real cultural and historical knowledge along the way, and packages the result as an interactive story, quiz, comic image, and shareable HTML page.

Instead of producing a static museum note, Night Curator designs a small learning journey: a 9-panel adventure, checkpoint-style questions, answer explanations, a cinematic 3x3 comic, and an HTML experience that can be saved locally or delivered through Lark/Feishu. The fun part is the structure: discovery first, knowledge second, then quiz-based progression so each daily run feels like a tiny guided expedition.

Highlights:

- **Daily scheduled exploration**: install the scheduler once and wake up to a new museum quest every day.
- **World-famous museum rotation**: each run selects a museum stop and builds the story around its collection, setting, and educational angle.
- **Adventure + knowledge + quiz loop**: the generated experience mixes narrative exploration, concise explanations, and answerable checkpoints.
- **Visual storytelling**: configured model APIs create both the 9-panel content plan and a cinematic 3x3 comic image for the day's journey.
- **Shareable output**: each run writes local artifacts and can optionally send the Markdown summary, comic, and HTML through Lark/Feishu.
- **Configurable model APIs**: users choose OpenAI-compatible text and image endpoints through one local config file.

Users configure model API endpoints in `~/.night-curator/night-curator-config.json`. API keys are read from environment variables such as `OPENAI_API_KEY`; raw key values are not written to the config file.

## Quick Start

```bash
git clone https://github.com/pivoine-maker/night-curator.git
cd night-curator
python3 -m pip install -e .
export OPENAI_API_KEY=sk-...
night-curator-setup --skip-dry-run
night-curator-daily --no-send --summary-json
```

Generated files are written to `~/.night-curator/runs/YYYY-MM-DD/`.

## Requirements

- Python 3.10+
- Text model API compatible with `/v1/responses` JSON-schema output
- Image model API compatible with `/v1/responses` image generation or `/v1/images/generations`
- Optional: `lark-cli` if you want Lark/Feishu delivery

## Configure Model APIs

By default Night Curator calls OpenAI-compatible endpoints and reads keys from environment variables:

```bash
export OPENAI_API_KEY=sk-...
night-curator-setup --text-base-url https://api.openai.com/v1 --text-model gpt-4.1-mini --text-api-key-env OPENAI_API_KEY --image-base-url https://api.openai.com/v1 --image-model gpt-image-1 --image-api-key-env OPENAI_API_KEY --image-endpoint responses --skip-dry-run
```

The config file at `~/.night-curator/night-curator-config.json` stores model base URLs, model names, API-key environment variable names, agent description, and optional Lark target. It does not store raw API keys. For providers that expose the Images API instead of Responses image generation, set `--image-endpoint images`.
## Lark/Feishu Delivery

Lark/Feishu is optional. Without it, Night Curator only writes local files.

```bash
night-curator-setup \
  --enable-lark \
  --lark-open-id ou_xxx \
  --skip-dry-run
```

A real run sends a Markdown summary, the comic image, and the HTML file:

```bash
night-curator-daily
```

Use `--no-send` to generate files without sending.

## macOS launchd Schedule

Install a daily 00:00 Asia/Shanghai task:

```bash
night-curator-schedule install-launchd --hour 0 --minute 0
night-curator-schedule status
```

Uninstall it:

```bash
night-curator-schedule uninstall-launchd
```

Logs are written under `~/.night-curator/logs/`.

## Cross-Platform Scheduling

Cron example:

```cron
0 0 * * * NIGHT_CURATOR_HOME=$HOME/.night-curator /usr/bin/python3 -m night_curator.daily >> $HOME/.night-curator/logs/cron.out.log 2>> $HOME/.night-curator/logs/cron.err.log
```

systemd user service command:

```ini
[Service]
Type=oneshot
Environment=NIGHT_CURATOR_HOME=%h/.night-curator
ExecStart=/usr/bin/python3 -m night_curator.daily
```

Windows Task Scheduler action:

```powershell
python -m night_curator.daily
```

GitHub Actions can run the same command on a schedule if the runner has the configured model API key environment variables and any optional Lark credentials.

## How Generation Works

- `night-curator-daily` creates a run directory.
- Python builds prompts and JSON schema for the 9-panel content.
- The configured text model API writes the content JSON.
- The configured image model API creates `comic.png` in the run directory.
- Python validates the content, writes `data.js` and `index.html`, and optionally sends via Lark/Feishu.

## Development

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Security

Do not commit generated state, Lark credentials, raw API keys, or run output. Night Curator stores only API-key environment variable names; keep the actual key values in your shell, scheduler, or CI secrets.

## Files

- `night_curator/codex_runner.py`: model API prompts, requests, and legacy Codex helpers.
- `night_curator/daily.py`: daily generator/renderer/sender.
- `night_curator/setup.py`: configuration CLI.
- `night_curator/schedule.py`: scheduling CLI and launchd plist generation.
- `night_curator/config.py`: config defaults and secret-safe helpers.
- `night_curator/vintage-template.html`: interactive HTML template.
- `night_curator/museum_catalog.json`: museum selection catalog.
