"""Command-line interface for ableton-draft-manager."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from admanager import __version__
from admanager.scanner import find_projects, inspect_project


def _fmt_length(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.path)
    projects = [inspect_project(p) for p in find_projects(root)]
    print(f"Found {len(projects)} project(s) in {root}")

    if args.backup:
        backup_dir = _snapshot(root, projects, args.keep)
        print(f"Snapshot saved to {backup_dir} (keep={args.keep})")

    if args.report:
        report = _render_report(root, projects)
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Report written to {args.report}")

    return 0


def _snapshot(root: Path, projects: list, keep: int) -> Path:
    base = root / ".snapshots"
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    snap = base / stamp
    snap.mkdir(parents=True, exist_ok=True)
    for project in projects:
        dest = snap / project.name
        if not dest.exists():
            shutil.copy2(project.path, dest)

    backups = sorted(base.glob("20*"))
    while len(backups) > keep:
        shutil.rmtree(backups[0])
        backups = sorted(base.glob("20*"))
    return snap


def _render_report(root: Path, projects: list) -> str:
    lines = [f"# Ableton Draft Report — {root}", ""]
    for p in sorted(projects, key=lambda p: p.path):
        lines.append(
            f"- **{p.name}** | BPM: {p.tempo or '-'} | "
            f"TS: {p.time_signature or '-'} | "
            f"Length: {_fmt_length(p.arrangement_length)} | "
            f"sha: {p.sha256[:12]}"
        )
    return "\n".join(lines) + "\n"


def cmd_dups(args: argparse.Namespace) -> int:
    root = Path(args.path)
    projects = [inspect_project(p) for p in find_projects(root)]
    by_hash: dict[str, list] = {}
    for p in projects:
        by_hash.setdefault(p.sha256, []).append(p)

    found = False
    for digest, group in sorted(by_hash.items()):
        if len(group) > 1:
            found = True
            print(f"Duplicate ({digest[:12]}):")
            for p in group:
                print(f"  {p.path}")
    if not found:
        print("No duplicates found.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="admanager",
        description="Manage Ableton Live draft projects.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan projects and produce a report")
    scan.add_argument("--path", default=".", help="root directory to scan")
    scan.add_argument("--report", help="write markdown report to this file")
    scan.add_argument("--backup", action="store_true", help="create a snapshot")
    scan.add_argument("--keep", type=int, default=5, help="max snapshots to keep")
    scan.set_defaults(func=cmd_scan)

    dups = sub.add_parser("dups", help="find duplicate projects by content hash")
    dups.add_argument("--path", default=".", help="root directory to scan")
    dups.set_defaults(func=cmd_dups)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
