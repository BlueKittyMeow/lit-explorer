"""Pacing analyzer — sentence length distribution and rhythm pattern detection."""

import statistics

from lit_engine.analyzers import Analyzer, AnalyzerResult, register


@register
class PacingAnalyzer(Analyzer):
    """Sentence length distribution and rhythm pattern detection."""

    name = "pacing"
    description = "Sentence length distribution and rhythm pattern detection"

    def requires(self) -> list[str]:
        return ["texttiling"]

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        staccato_threshold = config.get("pacing_staccato_threshold", 8)
        flowing_threshold = config.get("pacing_flowing_threshold", 25)

        # Collect all sentence lengths from texttiling blocks
        tt_result = context["texttiling"] if context else None
        blocks = tt_result.data.get("blocks", []) if tt_result else []

        all_sent_lengths: list[int] = []
        for block in blocks:
            all_sent_lengths.extend(block.get("sentence_lengths", []))

        if not all_sent_lengths:
            return AnalyzerResult(
                analyzer_name="pacing",
                data={
                    "sentence_count": 0,
                    "distribution": {
                        "mean": 0.0, "median": 0.0, "std_dev": 0.0,
                        "min": 0, "max": 0,
                        "percentiles": {"10": 0, "25": 0, "50": 0, "75": 0, "90": 0},
                    },
                    "staccato_passages": [],
                    "flowing_passages": [],
                },
                warnings=["No sentence data available for pacing analysis."],
            )

        # Distribution stats
        sorted_lengths = sorted(all_sent_lengths)
        n = len(sorted_lengths)
        distribution = {
            "mean": round(statistics.mean(all_sent_lengths), 1),
            "median": round(statistics.median(all_sent_lengths), 1),
            "std_dev": round(statistics.stdev(all_sent_lengths), 1) if n > 1 else 0.0,
            "min": min(all_sent_lengths),
            "max": max(all_sent_lengths),
            "percentiles": {
                "10": sorted_lengths[int(n * 0.10)] if n > 0 else 0,
                "25": sorted_lengths[int(n * 0.25)] if n > 0 else 0,
                "50": sorted_lengths[int(n * 0.50)] if n > 0 else 0,
                "75": sorted_lengths[min(int(n * 0.75), n - 1)] if n > 0 else 0,
                "90": sorted_lengths[min(int(n * 0.90), n - 1)] if n > 0 else 0,
            },
        }

        # Identify staccato and flowing passages
        staccato: list[dict] = []
        flowing: list[dict] = []

        for block in blocks:
            sent_lens = block.get("sentence_lengths", [])
            if not sent_lens:
                continue

            avg = statistics.mean(sent_lens)
            preview = block.get("preview", "")

            if avg < staccato_threshold:
                staccato.append({
                    "block_id": block["id"],
                    "avg_sentence_length": round(avg, 1),
                    "sentence_count": len(sent_lens),
                    "preview": preview,
                })
            elif avg > flowing_threshold:
                flowing.append({
                    "block_id": block["id"],
                    "avg_sentence_length": round(avg, 1),
                    "sentence_count": len(sent_lens),
                    "preview": preview,
                })

        return AnalyzerResult(
            analyzer_name="pacing",
            data={
                "sentence_count": len(all_sent_lengths),
                "distribution": distribution,
                "staccato_passages": staccato,
                "flowing_passages": flowing,
            },
        )
