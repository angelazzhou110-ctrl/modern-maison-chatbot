"""Retrieval evaluation for the hybrid keyword/semantic FAQ matcher.

Run directly: python tests/test_retrieval.py
Or with pytest, from the chatbot/ directory: pytest tests/test_retrieval.py -v

This is deliberately not mocked — it loads the real MiniLM model and the
real faq.json so scores stay honest. First run downloads/loads the model
(a few seconds); subsequent runs use the local HF cache.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import get_faq_response, _faq_data


# (message, expected_faq_id or None for "should fall back", category)
CASES = [
    # Exact FAQ wording
    ("Do you deliver to Detroit?", "faq_10", "exact"),
    ("What is included in the charcuterie workshops?", "faq_5", "exact"),
    ("What are your business hours?", "faq_21", "exact"),
    # Paraphrased questions
    ("Is my zip code covered for delivery?", "faq_10", "paraphrase"),
    ("What comes with the board making class", "faq_5", "paraphrase"),
    ("How soon before an event do i have to place my order", "faq_11", "paraphrase"),
    ("minimum guests for catering", "faq_12", "paraphrase"),
    # Misspellings
    ("do yuo deliver to detroit", "faq_10", "misspelling"),
    ("wat is teh cancelation policy", "faq_17", "misspelling"),
    ("chargcuterie boxs price", "faq_8", "misspelling"),
    # Short queries (single word / jargon, rescued by keyword fallback)
    ("deposit", "faq_16", "short"),
    ("stripe", "faq_15", "short"),
    ("greenery", "faq_14", "short"),
    ("jobs", "faq_20", "short"),
    # Delivery / catering / pricing / policy domain coverage
    ("do you deliver to Royal Oak", "faq_10", "delivery"),
    ("what if I need to cancel my order", "faq_17", "policy"),
    ("do you accept apple pay", "faq_15", "pricing"),
    # Ambiguous / unrelated — should NOT confidently match anything
    ("can you help me", None, "ambiguous"),
    ("tell me more", None, "ambiguous"),
    ("what is the weather today", None, "unrelated"),
    ("what is the capital of France", None, "unrelated"),
]


def _run_case(message, expected_id):
    result = get_faq_response(message, _faq_data)
    matched_faq = next(
        (f for f in _faq_data if f["answer"] == result["response"]), None
    )
    matched_id = matched_faq["id"] if matched_faq else None
    return result, matched_id


@pytest.mark.parametrize("message,expected_id,category", CASES)
def test_retrieval_case(message, expected_id, category):
    result, matched_id = _run_case(message, expected_id)

    if expected_id is None:
        assert matched_id is None, (
            f"[{category}] {message!r} should have fallen back but matched "
            f"{matched_id} (source={result['source']}, confidence={result['confidence']})"
        )
    else:
        assert matched_id == expected_id, (
            f"[{category}] {message!r} expected {expected_id}, got {matched_id} "
            f"(source={result['source']}, confidence={result['confidence']})"
        )


def test_empty_message_does_not_crash():
    result = get_faq_response("", _faq_data)
    assert result["source"] == "empty"

    result = get_faq_response("   ", _faq_data)
    assert result["source"] == "empty"


if __name__ == "__main__":
    print(f"{'category':12} {'message':50} {'expected':10} {'got':10} {'source':10} confidence")
    failures = 0
    for message, expected_id, category in CASES:
        result, matched_id = _run_case(message, expected_id)
        ok = (matched_id == expected_id) if expected_id else (matched_id is None)
        if not ok:
            failures += 1
        marker = "OK " if ok else "FAIL"
        conf = f"{result['confidence']:.3f}" if isinstance(result["confidence"], float) else "-"
        print(
            f"{marker} [{category:11}] {message!r:50} exp={str(expected_id):10} "
            f"got={str(matched_id):10} src={result['source']:10} conf={conf}"
        )
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    sys.exit(1 if failures else 0)
