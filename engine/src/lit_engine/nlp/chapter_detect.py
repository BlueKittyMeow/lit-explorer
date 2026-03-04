"""Chapter boundary detection for literary manuscripts."""

import re
from dataclasses import dataclass


@dataclass
class ChapterBoundary:
    """A detected chapter boundary with number, title, and char range."""

    number: int          # 1-indexed chapter number
    title: str           # chapter title (may be empty string)
    start_char: int      # inclusive start offset in text
    end_char: int        # exclusive end offset in text


# Default pattern: "Chapter N", "Chapter N - Title", "Kapitel N", "Teil N"
# Requires explicit marker word — no bare numerals (too many false positives).
DEFAULT_CHAPTER_PATTERN = re.compile(
    r"""(?ix)
    ^[ \t]*
    (?:chapter|kapitel|teil)
    \s+
    (\d+)                        # group 1: chapter number
    (?:\s*[-\u2013\u2014]\s*(.+))?   # group 2: optional title after dash/en-dash/em-dash
    \s*$
    """,
)


def detect_chapters(
    text: str,
    pattern: re.Pattern | str | None = None,
    min_chapter_words: int = 100,
) -> list[ChapterBoundary]:
    """
    Detect chapter boundaries in a manuscript.

    Strategy:
    1. Split text into lines, tracking char offsets.
    2. Match lines against chapter heading pattern.
    3. Require at least one blank line before heading (except at text start).
    4. Extract chapter number and optional title from the heading itself.
    5. Each chapter spans from heading to next heading (or end of text).
    6. Filter out "chapters" shorter than min_chapter_words.

    Returns list of ChapterBoundary sorted by start_char.
    Returns empty list if no chapters detected.
    """
    if pattern is None:
        pat = DEFAULT_CHAPTER_PATTERN
    elif isinstance(pattern, str):
        pat = re.compile(pattern)
    else:
        pat = pattern

    # Split into lines with char offsets
    lines: list[tuple[str, int]] = []  # (line_text, start_char)
    offset = 0
    for line in text.split("\n"):
        lines.append((line, offset))
        offset += len(line) + 1  # +1 for the newline

    # Find chapter headings
    headings: list[tuple[int, int, str]] = []  # (number, start_char, title)
    for i, (line_text, line_start) in enumerate(lines):
        m = pat.match(line_text)
        if m is None:
            continue

        # Require blank line before (except at very start of text)
        if i > 0:
            prev_line = lines[i - 1][0].strip()
            if prev_line != "":
                continue

        chapter_num = int(m.group(1))
        title = (m.group(2) or "").strip()
        headings.append((chapter_num, line_start, title))

    if not headings:
        return []

    # Build chapter boundaries
    chapters: list[ChapterBoundary] = []
    for idx, (num, start, title) in enumerate(headings):
        if idx + 1 < len(headings):
            end = headings[idx + 1][1]
        else:
            end = len(text)

        chapters.append(ChapterBoundary(
            number=num,
            title=title,
            start_char=start,
            end_char=end,
        ))

    # Filter by minimum word count
    if min_chapter_words > 0:
        chapters = [
            ch for ch in chapters
            if len(text[ch.start_char:ch.end_char].split()) >= min_chapter_words
        ]

    return chapters
