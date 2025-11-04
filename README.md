# Acme API

A FastAPI-based application for text ingestion, retrieval, and generation.

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

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

4. Run the application:
```bash
uvicorn app.main:app --reload
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

## Development

### Running Tests

```bash
pytest -q
```

### Linting

```bash
ruff .
```

## Project Structure

```
Acme/
├── app/
│   ├── main.py          # FastAPI application
│   ├── auth.py          # Authentication module
│   └── routers/         # API routers
├── tests/               # Test files
└── requirements.txt     # Python dependencies
```

## License

[Add license information here]

