# Configuration Guide

Citadel Local is configured via `.citadel-local.yaml` (copy from `.citadel-local.example.yaml`). This guide explains all options and tuning strategies.

## Full configuration reference

```yaml
# Directories to skip during scan (glob patterns)
ignore:
  - node_modules      # JavaScript dependencies
  - .git              # Git metadata
  - dist              # Build outputs
  - build             # Build artifacts
  - vendor            # PHP dependencies
  - .venv             # Python virtual environment
  - __pycache__       # Python bytecode

# File size limit (default: 2 MB)
# Larger files slow scans; secrets are usually in small config files
max_file_mb: 2

# Lines of context around findings in reports (default: 40)
# More context = more readable reports but larger JSON/reports
context_lines: 40

# LLM Council configuration
ollama:
  # Enable/disable LLM-based analysis
  enabled: true

  # Ollama server endpoint
  base_url: "http://127.0.0.1:11434"

  # Triage model (fast, category/severity labeling)
  triage_model: "llama3.2:3b"

  # Deep analysis model (code reasoning, remediation)
  deep_model: "qwen3-coder:30b"

  # Skeptic model (false-positive reduction)
  skeptic_model: "gpt-oss:20b"

  # API timeout in seconds
  timeout_s: 90
```

## Option details

### `ignore` (list of strings)
Directories/patterns to skip during file collection. Use glob syntax:
- `node_modules` — matches any directory named `node_modules`
- `.git` — matches `.git` anywhere
- `**/*.pyc` — matches `.pyc` files recursively
- `tests/fixtures` — matches `tests/fixtures` at root

**Why?** Large dependency directories and build outputs waste scan time and inflate false positives.

**Default set:**
```yaml
ignore:
  - node_modules
  - .git
  - dist
  - build
  - vendor
  - .venv
  - __pycache__
```

**Common additions:**
```yaml
ignore:
  - coverage        # coverage reports
  - .pytest_cache   # pytest cache
  - .mypy_cache     # mypy cache
  - target          # Java/Rust builds
  - bin             # Go builds
  - venv            # Python venv (alternative spelling)
```

### `max_file_mb` (int, default: 2)
Skip files larger than this threshold.

**Why?**
- Secrets are rarely in 100MB log files
- Large files slow deterministic detectors
- Saves LLM API time

**Tuning:**
- `1` — aggressive, faster (may miss large config files)
- `2` — balanced (recommended)
- `5` — permissive, slower
- `0` — no limit (not recommended)

### `context_lines` (int, default: 40)
Lines of context before/after a finding in reports and JSON.

**Trade-offs:**
- Lower (e.g., `10`) — compact reports, faster JSON output
- Higher (e.g., `50`) — easier to understand code context
- `0` — no context (not recommended)

### `ollama.enabled` (bool, default: true)
Run deterministic detectors only (no LLM council).

**Use case:** Quick feedback loop during development, or if Ollama is unavailable.

**Example:**
```bash
# Run without LLM (fast)
citadel scan /path/to/repo

# Output still includes detector findings in findings.json
```

### `ollama.base_url` (string, default: `http://127.0.0.1:11434`)
Ollama server endpoint.

**Examples:**
```yaml
# Local development
base_url: "http://127.0.0.1:11434"

# Remote Ollama server
base_url: "http://ollama.internal.company.com:11434"

# Docker container
base_url: "http://host.docker.internal:11434"

# Kubernetes service
base_url: "http://ollama-service.default.svc.cluster.local:11434"
```

### `ollama.triage_model` (string, default: `llama3.2:3b`)
Fast model for classifying findings (severity, category, confidence).

**Recommended:**
| Model | Params | Speed | Memory | Best for |
|-------|--------|-------|--------|----------|
| `llama3.2:3b` | 3B | ~1-2s | ~3GB | Fast triage (default) |
| `phi3:3.8b` | 3.8B | ~1-2s | ~4GB | Fast, competitive quality |
| `qwen2:7b` | 7B | ~3s | ~7GB | Balanced triage |
| `mistral:7b` | 7B | ~3s | ~8GB | Good English |

**Tuning:** Stick with 3-7B models here. Larger models are slower without proportional benefit for classification.

### `ollama.deep_model` (string, default: `qwen3-coder:30b`)
Strong model for code analysis and remediation guidance.

**Recommended:**
| Model | Params | Speed | Memory | Best for |
|-------|--------|-------|--------|----------|
| `qwen3-coder:30b` | 30B | ~10-20s | ~28GB | Code reasoning + fixes (default) |
| `mistral-large:30b` | 30B | ~10-20s | ~28GB | Strong all-rounder |
| `deepseek-coder:33b` | 33B | ~12-25s | ~32GB | Very strong code model |
| `llama2:70b` | 70B | ~30-60s | ~60GB | Top-tier quality, slower |

**Tuning:** Balance model strength with latency. For CI/CD, prefer faster models (20-30B). For deep analysis, use 33B+.

### `ollama.skeptic_model` (string, default: `gpt-oss:20b`)
Model for reducing false positives. Should be thoughtful and critical.

**Recommended:**
| Model | Params | Speed | Memory | Best for |
|-------|--------|-------|--------|----------|
| `gpt-oss:20b` | 20B | ~8-15s | ~20GB | FP reduction (default) |
| `mistral:20b` | 20B | ~8-15s | ~20GB | Strong reasoning |
| `neural-chat:7b` | 7B | ~2-5s | ~7GB | Fast, lighter |
| `qwen2:7b` | 7B | ~3s | ~7GB | Good skeptic reasoning |

