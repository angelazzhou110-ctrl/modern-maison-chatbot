import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from keyword_matcher import find_keyword_match, normalize
from semantic_matcher import SemanticMatcher

logging.basicConfig(level=logging.WARNING)
logging.getLogger("semantic_matcher").setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
FAQ_PATH = BASE_DIR / "data" / "faq.json"

# index.html lives in data/templates, not Flask's default ./templates
app = Flask(__name__, template_folder=str(BASE_DIR / "data" / "templates"))
UNANSWERED_LOG_PATH = BASE_DIR / "data" / "unanswered_log.jsonl"

SEMANTIC_THRESHOLD = 0.45

FALLBACK_RESPONSE = (
    "I’m sorry — I don’t have that information yet. "
    "Please visit the FAQ page or contact Modern Maison Co directly for additional details."
)
EMPTY_MESSAGE_RESPONSE = "Please type a question and I’ll do my best to help."


def load_faq() -> list[dict]:
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_faq_data = load_faq()

# Loaded once at process startup, never per-request: the model load (~seconds)
# and the FAQ embedding pass both happen exactly once here.
try:
    _semantic_matcher = SemanticMatcher(FAQ_PATH)
except Exception:
    logger.exception("Failed to load SemanticMatcher; falling back to keyword-only matching")
    _semantic_matcher = None


def log_unanswered(message: str, score: float | None) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "best_score": score,
    }
    try:
        with open(UNANSWERED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        logger.exception("Could not write to unanswered-question log")


def get_faq_response(user_message: str, faq_data: list[dict]) -> dict:
    """Hybrid retrieval: semantic search first, exact keyword match as a safety net.

    Empirically (see tests/test_retrieval.py), semantic search over question
    paraphrases is *more* accurate than greedy keyword substring matching for
    topical questions — keyword matching picks whichever FAQ happens to
    appear first in the JSON list with a matching substring, which often
    grabs the wrong entry (e.g. "minimum guests for catering" matching the
    generic "catering" keyword instead of the dedicated minimum-order FAQ).
    Keyword matching still earns its place as a fallback: short, jargon-y
    single-word queries ("stripe", "greenery") often score below the
    semantic confidence threshold, and an exact keyword hit rescues them.
    """
    message = normalize(user_message)

    if not message:
        return {"response": EMPTY_MESSAGE_RESPONSE, "source": "empty", "confidence": None}

    if _semantic_matcher is not None:
        try:
            result = _semantic_matcher.find_best_match(
                user_message, threshold=SEMANTIC_THRESHOLD
            )
        except Exception:
            logger.exception("Semantic matcher failed on message: %r", user_message)
            result = {"matched": False, "score": None, "faq": None}

        if result["matched"]:
            return {
                "response": result["faq"]["answer"],
                "source": "semantic",
                "confidence": result["score"],
            }

        keyword_hit = find_keyword_match(message, faq_data)
        if keyword_hit:
            return {"response": keyword_hit["answer"], "source": "keyword", "confidence": 1.0}

        log_unanswered(user_message, result["score"])
        return {"response": FALLBACK_RESPONSE, "source": "fallback", "confidence": result["score"]}

    # Semantic matcher unavailable (e.g. model failed to load) — degrade to keyword-only.
    keyword_hit = find_keyword_match(message, faq_data)
    if keyword_hit:
        return {"response": keyword_hit["answer"], "source": "keyword", "confidence": 1.0}

    log_unanswered(user_message, None)
    return {"response": FALLBACK_RESPONSE, "source": "fallback", "confidence": None}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")

    if not isinstance(user_message, str):
        return jsonify({"response": EMPTY_MESSAGE_RESPONSE}), 400

    result = get_faq_response(user_message, _faq_data)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
