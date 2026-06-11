import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticMatcher:
    def __init__(self, faq_path="faq.json"):
        self.faqs = self.load_faqs(faq_path)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.faq_texts = [
            self.build_search_text(faq)
            for faq in self.faqs
        ]

        self.faq_embeddings = self.model.encode(self.faq_texts)

    def load_faqs(self, faq_path):
        with open(faq_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def build_search_text(self, faq):
        title = faq.get("title", "")
        category = faq.get("category", "")
        keywords = " ".join(faq.get("keywords", []))
        answer = faq.get("answer", "")

        return f"{title} {category} {keywords} {answer}"

    def find_best_match(self, user_message, threshold=0.35):
        user_embedding = self.model.encode([user_message])

        similarities = cosine_similarity(
            user_embedding,
            self.faq_embeddings
        )[0]

        best_index = int(np.argmax(similarities))
        best_score = float(similarities[best_index])

        if best_score < threshold:
            return {
                "matched": False,
                "score": best_score,
                "faq": None
            }

        return {
            "matched": True,
            "score": best_score,
            "faq": self.faqs[best_index]
        }

    def find_top_matches(self, user_message, top_k=3, threshold=0.30):
        user_embedding = self.model.encode([user_message])

        similarities = cosine_similarity(
            user_embedding,
            self.faq_embeddings
        )[0]

        top_indices = similarities.argsort()[-top_k:][::-1]

        matches = []

        for index in top_indices:
            score = float(similarities[index])

            if score >= threshold:
                matches.append({
                    "score": score,
                    "faq": self.faqs[index]
                })

        return matches