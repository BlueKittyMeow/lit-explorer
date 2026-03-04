"""Sentiment analyzer — VADER sentence-level sentiment with emotional arc."""

from nltk.tokenize import sent_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from lit_engine.analyzers import Analyzer, AnalyzerResult, register
from lit_engine.nlp.chapter_detect import detect_chapters
from lit_engine.nlp.sentence_locate import locate_sentences


@register
class SentimentAnalyzer(Analyzer):
    """VADER sentence-level sentiment analysis with emotional arc."""

    name = "sentiment"
    description = "VADER sentence-level sentiment analysis with emotional arc"

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # 1. Sentence-tokenize
        sentences = sent_tokenize(text)
        if not sentences:
            return self._empty_result(warnings + ["No sentences found."])

        total = len(sentences)

        # 2. Map sentences to char offsets
        sent_offsets = locate_sentences(text, sentences)

        # 3. Score each sentence with VADER
        vader = SentimentIntensityAnalyzer()
        arc: list[dict] = []
        scored: list[tuple[int, int, int, dict]] = []  # (idx, start, end, scores)

        for i, (sent, (start, end)) in enumerate(zip(sentences, sent_offsets)):
            scores = vader.polarity_scores(sent)
            position = round(i / max(total - 1, 1), 4)
            arc.append({
                "position": position,
                "compound": round(scores["compound"], 4),
                "pos": round(scores["pos"], 4),
                "neg": round(scores["neg"], 4),
                "neu": round(scores["neu"], 4),
            })
            scored.append((i, start, end, scores))

        # 4. Detect chapters for chapter_averages
        chapter_pattern = config.get("chapter_pattern")
        min_ch_words = config.get("min_chapter_words", 100)
        chapters = detect_chapters(text, pattern=chapter_pattern, min_chapter_words=min_ch_words)

        chapter_averages: list[dict] = []
        for ch in chapters:
            # Filter sentences whose char range overlaps this chapter
            ch_compounds = [
                sc[3]["compound"]
                for sc in scored
                if sc[1] < ch.end_char and sc[2] > ch.start_char
            ]
            if ch_compounds:
                avg = round(sum(ch_compounds) / len(ch_compounds), 4)
            else:
                avg = 0.0
            chapter_averages.append({"chapter": ch.number, "compound": avg})

        # 5. Find extremes
        if arc:
            most_pos_idx = max(range(len(arc)), key=lambda j: arc[j]["compound"])
            most_neg_idx = min(range(len(arc)), key=lambda j: arc[j]["compound"])
            extremes = {
                "most_positive": {
                    "position": arc[most_pos_idx]["position"],
                    "text_preview": sentences[most_pos_idx][:120],
                    "score": arc[most_pos_idx]["compound"],
                },
                "most_negative": {
                    "position": arc[most_neg_idx]["position"],
                    "text_preview": sentences[most_neg_idx][:120],
                    "score": arc[most_neg_idx]["compound"],
                },
            }
        else:
            extremes = {"most_positive": None, "most_negative": None}

        # 6. Build smoothed_arc (decimation, not interpolation)
        target_points = config.get("smoothed_arc_points", 200)
        if len(arc) <= target_points:
            smoothed_arc = [{"position": e["position"], "compound": e["compound"]} for e in arc]
        else:
            # Evenly-spaced index selection
            step = (len(arc) - 1) / (target_points - 1)
            indices = [round(i * step) for i in range(target_points)]
            smoothed_arc = [
                {"position": arc[idx]["position"], "compound": arc[idx]["compound"]}
                for idx in indices
            ]

        return AnalyzerResult(
            analyzer_name="sentiment",
            data={
                "method": "vader",
                "granularity": "sentence",
                "arc": arc,
                "smoothed_arc": smoothed_arc,
                "chapter_averages": chapter_averages,
                "extremes": extremes,
            },
            warnings=warnings,
        )

    def _empty_result(self, warnings: list[str]) -> AnalyzerResult:
        return AnalyzerResult(
            analyzer_name="sentiment",
            data={
                "method": "vader",
                "granularity": "sentence",
                "arc": [],
                "smoothed_arc": [],
                "chapter_averages": [],
                "extremes": {"most_positive": None, "most_negative": None},
            },
            warnings=warnings,
        )
