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

## Setting Up API Keys

### Option 1: OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it won't be shown again)
5. Add to your `.env` file:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
6. Update `config.yaml` to use `openai` provider

### Option 2: Anthropic Claude API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign in or create an account
3. Go to "API Keys" in the sidebar
4. Click "Create Key"
5. Copy the key
6. Add to your `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
7. Update `config.yaml` to use `anthropic` provider

### Option 3: Internal OpenAI-Compatible Endpoint

If your organization has an internal AI gateway (common in banks/enterprises):

1. Get the endpoint URL and API key from your IT department
2. Add to your `.env` file:
   ```
   INTERNAL_OPENAI_KEY=your-internal-key-here
   ```
3. Update `config.yaml`:
   ```yaml
   model:
     provider: openai_internal
     endpoint: https://your-internal-endpoint/v1
     model_name: gpt-4o
     api_key_env: INTERNAL_OPENAI_KEY
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