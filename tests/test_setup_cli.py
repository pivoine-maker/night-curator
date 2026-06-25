import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from night_curator import setup


class SetupCliTests(unittest.TestCase):
    def test_main_writes_model_api_and_lark_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "night-curator-config.json"
            argv = [
                "night-curator-setup",
                "--config", str(config_path),
                "--skip-dry-run",
                "--text-base-url", "https://example.test/v1",
                "--text-model", "text-test",
                "--text-api-key-env", "TEXT_KEY",
                "--image-base-url", "https://images.test/v1",
                "--image-model", "image-test",
                "--image-api-key-env", "IMAGE_KEY",
                "--lark-open-id", "ou_user",
                "--enable-lark",
            ]
            with mock.patch("sys.argv", argv):
                self.assertEqual(setup.main(), 0)
            data = json.loads(config_path.read_text())
            self.assertEqual(data["models"]["text"]["base_url"], "https://example.test/v1")
            self.assertEqual(data["models"]["text"]["model"], "text-test")
            self.assertEqual(data["models"]["text"]["api_key_env"], "TEXT_KEY")
            self.assertEqual(data["models"]["image"]["base_url"], "https://images.test/v1")
            self.assertEqual(data["models"]["image"]["model"], "image-test")
            self.assertEqual(data["models"]["image"]["api_key_env"], "IMAGE_KEY")
            self.assertTrue(data["lark"]["enabled"])
            self.assertEqual(data["lark"]["open_id"], "ou_user")

    def test_print_automation_prompt_includes_state_and_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "night-curator-config.json"
            argv = ["night-curator-setup", "--config", str(config_path), "--print-automation-prompt"]
            with mock.patch("sys.argv", argv), mock.patch("builtins.print") as fake_print:
                self.assertEqual(setup.main(), 0)
            output = "\n".join(str(call.args[0]) for call in fake_print.call_args_list)
            self.assertIn(str(config_path.parent), output)
            self.assertIn("night_curator.daily", output)


if __name__ == "__main__":
    unittest.main()
