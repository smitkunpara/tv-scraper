"""MkDocs hooks for local/dev docs behavior."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _run_git(args: list[str]) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        out = subprocess.check_output(["git", *args], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    return out.strip()


def _load_gh_pages_versions() -> list[dict[str, Any]]:
    """Load versions from gh-pages if present."""
    raw = _run_git(["show", "origin/gh-pages:versions.json"])
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    result: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        version = str(item.get("version", "")).strip()
        title = str(item.get("title", version)).strip() or version
        aliases = item.get("aliases", [])
        if not version:
            continue
        if not isinstance(aliases, list):
            aliases = []
        result.append(
            {
                "version": version,
                "title": title,
                "aliases": aliases,
            }
        )
    return result


def _tag_versions() -> list[dict[str, Any]]:
    """Build versions entries from git tags."""
    tags_raw = _run_git(["tag", "--sort=v:refname"])
    if not tags_raw:
        return []

    tags = [line.strip() for line in tags_raw.splitlines() if line.strip()]
    entries: list[dict[str, Any]] = []
    for tag in tags:
        entries.append(
            {
                "version": tag,
                "title": tag,
                "aliases": [],
            }
        )
    return entries


def _merge_versions(
    base: list[dict[str, Any]],
    additions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge versions by unique version key while preserving order."""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []

    for item in [*base, *additions]:
        version = str(item.get("version", "")).strip()
        if not version or version in seen:
            continue
        seen.add(version)
        merged.append(item)

    return merged


def on_post_build(config: dict[str, Any]) -> None:
    """Write versions.json to site_dir after every build/serve cycle."""
    site_dir = Path(str(config.get("site_dir", "site")))
    site_dir.mkdir(parents=True, exist_ok=True)

    versions = _merge_versions(_load_gh_pages_versions(), _tag_versions())
    if not versions:
        versions = [{"version": "latest", "title": "latest", "aliases": []}]

    target = site_dir / "versions.json"
    target.write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
