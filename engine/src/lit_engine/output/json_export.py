"""Canonical JSON schema writer for lit-engine output."""

import json
import os
import re
import shutil
from datetime import datetime, timezone

from lit_engine import __version__


def write_json(output_dir: str, filename: str, data: dict) -> str:
    """Write a JSON file to the output directory. Returns the path written."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def write_manifest(output_dir: str, manifest: dict) -> str:
    """Write manifest.json."""
    return write_json(output_dir, "manifest.json", manifest)


def write_analysis(output_dir: str, data: dict) -> str:
    """Write analysis.json (TextTiling blocks)."""
    return write_json(output_dir, "analysis.json", data)


def write_characters(output_dir: str, data: dict) -> str:
    """Write characters.json (agency analysis)."""
    return write_json(output_dir, "characters.json", data)


def write_chapters(output_dir: str, data: dict) -> str:
    """Write chapters.json (chapter aggregation)."""
    return write_json(output_dir, "chapters.json", data)


def write_sentiment(output_dir: str, data: dict) -> str:
    """Write sentiment.json (VADER sentiment analysis)."""
    return write_json(output_dir, "sentiment.json", data)


def copy_manuscript(source_path: str, output_dir: str) -> str:
    """Copy manuscript to output dir for block reading. Returns dest path."""
    os.makedirs(output_dir, exist_ok=True)
    dest = os.path.join(output_dir, "manuscript.txt")
    if os.path.abspath(source_path) == os.path.abspath(dest):
        return dest  # source is already in output dir
    shutil.copy2(source_path, dest)
    return dest


def slugify(title: str) -> str:
    """
    Convert a title to a URL-safe slug.

    Rules:
    - Lowercase
    - Replace spaces and underscores with hyphens
    - Strip non-alphanumeric characters (except hyphens)
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens
    """
    slug = title.lower()
    slug = re.sub(r"[_ ]+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def build_manifest(
    title: str,
    slug: str,
    source_file: str,
    word_count: int,
    char_count: int,
    character_list: list[str],
    analyzers_run: list[str],
    parameters: dict,
    chapter_count: int = 0,
    warnings: list[str] | None = None,
) -> dict:
    """Build a manifest dict matching the canonical schema."""
    return {
        "title": title,
        "slug": slug,
        "source_file": os.path.basename(source_file),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "engine_version": __version__,
        "word_count": word_count,
        "char_count": char_count,
        "chapter_count": chapter_count,
        "character_list": character_list,
        "analyzers_run": analyzers_run,
        "parameters": parameters,
        "warnings": warnings or [],
    }
