def normalize(text: str) -> str:
    return text.strip().lower()


def find_keyword_match(message: str, faq_data: list[dict]) -> dict | None:
    """Deterministic substring match against each FAQ's keyword list.

    Returns the first FAQ whose keyword appears in the (already normalized)
    message, or None. Kept separate from semantic search because exact
    keyword hits are free, instant, and zero-risk of drift.
    """
    for item in faq_data:
        for keyword in item.get("keywords", []):
            if normalize(keyword) in message:
                return item

    return None
