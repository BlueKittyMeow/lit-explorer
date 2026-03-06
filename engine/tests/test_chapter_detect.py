"""Tests for chapter boundary detection utility."""

import pytest

from lit_engine.nlp.chapter_detect import ChapterBoundary, detect_chapters


# --- Fixtures ---

CHAPTERS_TEXT = (
    "Some introductory text before the first chapter.\n"
    "\n"
    "Chapter 1 - Café Union\n"
    "Emil walked to the window. He opened the door carefully. "
    "The morning light streamed through the glass. "
    "He looked around the room and shook his head slowly. "
    "Felix sat at the table, absorbed in thought. "
    "They stood there looking at one another.\n"
    "\n"
    "Chapter 2 - The Theatre\n"
    "Clara entered the hall and looked around. "
    "The seats were empty, the stage dark. "
    "She noticed a figure in the balcony above. "
    "The silence was absolute.\n"
    "\n"
    "Chapter 3 - Pruritus\n"
    "The laboratory was cold. Emil shivered.\n"
)


class TestDetectChapters:
    def test_finds_all_chapters(self):
        """Detects all three chapters in the fixture text."""
        chapters = detect_chapters(CHAPTERS_TEXT, min_chapter_words=0)
        assert len(chapters) == 3

    def test_chapter_numbers(self):
        """Chapter numbers are extracted correctly."""
        chapters = detect_chapters(CHAPTERS_TEXT, min_chapter_words=0)
        assert [c.number for c in chapters] == [1, 2, 3]

    def test_chapter_titles(self):
        """Chapter titles are extracted from the dash separator."""
        chapters = detect_chapters(CHAPTERS_TEXT, min_chapter_words=0)
        assert chapters[0].title == "Café Union"
        assert chapters[1].title == "The Theatre"
        assert chapters[2].title == "Pruritus"

    def test_chapter_boundaries_contiguous(self):
        """Each chapter ends where the next begins (no gaps)."""
        chapters = detect_chapters(CHAPTERS_TEXT, min_chapter_words=0)
        for i in range(len(chapters) - 1):
            assert chapters[i].end_char == chapters[i + 1].start_char, (
                f"Gap between chapter {chapters[i].number} and {chapters[i+1].number}"
            )

    def test_last_chapter_ends_at_text_end(self):
        """Last chapter extends to end of text."""
        chapters = detect_chapters(CHAPTERS_TEXT, min_chapter_words=0)
        assert chapters[-1].end_char == len(CHAPTERS_TEXT)

    def test_no_chapters_returns_empty(self):
        """Text with no chapter markers returns empty list."""
        text = "Just some plain text with no chapter headings at all."
        chapters = detect_chapters(text)
        assert chapters == []

    def test_blank_line_required_for_subsequent_headings(self):
        """Second+ heading mid-paragraph without blank line is not detected."""
        text = (
            "\n"
            "Chapter 1 - Real Chapter\n"
            + ("Word " * 200) + "\n"
            "Chapter 2 - False Positive\n"  # no blank line before
            + ("Word " * 200) + "\n"
            "\n"
            "Chapter 3 - Also Real\n"
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=0)
        numbers = [c.number for c in chapters]
        assert 1 in numbers
        assert 2 not in numbers  # rejected: no blank line
        assert 3 in numbers

    def test_first_heading_tolerates_frontmatter(self):
        """First chapter heading detected even without blank line (epigraph/frontmatter).

        The content between chapters must span >15 lines so the lookahead
        TOC detector doesn't see Chapter 2 as a nearby heading.
        """
        body = "".join(f"Sentence number {i} in this chapter.\n" for i in range(20))
        text = (
            "When lights were paling one by one\n"
            "- W.B. Yeats\n"
            "Chapter 1 - Café Union\n"
            + body
            + "\n"
            "Chapter 2 - The Theatre\n"
            + body
        )
        chapters = detect_chapters(text, min_chapter_words=0)
        assert len(chapters) == 2
        assert chapters[0].number == 1
        assert chapters[0].title == "Café Union"
        assert chapters[1].number == 2

    def test_min_chapter_words_filter(self):
        """Chapters shorter than min_chapter_words are filtered out."""
        text = (
            "\n"
            "Chapter 1 - Real Chapter\n"
            + ("Word " * 200) + "\n"
            "\n"
            "Chapter 2 - Too Short\n"
            "Only a few words here.\n"
            "\n"
            "Chapter 3 - Also Real\n"
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=100)
        numbers = [c.number for c in chapters]
        assert 1 in numbers
        assert 3 in numbers
        assert 2 not in numbers

    def test_filtered_chapters_remain_contiguous(self):
        """After filtering a short middle chapter, ranges stay contiguous."""
        text = (
            "\n"
            "Chapter 1 - Real Chapter\n"
            + ("Word " * 200) + "\n"
            "\n"
            "Chapter 2 - Too Short\n"
            "Only a few words here.\n"
            "\n"
            "Chapter 3 - Also Real\n"
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=100)
        assert len(chapters) == 2
        # Chapter 1 should extend to Chapter 3's start (no gap)
        assert chapters[0].end_char == chapters[1].start_char
        # Chapter 3 extends to end of text
        assert chapters[1].end_char == len(text)

    def test_chapter_without_title(self):
        """Chapter heading without dash/title extracts empty title."""
        text = (
            "\n"
            "Chapter 1\n"
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=0)
        assert len(chapters) == 1
        assert chapters[0].number == 1
        assert chapters[0].title == ""

    def test_en_dash_separator(self):
        """En-dash in heading is accepted as title separator."""
        text = (
            "\n"
            "Chapter 1 \u2013 The Beginning\n"
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=0)
        assert chapters[0].title == "The Beginning"

    def test_toc_entries_rejected_by_lookahead(self):
        """TOC entries are rejected: nearby heading patterns trigger the lookahead guard."""
        text = (
            "Table of Contents\n"
            "Chapter 1 - Dawn\n"        # TOC entry (first heading, no blank line)
            "Chapter 2 - Midday\n"      # TOC entry (rejected: no blank line, not first)
            "\n"
            "Chapter 1 - Dawn\n"        # Real chapter
            + ("Word " * 200) + "\n"
            "\n"
            "Chapter 2 - Midday\n"      # Real chapter
            + ("Word " * 200) + "\n"
        )
        chapters = detect_chapters(text, min_chapter_words=100)
        # TOC entries rejected by lookahead (nearby headings). Real chapters survive.
        assert len(chapters) == 2
        assert chapters[0].number == 1
        assert chapters[1].number == 2
