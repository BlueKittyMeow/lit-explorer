"""TextTiling analyzer: semantic segmentation with MATTR and readability metrics."""

import textstat
from nltk.tokenize import TextTilingTokenizer, sent_tokenize, word_tokenize

from lit_engine.analyzers import Analyzer, AnalyzerResult, register


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


def mattr(tokens: list[str], window_length: int = 50) -> float:
    """
    Moving Average Type-Token Ratio.

    Slides a window across the token list and averages the TTR
    at each position. Length-independent unlike naive TTR.
    """
    if not tokens:
        return 0.0

    if len(tokens) < window_length:
        return len(set(tokens)) / len(tokens)

    ttrs = []
    for i in range(len(tokens) - window_length + 1):
        window = tokens[i : i + window_length]
        ttrs.append(len(set(window)) / window_length)

    return sum(ttrs) / len(ttrs)


def prepare_text(raw_text: str) -> tuple[str, str, list[int]]:
    """
    Prepare text for TextTiling and build an offset map.

    Returns:
        clean_text: BOM-stripped original text (for offset references).
        formatted_text: Double-newlined text for TextTiling.
        offset_map: Maps each index in formatted_text to its index
                     in clean_text. offset_map[formatted_idx] = clean_idx.
                     Inserted characters map to the preceding clean index.
    """
    # Strip BOM
    clean = raw_text.lstrip("\uFEFF")

    # Build formatted text + index map
    formatted_chars: list[str] = []
    offset_map: list[int] = []

    for i, ch in enumerate(clean):
        formatted_chars.append(ch)
        offset_map.append(i)

        if ch == "\n":
            # Insert an extra newline (TextTiling needs paragraph breaks)
            formatted_chars.append("\n")
            offset_map.append(i)  # inserted char maps to same original position

    formatted = "".join(formatted_chars)
    return clean, formatted, offset_map


def map_tile_offsets(
    formatted_text: str,
    tiles: list[str],
    offset_map: list[int],
    clean_text: str,
) -> tuple[list[tuple[int, int]], list[str]]:
    """
    Map TextTiling tile boundaries back to clean_text character offsets.

    Returns:
        offsets: list of (start_char, end_char) tuples in clean_text coordinates.
        warnings: list of warnings if fallback paths were used.
    """
    offsets = []
    warnings: list[str] = []
    search_from = 0

    for i, tile in enumerate(tiles):
        # Find this tile in the formatted text.
        # Tiles are substrings of formatted_text (TextTiling splits it).
        tile_start_formatted = formatted_text.find(tile, search_from)

        if tile_start_formatted == -1:
            # Fallback 1: stripped tile might differ slightly
            stripped = tile.strip()
            tile_start_formatted = formatted_text.find(stripped, search_from)
            if tile_start_formatted != -1:
                warnings.append(
                    f"Tile {i}: exact match failed, matched after stripping whitespace. "
                    f"Offset may be approximate."
                )

        if tile_start_formatted == -1:
            # Fallback 2: use sequential position (degraded)
            if offsets:
                tile_start_formatted = search_from
            else:
                tile_start_formatted = 0
            warnings.append(
                f"Tile {i}: could not locate in formatted text. "
                f"Using sequential offset (approximate)."
            )

        tile_end_formatted = tile_start_formatted + len(tile)

        # Clamp to offset_map bounds
        start_idx = min(tile_start_formatted, len(offset_map) - 1)
        end_idx = min(tile_end_formatted - 1, len(offset_map) - 1)

        start_char = offset_map[start_idx]
        end_char = offset_map[end_idx] + 1  # exclusive end

        offsets.append((start_char, end_char))
        search_from = tile_end_formatted

    return offsets, warnings


