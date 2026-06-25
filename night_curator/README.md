# The Night Curator

The Night Curator is a nightly museum-adventure generator. It chooses a museum, writes a 9-panel educational story/quiz, generates a cinematic 3×3 comic image, builds an interactive HTML page, and can optionally send the result through a Lark/Feishu bot.

It is designed for open-source use:

- text generation uses an OpenAI-compatible chat endpoint;
- image generation uses an OpenAI-compatible image endpoint;
- secrets stay in environment variables, not config files;
- output works locally even without Lark/Feishu;
- scheduling supports macOS `launchd`, plus cron/systemd/Windows/GitHub Actions examples.

## Quick Start

```bash
git clone https://github.com/pivoine-maker/night-curator.git
cd night-curator
python3 -m pip install -e .
export OPENAI_API_KEY="your-api-key"
night-curator-setup --skip-anchor --skip-dry-run
night-curator-daily --dry-run --no-send --summary-json
```

Generated files are written to `~/.night-curator/runs/YYYY-MM-DD/`.

## Configure Models

The setup command writes `~/.night-curator/night-curator-config.json`. The file stores environment variable names, model names, and base URLs. It never needs raw API keys.

```bash
export OPENAI_API_KEY="your-api-key"
night-curator-setup \
  --text-api-key-env OPENAI_API_KEY \
  --text-base-url https://api.openai.com/v1 \
  --text-model gpt-4.1-mini \
  --image-api-key-env OPENAI_API_KEY \
  --image-base-url https://api.openai.com/v1 \
  --image-model gpt-image-1 \
  --skip-anchor \
  --skip-dry-run
```

If your provider requires an additional `api-key` header, set `--text-header-key-env` or `--image-header-key-env` to the environment variable that contains that header value.

## Lark/Feishu Delivery

Lark/Feishu is optional. Without it, Night Curator only writes local files.

To enable delivery:

1. Install and authenticate `lark-cli` for a Lark/Feishu app bot.
2. Confirm bot sending works with your app.
3. Configure Night Curator with your recipient `open_id`:

```bash
night-curator-setup \
  --enable-lark \
  --lark-open-id ou_xxx \
  --skip-anchor \
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

GitHub Actions can run the same command on a schedule, but you must provide model and Lark credentials as repository secrets.

## Codex Automation Mode

If you want Codex to write the daily text content, print the automation prompt:

```bash
night-curator-setup --print-automation-prompt
```

Codex should write `~/.night-curator/codex-content/today.json`, then run:

```bash
python3 -m night_curator.daily --content-json ~/.night-curator/codex-content/today.json --no-send --summary-json
```

Remove `--no-send` only after Lark/Feishu delivery is configured.

## Development

```bash
python3 -m pip install -e .
python3 -m unittest discover -v
```

## Security

Do not commit API keys, Lark credentials, generated state, or run output. Keep secrets in environment variables and put only their variable names in `night-curator-config.json`.

## Files

- `night_curator/daily.py`: daily generator/renderer/sender.
- `night_curator/setup.py`: configuration CLI.
- `night_curator/schedule.py`: scheduling CLI and launchd plist generation.
- `night_curator/config.py`: config defaults and secret-safe helpers.
- `night_curator/vintage-template.html`: interactive HTML template.
- `night_curator/museum_catalog.json`: museum selection catalog.
