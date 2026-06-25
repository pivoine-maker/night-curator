import json
from pathlib import Path
import tempfile
import unittest

from night_curator.onboarding import build_anchor_prompt, choose_first_stop, save_project_config


class OnboardingTests(unittest.TestCase):
    def test_save_project_config_writes_model_and_character_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            save_project_config(
                config_path,
                image_api_key_env="OPENAI_API_KEY",
                image_model="gpt-image-1",
                image_base_url="https://example.test/v1",
                first_stop_id="british-museum",
                agent_description="a tiny brass curator robot with moonlit eyes",
                reference_images=["refs/agent.png"],
            )
            data = json.loads(config_path.read_text())
            self.assertEqual(data["image"]["api_key_env"], "OPENAI_API_KEY")
            self.assertEqual(data["image"]["model"], "gpt-image-1")
            self.assertEqual(data["image"]["base_url"], "https://example.test/v1")
            self.assertEqual(data["agent"]["first_stop_id"], "british-museum")
            self.assertEqual(data["agent"]["description"], "a tiny brass curator robot with moonlit eyes")
            self.assertEqual(data["agent"]["reference_images"], ["refs/agent.png"])
            self.assertNotIn("api_key\"", config_path.read_text())

    def test_choose_first_stop_accepts_explicit_id(self):
        museums = [{"id": "louvre", "museum": "Louvre Museum"}, {"id": "british-museum", "museum": "British Museum"}]
        self.assertEqual(choose_first_stop(museums, "british-museum")["museum"], "British Museum")

    def test_choose_first_stop_is_deterministic_when_extracting(self):
        museums = [{"id": "louvre", "museum": "Louvre Museum"}, {"id": "british-museum", "museum": "British Museum"}, {"id": "palace-museum", "museum": "Palace Museum"}]
        self.assertEqual(choose_first_stop(museums, "surprise me", seed="abc")["id"], choose_first_stop(museums, "surprise me", seed="abc")["id"])

    def test_build_anchor_prompt_includes_user_description_and_reference_policy(self):
        prompt = build_anchor_prompt("small owl-like robot in a velvet curator cape", has_reference=True)
        self.assertIn("small owl-like robot in a velvet curator cape", prompt)
        self.assertIn("character anchor sheet", prompt)
        self.assertIn("preserve the reference identity", prompt)
        self.assertIn("dark cinematic graphic novel", prompt)


if __name__ == "__main__":
    unittest.main()
