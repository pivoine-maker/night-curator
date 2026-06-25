import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from night_curator.codex_runner import (
    CONTENT_SCHEMA,
    build_codex_command,
    build_image_request,
    build_json_request,
    generate_content_with_api,
    generate_content_with_codex,
    generate_image_with_api,
    generate_image_with_codex,
)


class CodexRunnerTests(unittest.TestCase):
    def test_build_codex_command_uses_exec_schema_and_output_file(self):
        command = build_codex_command(
            prompt="make content",
            output_last_message=Path("/tmp/out.json"),
            output_schema=Path("/tmp/schema.json"),
            codex_bin="codex",
            profile="night",
            model="gpt-test",
            cwd=Path("/tmp/work"),
        )
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--output-last-message", command)
        self.assertIn("--output-schema", command)
        self.assertIn("/tmp/schema.json", command)
        self.assertIn("--profile", command)
        self.assertIn("night", command)
        self.assertIn("--model", command)
        self.assertIn("gpt-test", command)
        self.assertIn("--cd", command)
        self.assertIn("/tmp/work", command)
        self.assertEqual(command[-1], "make content")

    def test_content_schema_requires_nine_panels(self):
        self.assertEqual(CONTENT_SCHEMA["properties"]["panels"]["minItems"], 9)
        self.assertEqual(CONTENT_SCHEMA["properties"]["panels"]["maxItems"], 9)

    def test_build_json_request_uses_openai_compatible_responses_shape(self):
        request = build_json_request({"base_url": "https://api.example/v1", "model": "gpt-test", "temperature": 0.4}, "hello")
        self.assertEqual(request["url"], "https://api.example/v1/responses")
        self.assertEqual(request["payload"]["model"], "gpt-test")
        self.assertEqual(request["payload"]["text"]["format"]["type"], "json_schema")

    def test_build_image_request_uses_configured_model_and_prompt(self):
        request = build_image_request({"base_url": "https://api.example/v1", "model": "image-test", "size": "1024x1024", "endpoint": "images"}, "draw it")
        self.assertEqual(request["url"], "https://api.example/v1/images/generations")
        self.assertEqual(request["payload"]["model"], "image-test")
        self.assertEqual(request["payload"]["prompt"], "draw it")

class CodexRunnerBehaviorTests(unittest.TestCase):
    def test_generate_content_with_api_posts_prompt_and_parses_json(self):
        captured = {}

        def fake_post_json(url, payload, settings):
            captured["url"] = url
            captured["payload"] = payload
            return {"output_text": json.dumps({"title": "T", "subtitle": "S", "panels": []})}

        config = {"models": {"text": {"base_url": "https://api.example/v1", "model": "gpt-test", "api_key_env": "KEY"}}}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"KEY": "secret"}, clear=False), mock.patch("night_curator.codex_runner.post_json", fake_post_json):
                content = generate_content_with_api({"museum":"M","city":"C","artifact":"A"}, Path(tmp), config)
        self.assertEqual(content["title"], "T")
        self.assertEqual(captured["url"], "https://api.example/v1/responses")
        self.assertIn("Return exactly 9 panels", captured["payload"]["input"])

    def test_generate_image_with_api_writes_base64_image(self):
        def fake_post_json(url, payload, settings):
            return {"data": [{"b64_json": "aW1n"}]}

        config = {"models": {"image": {"base_url": "https://api.example/v1", "model": "image-test", "api_key_env": "KEY", "endpoint": "images"}}}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"KEY": "secret"}, clear=False), mock.patch("night_curator.codex_runner.post_json", fake_post_json):
                path = generate_image_with_api({"museum":"M","city":"C","artifact":"A"}, {"title":"T"}, Path(tmp), config)
            self.assertEqual(path.name, "comic.png")
            self.assertEqual(path.read_bytes(), b"img")

    def test_generate_content_with_codex_writes_schema_and_loads_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            panel = {"t":"t","m":"m","story":"s","note":"n","q":"q","choices":["A","B","C"],"a":0,"why":"w"}
            content = {"title":"T","subtitle":"S","panels":[panel for _ in range(9)]}

            def fake_run(command, text, capture_output, check, cwd):
                output_path = Path(command[command.index("--output-last-message") + 1])
                output_path.write_text(json.dumps(content))
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})

            with mock.patch("night_curator.codex_runner.subprocess.run", fake_run):
                result = generate_content_with_codex({"museum":"M","city":"C","artifact":"A"}, out_dir, {"codex": {"bin": "codex"}})
            self.assertEqual(result["title"], "T")
            self.assertTrue((out_dir / "content.schema.json").exists())
            self.assertTrue((out_dir / "codex-content-message.txt").exists())

    def test_generate_image_with_codex_requires_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)

            def fake_run(command, text, capture_output, check, cwd):
                self.assertIn(str(out_dir / "comic.png"), command[-1])
                (out_dir / "comic.png").write_bytes(b"png")
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})

            with mock.patch("night_curator.codex_runner.subprocess.run", fake_run):
                path = generate_image_with_codex({"museum":"M","city":"C","artifact":"A"}, {"title":"T","panels":[]}, out_dir, {"codex": {"bin": "codex"}})
            self.assertEqual(path.read_bytes(), b"png")
