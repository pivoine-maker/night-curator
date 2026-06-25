import plistlib
import tempfile
import unittest
from pathlib import Path

from night_curator.schedule import build_launchd_plist, launchd_plist_path


class ScheduleTests(unittest.TestCase):
    def test_build_launchd_plist_contains_midnight_command_and_state(self):
        plist = build_launchd_plist(
            label="com.example.night-curator",
            state_dir=Path("/tmp/night-state"),
            python="/usr/bin/python3",
            hour=0,
            minute=0,
        )
        self.assertEqual(plist["Label"], "com.example.night-curator")
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 0, "Minute": 0})
        self.assertEqual(plist["EnvironmentVariables"]["NIGHT_CURATOR_HOME"], "/tmp/night-state")
        self.assertEqual(plist["ProgramArguments"], ["/usr/bin/python3", "-m", "night_curator.daily"])
        self.assertIn("launchd.out.log", plist["StandardOutPath"])
        self.assertIn("launchd.err.log", plist["StandardErrorPath"])

    def test_launchd_plist_path_uses_home_launchagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = launchd_plist_path("com.example.night-curator", home=Path(tmp))
            self.assertEqual(path, Path(tmp) / "Library" / "LaunchAgents" / "com.example.night-curator.plist")

    def test_plist_serializes(self):
        data = build_launchd_plist(state_dir=Path("/tmp/night-state"), python="/usr/bin/python3")
        raw = plistlib.dumps(data)
        loaded = plistlib.loads(raw)
        self.assertEqual(loaded["Label"], "com.night-curator.daily")


if __name__ == "__main__":
    unittest.main()
