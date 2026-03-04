"""Readability analyzer — extended textstat metrics per block and whole text."""

import textstat

from lit_engine.analyzers import Analyzer, AnalyzerResult, register


@register
class ReadabilityAnalyzer(Analyzer):
    """Extended readability metrics (Coleman-Liau, SMOG, ARI) per block."""

    name = "readability"
    description = "Extended readability metrics (Coleman-Liau, SMOG, ARI) per block"

    def requires(self) -> list[str]:
        return ["texttiling"]

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # Get texttiling blocks for per-block computation
        tt_result = context["texttiling"] if context else None
        blocks = tt_result.data.get("blocks", []) if tt_result else []

        per_block: list[dict] = []
        for block in blocks:
            # Extract block text from the full text using char offsets
            start = block["start_char"]
            end = block["end_char"]
            block_text = text[start:end].replace("\n", " ").strip()

            if not block_text or len(block_text.split()) < 3:
                per_block.append({
                    "block_id": block["id"],
                    "coleman_liau": 0.0,
                    "smog": 0.0,
                    "ari": 0.0,
                })
                continue

            per_block.append({
                "block_id": block["id"],
                "coleman_liau": round(textstat.coleman_liau_index(block_text), 1),
                "smog": round(textstat.smog_index(block_text), 1),
                "ari": round(textstat.automated_readability_index(block_text), 1),
            })

        # Whole-text readability summary
        if text.strip() and len(text.split()) >= 3:
            whole_text = {
                "flesch_ease": round(textstat.flesch_reading_ease(text), 1),
                "flesch_grade": round(textstat.flesch_kincaid_grade(text), 1),
                "gunning_fog": round(textstat.gunning_fog(text), 1),
                "coleman_liau": round(textstat.coleman_liau_index(text), 1),
                "smog": round(textstat.smog_index(text), 1),
                "ari": round(textstat.automated_readability_index(text), 1),
            }
        else:
            whole_text = {
                "flesch_ease": 0.0, "flesch_grade": 0.0, "gunning_fog": 0.0,
                "coleman_liau": 0.0, "smog": 0.0, "ari": 0.0,
            }

        return AnalyzerResult(
            analyzer_name="readability",
            data={
                "per_block": per_block,
                "whole_text": whole_text,
            },
            warnings=warnings,
        )
