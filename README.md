# Acme API

A FastAPI-based application for text ingestion, retrieval, and generation.

## Quick Start

### Prerequisites

- Python 3.11+ (for local development)
- pip (for local development)
- Docker (for containerized deployment)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd Acme
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Set your API keys in `.env`:
```bash
API_KEY=your-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t acme-api:latest .
```

2. Run the container:
```bash
docker run -d \
  --name acme-api \
  -p 8000:8000 \
  -e API_KEY=your-api-key-here \
  -e OPENAI_API_KEY=your-openai-api-key-here \
  acme-api:latest
```

3. Check the health endpoint:
```bash
curl http://localhost:8000/health
```

The API will be available at `http://localhost:8000`

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok"}
```

### Authentication

All endpoints except `/health` require an `X-API-Key` header. Set your API key in the `.env` file:

```bash
echo "API_KEY=your-secret-key-here" >> .env
```

Then make authenticated requests:

```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8000/docs
```

### Ingest Endpoint

The `/ingest` endpoint accepts text documents and stores them with embeddings for retrieval.

**Supported formats:**
1. Multipart file upload
2. Base64 JSON body
3. Base64 form field

**Example - Multipart file upload:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-secret-key-here" \
  -F "file=@document.txt"
```

**Example - Base64 JSON:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"content": "base64-encoded-content", "filename": "document.txt"}'
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
- Generates embeddings
- Stores content in FAISS index
- Deduplicates by content hash (idempotent)

### Retrieve Endpoint

The `/retrieve` endpoint searches for similar documents and returns top-k results.

**Request:**
```bash
curl -X POST http://localhost:8000/retrieve \
  -H "X-API-Key: your-secret-key-here" \
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
      "snippet": "Software development guidelines. This document covers best practices for...",
      "language": "en"
    },
    {
      "doc_id": "doc_1",
      "score": 0.456,
      "snippet": "Programming languages and frameworks. Learn about popular technologies...",
      "language": "en"
    }
  ]
}
```

**Features:**
- Default k=3 (customizable via `k` parameter)
- Returns ≤k results
- Snippets ≤160 characters, word-safe, no newlines
- Scores are monotonic (r0 ≤ r1 ≤ r2, lower is better)
- Deterministic ordering on ties (by doc_id)
- Empty corpus returns empty results (no error)

### Generate Endpoint

The `/generate` endpoint composes an answer from retrieved snippets with citations.

**Request:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "software development", "k": 3, "output_language": "en"}'
```

**Response:**
```json
{
  "answer": "Based on your query \"software development\", I found the following information:\n\n1. Software development guidelines... [Citation: doc_0]\n2. Programming best practices... [Citation: doc_1]\n\nI hope this information helps answer your question.",
  "citations": ["doc_0", "doc_1"],
  "language": "en",
  "query": "software development"
}
```

**Features:**
- Composes deterministic mock answer from retrieved snippets
- Includes ≥1 citation when results exist
- Respects `output_language` parameter ('en' or 'ja')
- Auto-detects query language if `output_language` not provided
- Graceful message when corpus is empty
- Supports custom `k` parameter for result count

### Error Responses

All errors follow a uniform format:

```json
{
  "error": {
    "message": "Error message",
    "status_code": 401
  }
}
```

Validation errors include additional details:

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

## Development

### Running Tests

```bash
pytest -q
```

Note: Tests require `OPENAI_API_KEY` to be set in the environment.

### Linting

```bash
ruff .
```

### Docker Build

To build and test the Docker image locally:

```bash
# Build the image
docker build -t acme-api:latest .

# Run the container
docker run -d \
  --name acme-api-test \
  -p 8000:8000 \
  -e API_KEY=test-key-123 \
  -e OPENAI_API_KEY=your-openai-api-key \
  acme-api:latest

# Test the health endpoint
curl http://localhost:8000/health

# Stop and remove the container
docker stop acme-api-test
docker rm acme-api-test
```

## Project Structure

```
Acme/
├── app/
│   ├── main.py          # FastAPI application
│   ├── auth.py          # Authentication module
│   ├── common/          # Common utilities (errors, etc.)
│   ├── routers/         # API routers
│   │   ├── ingest.py    # Ingest endpoint
│   │   ├── retrieve.py  # Retrieve endpoint
│   │   └── generate.py  # Generate endpoint
│   └── services/        # Service modules
│       ├── llm.py       # Mock LLM composer
│       └── translate.py # Translation service
│       ├── language.py  # Language detection
│       ├── embeddings.py # Embedding generation
│       └── store.py     # FAISS storage
├── samples/             # Sample text files
├── tests/               # Test files
└── requirements.txt     # Python dependencies
```

## License

[Add license information here]