def build_blocks(
    tiles: list[str],
    tile_offsets: list[tuple[int, int]],
    clean_text: str,
    config: dict,
) -> tuple[list[dict], list[str]]:
    """
    Process tiles into blocks with metrics.

    Short tiles are merged into the preceding block to ensure
    contiguous character coverage (no gaps for the block explorer).

    Returns:
        blocks: List of block dicts matching analysis.json schema.
        warnings: List of warning messages.
    """
    min_words = config.get("texttiling_min_words", 30)
    min_alpha = config.get("texttiling_min_alpha", 20)
    mattr_window = config.get("mattr_window", 50)
    warnings: list[str] = []

    raw_blocks: list[dict] = []  # before merging

    for i, (tile, (start_char, end_char)) in enumerate(zip(tiles, tile_offsets)):
        text_content = tile.replace("\n", " ").strip()
        words = word_tokenize(text_content)
        alpha_words = [w.lower() for w in words if w.isalpha()]

        raw_blocks.append({
            "tile_index": i,
            "start_char": start_char,
            "end_char": end_char,
            "text_content": text_content,
            "words": words,
            "alpha_words": alpha_words,
        })

    # Merge pass: fold short blocks into their predecessor
    merged: list[dict] = []
    for block in raw_blocks:
        is_short = (
            len(block["words"]) < min_words
            or len(block["alpha_words"]) < min_alpha
        )

        if is_short and merged:
            # Merge into preceding block
            prev = merged[-1]
            prev["end_char"] = block["end_char"]
            prev["text_content"] += " " + block["text_content"]
            prev["words"].extend(block["words"])
            prev["alpha_words"].extend(block["alpha_words"])
        elif is_short and not merged:
            # First block is short — keep it, will be merged forward
            merged.append(block)
        else:
            # Check if previous block was a kept-short first block
            if merged and len(merged[-1].get("alpha_words", [])) < min_alpha:
                # Merge the short first block into this one
                prev = merged[-1]
                block["start_char"] = prev["start_char"]
                block["text_content"] = prev["text_content"] + " " + block["text_content"]
                block["words"] = prev["words"] + block["words"]
                block["alpha_words"] = prev["alpha_words"] + block["alpha_words"]
                merged[-1] = block
            else:
                merged.append(block)

    # Compute metrics for each merged block
    blocks: list[dict] = []
    for block_data in merged:
        alpha_words = block_data["alpha_words"]
        text_content = block_data["text_content"]
        sentences = sent_tokenize(text_content)

        if not sentences or not alpha_words:
            warnings.append(
                f"Tile {block_data['tile_index']}: empty after processing, skipped"
            )
            continue

        sent_word_counts = [
            (len([w for w in word_tokenize(s) if w.isalpha()]), s)
            for s in sentences
        ]
        sent_lengths = [wc for wc, _ in sent_word_counts]

        # Find the longest sentence text for the notable preview
        longest_sent_text = max(sent_word_counts, key=lambda x: x[0])[1] if sent_word_counts else ""

        mattr_score = mattr(alpha_words, window_length=min(mattr_window, len(alpha_words)))

        # Readability metrics (textstat wants raw text)
        flesch_ease = textstat.flesch_reading_ease(text_content)
        flesch_grade = textstat.flesch_kincaid_grade(text_content)
        fog = textstat.gunning_fog(text_content)

        block_id = len(blocks) + 1  # 1-indexed, sequential

        blocks.append({
            "id": block_id,
            "tile_index": block_data["tile_index"],
            "start_char": block_data["start_char"],
            "end_char": block_data["end_char"],
            "word_count": len(alpha_words),
            "sentence_count": len(sentences),
            "metrics": {
                "mattr": round(mattr_score, 4),
                "avg_sentence_length": round(len(alpha_words) / len(sentences), 1),
                "max_sentence_length": max(sent_lengths) if sent_lengths else 0,
                "flesch_ease": round(flesch_ease, 1),
                "flesch_grade": round(flesch_grade, 1),
                "gunning_fog": round(fog, 1),
            },
            "sentence_lengths": sent_lengths,
            "preview": text_content[:120] + ("..." if len(text_content) > 120 else ""),
            "longest_sentence_preview": longest_sent_text[:200] + ("..." if len(longest_sent_text) > 200 else ""),
            "chapter": None,  # filled by chapters analyzer in Stage 3
        })

    return blocks, warnings


