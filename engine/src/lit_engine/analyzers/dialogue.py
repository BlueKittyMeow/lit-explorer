"""Dialogue analyzer — curly-quote-aware dialogue extraction and ratio analysis."""

from lit_engine.analyzers import Analyzer, AnalyzerResult, register
from lit_engine.nlp.dialogue_extract import extract_dialogue


@register
class DialogueAnalyzer(Analyzer):
    """Curly-quote-aware dialogue extraction and ratio analysis."""

    name = "dialogue"
    description = "Curly-quote-aware dialogue extraction and ratio analysis"

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        quote_pairs = config.get("dialogue_quote_pairs")
        spans = extract_dialogue(text, quote_pairs=quote_pairs)

        # Compute word counts
        total_words = len(text.split())
        dialogue_words = sum(len(s.text.split()) for s in spans)
        narrative_words = max(0, total_words - dialogue_words)

        if total_words > 0:
            ratio = round(dialogue_words / total_words, 3)
        else:
            ratio = 0.0

        # Build span list for output (without full text, just offsets + word count)
        span_list = [
            {
                "start_char": s.start_char,
                "end_char": s.end_char,
                "word_count": len(s.text.split()),
            }
            for s in spans
        ]

        return AnalyzerResult(
            analyzer_name="dialogue",
            data={
                "total_dialogue_words": dialogue_words,
                "total_narrative_words": narrative_words,
                "overall_dialogue_ratio": ratio,
                "span_count": len(spans),
                "spans": span_list,
            },
        )
