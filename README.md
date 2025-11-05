# Acme API

A FastAPI application for ingesting text, searching documents, and generating answers with citations.

## Quick Start

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your API key:
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

3. (Optional) Customize prompts and messages:
```bash
cp config.yml.example config.yml
# Edit config.yml to tweak prompts, messages, etc.
```

4. Run it:
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to see the API docs.

### Docker

Build and run:
```bash
docker build -t acme-api:latest .
docker run -d \
  --name acme-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/app/data:/app/app/data \
  acme-api:latest
```

The volume mount keeps your data safe when the container stops.

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

Returns `{"status":"ok"}` - no auth needed.

### Authentication

All endpoints except `/health` need an `X-API-Key` header with your `OPENAI_API_KEY`:

```bash
curl -H "X-API-Key: your-key-here" http://localhost:8000/docs
```

### Ingest Documents

Upload text files (`.txt` only) to store them with embeddings:

```bash
# Upload a file
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-key-here" \
  -F "file=@document.txt"
```

Or send base64-encoded content:
```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"content": "base64-encoded-text"}'
```

**Response:**
```json
{
  "doc_id": "doc_0",
  "language": "en",
  "added": true,
  "index_size": 1
}
```

The endpoint automatically:
- Detects language (English or Japanese)
- Creates embeddings
- Stores in FAISS index
- Deduplicates by content hash

### Search Documents

Search for similar documents:

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "X-API-Key: your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "software development", "k": 3}'
```

**Response:**
```json
{
  "results": [
    {
      "doc_id": "doc_0",
      "score": 0.123,
      "snippet": "Software development guidelines...",
      "language": "en"
    }
  ]
}
```

- Default `k=3` (change with `k` parameter)
- Snippets are ≤160 chars, word-safe
- Lower scores = better matches
- Empty corpus returns empty results (no error)

### Generate Answers

Get an AI-generated answer with citations:

```bash
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "software development", "k": 3, "output_language": "en"}'
```

**Response:**
```json
{
  "answer": "Based on your query... [Citation: doc_0]",
  "citations": ["doc_0", "doc_1"],
  "language": "en",
  "query": "software development"
}
```

Features:
- Auto-detects query language
- Optional `output_language` for translation ('en' or 'ja')
- Includes citations from retrieved docs
- Works even with empty corpus

## Configuration

We use a hybrid config approach:

1. **Python config** (`app/config.py`) - Technical settings (model names, thresholds, paths)
   - Override with environment variables
   - Type-safe, IDE-friendly

2. **YAML config** (`config.yml`) - User-friendly settings (prompts, messages)
   - Easy to edit without Python knowledge
   - Copy `config.yml.example` to get started

**Priority:** Environment variables > YAML config > Python defaults

If `config.yml` doesn't exist, it falls back to Python defaults - no worries!

## Development

Run tests:
```bash
pytest -q
```

Lint code:
```bash
ruff .
```

## Project Structure

```
Acme/
├── app/
│   ├── main.py          # FastAPI app
│   ├── config.py        # Config (Python + YAML)
│   ├── common/          # Utilities
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── config.yml           # YAML config (optional)
├── tests/               # Tests
└── requirements.txt     # Dependencies
```

## Error Format

All errors follow the same format:

```json
{
  "error": {
    "message": "Error message",
    "status_code": 401
  }
}
```

Validation errors include details:
```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "details": {
      "field_name": "error message"
    }
  }
}
```
