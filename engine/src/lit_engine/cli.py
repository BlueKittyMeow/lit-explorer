"""CLI entry point for lit-engine."""

import json
import os

import click
from nltk.tokenize import sent_tokenize, word_tokenize

from lit_engine import __version__
from lit_engine.analyzers import get_analyzer, list_analyzers, resolve_execution_order
from lit_engine.analyzers import _REGISTRY
from lit_engine.config import merge_config
from lit_engine.output.json_export import (
    build_manifest,
    copy_manuscript,
    slugify,
    write_analysis,
    write_characters,
    write_chapters,
    write_manifest,
    write_sentiment,
)


@click.group()
@click.version_option(__version__)
def main():
    """lit-engine: computational stylistics for literary manuscripts."""
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--title", "-t", default=None, help="Manuscript title (for slug)")
@click.option("--only", default=None, help="Comma-separated analyzer names")
@click.option("--tt-window", default=40, type=int, help="TextTiling window size (w)")
@click.option("--tt-smoothing", default=20, type=int, help="TextTiling smoothing (k)")
@click.option("--characters", default=None, help="Comma-separated character names (e.g., emil,felix)")
def analyze(file_path, output, title, only, tt_window, tt_smoothing, characters):
    """Analyze a manuscript file."""
    # Read manuscript
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip BOM
    text = text.lstrip("\uFEFF")

    # Derive title and slug
    if title is None:
        title = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").title()
    slug = slugify(title)

    # Output directory
    if output is None:
        output = os.path.join("shared", "analyses", slug)

    # Parse --characters flag
    character_list: list[str] = []
    if characters:
        parsed = [name for name in (n.strip().lower() for n in characters.split(",")) if name]
        character_list = list(dict.fromkeys(parsed))  # dedupe, preserve order

    # Build config
    overrides: dict = {
        "texttiling_w": tt_window,
        "texttiling_k": tt_smoothing,
    }
    if character_list:
        overrides["characters"] = character_list
    config = merge_config(overrides)

    # Determine which analyzers to run
    if only:
        analyzer_names = [n.strip() for n in only.split(",")]
    else:
        analyzer_names = list_analyzers()

    # Topological sort for dependency ordering
    try:
        analyzer_names = resolve_execution_order(analyzer_names)
    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        raise SystemExit(1)

    # Run analyzers
    click.echo(f"Analyzing: {file_path}")
    click.echo(f"Output:    {output}")
    click.echo(f"Title:     {title} (slug: {slug})")
    click.echo(f"Analyzers: {', '.join(analyzer_names)}")
    click.echo()

    all_warnings: list[str] = []
    results = {}

    for name in analyzer_names:
        try:
            analyzer = get_analyzer(name)
        except KeyError:
            click.echo(f"  WARNING: Unknown analyzer '{name}', skipping.")
            all_warnings.append(f"Unknown analyzer: {name}")
            continue

        click.echo(f"  Running {name}...")
        try:
            result = analyzer.analyze(text, config, context=results)
        except Exception as e:
            click.echo(f"  ERROR: Analyzer '{name}' failed: {e}", err=True)
            all_warnings.append(f"Analyzer '{name}' failed: {e}")
            continue
        results[name] = result

        if result.warnings:
            for w in result.warnings:
                click.echo(f"    WARNING: {w}")
            all_warnings.extend(result.warnings)

    # Fail if no analyzers succeeded
    if analyzer_names and not results:
        click.echo("ERROR: All analyzers failed.", err=True)
        raise SystemExit(1)

    # --- Enrichment pipeline ---

    # 1. Apply readability enrichment to texttiling blocks
    if "readability" in results and "texttiling" in results:
        readability_blocks = {
            b["block_id"]: b for b in results["readability"].data["per_block"]
        }
        for block in results["texttiling"].data["blocks"]:
            extra = readability_blocks.get(block["id"], {})
            for key in ("coleman_liau", "smog", "ari"):
                if key in extra:
                    block["metrics"][key] = extra[key]

    # 2. Apply chapter assignments to texttiling blocks
    if "chapters" in results and "texttiling" in results:
        mapping = results["chapters"].data.get("block_to_chapter", {})
        for block in results["texttiling"].data["blocks"]:
            block["chapter"] = mapping.get(str(block["id"]))

    # 3. Add pacing to texttiling data
    if "pacing" in results and "texttiling" in results:
        results["texttiling"].data["pacing"] = dict(results["pacing"].data)

    # --- Write output ---
    click.echo()
    click.echo("Writing output...")

    # analysis.json (AFTER enrichment)
    if "texttiling" in results:
        path = write_analysis(output, results["texttiling"].data)
        click.echo(f"  {path}")

    # characters.json (from agency) — spec-compliant, characters dict only
    if "agency" in results:
        characters_payload = {"characters": results["agency"].data["characters"]}
        path = write_characters(output, characters_payload)
        click.echo(f"  {path}")

    # chapters.json (spec-compliant: chapters list only, no block_to_chapter)
    if "chapters" in results:
        chapters_payload = {"chapters": results["chapters"].data["chapters"]}
        path = write_chapters(output, chapters_payload)
        click.echo(f"  {path}")

    # sentiment.json
    if "sentiment" in results:
        path = write_sentiment(output, results["sentiment"].data)
        click.echo(f"  {path}")

    # Copy manuscript
    ms_path = copy_manuscript(file_path, output)
    click.echo(f"  {ms_path}")

    # Word/char count from clean text
    word_count = len(text.split())
    char_count = len(text)

    # Use agency-detected character list if available, else config
    if "agency" in results:
        manifest_character_list = results["agency"].data.get("character_list", [])
    else:
        manifest_character_list = config["characters"]

    # Chapter count from chapters result
    chapter_count = 0
    if "chapters" in results:
        chapter_count = len(results["chapters"].data["chapters"])

    # Manifest
    manifest = build_manifest(
        title=title,
        slug=slug,
        source_file=file_path,
        word_count=word_count,
        char_count=char_count,
        character_list=manifest_character_list,
        analyzers_run=list(results.keys()),
        parameters={
            "texttiling_w": tt_window,
            "texttiling_k": tt_smoothing,
            "spacy_model": config["spacy_model"],
            "coref_enabled": config["coref_enabled"],
            "mattr_window": config["mattr_window"],
        },
        chapter_count=chapter_count,
        warnings=all_warnings,
    )
    path = write_manifest(output, manifest)
    click.echo(f"  {path}")

    click.echo()
    click.echo("Done.")


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--block", required=True, type=int, help="Block ID to extract (1-based, matches analysis.json)")
@click.option("--tt-window", default=40, type=int, help="TextTiling window size (w)")
@click.option("--tt-smoothing", default=20, type=int, help="TextTiling smoothing (k)")
@click.option("--json", "output_json", is_flag=True, default=False, help="Output as JSON")
def extract(file_path, block, tt_window, tt_smoothing, output_json):
    """Extract a specific block for close reading."""
    from nltk.tokenize import TextTilingTokenizer

    from lit_engine.analyzers.texttiling import build_blocks, map_tile_offsets, prepare_text

    # Read manuscript
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.lstrip("\uFEFF")

    # Prepare and tile
    clean, formatted, offset_map = prepare_text(text)

    config = merge_config({
        "texttiling_w": tt_window,
        "texttiling_k": tt_smoothing,
    })

    tt = TextTilingTokenizer(w=tt_window, k=tt_smoothing)
    try:
        tiles = tt.tokenize(formatted)
    except ValueError:
        fallback_w = config.get("texttiling_fallback_w", 20)
        fallback_k = config.get("texttiling_fallback_k", 10)
        tt = TextTilingTokenizer(w=fallback_w, k=fallback_k)
        try:
            tiles = tt.tokenize(formatted)
        except ValueError as e2:
            click.echo(f"ERROR: TextTiling failed: {e2}", err=True)
            raise SystemExit(1)

    if not tiles:
        click.echo("ERROR: TextTiling produced 0 blocks. Try smaller window/smoothing values.", err=True)
        raise SystemExit(1)

    tile_offsets, _offset_warnings = map_tile_offsets(formatted, tiles, offset_map, clean)
    blocks, _warnings = build_blocks(tiles, tile_offsets, clean, config)

    total_blocks = len(blocks)

    # Bounds check (1-based)
    if block < 1 or block > total_blocks:
        click.echo(f"ERROR: Block {block} out of range (1..{total_blocks})", err=True)
        raise SystemExit(1)

    b = blocks[block - 1]
    block_text = clean[b["start_char"]:b["end_char"]]
    sentences = sent_tokenize(block_text)
    alpha_words = [w for w in word_tokenize(block_text) if w.isalpha()]
    word_count = len(alpha_words)
    sentence_count = len(sentences)
    avg_wps = round(word_count / sentence_count, 1) if sentence_count > 0 else 0.0

    # Per-sentence breakdown
    sent_details = []
    for i, s in enumerate(sentences):
        s_words = [w for w in word_tokenize(s) if w.isalpha()]
        sent_details.append({
            "index": i + 1,
            "word_count": len(s_words),
            "text": s,
        })

    if output_json:
        payload = {
            "block_id": block,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": avg_wps,
            "text": block_text,
            "sentences": sent_details,
            "parameters": {"tt_window": tt_window, "tt_smoothing": tt_smoothing},
            "total_blocks": total_blocks,
        }
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        click.echo(f"--- Block {block} ---")
        click.echo(f"Words: {word_count}")
        click.echo(f"Sentences: {sentence_count}")
        click.echo(f"Avg words/sentence: {avg_wps}")
        click.echo()
        click.echo("--- Full text ---")
        click.echo(block_text)
        click.echo()
        click.echo("--- Sentence breakdown ---")
        for sd in sent_details:
            preview = sd["text"][:100]
            ellipsis = "..." if len(sd["text"]) > 100 else ""
            click.echo(f"  [{sd['index']}] ({sd['word_count']} words) {preview}{ellipsis}")


