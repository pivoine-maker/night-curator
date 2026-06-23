# The Night Curator

The Night Curator is a nightly museum-adventure agent. Every day at **00:00 UTC+8**, it chooses the next museum stop, generates a dark cinematic 3×3 educational comic, writes rich story/curator notes/quizzes into an interactive HTML page, and pushes the result through a Lark/Feishu bot.

## What it does

- Onboarding asks for image model settings, first museum stop, recurring agent appearance, optional reference images, and Lark delivery target.
- Generates an **Agent anchor image** so the recurring character stays visually consistent.
- Generates daily museum adventure content: story, historical/cultural knowledge, and indirect quiz questions.
- Generates a 3×3 comic image with an OpenAI-compatible image model.
- Builds a vintage gilded interactive HTML page.
- Installs a macOS `launchd` task for daily UTC+8 midnight delivery.
- Sends a markdown summary, comic image, and HTML file through Lark/Feishu.

## Requirements

- macOS for automatic `launchd` scheduling.
- Python 3.10+.
- `lark-cli` installed and configured with a Feishu/Lark app bot.
- An OpenAI-compatible image endpoint, for example `gpt-image-2`.
- Optional local text endpoint for content generation; default is `http://127.0.0.1:4002/v1`.

## Install from GitHub

```bash
pipx install git+https://github.com/<your-user>/night-curator.git
# or
pip install git+https://github.com/<your-user>/night-curator.git
```

For local development:

```bash
git clone https://github.com/<your-user>/night-curator.git
cd night-curator
python3 -m pip install -e .
```

## Configure Lark/Feishu bot

1. Install and configure `lark-cli`.
2. Confirm bot identity is ready:

```bash
lark-cli auth status --json
lark-cli im +chat-list --as bot --page-size 5 --json
```

3. The setup wizard asks for your `open_id` for the same Lark app. If `lark-cli auth status --json` has a user `openId`, the wizard uses it as the default.

## Run onboarding

```bash
night-curator-setup
```

The wizard asks:

- image API key env var, model name, base URL, and extra `api-key` header env var;
- first museum stop, or deterministic random selection;
- recurring Agent appearance description;
- optional reference image paths;
- Lark open_id for bot delivery;
- whether to generate the Agent anchor image now;
- whether to install the daily 00:00 UTC+8 task;
- whether to run a dry-run.

State is stored in:

```bash
~/.night-curator/
```

## Manual commands

Run one dry-run without sending:

```bash
night-curator-daily --dry-run
```

Run a real daily generation and Lark push:

```bash
night-curator-daily
```

Generate only onboarding config/anchor image from arguments:

```bash
night-curator-onboarding \
  --image-api-key-env AIDP_IMAGE_API_KEY \
  --image-header-key-env AIDP_IMAGE_HEADER_KEY \
  --image-model gpt-image-2 \
  --image-base-url https://aidp.bytedance.net/api/modelhub/online/v2/crawl/openai \
  --first-stop louvre-museum \
  --agent-description "a tiny brass owl-like AI curator with moon-white glowing eyes, velvet cape, antique gold satchel, and a moon-key badge"
```

## Output

Daily runs are written to:

```bash
~/.night-curator/runs/YYYY-MM-DD/
```

Each run contains:

- `comic.png`
- `content.json`
- `data.js`
- `index.html`

## Security notes

Do not commit API keys. Store keys in environment variables and point the wizard at the variable names. Lark tokens remain managed by `lark-cli`.
