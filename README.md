# Modern Maison Co — Customer Support Chatbot & Delivery Zone Locator

## Delivery Zone Locator Demo
<img width="1084" height="656" alt="Screen Recording 2026-06-09 at 1 44 59 PM" src="https://github.com/user-attachments/assets/3a074b1a-f0a3-4419-954b-926c0b00bdb4" />


A lightweight, embeddable FAQ chatbot and ZIP-code delivery checker built for a Detroit-based charcuterie and catering business, reducing repetitive customer inquiries by surfacing order minimums, dietary accommodations, cancellation policy, and service-area availability instantly on the site.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| NLP / retrieval | `sentence-transformers` (`all-MiniLM-L6-v2`), scikit-learn cosine similarity — runs locally, no paid API |
| Deployment | Gunicorn (WSGI) |
| Frontend (embeds) | JavaScript, HTML/CSS |
| Data | JSON (structured FAQ knowledge base) |
| (Optional / future) | OpenAI Embeddings API (`text-embedding-3-small`) via `embed.py`, kept as an unused upgrade path |

---

## Features

### FAQ Chatbot (`app.py`)
- **Hybrid semantic + keyword retrieval pipeline** — the user's message is first checked against sentence-transformer embeddings of every FAQ's title and example question phrasings (cosine similarity, confidence-thresholded); a plain keyword-substring pass acts as a safety net for short/jargon queries the model under-scores (e.g. "stripe", "greenery"). See `semantic_matcher.py` and `keyword_matcher.py`.
- **Runs entirely locally, for free** — `all-MiniLM-L6-v2` (~80MB) loads once at process startup and stays in memory; no per-request API calls, no OpenAI dependency in the live path.
- **REST API endpoint** — `POST /chat` accepts JSON, processes the query server-side, and returns `{response, source, confidence}` (source/confidence are diagnostic metadata; the widget only reads `response`), keeping business logic off the client.
- **Structured knowledge base** (`data/faq.json`) — 21 FAQ entries organized by `id`, `category`, `title`, `questions[]` (paraphrase examples used for embeddings), `keywords[]`, `answer`, and `url`, independently maintainable without touching application logic.
- **Graceful fallback + unanswered-question logging** — low-confidence queries return a soft handoff message directing users to the FAQ page or direct email, and get appended to `data/unanswered_log.jsonl` (gitignored) so real user questions can inform future FAQ entries.

### Delivery Zone Locator (`zip-code-locater/boards-and-grazing-locater.html`)
- **Client-side ZIP validation** — regex and length checks prevent malformed input before any lookup runs.
- **O(1) set lookup** — delivery eligibility is checked against a hardcoded JavaScript array of ~120 ZIP codes covering Metro Detroit, with instant feedback and no backend call needed. This stays deterministic by design — there's no ambiguity to resolve with ML here.
- **Embedded widget architecture** — self-contained `<div>` with scoped CSS and an inline `<script>`, designed to drop into any CMS or website builder (Squarespace, Webflow, etc.) without dependency conflicts.

### Embedding Pipeline (`embed.py`)
- Scaffolded integration with **OpenAI's `text-embedding-3-small`** model, kept as a documented but unused alternative if the knowledge base ever outgrows a locally-run model. Not part of the live request path.

---

## Architecture Decisions & Trade-offs

**Semantic search first, keyword match as a safety net** — Evaluation (`tests/test_retrieval.py`) showed plain keyword substring matching, run first, frequently grabbed the wrong FAQ (e.g. "minimum guests for catering" matched the generic "catering" keyword instead of the dedicated minimum-order entry) because it takes the first substring hit in JSON order with no ranking. Semantic similarity over question paraphrases picks the right entry far more often, so it runs first; keyword matching only kicks in when the semantic score falls below the confidence threshold, which mainly rescues short jargon queries ("stripe", "greenery") that don't embed distinctively.

**Local embedding model, no paid API** — `all-MiniLM-L6-v2` runs on CPU, loads once at startup (a few seconds), and needs no network calls per request. This keeps the chatbot free to run and avoids depending on OpenAI/Anthropic API keys or usage limits for the core FAQ-answering path. `embed.py`'s OpenAI pipeline is kept only as a documented alternative if the FAQ set grows large enough that a hosted embedding model becomes worth the cost.

**Client-side ZIP lookup** — Delivery zone data is embedded directly in the frontend widget rather than fetched from an API or matched semantically. ZIP-in-delivery-zone is a deterministic yes/no fact, not a natural-language question, so it doesn't benefit from embeddings — this eliminates a network round-trip and keeps the widget functional even if the backend is unavailable, at the cost of requiring a code update when zones change.

**Stateless REST design** — The Flask chat endpoint is fully stateless; no session or conversation history is stored. Each request is self-contained, making the service horizontally scalable and trivially deployable on any WSGI host.

**Separation of data and logic** — FAQ content lives in `data/faq.json` rather than being hardcoded in `app.py`, so non-technical stakeholders can update answers, add entries, or adjust keywords/paraphrases without modifying application code. Matching logic is split across `keyword_matcher.py` and `semantic_matcher.py` so each retrieval strategy can be tested and tuned independently.

---

## Project Structure

```
chatbot/
├── app.py                    # Flask routes + hybrid retrieval orchestration
├── keyword_matcher.py        # Deterministic keyword substring matching
├── semantic_matcher.py       # Sentence-transformer embedding + cosine similarity search
├── embed.py                  # OpenAI embedding pipeline (documented alternative, unused)
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # + pytest, for running tests/
├── data/
│   ├── faq.json               # Structured FAQ knowledge base (21 entries)
│   ├── templates/index.html   # Chat widget UI
│   └── unanswered_log.jsonl   # Logged low-confidence queries (gitignored, created at runtime)
└── tests/
    └── test_retrieval.py     # Retrieval evaluation set + pytest assertions

zip-code-locater/
└── boards-and-grazing-locater.html   # Delivery ZIP checker widget (embed as-is in any site)
```

---

## Setup & Running Locally

```bash
cd chatbot

# Install dependencies (add requirements-dev.txt to also run tests)
pip install -r requirements.txt

# Run development server
python app.py

# Run with Gunicorn (production)
gunicorn app:app
```

The chat API will be available at `http://localhost:5000/chat`.

**Example request:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "do you deliver to detroit?"}'
```

## Running Tests

```bash
cd chatbot
pip install -r requirements-dev.txt
pytest tests/test_retrieval.py -v

# or run it directly for a readable table of scores per test case
python tests/test_retrieval.py
```
