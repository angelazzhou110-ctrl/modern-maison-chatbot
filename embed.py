#THIS IS USED FOR IF I WANT TO EMBED OPEN AI API
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

INPUT_PATH = "data/faq.json"
OUTPUT_PATH = "data/kb_vectors.json"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    texts = [f"{item['title']}\n{item['content']}" for item in items]

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    output = []
    for item, emb in zip(items, response.data):
        output.append({
            "id": item["id"],
            "title": item["title"],
            "content": item["content"],
            "url": item["url"],
            "embedding": emb.embedding
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Saved {len(output)} vectorized knowledge entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()