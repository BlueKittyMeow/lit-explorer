"""Curly-quote-aware dialogue extraction."""

from dataclasses import dataclass


@dataclass
class DialogueSpan:
    """A dialogue span with char offsets and extracted text."""

    start_char: int      # inclusive (at opening quote)
    end_char: int        # exclusive (after closing quote)
    text: str            # dialogue content (without quotes)


# Quote pairs: (open_char, close_char) — processed in priority order.
# German „..." first (most specific opener), then English curly, then straight.
QUOTE_PAIRS: list[tuple[str, str]] = [
    ("\u201e", "\u201c"),   # „ " German low-high
    ("\u201c", "\u201d"),   # " " English curly double
    ('"', '"'),             # " " straight double (fallback)
]


def _find_paragraph_end(text: str, pos: int) -> int:
    """Find the end of the paragraph containing pos (double newline or EOF)."""
    idx = text.find("\n\n", pos)
    if idx == -1:
        return len(text)
    return idx


def extract_dialogue(
    text: str,
    quote_pairs: list[tuple[str, str]] | None = None,
) -> list[DialogueSpan]:
    """
    Extract dialogue spans using paired quote matching.

    Algorithm:
    1. Scan character by character.
    2. When an opening quote is found, record position and which pair.
    3. Scan for matching closing quote of the same pair.
    4. If closing quote not found in same paragraph:
       a. Check if next paragraph starts with opening quote (continued dialogue).
       b. If yes: continue scanning past the next opening quote.
       c. If no: terminate span at paragraph end.
    5. If no closing quote before EOF: terminate span at EOF.
    6. Filter out spans with empty text.

    Returns list of DialogueSpan sorted by start_char.
    """
    if quote_pairs is None:
        quote_pairs = QUOTE_PAIRS

    # Build opener→(closer, pair_index) lookup, respecting priority order.
    # If an opener appears in multiple pairs, first one wins.
    opener_map: dict[str, tuple[str, int]] = {}
    for idx, (opener, closer) in enumerate(quote_pairs):
        if opener not in opener_map:
            opener_map[opener] = (closer, idx)

    spans: list[DialogueSpan] = []
    i = 0
    text_len = len(text)

    while i < text_len:
        ch = text[i]

        if ch not in opener_map:
            i += 1
            continue

        closer, _pair_idx = opener_map[ch]
        span_start = i
        i += 1  # move past opening quote

        # Scan for closing quote
        found_close = False
        while i < text_len:
            if text[i] == closer:
                # Found closing quote
                span_end = i + 1  # exclusive, after closing quote
                content = text[span_start + 1:i]
                found_close = True
                i += 1
                break

            # Check for paragraph break (double newline)
            if text[i] == "\n" and i + 1 < text_len and text[i + 1] == "\n":
                # Look ahead past blank lines for continuation
                j = i + 2
                while j < text_len and text[j] in ("\n", " ", "\t"):
                    j += 1

                if j < text_len and text[j] == ch:
                    # Next paragraph starts with opening quote → continued dialogue
                    # Skip the opening quote of continuation
                    i = j + 1
                    continue
                else:
                    # No continuation — terminate at paragraph break
                    span_end = i
                    content = text[span_start + 1:i]
                    found_close = True
                    i = j
                    break

            i += 1

        if not found_close:
            # EOF reached without closing quote
            span_end = text_len
            content = text[span_start + 1:text_len]

        # Filter empty spans
        if content.strip():
            spans.append(DialogueSpan(
                start_char=span_start,
                end_char=span_end,
                text=content,
            ))

    return spans
