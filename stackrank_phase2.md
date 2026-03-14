# StackRank — Phase 2: FastAPI Backend

## Context

Phase 1 built the core CLI engine. Phase 2 wraps that engine in a FastAPI backend so it can be:
- Tested via Postman
- Eventually called by the React frontend (Phase 3)

**Critical rule: do not modify any Phase 1 core modules.** (`scorer.py`, `resume_parser.py`, `jd_parser.py`, `model_client.py`, `prompts.py`, `output_formatter.py`). Phase 2 only adds new files on top.

---

## New Files to Add

```
stackrank/
├── api/
│   ├── __init__.py
│   ├── app.py               # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   ├── jobs.py          # Job management endpoints
│   │   └── screening.py     # Resume screening endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py      # Pydantic request models
│   │   └── responses.py     # Pydantic response models
│   └── middleware.py        # CORS, error handling
├── Dockerfile
└── railway.toml             # Railway deployment config
```

---

## API Endpoints

### Health

#### `GET /health`
Returns API status. Used by Railway for health checks.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### Jobs

#### `POST /jobs`
Create a new job by uploading a JD file.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | ✅ | Job title e.g. "Senior Engineer" |
| `jd_file` | file | ✅ | `.docx` job description file |

**Response `201`:**
```json
{
  "job_id": "uuid",
  "title": "Senior Engineer",
  "created_at": "2026-03-14T10:00:00",
  "status": "active"
}
```

#### `GET /jobs`
List all jobs.

**Response `200`:**
```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "title": "Senior Engineer",
      "created_at": "2026-03-14T10:00:00",
      "status": "active",
      "screening_runs": 2
    }
  ]
}
```

#### `GET /jobs/{job_id}`
Get a single job's details.

#### `DELETE /jobs/{job_id}`
Delete a job and all associated screening runs.

---

### Screening

#### `POST /jobs/{job_id}/screen`
Upload resumes and run screening against the job's JD.

**Request:** `multipart/form-data`
| Field | Type | Required | Description |
|---|---|---|---|
| `resumes` | file[] | ✅ | One or more `.pdf` or `.docx` resume files |
| `top_n` | integer | ❌ | Only return top N candidates (default: all) |

**Response `200`:**
```json
{
  "run_id": "uuid",
  "job_id": "uuid",
  "job_title": "Senior Engineer",
  "run_timestamp": "2026-03-14T10:30:00",
  "model": "gpt-4o",
  "provider": "openai_internal",
  "total_candidates_evaluated": 12,
  "candidates": [
    {
      "rank": 1,
      "candidate_name": "Jane Smith",
      "file_name": "jane_smith.pdf",
      "total_score": 91,
      "recommendation": "STRONG_YES",
      "summary": "Strong alignment across all dimensions...",
      "dimensions": {
        "skills_match": { "score": 24, "rationale": "..." },
        "experience_relevance": { "score": 23, "rationale": "..." },
        "seniority_alignment": { "score": 22, "rationale": "..." },
        "employment_patterns": { "score": 22, "rationale": "..." }
      }
    }
  ]
}
```

**Error responses:**
- `404` — job_id not found
- `422` — no valid resume files uploaded
- `500` — AI provider error (include message)

#### `GET /jobs/{job_id}/runs`
List all screening runs for a job.

#### `GET /jobs/{job_id}/runs/{run_id}`
Retrieve full results of a past screening run.

---

## Implementation Details

### `api/app.py`
```python
from fastapi import FastAPI
from api.routes import health, jobs, screening
from api.middleware import setup_middleware

app = FastAPI(
    title="StackRank API",
    version="0.1.0",
    description="AI-powered resume screening"
)

setup_middleware(app)

app.include_router(health.router)
app.include_router(jobs.router, prefix="/jobs")
app.include_router(screening.router, prefix="/jobs")
```

### `api/middleware.py`
- Add CORS middleware — allow all origins for now (`*`), tighten in Phase 3
- Add global exception handler that returns consistent error shape:
```json
{
  "error": "string",
  "detail": "string"
}
```

### In-Memory Storage (Phase 2 only)
For Phase 2, store jobs and runs **in memory** using a simple dict — no database yet. Supabase persistence comes in Phase 3.

```python
# Simple in-memory store
jobs_store: dict[str, Job] = {}
runs_store: dict[str, ScreeningRun] = {}
```

This is intentional — keeps Phase 2 focused on API correctness, not persistence.

### File Handling
- Accept uploaded files as `UploadFile` from FastAPI
- Write to a temp directory (`tempfile.mkdtemp()`) for processing
- Pass temp file paths to the existing Phase 1 parsers unchanged
- Clean up temp files after processing with `shutil.rmtree()`
- Never persist resume files to disk beyond the request lifecycle

### Calling Phase 1 Core
The screening route should call Phase 1 modules directly:

```python
from stackrank.jd_parser import parse_jd
from stackrank.resume_parser import parse_resume
from stackrank.scorer import score_candidate
from stackrank.config_loader import load_config

# Load config once at startup
config = load_config()

# In the screening route:
jd_text = parse_jd(jd_temp_path)
for resume_file in resume_files:
    candidate = parse_resume(resume_temp_path)
    result = score_candidate(jd_text, candidate, config)
    results.append(result)
```

---

## Pydantic Models (`api/models/`)

### `requests.py`
- `CreateJobRequest` — title (string, required)
- No body model needed for screening (multipart form)

### `responses.py`
- `JobResponse` — job_id, title, created_at, status, screening_runs
- `JobListResponse` — list of JobResponse
- `DimensionScore` — score (int), rationale (str)
- `CandidateResult` — rank, candidate_name, file_name, total_score, recommendation, summary, dimensions
- `ScreeningRunResponse` — run_id, job_id, job_title, run_timestamp, model, provider, total_candidates_evaluated, candidates
- `HealthResponse` — status, version

---

## Updated `requirements.txt`

Add to existing Phase 1 requirements:
```
fastapi>=0.110.0
uvicorn>=0.29.0
python-multipart>=0.0.9
```

---

## Running Locally

```bash
uvicorn api.app:app --reload --port 8000
```

FastAPI auto-generates interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## `railway.toml`

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "uvicorn api.app:app --host 0.0.0.0 --port 8000"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on-failure"
```

---

## Postman Testing Sequence

Once running locally, test in this order:

1. `GET /health` → confirm API is up
2. `POST /jobs` → upload a real `.docx` JD, note the `job_id` returned
3. `GET /jobs` → confirm job appears in list
4. `POST /jobs/{job_id}/screen` → upload 3-5 real resumes, review ranked output
5. `GET /jobs/{job_id}/runs` → confirm run was stored
6. `GET /jobs/{job_id}/runs/{run_id}` → confirm full results retrievable
7. `DELETE /jobs/{job_id}` → confirm deletion works

---

## Phase 2 Success Criteria

Before moving to Phase 3, confirm:
- [ ] All 7 Postman tests pass
- [ ] Screening a batch of 5 real resumes returns sensible ranked results
- [ ] Model switching works — test once with `openai_internal`, once with external
- [ ] Temp files are cleaned up after each request (check disk)
- [ ] Error cases return clean JSON error responses (try uploading a `.jpg` as a resume)
