"""Map tokenized sentences back to character offsets in original text."""


def locate_sentences(text: str, sentences: list[str]) -> list[tuple[int, int]]:
    """
    Map sentence strings back to (start_char, end_char) in the original text.

    Uses cumulative search_from to handle repeated sentences correctly.
    Falls back to search_from position if text.find() fails (tokenizer
    may normalize whitespace).
    """
    offsets: list[tuple[int, int]] = []
    search_from = 0

    for sent in sentences:
        idx = text.find(sent, search_from)
        if idx == -1:
            # Fallback: use current search position
            idx = search_from
        start = idx
        end = start + len(sent)
        offsets.append((start, end))
        search_from = end

    return offsets
