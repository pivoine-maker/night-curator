import json
import os
import tempfile
import unittest
from pathlib import Path

from night_curator.config import default_config, default_state_dir, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_default_state_dir_uses_home_when_env_missing(self):
        old = os.environ.pop("NIGHT_CURATOR_HOME", None)
        try:
            self.assertEqual(default_state_dir(), Path.home() / ".night-curator")
        finally:
            if old is not None:
                os.environ["NIGHT_CURATOR_HOME"] = old

    def test_default_state_dir_uses_env_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("NIGHT_CURATOR_HOME")
            os.environ["NIGHT_CURATOR_HOME"] = tmp
            try:
                self.assertEqual(default_state_dir(), Path(tmp))
            finally:
                if old is None:
                    os.environ.pop("NIGHT_CURATOR_HOME", None)
                else:
                    os.environ["NIGHT_CURATOR_HOME"] = old

    def test_load_config_merges_codex_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"codex": {"profile": "night"}, "lark": {"enabled": True}}))
            config = load_config(path)
            self.assertEqual(config["codex"]["bin"], "codex")
            self.assertEqual(config["codex"]["profile"], "night")
            self.assertTrue(config["lark"]["enabled"])

    def test_save_config_does_not_persist_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            save_config(path, {"codex": {"bin": "codex"}, "api_key": "sk-secret", "token": "secret-token"})
            raw = path.read_text()
            self.assertIn("codex", raw)
            self.assertNotIn("sk-secret", raw)
            self.assertNotIn("secret-token", raw)

    def test_default_config_has_no_model_provider_settings(self):
        config = default_config()
        self.assertIn("codex", config)
        self.assertNotIn("text", config)
        self.assertNotIn("image", config)
        rendered = json.dumps(config)
        self.assertNotIn("bytedance", rendered.lower())
        self.assertNotIn("api.openai.com", rendered.lower())


if __name__ == "__main__":
    unittest.main()
