from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
FAQ_PATH = BASE_DIR / "data" / "faq.json"


def load_faq():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    return text.strip().lower()


def get_faq_response(user_message: str, faq_data: list[dict]) -> str:
    message = normalize(user_message)

    if not message:
        return "Please type a question and I’ll do my best to help."

    for item in faq_data:
        keywords = item.get("keywords", [])
        answer = item.get("answer", "")

        for keyword in keywords:
            if normalize(keyword) in message:
                return answer

    return (
        "I’m sorry — I don’t have that information yet. "
        "Please visit the FAQ page or contact Modern Maison Co directly for additional details."
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")
    faq_data = load_faq()
    response = get_faq_response(user_message, faq_data)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)