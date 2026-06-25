import tempfile
import unittest
from pathlib import Path
from unittest import mock

import night_curator.daily as daily


class DailyCodexTests(unittest.TestCase):
    def test_main_uses_codex_content_and_image_when_not_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            content = {"title":"Codex Title","subtitle":"Sub","panels":[{"t":"t","m":"m","story":"s","note":"n","q":"q","choices":["A","B","C"],"a":0,"why":"w"} for _ in range(9)]}
            image = state / "runs" / "2026-06-25" / "comic.png"

            def fake_content(item, out_dir, config):
                return content

            def fake_image(item, generated_content, out_dir, config):
                path = out_dir / "comic.png"
                path.write_bytes(b"png")
                return path

            with mock.patch.dict("os.environ", {"NIGHT_CURATOR_HOME": str(state), "NIGHT_CURATOR_FORCE_FALLBACK": "0"}, clear=False), \
                 mock.patch.object(daily, "choose_museum", return_value=(1, {"museum":"M","city":"C","country":"X","artifact":"A"}, daily.datetime(2026, 6, 25, tzinfo=daily.TZ))), \
                 mock.patch.object(daily, "generate_content_with_codex", fake_content), \
                 mock.patch.object(daily, "generate_image_with_codex", fake_image):
                self.assertEqual(daily.main(["--no-send", "--summary-json"]), 0)
            self.assertTrue(image.exists())
            self.assertIn("Codex Title", (image.parent / "content.json").read_text())


if __name__ == "__main__":
    unittest.main()
