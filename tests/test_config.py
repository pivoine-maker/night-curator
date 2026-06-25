import json
import os
import tempfile
import unittest
from pathlib import Path

from night_curator.config import (
    default_config,
    default_state_dir,
    load_config,
    provider_api_key,
    provider_header_key,
    save_config,
)


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

    def test_load_config_merges_public_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"text": {"model": "custom-text"}, "lark": {"enabled": True}}))
            config = load_config(path)
            self.assertEqual(config["text"]["model"], "custom-text")
            self.assertEqual(config["text"]["api_key_env"], "OPENAI_API_KEY")
            self.assertEqual(config["image"]["model"], "gpt-image-1")
            self.assertTrue(config["lark"]["enabled"])

    def test_save_config_does_not_persist_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            save_config(path, {"text": {"api_key_env": "MY_SECRET", "api_key": "sk-secret"}})
            raw = path.read_text()
            self.assertIn("MY_SECRET", raw)
            self.assertNotIn("sk-secret", raw)

    def test_provider_api_key_and_header_key_read_environment(self):
        old_key = os.environ.get("NC_TEST_KEY")
        old_header = os.environ.get("NC_TEST_HEADER")
        os.environ["NC_TEST_KEY"] = "key-value"
        os.environ["NC_TEST_HEADER"] = "header-value"
        try:
            provider = {"api_key_env": "NC_TEST_KEY", "header_key_env": "NC_TEST_HEADER"}
            self.assertEqual(provider_api_key(provider), "key-value")
            self.assertEqual(provider_header_key(provider), "header-value")
        finally:
            if old_key is None:
                os.environ.pop("NC_TEST_KEY", None)
            else:
                os.environ["NC_TEST_KEY"] = old_key
            if old_header is None:
                os.environ.pop("NC_TEST_HEADER", None)
            else:
                os.environ["NC_TEST_HEADER"] = old_header

    def test_default_config_has_no_private_urls(self):
        rendered = json.dumps(default_config())
        self.assertNotIn("bytedance", rendered.lower())
        self.assertEqual(default_config()["text"]["base_url"], "https://api.openai.com/v1")


if __name__ == "__main__":
    unittest.main()
