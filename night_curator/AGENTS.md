# Night Curator Install Protocol

When the user asks to install, setup, configure, or enable Night Curator, keep the flow short and project-local.

## Install Flow

1. Explain that content and comic generation use the user's authenticated Codex CLI.
2. Ask only for optional Codex CLI overrides: command path, profile, or model.
3. Ask only if Lark/Feishu delivery is wanted. If yes, collect `--lark-open-id`; otherwise keep local output only.
4. Run setup with project-local state:

   ```bash
   NIGHT_CURATOR_HOME="$PWD/.night-curator" python3 -m night_curator.setup --skip-dry-run
   ```

5. For macOS scheduling, use `python3 -m night_curator.schedule install-launchd --hour 0 --minute 0`. For other systems, provide cron/systemd/Windows examples from README.

## Daily Command

```bash
NIGHT_CURATOR_HOME="$PWD/.night-curator" python3 -m night_curator.daily --no-send --summary-json
```

Remove `--no-send` only if Lark/Feishu delivery is configured.

## Do Not

- Do not ask users to configure separate text or image API providers.
- Do not ask for raw API key values.
- Do not commit generated `.night-curator` state.
- Do not create plugin or marketplace files.
- Do not run lengthy test suites during user install unless the user asks.
