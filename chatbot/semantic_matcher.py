import json
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"


class SemanticMatcher:
    """Embedding-based FAQ retrieval.

    Loads the sentence-transformer model once (at construction time) and
    embeds every FAQ's title + example question phrasings once. Each FAQ can
    have several natural-language variants (paraphrases); at query time we
    compare the user's message against every variant and take the best
    matching variant per FAQ, which is more robust than embedding one long
    blob of keywords + answer text per FAQ.
    """

    def __init__(self, faq_path: str | Path):
        self.faqs = self._load_faqs(faq_path)

        logger.info("Loading sentence-transformer model %s ...", MODEL_NAME)
        self.model = SentenceTransformer(MODEL_NAME, device="cpu")

        self.variant_texts: list[str] = []
        self.variant_faq_index: list[int] = []

        for faq_index, faq in enumerate(self.faqs):
            for text in self._build_variants(faq):
                self.variant_texts.append(text)
                self.variant_faq_index.append(faq_index)

        self.variant_embeddings = self.model.encode(
            self.variant_texts, normalize_embeddings=True
        )
        logger.info(
            "Embedded %d question variants across %d FAQ entries",
            len(self.variant_texts),
            len(self.faqs),
        )

    @staticmethod
    def _load_faqs(faq_path: str | Path) -> list[dict]:
        with open(faq_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _build_variants(faq: dict) -> list[str]:
        variants = [faq.get("title", "")]
        variants.extend(faq.get("questions", []))
        return [v for v in variants if v.strip()]

    def find_best_match(self, user_message: str, threshold: float = 0.45) -> dict:
        if not user_message or not user_message.strip():
            return {"matched": False, "score": 0.0, "faq": None}

        user_embedding = self.model.encode(
            [user_message], normalize_embeddings=True
        )
        similarities = cosine_similarity(user_embedding, self.variant_embeddings)[0]

        best_variant_index = int(np.argmax(similarities))
        best_score = float(similarities[best_variant_index])
        best_faq = self.faqs[self.variant_faq_index[best_variant_index]]

        if best_score < threshold:
            return {"matched": False, "score": best_score, "faq": None}

        return {"matched": True, "score": best_score, "faq": best_faq}
