# Codex Automation Prompt

Schedule this as a standalone Codex Automation that runs every day at 00:00 Asia/Shanghai.

Working directory: `{{PROJECT_DIR}}`
State directory: `{{STATE_DIR}}`

Run this command:

```bash
{{DAILY_COMMAND}}
```

Night Curator itself will invoke `codex exec` to create the JSON content and comic image. After the command finishes, report the generated title, museum, output directory, HTML path, image path, and delivery status.

If the command fails, report the exact failing step and stderr/stdout excerpt. Ask the user for input only when Codex CLI authentication, filesystem permissions, missing dependencies, or optional Lark credentials are required.
