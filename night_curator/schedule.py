#!/usr/bin/env python3
import argparse
import plistlib
import subprocess
import sys
from pathlib import Path

try:
    from .config import default_state_dir
except ImportError:
    from config import default_state_dir

DEFAULT_LABEL = "com.night-curator.daily"


def launchd_plist_path(label=DEFAULT_LABEL, home=None):
    root = Path(home).expanduser() if home else Path.home()
    return root / "Library" / "LaunchAgents" / f"{label}.plist"


def build_launchd_plist(label=DEFAULT_LABEL, state_dir=None, python=None, hour=0, minute=0):
    resolved_state = Path(state_dir).expanduser() if state_dir else default_state_dir()
    logs = resolved_state / "logs"
    return {
        "Label": label,
        "ProgramArguments": [python or sys.executable, "-m", "night_curator.daily"],
        "StartCalendarInterval": {"Hour": int(hour), "Minute": int(minute)},
        "StandardOutPath": str(logs / "launchd.out.log"),
        "StandardErrorPath": str(logs / "launchd.err.log"),
        "EnvironmentVariables": {
            "NIGHT_CURATOR_HOME": str(resolved_state),
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "TZ": "Asia/Shanghai",
        },
    }


def write_launchd_plist(path, plist):
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    Path(plist["EnvironmentVariables"]["NIGHT_CURATOR_HOME"]).joinpath("logs").mkdir(parents=True, exist_ok=True)
    path.write_bytes(plistlib.dumps(plist, sort_keys=False))
    return path


def run_launchctl(args):
    return subprocess.run(["launchctl", *args], text=True, capture_output=True, check=False)


def user_domain():
    return f"gui/{subprocess.getoutput('id -u')}"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Manage Night Curator schedules.")
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install-launchd", help="Install a macOS launchd job.")
    install.add_argument("--label", default=DEFAULT_LABEL)
    install.add_argument("--state-dir", default=str(default_state_dir()))
    install.add_argument("--python", default=sys.executable)
    install.add_argument("--hour", type=int, default=0)
    install.add_argument("--minute", type=int, default=0)
    install.add_argument("--no-load", action="store_true")
    uninstall = sub.add_parser("uninstall-launchd", help="Unload and remove the macOS launchd job.")
    uninstall.add_argument("--label", default=DEFAULT_LABEL)
    status = sub.add_parser("status", help="Print launchd status for the job.")
    status.add_argument("--label", default=DEFAULT_LABEL)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "install-launchd":
        plist = build_launchd_plist(args.label, args.state_dir, args.python, args.hour, args.minute)
        path = write_launchd_plist(launchd_plist_path(args.label), plist)
        if not args.no_load:
            run_launchctl(["bootout", user_domain(), str(path)])
            result = run_launchctl(["bootstrap", user_domain(), str(path)])
            if result.returncode != 0:
                print(result.stderr or result.stdout, file=sys.stderr, end="")
                return result.returncode
        print(f"installed {path}")
        return 0
    if args.command == "uninstall-launchd":
        path = launchd_plist_path(args.label)
        run_launchctl(["bootout", user_domain(), str(path)])
        if path.exists():
            path.unlink()
        print(f"uninstalled {path}")
        return 0
    if args.command == "status":
        result = run_launchctl(["print", f"{user_domain()}/{args.label}"])
        print(result.stdout or result.stderr, end="")
        return result.returncode
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