def _expand_with_deps(analyzer_name: str) -> list[str]:
    """Expand an analyzer name to include all transitive dependencies."""
    if analyzer_name not in _REGISTRY:
        raise click.ClickException(f"Unknown analyzer: {analyzer_name!r}")

    seen: set[str] = set()
    order: list[str] = []
    queue = [analyzer_name]
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        order.append(name)
        if name in _REGISTRY:
            inst = _REGISTRY[name]()
            for dep in inst.requires():
                if dep not in seen:
                    queue.append(dep)

    return order


@main.command()
@click.argument("analyzer_name")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--title", "-t", default=None, help="Manuscript title (for slug)")
@click.option("--tt-window", default=40, type=int, help="TextTiling window size (w)")
@click.option("--tt-smoothing", default=20, type=int, help="TextTiling smoothing (k)")
@click.option("--characters", default=None, help="Comma-separated character names")
@click.pass_context
def rerun(ctx, analyzer_name, file_path, output, title, tt_window, tt_smoothing, characters):
    """Re-run a single analyzer (with its dependencies).

    Expands transitive dependencies and delegates to `analyze`. This performs
    a fresh partial recompute — output files and manifest reflect only the
    rerun subset, not a merge with prior results.
    """
    expanded = _expand_with_deps(analyzer_name)
    only_str = ",".join(expanded)
    ctx.invoke(
        analyze,
        file_path=file_path,
        output=output,
        title=title,
        only=only_str,
        tt_window=tt_window,
        tt_smoothing=tt_smoothing,
        characters=characters,
    )


@main.command("list-analyzers")
def list_analyzers_cmd():
    """List available analyzers."""
    for name in list_analyzers():
        analyzer = get_analyzer(name)
        click.echo(f"  {name:20s} {analyzer.description}")


if __name__ == "__main__":
    main()
