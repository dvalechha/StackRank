# StackRank API Testing Instructions

This guide provides CURL commands to test the StackRank API endpoints.

## Prerequisites

1. Start the API server:
   ```bash
   # Windows
   venv\Scripts\activate.bat
   uvicorn stackrank.api.app:app --reload --port 8000

   # macOS/Linux
   source venv/bin/activate
   uvicorn stackrank.api.app:app --reload --port 8000
   ```

2. Prepare test files:
   - A Job Description file: `jds/senior_engineer.docx`
   - Resume files in: `resumes/` (PDF or DOCX)

---

## Test Sequence

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"ok","version":"0.1.0"}
```

---

### 2. Create a Job

Upload a job description file to create a new job.

```bash
curl -X POST "http://localhost:8000/jobs?title=Senior%20Engineer" \
  -F "jd_file=@jds/senior_engineer.docx"
```

**Expected Response (201):**
```json
{
  "job_id": "uuid-string",
  "title": "Senior Engineer",
  "created_at": "2026-03-14T10:00:00",
  "status": "active",
  "screening_runs": 0
}
```

> **Note:** Copy the `job_id` from the response for use in subsequent tests.

---

### 3. List All Jobs

```bash
curl -X GET http://localhost:8000/jobs
```

**Expected Response:**
```json
{
  "jobs": [
    {
      "job_id": "uuid-string",
      "title": "Senior Engineer",
      "created_at": "2026-03-14T10:00:00",
      "status": "active",
      "screening_runs": 0
    }
  ]
}
```

---

### 4. Get a Single Job

Replace `{job_id}` with the actual job ID from step 2.

```bash
curl -X GET http://localhost:8000/jobs/{job_id}
```

---

### 5. Run Screening (Upload Resumes)

Upload resumes to screen against the job. Replace `{job_id}` with your job ID.

```bash
curl -X POST "http://localhost:8000/jobs/{job_id}/screen" \
  -F "resumes=@resumes/resume1.pdf" \
  -F "resumes=@resumes/resume2.pdf" \
  -F "resumes=@resumes/resume3.docx"
```

**Optional:** Limit to top N candidates:
```bash
curl -X POST "http://localhost:8000/jobs/{job_id}/screen?top_n=5" \
  -F "resumes=@resumes/resume1.pdf" \
  -F "resumes=@resumes/resume2.pdf"
```

**Expected Response (200):**
```json
{
  "run_id": "uuid-string",
  "job_id": "uuid-string",
  "job_title": "Senior Engineer",
  "run_timestamp": "2026-03-14T10:30:00",
  "model": "gpt-4o",
  "provider": "openai_internal",
  "total_candidates_evaluated": 3,
  "candidates": [
    {
      "rank": 1,
      "candidate_name": "Jane Smith",
      "file_name": "resume1.pdf",
      "total_score": 91,
      "recommendation": "STRONG_YES",
      "summary": "Strong alignment...",
      "dimensions": {
        "skills_match": {"score": 24, "rationale": "..."},
        "experience_relevance": {"score": 23, "rationale": "..."},
        "seniority_alignment": {"score": 22, "rationale": "..."},
        "employment_patterns": {"score": 22, "rationale": "..."}
      }
    }
  ]
}
```

> **Note:** Copy the `run_id` from the response for the next test.

---

### 6. List Screening Runs for a Job

```bash
curl -X GET http://localhost:8000/jobs/{job_id}/runs
```

---

### 7. Get a Specific Screening Run

```bash
curl -X GET http://localhost:8000/jobs/{job_id}/runs/{run_id}
```

---

### 8. Delete a Job

```bash
curl -X DELETE http://localhost:8000/jobs/{job_id}
```

**Expected Response:** 204 No Content

---

## Error Cases

### Invalid Resume File

```bash
curl -X POST "http://localhost:8000/jobs/{job_id}/screen" \
  -F "resumes=@resumes/image.jpg"
```

**Expected Response (422):**
```json
{
  "detail": "No valid resume files uploaded. Allowed: .pdf, .docx"
}
```

### Job Not Found

```bash
curl -X GET http://localhost:8000/jobs/nonexistent-id
```

**Expected Response (404):**
```json
{
  "detail": "Job nonexistent-id not found"
}
```

---

## Interactive Testing

For interactive testing, open http://localhost:8000/docs in your browser. The Swagger UI provides:
- Form-based endpoint testing
- Request/response visualization
- Auto-generated client code