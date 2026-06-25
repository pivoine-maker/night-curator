# Night Curator Install Protocol

When the user asks to install, setup, configure, or enable Night Curator, keep the flow short and project-local.

## Install Flow

1. Explain that text and image generation use OpenAI-compatible endpoints configured by the user.
2. Ask for text model config: API key environment variable name, base URL, model name, and optional extra `api-key` header environment variable.
3. Ask for image model config: API key environment variable name, base URL, model name, and optional extra `api-key` header environment variable.
4. Ask only if Lark/Feishu delivery is wanted. If yes, collect `--lark-open-id`; otherwise keep local output only.
5. Run setup with project-local state:

   ```bash
   NIGHT_CURATOR_HOME="$PWD/.night-curator" python3 -m night_curator.setup --skip-anchor --skip-dry-run
   ```

6. For macOS scheduling, use `python3 -m night_curator.schedule install-launchd --hour 0 --minute 0`. For other systems, provide cron/systemd/Windows examples from README.

## Daily Command

```bash
NIGHT_CURATOR_HOME="$PWD/.night-curator" python3 -m night_curator.daily --no-send --summary-json
```

Remove `--no-send` only if Lark/Feishu delivery is configured.

## Do Not

- Do not ask for raw API key values; ask for environment variable names.
- Do not commit generated `.night-curator` state.
- Do not create plugin or marketplace files.
- Do not run lengthy test suites during user install unless the user asks.
