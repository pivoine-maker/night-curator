# The Night Curator

The Night Curator is a **daily scheduled museum night-adventure generator** powered by the Codex CLI. Every night it picks a world-class museum, turns the visit into a playful night-at-the-museum quest, teaches real cultural and historical knowledge along the way, and packages the result as an interactive story, quiz, comic image, and shareable HTML page.

Instead of producing a static museum note, Night Curator designs a small learning journey: a 9-panel adventure, checkpoint-style questions, answer explanations, a cinematic 3x3 comic, and an HTML experience that can be saved locally or delivered through Lark/Feishu. The fun part is the structure: discovery first, knowledge second, then quiz-based progression so each daily run feels like a tiny guided expedition.

Highlights:

- **Daily scheduled exploration**: install the scheduler once and wake up to a new museum quest every day.
- **World-famous museum rotation**: each run selects a museum stop and builds the story around its collection, setting, and educational angle.
- **Adventure + knowledge + quiz loop**: the generated experience mixes narrative exploration, concise explanations, and answerable checkpoints.
- **Visual storytelling**: Codex creates both the 9-panel content plan and a cinematic 3x3 comic image for the day's journey.
- **Shareable output**: each run writes local artifacts and can optionally send the Markdown summary, comic, and HTML through Lark/Feishu.
- **CLI-native design**: users only log in to `codex`; there is no separate text-model or image-model provider setup.

Users do **not** configure separate text or image model providers. Install and log in to `codex`; Night Curator delegates creation to the model configured in your Codex CLI.

## Quick Start

```bash
git clone https://github.com/pivoine-maker/night-curator.git
cd night-curator
python3 -m pip install -e .
codex login
night-curator-setup --skip-dry-run
night-curator-daily --no-send --summary-json
```

Generated files are written to `~/.night-curator/runs/YYYY-MM-DD/`.

## Requirements

- Python 3.10+
- Codex CLI installed and authenticated
- A Codex model/session capable of writing files and generating images
- Optional: `lark-cli` if you want Lark/Feishu delivery

## Configure Codex CLI

By default Night Curator runs:

```bash
codex exec --sandbox workspace-write --ask-for-approval never ...
```

You can override the Codex command, profile, or model name without configuring API keys:

```bash
night-curator-setup \
  --codex-bin codex \
  --codex-profile default \
  --codex-model "" \
  --skip-dry-run
```

The config file at `~/.night-curator/night-curator-config.json` stores only Codex CLI preferences, agent description, and optional Lark target.

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

GitHub Actions can run the same command on a schedule if the runner has an authenticated Codex CLI and any optional Lark credentials.

## How Generation Works

- `night-curator-daily` creates a run directory.
- Python writes a JSON schema for the 9-panel content.
- `codex exec --output-schema ... --output-last-message ...` writes the content JSON.
- A second `codex exec` prompt asks Codex to create `comic.png` in the run directory.
- Python validates the content, writes `data.js` and `index.html`, and optionally sends via Lark/Feishu.

## Development

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Security

Do not commit generated state, Lark credentials, or run output. Night Curator does not store model API keys; Codex authentication stays managed by the Codex CLI.

## Files

- `night_curator/codex_runner.py`: Codex CLI prompts and command execution.
- `night_curator/daily.py`: daily generator/renderer/sender.
- `night_curator/setup.py`: configuration CLI.
- `night_curator/schedule.py`: scheduling CLI and launchd plist generation.
- `night_curator/config.py`: config defaults and secret-safe helpers.
- `night_curator/vintage-template.html`: interactive HTML template.
- `night_curator/museum_catalog.json`: museum selection catalog.
