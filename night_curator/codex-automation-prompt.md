# Night Curator Automation Prompt

Schedule this as a standalone automation that runs every day at 00:00 Asia/Shanghai.

Project directory:

```bash
{{PROJECT_DIR}}
```

Daily command:

```bash
{{DAILY_COMMAND}}
```

Night Curator invokes configured text and image model APIs to create the JSON content and comic image. Ensure the scheduler environment includes the API key variables referenced by `{{STATE_DIR}}/night-curator-config.json`. After the command finishes, report the generated title, museum, output directory, HTML path, image path, and delivery status.

If the command fails, report the exact failing step and stderr/stdout excerpt. Ask the user for input only when model API credentials, filesystem permissions, missing dependencies, or optional Lark credentials are required.
