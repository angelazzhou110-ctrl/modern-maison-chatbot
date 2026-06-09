# Modern Maison Co — Customer Support Chatbot & Delivery Zone Locator

## Delivery Zone Locator Demo
<img width="1084" height="656" alt="Screen Recording 2026-06-09 at 1 44 59 PM" src="https://github.com/user-attachments/assets/3a074b1a-f0a3-4419-954b-926c0b00bdb4" />


A lightweight, embeddable FAQ chatbot and ZIP-code delivery checker built for a Detroit-based charcuterie and catering business, reducing repetitive customer inquiries by surfacing order minimums, dietary accommodations, cancellation policy, and service-area availability instantly on the site.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Deployment | Gunicorn (WSGI) |
| Frontend (embeds) | JavaScript, HTML/CSS |
| Data | JSON (structured FAQ knowledge base) |
| (Optional / future) | OpenAI Embeddings API (`text-embedding-3-small`) via `embed.py` |

---

## Features

### FAQ Chatbot (`app.py`)
- **Keyword-matching NLP pipeline** — normalizes user input (lowercased, stripped) and scans a structured JSON knowledge base for keyword hits, returning the most relevant pre-authored answer.
- **REST API endpoint** — `POST /chat` accepts JSON, processes the query server-side, and returns a response object, keeping business logic off the client.
- **Structured knowledge base** (`faq.json`) — 21 FAQ entries organized by `id`, `category`, `keywords[]`, `answer`, and `url`, making the data independently maintainable without touching application logic.
- **Graceful fallback** — unmatched queries return a soft handoff message directing users to the FAQ page or direct email, avoiding dead ends.

### Delivery Zone Locator (`boards-and-grazing-locater.html`)
- **Client-side ZIP validation** — regex and length checks prevent malformed input before any lookup runs.
- **O(1) set lookup** — delivery eligibility is checked against a hardcoded JavaScript array of ~100+ ZIP codes covering Metro Detroit, with instant feedback and no backend call needed.
- **Embedded widget architecture** — self-contained `<div>` with scoped CSS and an inline `<script>`, designed to drop into any CMS or website builder (Squarespace, Webflow, etc.) without dependency conflicts.

### Embedding Pipeline (`embed.py`)
- Scaffolded integration with **OpenAI's `text-embedding-3-small`** model for future semantic search, enabling cosine-similarity FAQ retrieval as an upgrade path beyond keyword matching.
- Outputs a `kb_vectors.json` file pairing each FAQ entry with its dense vector representation, ready for nearest-neighbor search.

---

## Architecture Decisions & Trade-offs

**Keyword matching vs. semantic search** — The current implementation uses deterministic keyword lookup for zero latency and no API cost, which is appropriate for a small, well-defined FAQ domain. The `embed.py` module provides a documented upgrade path to vector similarity search if the knowledge base grows or query variety increases.

**Client-side ZIP lookup** — Delivery zone data is embedded directly in the frontend widget rather than fetched from an API. This eliminates a network round-trip and keeps the widget functional even if the backend is unavailable, at the cost of requiring a code update when zones change.

**Stateless REST design** — The Flask chat endpoint is fully stateless; no session or conversation history is stored. Each request is self-contained, making the service horizontally scalable and trivially deployable on any WSGI host.

**Separation of data and logic** — FAQ content lives in `faq.json` rather than being hardcoded in `app.py`, so non-technical stakeholders can update answers, add entries, or adjust keywords without modifying application code.

---

## Project Structure

```
├── app.py                          # Flask application and keyword-matching logic
├── embed.py                        # OpenAI embedding pipeline (future semantic search)
├── requirements.txt                # Python dependencies
├── data/
│   └── faq.json                    # Structured FAQ knowledge base (21 entries)
└── embeds/
    ├── boards-and-grazing-locater.html   # Delivery ZIP checker widget
    └── catering-locater.html             # Catering service area widget (not deployed)
```

---

## Setup & Running Locally

```bash
# Install dependencies
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
