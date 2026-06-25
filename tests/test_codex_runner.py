import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from night_curator.codex_runner import CONTENT_SCHEMA, build_codex_command, generate_content_with_codex, generate_image_with_codex


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

class CodexRunnerBehaviorTests(unittest.TestCase):
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
