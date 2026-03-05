"""Chapters analyzer — chapter boundary detection and per-chapter aggregation."""

from collections import Counter

import textstat
from nltk.tokenize import sent_tokenize, word_tokenize

from lit_engine.analyzers import Analyzer, AnalyzerResult, register
from lit_engine.analyzers.texttiling import mattr as compute_mattr
from lit_engine.nlp.chapter_detect import detect_chapters
from lit_engine.nlp.sentence_locate import locate_sentences


@register
class ChaptersAnalyzer(Analyzer):
    """Chapter boundary detection and per-chapter metric aggregation."""

    name = "chapters"
    description = "Chapter boundary detection and per-chapter metric aggregation"

    def requires(self) -> list[str]:
        return ["texttiling", "agency", "dialogue", "sentiment"]

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # 1. Detect chapter boundaries
        chapter_pattern = config.get("chapter_pattern")
        min_ch_words = config.get("min_chapter_words", 100)
        boundaries = detect_chapters(
            text, pattern=chapter_pattern, min_chapter_words=min_ch_words,
        )

        # Single-chapter fallback
        if not boundaries:
            from lit_engine.nlp.chapter_detect import ChapterBoundary
            boundaries = [ChapterBoundary(
                number=1, title="", start_char=0, end_char=len(text),
            )]
            warnings.append("No chapter headings detected; treating entire text as one chapter.")

        # 2. Get context results
        tt_result = context.get("texttiling") if context else None
        agency_result = context.get("agency") if context else None
        dialogue_result = context.get("dialogue") if context else None
        sentiment_result = context.get("sentiment") if context else None
        blocks = tt_result.data.get("blocks", []) if tt_result else []
        character_list = agency_result.data.get("character_list", []) if agency_result else []
        dialogue_spans = dialogue_result.data.get("spans", []) if dialogue_result else []
        sentiment_arc = sentiment_result.data.get("arc", []) if sentiment_result else []

        # Pre-compute sentiment sentence offsets for chapter averaging
        sentences = sent_tokenize(text)
        sent_offsets = locate_sentences(text, sentences)

        # 3. Build block_to_chapter mapping
        block_to_chapter: dict[str, int] = {}
        for block in blocks:
            block_mid = (block["start_char"] + block["end_char"]) / 2
            assigned = boundaries[0].number  # default to first chapter
            for ch in boundaries:
                if ch.start_char <= block_mid < ch.end_char:
                    assigned = ch.number
                    break
            block_to_chapter[str(block["id"])] = assigned

        # 4. Build per-chapter data
        mattr_window = config.get("mattr_window", 50)
        chapters_output: list[dict] = []

        for ch in boundaries:
            ch_text = text[ch.start_char:ch.end_char]
            ch_words = ch_text.split()
            word_count = len(ch_words)

            ch_sentences = sent_tokenize(ch_text)
            sentence_count = len(ch_sentences)

            if sentence_count > 0 and word_count > 0:
                avg_sentence_length = round(word_count / sentence_count, 1)
            else:
                avg_sentence_length = 0.0

            # MATTR
            alpha_words = [w.lower() for w in word_tokenize(ch_text) if w.isalpha()]
            ch_mattr = round(
                compute_mattr(alpha_words, window_length=min(mattr_window, len(alpha_words)))
                if alpha_words else 0.0,
                3,
            )

            # Readability
            if ch_text.strip() and len(ch_text.split()) >= 3:
                flesch_ease = round(textstat.flesch_reading_ease(ch_text), 1)
                fog = round(textstat.gunning_fog(ch_text), 1)
            else:
                flesch_ease = 0.0
                fog = 0.0

            # Dialogue ratio: intersect dialogue spans with chapter char range
            ch_dialogue_words = 0
            for span in dialogue_spans:
                s_start = span["start_char"]
                s_end = span["end_char"]
                # Overlap with chapter
                overlap_start = max(s_start, ch.start_char)
                overlap_end = min(s_end, ch.end_char)
                if overlap_start < overlap_end:
                    overlap_text = text[overlap_start:overlap_end]
                    ch_dialogue_words += len(overlap_text.split())

            dialogue_ratio = round(ch_dialogue_words / word_count, 3) if word_count > 0 else 0.0

            # Character mentions (token-level, case-insensitive)
            ch_token_counts = Counter(w.lower() for w in word_tokenize(ch_text))
            character_mentions: dict[str, int] = {}
            for name in character_list:
                character_mentions[name] = ch_token_counts.get(name.lower(), 0)

            # Dominant character
            if character_mentions:
                sorted_chars = sorted(
                    character_mentions.items(), key=lambda x: x[1], reverse=True,
                )
                if len(sorted_chars) >= 2:
                    top, second = sorted_chars[0], sorted_chars[1]
                    if top[1] > 0 and second[1] > 0:
                        ratio_diff = abs(top[1] - second[1]) / max(top[1], 1)
                        if ratio_diff <= 0.20:
                            dominant = "shared"
                        else:
                            dominant = top[0]
                    elif top[1] > 0:
                        dominant = top[0]
                    else:
                        dominant = "none"
                elif sorted_chars[0][1] > 0:
                    dominant = sorted_chars[0][0]
                else:
                    dominant = "none"
            else:
                dominant = "none"

            # Sentiment: average of sentences overlapping this chapter
            ch_compounds = []
            for i, (s_start, s_end) in enumerate(sent_offsets):
                if s_start < ch.end_char and s_end > ch.start_char and i < len(sentiment_arc):
                    ch_compounds.append(sentiment_arc[i]["compound"])

            if ch_compounds:
                sentiment = {
                    "compound": round(sum(ch_compounds) / len(ch_compounds), 4),
                    "pos": 0.0,  # Could compute averages for these too
                    "neg": 0.0,
                    "neu": 0.0,
                }
                # Compute pos/neg/neu averages from arc
                ch_pos = []
                ch_neg = []
                ch_neu = []
                for i, (s_start, s_end) in enumerate(sent_offsets):
                    if s_start < ch.end_char and s_end > ch.start_char and i < len(sentiment_arc):
                        ch_pos.append(sentiment_arc[i].get("pos", 0))
                        ch_neg.append(sentiment_arc[i].get("neg", 0))
                        ch_neu.append(sentiment_arc[i].get("neu", 0))
                if ch_pos:
                    sentiment["pos"] = round(sum(ch_pos) / len(ch_pos), 4)
                if ch_neg:
                    sentiment["neg"] = round(sum(ch_neg) / len(ch_neg), 4)
                if ch_neu:
                    sentiment["neu"] = round(sum(ch_neu) / len(ch_neu), 4)
            else:
                sentiment = {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 0.0}

            # Block range
            ch_block_ids = [
                int(bid) for bid, cnum in block_to_chapter.items()
                if cnum == ch.number
            ]
            if ch_block_ids:
                block_range = [min(ch_block_ids), max(ch_block_ids)]
            else:
                block_range = [0, 0]

            chapters_output.append({
                "number": ch.number,
                "title": ch.title,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "dialogue_ratio": dialogue_ratio,
                "avg_sentence_length": avg_sentence_length,
                "mattr": ch_mattr,
                "flesch_ease": flesch_ease,
                "fog": fog,
                "character_mentions": character_mentions,
                "dominant_character": dominant,
                "sentiment": sentiment,
                "block_range": block_range,
            })

        return AnalyzerResult(
            analyzer_name="chapters",
            data={
                "chapters": chapters_output,
                "block_to_chapter": block_to_chapter,
            },
            warnings=warnings,
        )
