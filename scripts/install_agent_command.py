#!/usr/bin/env python3
"""Install JW and jw launchers for the terminal agent."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_AGENT_PATH = SCRIPT_DIR / "agent.py"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"


def directory_is_case_insensitive(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    probe = directory / ".jw_case_probe"
    probe.write_text("x", encoding="utf-8")
    try:
        return (directory / ".JW_CASE_PROBE").exists()
    finally:
        probe.unlink(missing_ok=True)


def install_launchers(bin_dir: Path = DEFAULT_BIN_DIR, agent_path: Path = DEFAULT_AGENT_PATH) -> list[Path]:
    bin_dir.mkdir(parents=True, exist_ok=True)
    names = ("jw",) if directory_is_case_insensitive(bin_dir) else ("JW", "jw")
    created = []
    for name in names:
        launcher = bin_dir / name
        launcher.write_text(
            "#!/usr/bin/env bash\n"
            f'exec "{sys.executable}" "{agent_path}" "$@"\n',
            encoding="utf-8",
        )
        launcher.chmod(0o755)
        created.append(launcher)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install JW and jw commands.")
    parser.add_argument("--bin-dir", default=str(DEFAULT_BIN_DIR), help="Directory to install launchers into")
    args = parser.parse_args(argv)

    created = install_launchers(Path(args.bin_dir))
    print("Installed launchers:")
    for path in created:
        print(f"  {path}")
    if len(created) == 1 and created[0].name.lower() == "jw":
        print("  Case-insensitive filesystem detected; this single launcher works as both JW and jw.")
    if str(Path(args.bin_dir)) not in os.environ.get("PATH", ""):
        print(f"\nAdd this to your PATH if needed: export PATH=\"{args.bin_dir}:$PATH\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
