"""Silence analyzer — measures gaps between dialogue."""

from lit_engine.analyzers import Analyzer, AnalyzerResult, register


@register
class SilenceAnalyzer(Analyzer):
    """Measures gaps between dialogue and maps character silence."""

    name = "silence"
    description = "Measures gaps between dialogue and maps character silence"

    def requires(self) -> list[str]:
        return ["dialogue"]

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # Get dialogue spans from dialogue result
        dialogue_result = context["dialogue"] if context else None
        spans = dialogue_result.data.get("spans", []) if dialogue_result else []

        if not spans:
            warnings.append("No dialogue spans found.")
            return AnalyzerResult(
                analyzer_name="silence",
                data={
                    "gaps": [],
                    "longest_silence": None,
                    "avg_gap_words": 0.0,
                    "total_gaps": 0,
                },
                warnings=warnings,
            )

        # Sort spans by start_char (should already be sorted)
        sorted_spans = sorted(spans, key=lambda s: s["start_char"])

        # Compute gaps
        text_len = len(text)
        gaps: list[dict] = []

        # Gap before first dialogue
        if sorted_spans[0]["start_char"] > 0:
            gap_text = text[0:sorted_spans[0]["start_char"]]
            wc = len(gap_text.split())
            if wc > 0:
                gaps.append({
                    "start_char": 0,
                    "end_char": sorted_spans[0]["start_char"],
                    "word_count": wc,
                })

        # Gaps between consecutive spans
        for i in range(len(sorted_spans) - 1):
            gap_start = sorted_spans[i]["end_char"]
            gap_end = sorted_spans[i + 1]["start_char"]
            if gap_end > gap_start:
                gap_text = text[gap_start:gap_end]
                wc = len(gap_text.split())
                if wc > 0:  # Filter 0-word gaps (adjacent quotes)
                    gaps.append({
                        "start_char": gap_start,
                        "end_char": gap_end,
                        "word_count": wc,
                    })

        # Gap after last dialogue
        last_end = sorted_spans[-1]["end_char"]
        if last_end < text_len:
            gap_text = text[last_end:text_len]
            wc = len(gap_text.split())
            if wc > 0:
                gaps.append({
                    "start_char": last_end,
                    "end_char": text_len,
                    "word_count": wc,
                })

        # Statistics
        total_gaps = len(gaps)
        if gaps:
            avg_gap_words = round(
                sum(g["word_count"] for g in gaps) / total_gaps, 1
            )
            longest = max(gaps, key=lambda g: g["word_count"])
            longest_silence = {
                "word_count": longest["word_count"],
                "position": round(longest["start_char"] / max(text_len, 1), 4),
                "preview": text[longest["start_char"]:longest["end_char"]][:120],
            }
        else:
            avg_gap_words = 0.0
            longest_silence = None

        return AnalyzerResult(
            analyzer_name="silence",
            data={
                "gaps": gaps,
                "longest_silence": longest_silence,
                "avg_gap_words": avg_gap_words,
                "total_gaps": total_gaps,
            },
            warnings=warnings,
        )
