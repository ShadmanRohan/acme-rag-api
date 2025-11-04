# Implementation Plan

## Global Rules (Apply to All Sprints)

- Implement exactly what's asked—nothing more.
- Only edit files listed under "Allowed to create/edit" for that sprint.
- Do NOT touch any file or directory listed as "out of scope" for that sprint.
- Keep implementations deterministic where acceptance tests require it (e.g., tie-breakers).
- Use FastAPI; tests via pytest; lint via ruff.
- All endpoints must respect X-API-Key once Sprint 1 lands.

## Environment

- Python 3.11+ (default GitHub Actions runner is fine)
- `.env.example` should include `API_KEY=` so tests can set it
- Commands (used by CI/tests): `ruff .` and `pytest -q`

---

## Sprint 0 — "We can boot and we can test"

**High-level objective:** Minimal FastAPI app runs; CI (ruff + pytest) is green; GET /health works.

**Allowed to create/edit:**
- `app/main.py`
- `app/auth.py`
- `app/routers/__init__.py`
- `tests/test_health.py`
- `.github/workflows/ci.yml`
- `requirements.txt`
- `.env.example`
- `README.md`

**Do NOT touch:**
- `app/services/*`
- `app/data/*`
- `Dockerfile` or GHCR config

**Acceptance tests:**
- GET /health → `{"status":"ok"}` with 200
- CI runs ruff + pytest and passes on push/PR

**Prompt to use:**
> "Implement a minimal FastAPI app with GET /health returning {"status":"ok"}. Allowed files: app/main.py, app/auth.py, app/routers/__init__.py, tests/test_health.py, .github/workflows/ci.yml, requirements.txt, .env.example, README.md. Do not create or change any other files."

---

## Sprint 1 — "Every request is safe and predictable"

**High-level objective:** Add X-API-Key auth and apply it globally.

**Allowed to create/edit:**
- `app/auth.py` (implement `require_api_key`)
- `app/main.py` (wire global dependency/exception handlers if needed)
- `app/routers/*` (only to add the auth dependency)
- `app/common/errors.py` (optional)
- `tests/test_auth.py`
- `README.md`

**Do NOT touch:**
- `app/services/*`
- `app/data/*`
- CI workflow/Dockerfile

**Acceptance tests:**
- Missing/invalid X-API-Key → 401 on all routes
- Malformed payloads → 422 (uniform error envelope if implemented)

**Prompt to use:**
> "Add X-API-Key auth and a uniform error envelope. Allowed files: app/auth.py, app/main.py, app/routers/__init__.py, app/common/errors.py, tests/test_auth.py, README.md. Do not create or edit any services or data files."

---

## Sprint 2 — "We can ingest real text"

**High-level objective:** POST /ingest accepts .txt (multipart or base64 JSON), detects EN/JA, embeds, persists FAISS + metadata; idempotent by content hash.

**Allowed to create/edit:**
- `app/routers/ingest.py`
- `app/services/language.py`
- `app/services/embeddings.py`
- `app/services/store.py`
- `tests/test_ingest.py`
- `samples/guideline_en.txt`
- `samples/guideline_ja.txt`
- `README.md`
- (Runtime files may be created under `app/data/`.)

**Do NOT touch:**
- `app/routers/retrieve.py`
- `app/routers/generate.py`
- CI workflow/Dockerfile

**Acceptance tests:**
- Accepts multipart and base64 JSON
- Detects EN & JA on the samples
- Index size increases; metadata written; re-upload same content dedupes

**Prompt to use:**
> "Implement POST /ingest to accept .txt (multipart or base64 JSON), detect EN/JA, embed, and persist to FAISS + metadata. Idempotent by content hash. Allowed files: app/routers/ingest.py, app/services/language.py, app/services/embeddings.py, app/services/store.py, tests/test_ingest.py, samples/guideline_en.txt, samples/guideline_ja.txt, README.md. Do not modify other routers or CI/Docker files."

---

## Sprint 3 — "We can find things"

**High-level objective:** /retrieve returns top-k (default 3) with {doc_id, score, snippet≤160 (word-safe, no newlines), language}; deterministic ordering on ties; empty corpus is graceful.

**Allowed to create/edit:**
- `app/routers/retrieve.py`
- `app/services/language.py` (read/update if needed)
- `app/services/embeddings.py` (read-only)
- `app/services/store.py` (search only)
- `tests/test_retrieve.py`
- `README.md`

**Do NOT touch:**
- `app/routers/ingest.py` (except reading shared helpers)
- `app/routers/generate.py`
- Persistence format changes

**Acceptance tests:**
- Default k=3; return ≤k results; deterministic ordering on ties
- Empty corpus → successful, polite response (no 500)
- Snippets ≤160 chars, word-safe, no newlines
- Scores monotonic (r0 ≥ r1 ≥ r2)

**Prompt to use:**
> "Implement POST /retrieve per contract: {query, k?=3} -> results[{doc_id, score, snippet, language}]. Allowed files: app/routers/retrieve.py, app/services/language.py (if needed), app/services/embeddings.py (read-only), app/services/store.py (search only), tests/test_retrieve.py, README.md. Do not modify ingest or generate routers, or persistence formats."

---

## Sprint 4 — "We can answer, in the right language"

**High-level objective:** /generate composes deterministic mock answer from retrieved snippets; includes citations; optional translation via output_language.

**Allowed to create/edit:**
- `app/routers/generate.py`
- `app/services/llm.py` (mock composer)
- `app/services/translate.py` (optional)
- `tests/test_generate.py`
- `README.md`

**Do NOT touch:**
- `app/services/store.py` (no write ops)
- Retrieval contract/behavior
- Persistence formats

**Acceptance tests:**
- Includes ≥1 citation when results exist
- Respects output_language; else uses detected query language
- Graceful message when corpus empty

**Prompt to use:**
> "Implement POST /generate to call retrieval internally, compose a deterministic mock answer with citations, and apply output_language if provided. Allowed files: app/routers/generate.py, app/services/llm.py, app/services/translate.py, tests/test_generate.py, README.md. Do not change retrieval/store behavior or formats."

---

## Sprint 5 — "Ship shape"

**High-level objective:** Reproducible runs; build container after tests pass.

**Allowed to create/edit:**
- `Dockerfile`
- `.dockerignore`
- `.github/workflows/ci.yml`
- `README.md`

**Do NOT touch:**
- App contracts or service logic

**Acceptance tests:**
- Local: `uvicorn app.main:app` works; sample flows run
- CI: tests pass; Docker build step runs (push optional)

**Prompt to use:**
> "Add a slim Dockerfile and extend the existing CI to build the image after tests pass. Allowed files: Dockerfile, .dockerignore, .github/workflows/ci.yml, README.md. Do not edit application code or service contracts."

---

## Sprint 6 — "Explain it and disclose AI help"

**High-level objective:** Clear docs, design notes, AI disclosure (if used); final single PDF.

**Allowed to create/edit:**
- `README.md`
- `DESIGN_NOTES.md`
- `PLAN.md`
- (Plus short comment-only headers in AI-assisted files.)

**Do NOT touch:**
- Code behavior (beyond adding comment headers)

**Acceptance tests:**
- Fresh clone → follow README → app runs; ingest/retrieve/generate succeed
- AI disclosure present in README + file headers (if AI used)
- Single PDF assembled per submission rules

**Prompt to use:**
> "Draft README quickstart, DESIGN_NOTES (tradeoffs, future work), and AI disclosure. Add brief header comments to AI-assisted files. Allowed files: README.md, DESIGN_NOTES.md, PLAN.md, and comment-only edits to existing source files. Do not change runtime behavior."