**Tuning:** The skeptic's job is to argue *against* findings. Smaller models (7B) work fine; focus on thoughtful prompts over model size.

### `ollama.timeout_s` (int, default: 90)
API request timeout in seconds.

**Tuning:**
- `30` — strict, may timeout on slow machines
- `60` — balanced
- `90` — lenient (default)
- `180` — very lenient for large models or slow GPUs

## Performance tuning

### Faster scans (trade: less depth)

```yaml
# Run detectors only
ollama:
  enabled: false

# Skip large files
max_file_mb: 1

# Reduce context
context_lines: 20

# Use smaller triage model
triage_model: "phi3:3.8b"
deep_model: "qwen2:7b"  # smaller
skeptic_model: "neural-chat:7b"  # smaller
```

**Expected speedup:** 2-3x faster, minimal quality loss for high-confidence findings.

### Higher quality (trade: slower)

```yaml
# Keep LLM council enabled
ollama:
  enabled: true

# Larger file limit
max_file_mb: 5

# More context
context_lines: 50

# Stronger models
triage_model: "qwen2:7b"
deep_model: "deepseek-coder:33b"  # larger, stronger
skeptic_model: "mistral:20b"  # larger, more critical
```

**Expected trade-off:** 2-3x slower, higher quality remediation guidance.

### Memory-constrained environments

```yaml
# Use smallest working models
triage_model: "phi3:3.8b"      # ~4GB
deep_model: "mistral:7b"        # ~8GB
skeptic_model: "phi3:3.8b"      # ~4GB

# Reduce other overhead
ignore:
  - "*"  # add aggressively as needed
max_file_mb: 1
context_lines: 10
```

**Note:** This setup uses ~16GB peak memory but sacrifices accuracy. Test on your codebase first.

## Model selection guide

**Choose based on your priorities:**

1. **Speed matters (CI/CD pipelines)**
   ```yaml
   triage_model: "llama3.2:3b"
   deep_model: "qwen2:7b"
   skeptic_model: "phi3:3.8b"
   ```
   → ~15-20s total per finding

2. **Quality matters (security audits)**
   ```yaml
   triage_model: "qwen2:7b"
   deep_model: "deepseek-coder:33b"
   skeptic_model: "mistral:20b"
   ```
   → ~40-60s total per finding, better fixes

3. **Balanced (recommended for most teams)**
   ```yaml
   triage_model: "llama3.2:3b"
   deep_model: "qwen3-coder:30b"
   skeptic_model: "gpt-oss:20b"
   ```
   → ~20-30s per finding, good quality/speed

## Environment variables

Override config with env vars:

```bash
CITADEL_OLLAMA_BASE_URL=http://ollama.internal:11434 \
CITADEL_OLLAMA_TRIAGE_MODEL=mistral:7b \
citadel scan /path/to/repo
```

## Per-repo overrides

Store `.citadel-local.yaml` in the repo root to customize for that project:

```yaml
# .citadel-local.yaml (in the repo being scanned)
ignore:
  - node_modules
  - tests/fixtures
  - docs/examples  # ignore example code

max_file_mb: 5  # this repo has large config files
```

## Testing your config

Dry run to see what files will be scanned:

```bash
citadel scan /path/to/repo --dry-run
# Output: list of files that will be scanned
```

Run with verbose output:

```bash
citadel scan /path/to/repo --verbose
# Output: detector names, LLM calls, timing info
```

## Common configs

### Startup/Web App
```yaml
ignore:
  - node_modules
  - .git
  - dist
  - build
  - .env          # already excluded by detectors
  - venv

max_file_mb: 2
context_lines: 40

ollama:
  enabled: true
  triage_model: "llama3.2:3b"
  deep_model: "qwen3-coder:30b"
  skeptic_model: "gpt-oss:20b"
```

### Enterprise/Large Codebase
```yaml
ignore:
  - node_modules
  - .git
  - dist
  - build
  - vendor
  - venv
  - .mypy_cache
  - __pycache__
  - .pytest_cache
  - coverage

max_file_mb: 3
context_lines: 50

ollama:
  enabled: true
  triage_model: "qwen2:7b"          # faster classification
  deep_model: "deepseek-coder:33b"  # strong analysis
  skeptic_model: "mistral:20b"      # thorough FP reduction
  timeout_s: 120
```

### CI/CD (Speed optimized)
```yaml
ignore:
  - node_modules
  - .git
  - dist
  - build
  - vendor
  - venv
  - tests

max_file_mb: 1
context_lines: 20

ollama:
  enabled: true
  triage_model: "phi3:3.8b"      # smallest, fast
  deep_model: "qwen2:7b"         # smaller, reasonable
  skeptic_model: "neural-chat:7b"  # small, critical
  timeout_s: 60
```

## Troubleshooting config issues

**"Model not found" error**
```bash
# List available models
curl http://127.0.0.1:11434/api/tags

# Pull a model
ollama pull llama3.2:3b
```

**Slow scans**
- Reduce `max_file_mb`
- Use smaller models (3-7B instead of 30B+)
- Disable `ollama.enabled: false` for quick feedback
- Add more directories to `ignore`

**Out of memory**
- Use smaller models (3-7B)
- Reduce context_lines
- Check GPU availability (`ollama status`)
- Run Ollama on a separate machine

**Timeouts**
- Increase `timeout_s` (more lenient)
- Use smaller models (faster)
- Check network connectivity to Ollama
