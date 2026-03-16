# StackRank Testing Instructions

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key:**
   - Copy `.env.example` to `.env`
   - Add your API key to `.env` based on your provider in `config.yaml`

3. **Create test files:**
   - Create a folder `test_jd/` with a sample job description (`.docx`)
   - Create a folder `test_resumes/` with sample resumes (`.pdf` or `.docx`)

---

## Test Case 1: Basic Run with OpenAI Internal

**Setup:**
- Provider: `openai_internal` (or switch to `openai` if you have an API key)
- Files: At least 2 resumes

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/
```

**Expected Output:**
```
Found 2 resume(s) to process
Processing: resume1.pdf
  → 85/100 YES
Processing: resume2.docx
  → 72/100 MAYBE

✅ Complete! Processed 2 candidates
   JSON: output/results_<timestamp>.json
   Markdown: output/results_<timestamp>.md
```

**Verify:**
- [ ] JSON file contains `total_candidates_evaluated: 2`
- [ ] JSON file has candidates sorted by `total_score` descending
- [ ] Markdown file shows shortlist table with rankings
- [ ] Markdown file has detailed assessments for each candidate

---

## Test Case 2: Top N Filter

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/ --top 1
```

**Expected Output:**
- Only 1 candidate appears in output files
- `total_candidates_evaluated` in JSON shows the original count (e.g., 5)
- But only top 1 is listed in the `candidates` array

---

## Test Case 3: Custom Output Folder

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/ --output ./custom_output
```

**Expected Output:**
- Results written to `./custom_output/` instead of `./output/`

---

## Test Case 4: Custom Config File

**Setup:** Create `config_test.yaml`:
```yaml
model:
  provider: openai
  model_name: gpt-4o
  api_key_env: OPENAI_API_KEY

output:
  folder: ./output
  json: true
  markdown: true
```

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/ --config config_test.yaml
```

**Expected Output:**
- Uses the config from `config_test.yaml`
- Provider shows as `openai` in output

---

## Test Case 5: Error Handling - Missing API Key

**Setup:** Create an empty `.env` file or remove the API key

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/
```

**Expected Output:**
```
Configuration error: API key not found in environment: INTERNAL_OPENAI_KEY. Set it in .env file.
```

---

## Test Case 6: Error Handling - Missing Config File

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/ --config nonexistent.yaml
```

**Expected Output:**
```
Configuration error: Config file not found: nonexistent.yaml
```

---

## Test Case 7: Error Handling - Invalid Provider

**Setup:** Edit `config.yaml`:
```yaml
model:
  provider: invalid_provider
```

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/
```

**Expected Output:**
```
Configuration error: Invalid provider: invalid_provider. Must be one of ['openai_internal', 'openai', 'anthropic']
```

---

## Test Case 8: No Resumes Found

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes empty_folder/
```

**Expected Output:**
```
No resume files (.pdf or .docx) found in empty_folder/
```

---

## Test Case 9: Mixed File Types

**Setup:** Create resumes with both `.pdf` and `.docx` extensions

**Command:**
```bash
python main.py --jd test_jd/senior_engineer.docx --resumes test_resumes/
```

**Expected Output:**
- All valid files are processed
- Unsupported files are skipped (with warning in logs)

---

## JSON Output Schema Verification

Check that the generated JSON matches this structure:

```json
{
  "job_description_file": "senior_engineer.docx",
  "run_timestamp": "2026-03-13T10:30:00",
  "model": "gpt-4o",
  "provider": "openai_internal",
  "total_candidates_evaluated": 2,
  "candidates": [
    {
      "rank": 1,
      "candidate_name": "John Doe",
      "file_name": "john_doe.pdf",
      "total_score": 85,
      "recommendation": "YES",
      "summary": "...",
      "dimensions": {
        "skills_match": {"score": 22, "rationale": "..."},
        "experience_relevance": {"score": 21, "rationale": "..."},
        "seniority_alignment": {"score": 21, "rationale": "..."},
        "employment_patterns": {"score": 21, "rationale": "..."}
      },
      "parse_error": false
    }
  ]
}
```

---

## Markdown Output Verification

Check that the generated Markdown contains:
- [ ] Header with role, date, candidates evaluated, model info
- [ ] Shortlist table with Rank, Candidate, Score, Recommendation columns
- [ ] Detailed Assessments section with dimension scores
- [ ] Emoji indicators (✅ for STRONG_YES/YES, ⚠️ for MAYBE, ❌ for NO)