def compute_notable(blocks: list[dict], top_n: int = 5) -> dict:
    """Compute notable block rankings."""
    if not blocks:
        return {
            "longest_sentences": [],
            "highest_mattr": [],
            "highest_fog": [],
            "shortest_sentences": [],
        }

    by_max_sent = sorted(
        blocks, key=lambda b: b["metrics"]["max_sentence_length"], reverse=True
    )
    by_mattr = sorted(blocks, key=lambda b: b["metrics"]["mattr"], reverse=True)
    by_fog = sorted(blocks, key=lambda b: b["metrics"]["gunning_fog"], reverse=True)
    by_avg_sent_asc = sorted(
        blocks, key=lambda b: b["metrics"]["avg_sentence_length"]
    )

    return {
        "longest_sentences": [b["id"] for b in by_max_sent[:top_n]],
        "highest_mattr": [b["id"] for b in by_mattr[:top_n]],
        "highest_fog": [b["id"] for b in by_fog[:top_n]],
        "shortest_sentences": [b["id"] for b in by_avg_sent_asc[:top_n]],
    }


# ---------------------------------------------------------------------------
# Analyzer class
# ---------------------------------------------------------------------------


@register
class TextTilingAnalyzer(Analyzer):
    name = "texttiling"
    description = "Semantic segmentation via TextTiling with MATTR and readability metrics"

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # Prepare text with offset mapping
        clean_text, formatted_text, offset_map = prepare_text(text)

        # TextTiling with fallback
        w = config.get("texttiling_w", 40)
        k = config.get("texttiling_k", 20)
        fallback_w = config.get("texttiling_fallback_w", 20)
        fallback_k = config.get("texttiling_fallback_k", 10)

        tt = TextTilingTokenizer(w=w, k=k)
        try:
            tiles = tt.tokenize(formatted_text)
        except ValueError as e:
            warnings.append(
                f"TextTiling failed with w={w}, k={k}: {e}. "
                f"Falling back to w={fallback_w}, k={fallback_k}."
            )
            tt = TextTilingTokenizer(w=fallback_w, k=fallback_k)
            try:
                tiles = tt.tokenize(formatted_text)
            except ValueError as e2:
                warnings.append(f"TextTiling fallback also failed: {e2}.")
                tiles = []

        if not tiles:
            return AnalyzerResult(
                analyzer_name=self.name,
                data={
                    "parameters": {
                        "w": w,
                        "k": k,
                        "mattr_window": config.get("mattr_window", 50),
                    },
                    "total_blocks": 0,
                    "blocks": [],
                    "notable": {
                        "longest_sentences": [],
                        "highest_mattr": [],
                        "highest_fog": [],
                        "shortest_sentences": [],
                    },
                },
                warnings=warnings + ["TextTiling produced 0 tiles."],
            )

        # Map tile offsets back to clean text
        tile_offsets, offset_warnings = map_tile_offsets(
            formatted_text, tiles, offset_map, clean_text
        )
        warnings.extend(offset_warnings)

        # Build blocks with metrics (merging short tiles)
        blocks, block_warnings = build_blocks(tiles, tile_offsets, clean_text, config)
        warnings.extend(block_warnings)

        # Notable rankings
        notable = compute_notable(blocks)

        return AnalyzerResult(
            analyzer_name=self.name,
            data={
                "parameters": {
                    "w": w,
                    "k": k,
                    "mattr_window": config.get("mattr_window", 50),
                },
                "total_blocks": len(blocks),
                "blocks": blocks,
                "notable": notable,
            },
            warnings=warnings,
        )
