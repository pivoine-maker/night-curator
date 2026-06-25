import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import night_curator.daily as daily


class DailyConfigTests(unittest.TestCase):
    def with_state(self, config):
        tmp = tempfile.TemporaryDirectory()
        state = Path(tmp.name)
        (state / "night-curator-config.json").write_text(json.dumps(config))
        return tmp, state

    def restore_env(self, name, value):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    def test_configured_open_id_uses_lark_config(self):
        tmp, state = self.with_state({"lark": {"enabled": True, "open_id": "ou_public"}})
        old_home = os.environ.get("NIGHT_CURATOR_HOME")
        old_open = os.environ.pop("NIGHT_CURATOR_LARK_OPEN_ID", None)
        os.environ["NIGHT_CURATOR_HOME"] = str(state)
        try:
            self.assertEqual(daily.configured_open_id(), "ou_public")
        finally:
            tmp.cleanup()
            self.restore_env("NIGHT_CURATOR_HOME", old_home)
            self.restore_env("NIGHT_CURATOR_LARK_OPEN_ID", old_open)

    def test_llm_json_uses_configured_text_provider(self):
        config = {"text": {"base_url": "https://example.test/v1", "model": "text-model", "api_key_env": "NC_TEXT_KEY", "header_key_env": "NC_TEXT_HEADER"}}
        tmp, state = self.with_state(config)
        old_home = os.environ.get("NIGHT_CURATOR_HOME")
        os.environ["NIGHT_CURATOR_HOME"] = str(state)
        os.environ["NC_TEXT_KEY"] = "text-key"
        os.environ["NC_TEXT_HEADER"] = "text-header"
        calls = {}

        class FakeCompletions:
            def create(self, **kwargs):
                calls["create"] = kwargs
                panel = {"t":"t","m":"m","story":"s","note":"n","q":"q","choices":["A","B","C"],"a":0,"why":"w"}
                message = type("Message", (), {"content": json.dumps({"title": "T", "subtitle": "S", "panels": [panel for _ in range(9)]})})
                choice = type("Choice", (), {"message": message})
                return type("Response", (), {"choices": [choice]})

        class FakeClient:
            def __init__(self, api_key, base_url):
                calls["client"] = {"api_key": api_key, "base_url": base_url}
                self.chat = type("Chat", (), {"completions": FakeCompletions()})()

        try:
            with mock.patch.object(daily, "OpenAI", FakeClient):
                data = daily.llm_json(0, {"museum": "M", "city": "C", "country": "X", "artifact": "A"})
            self.assertEqual(data["title"], "T")
            self.assertEqual(calls["client"], {"api_key": "text-key", "base_url": "https://example.test/v1"})
            self.assertEqual(calls["create"]["model"], "text-model")
            self.assertEqual(calls["create"]["extra_headers"], {"api-key": "text-header"})
        finally:
            tmp.cleanup()
            os.environ.pop("NC_TEXT_KEY", None)
            os.environ.pop("NC_TEXT_HEADER", None)
            self.restore_env("NIGHT_CURATOR_HOME", old_home)

class DailyImageConfigTests(unittest.TestCase):
    def restore_env(self, name, value):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    def test_generate_image_uses_configured_image_provider(self):
        tmp = tempfile.TemporaryDirectory()
        state = Path(tmp.name)
        config = {"image": {"base_url": "https://image.test/v1", "model": "image-model", "api_key_env": "NC_IMAGE_KEY", "header_key_env": "NC_IMAGE_HEADER", "size": "512x512", "quality": "low"}}
        (state / "night-curator-config.json").write_text(json.dumps(config))
        old_home = os.environ.get("NIGHT_CURATOR_HOME")
        os.environ["NIGHT_CURATOR_HOME"] = str(state)
        os.environ["NC_IMAGE_KEY"] = "image-key"
        os.environ["NC_IMAGE_HEADER"] = "image-header"
        calls = {}

        class FakeImages:
            def generate(self, **kwargs):
                calls["generate"] = kwargs
                item = type("Image", (), {"b64_json": "aW1hZ2U=", "url": None})
                return type("Response", (), {"data": [item]})

        class FakeClient:
            def __init__(self, api_key, base_url):
                calls["client"] = {"api_key": api_key, "base_url": base_url}
                self.images = FakeImages()

        try:
            with mock.patch.object(daily, "OpenAI", FakeClient):
                out = daily.generate_image(0, {"museum":"M","city":"C","artifact":"A"}, {"panels": []}, state)
            self.assertEqual(out.read_bytes(), b"image")
            self.assertEqual(calls["client"], {"api_key": "image-key", "base_url": "https://image.test/v1"})
            self.assertEqual(calls["generate"]["model"], "image-model")
            self.assertEqual(calls["generate"]["size"], "512x512")
            self.assertEqual(calls["generate"]["quality"], "low")
            self.assertEqual(calls["generate"]["extra_headers"], {"api-key": "image-header"})
        finally:
            tmp.cleanup()
            os.environ.pop("NC_IMAGE_KEY", None)
            os.environ.pop("NC_IMAGE_HEADER", None)
            self.restore_env("NIGHT_CURATOR_HOME", old_home)
