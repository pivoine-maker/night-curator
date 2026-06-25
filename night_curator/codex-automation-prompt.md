# Codex Automation Prompt

Schedule this as a standalone Codex Automation that runs every day at 00:00 Asia/Shanghai.

Working directory: `{{PROJECT_DIR}}`
State directory: `{{STATE_DIR}}`

## What Codex Does Each Day

1. Read `museum_catalog.json` and `{{STATE_DIR}}/night-curator-config.json` if present.
2. Choose today's museum using the same deterministic approach as `night_curator.daily`.
3. Create today's Night Curator content as strict JSON.
4. Save that JSON to `{{STATE_DIR}}/codex-content/today.json`.
5. Run the renderer command below.
6. Report the title, museum, output directory, HTML path, image path, and delivery status.

## Content JSON Shape

Generate exactly this shape, with exactly 9 panels:

```json
{
  "title": "The Night Curator · Day N: Museum Name",
  "subtitle": "City · artifact/theme",
  "panels": [
    {
      "t": "短标题",
      "m": "English knowledge label",
      "story": "120-180 Chinese chars rich adventure plot",
      "note": "150-240 Chinese chars detailed history, archaeology, or culture knowledge",
      "q": "indirect higher-order question in Chinese",
      "choices": ["A", "B", "C"],
      "a": 0,
      "why": "Chinese explanation"
    }
  ]
}
```

Rules:

- Questions must require reasoning from the story and note, not direct lookup.
- Correct answer indexes must vary across panels.
- Use real historical/cultural knowledge and avoid hallucinated precise facts when uncertain.
- Keep the JSON valid. Do not wrap it in Markdown fences when writing the file.

## Render Command

```bash
{{DAILY_COMMAND}}
```

## Failure Policy

If the command fails, report the exact failing step and stderr/stdout excerpt. Ask the user for input only when credentials, permissions, missing dependencies, or unavailable model capability are required.
