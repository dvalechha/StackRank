# StackRank

A local CLI tool that screens resumes against a job description using AI and outputs a ranked candidate list.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` and add your API key:
   ```bash
   cp .env.example .env
   ```

2. Edit `config.yaml` to configure your AI provider:

### Internal OpenAI-compatible endpoint (air-gapped)
```yaml
model:
  provider: openai_internal
  endpoint: https://your-internal-endpoint/v1
  model_name: gpt-4o
  api_key_env: INTERNAL_OPENAI_KEY

output:
  folder: ./output
  json: true
  markdown: true
```

### External OpenAI
```yaml
model:
  provider: openai
  model_name: gpt-4o
  api_key_env: OPENAI_API_KEY
```

### Anthropic Claude
```yaml
model:
  provider: anthropic
  model_name: claude-3-opus-20240229
  api_key_env: ANTHROPIC_API_KEY
```

## Usage

```bash
# Basic usage
python main.py --jd ./jds/senior_engineer.docx --resumes ./resumes/

# With top N output
python main.py --jd ./jds/senior_engineer.docx --resumes ./resumes/ --top 10

# Custom config
python main.py --jd ./jds/role.docx --resumes ./resumes/ --config ./config_openai.yaml
```

## Output

Results are written to the configured output folder (default: `./output`):

- `results_<timestamp>.json` - Full results in JSON format
- `results_<timestamp>.md` - Human-readable Markdown report

## Privacy

Resumes are only sent to the configured AI endpoint. No other network calls are made. When using `openai_internal`, all data stays within your organization's network.