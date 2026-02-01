# Troubleshooting & FAQ

Common issues and solutions.

## Installation & Setup

### "ModuleNotFoundError: No module named 'citadel_local'"

**Cause:** Package not installed in editable mode.

**Solution:**
```bash
cd /path/to/Citadel-Local
pip install -e .
```

Verify:
```bash
which citadel
citadel --version
```

### "Python 3.11+ required"

**Cause:** Running on Python 3.10 or older.

**Solution:**
```bash
# Check version
python --version

# Install Python 3.11+
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Then create venv with correct version
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Import errors with YAML/requests

**Cause:** Dependencies not installed.

**Solution:**
```bash
pip install -e .  # installs pyyaml, requests
```

## Ollama Issues

### "Connection refused: http://127.0.0.1:11434"

**Cause:** Ollama server not running.

**Solution:**

1. **Start Ollama:**
   ```bash
   ollama serve
   ```

2. **In another terminal, verify:**
   ```bash
   curl http://127.0.0.1:11434/api/tags
   # Should return JSON with available models
   ```

3. **If Ollama not installed:**
   - macOS: `brew install ollama`
   - Linux: [Download](https://ollama.ai/download/linux)
   - Windows: [Download](https://ollama.ai/download/windows)

### "Model not found: qwen3-coder:30b"

**Cause:** Model not pulled to local Ollama.

**Solution:**
```bash
# Pull the model
ollama pull qwen3-coder:30b

# List available models
ollama list

# See all available models
ollama show  # (or check ollama.ai for full list)
```

**Note:** Large models (20B+) require 20-30GB disk space and 16-32GB RAM to run.

### API timeout / "Request timed out"

**Cause:** Model taking longer than configured timeout.

**Reasons:**
- GPU not available (falling back to CPU)
- Slow network to Ollama
- Model is very large (70B+)
- System under heavy load

**Solutions:**

1. **Increase timeout in config:**
   ```yaml
   ollama:
     timeout_s: 180  # up from 90
   ```

2. **Use faster models:**
   ```yaml
   triage_model: "llama3.2:3b"      # fast
   deep_model: "qwen2:7b"            # smaller
   skeptic_model: "neural-chat:7b"   # smaller
   ```

3. **Check GPU availability:**
   ```bash
   # NVIDIA
   nvidia-smi

   # Check Ollama is using GPU
   ollama status
   ```

4. **Run scanner without LLM:**
   ```bash
   # Disable LLM council in config
   ollama:
     enabled: false

   # Or override via CLI
   CITADEL_OLLAMA_ENABLED=false citadel scan /path
   ```

### "Out of memory" / GPU memory errors

**Cause:** Model too large for available GPU/RAM.

**Solutions:**

1. **Use smaller models:**
   ```yaml
   deep_model: "mistral:7b"  # instead of 30B
   ```

2. **Run on CPU only (slower):**
   - Stop Ollama
   - Set `OLLAMA_GPU=0` before running
   - Restart Ollama: `OLLAMA_GPU=0 ollama serve`

3. **Run Ollama on separate machine:**
   ```yaml
   base_url: "http://ollama-server.internal:11434"
   ```

4. **Run with GPU memory limits:**
   ```bash
   CUDA_VISIBLE_DEVICES=0 ollama serve  # use only first GPU
   ```

## Scanning Issues

### No output files created / "out/ directory empty"

**Cause:** Scan completed but no findings; directories might not exist.

**Solution:**

1. **Check if findings exist:**
   ```bash
   ls -la out/
   cat out/findings.json
   ```

2. **Run verbose scan:**
   ```bash
   citadel scan /path --verbose
   # Should show detector runs, findings
   ```

3. **Dry run to check what's being scanned:**
   ```bash
   citadel scan /path --dry-run
   # Lists files, ignores patterns, etc.
   ```

### "Permission denied" / Cannot read files

**Cause:** Running as wrong user; insufficient permissions.

**Solution:**
```bash
# Check permissions
ls -la /path/to/repo

# Run with appropriate user
sudo citadel scan /path  # if needed

# Or fix permissions
chmod -R u+r /path/to/repo
```

### Scan is very slow

**Cause:** Scanning too many files, LLM calls slow, large file limits.

**Solutions:**

1. **Reduce scope:**
   ```yaml
   ignore:
     - node_modules
     - dist
     - build
     - __pycache__
     - .git
     - vendor
     - .mypy_cache
   ```

2. **Use faster models:**
   ```yaml
   triage_model: "phi3:3.8b"
   deep_model: "qwen2:7b"
   skeptic_model: "neural-chat:7b"
   ```

3. **Disable LLM:**
   ```yaml
   ollama:
     enabled: false
   ```

4. **Reduce file size limit:**
   ```yaml
   max_file_mb: 1
   ```

5. **Use `diff` instead of full scan:**
   ```bash
   citadel diff /path  # scan only changed files
   ```

### "Too many false positives"

**Cause:** Detectors are noisy or LLM skeptic model is weak.

**Solutions:**

1. **Stronger skeptic model:**
   ```yaml
   skeptic_model: "mistral:20b"  # or deepseek
   ```

2. **Review and tune detector thresholds** (see CONTRIBUTING.md)

3. **Create baseline and track deltas:**
   ```bash
   # Record known issues
   citadel baseline /path

   # Future scans show only new findings
   citadel scan /path
   ```

4. **Manually review findings:**
   - Edit `out/findings.json`
   - Remove false positives
   - Discuss with team

## Reporting Issues

### "Invalid JSON in findings.json"

**Cause:** Encoding issues, truncated output, or internal error.

**Solution:**

1. **Validate JSON:**
   ```bash
   python -m json.tool out/findings.json
   ```

2. **Check encoding:**
   ```bash
   file out/findings.json
   iconv -f UTF-8 -t UTF-8 -c out/findings.json
   ```

3. **Re-run scan:**
   ```bash
   rm out/findings.json
   citadel scan /path --verbose
   ```

### "report.md not generated"

**Cause:** findings.json is empty or malformed.

**Solution:**

1. **Check findings.json:**
   ```bash
   cat out/findings.json | python -m json.tool
   ```

2. **Regenerate report:**
   ```bash
   citadel report out/findings.json
   ```

3. **Check permissions:**
   ```bash
   ls -la out/
   chmod 644 out/*
   ```

### "LLM output not included in findings"

**Cause:** LLM disabled, timeout, or parse error.

**Solution:**

1. **Check if LLM is enabled:**
   ```yaml
   ollama:
     enabled: true
   ```

2. **Check Ollama is running:**
   ```bash
   curl http://127.0.0.1:11434/api/tags
   ```

3. **Check logs for errors:**
   ```bash
   citadel scan /path --verbose 2>&1 | grep -i error
   ```

4. **Try with single model:**
   ```bash
   # Disable skeptic to isolate
   citadel scan /path --verbose
   ```

## Performance & Memory

### "Scan uses 100% CPU"

**Cause:** Deterministic detectors running, LLM inference, or GPU contention.

**Solutions:**

1. **Limit to detector phase:**
   ```yaml
   ollama:
     enabled: false
   ```

2. **Reduce parallelism** (if implemented):
   - Check config for concurrency settings
   - Reduce to 1 worker

3. **Run off-peak:**
   - Schedule scans during low-traffic hours
   - Separate Ollama server for scanning

### "Scan stalls / freezes"

**Cause:** LLM inference hanging, deadlock, or network issue.

**Solutions:**

1. **Add timeout, interrupt:**
   ```bash
   timeout 300 citadel scan /path  # 5-minute timeout
   ```

2. **Check Ollama status:**
   ```bash
   curl http://127.0.0.1:11434/api/tags
   # If no response, Ollama may have crashed
   ```

3. **Restart Ollama:**
   ```bash
   pkill ollama
   sleep 2
   ollama serve &
   ```

4. **Check disk space:**
   ```bash
   df -h
   du -sh ~/.ollama  # Ollama model cache
   ```

## Git & Version Control

### "citadel diff" shows no changes

**Cause:** Not a git repo, or no uncommitted changes.

**Solutions:**

1. **Check if git repo:**
   ```bash
   git status
   ```

2. **Commit or stage changes:**
   ```bash
   git add .
   git commit -m "message"
   ```

3. **Check which branch is base:**
   ```bash
   git log --oneline -5
   # diff compares against origin/main by default
   ```

## Contributing & Development

### "Tests fail"

**Cause:** Environment, missing dependencies, or code issue.

**Solutions:**

1. **Install dev dependencies:**
   ```bash
   pip install -e .[dev]
   ```

2. **Run tests:**
   ```bash
   pytest -q
   pytest -v  # verbose
   pytest -k test_name  # single test
   ```

3. **Check Python version:**
   ```bash
   python --version  # must be 3.11+
   ```

### "Linting fails"

**Cause:** Code doesn't match style.

**Solutions:**

1. **Check linting:**
   ```bash
   ruff check src/
   ```

2. **Auto-format:**
   ```bash
   ruff format src/
   ```

3. **Fix specific issues:**
   - Read ruff output
   - Manually update code
   - Re-run check

## FAQ

### Q: Does Citadel send data to external servers?

**A:** No. Ollama models run locally. All code stays on your machine. No cloud services, no telemetry. This is the core "offline-first" design.

### Q: Can I use Citadel for penetration testing?

**A:** No. Citadel is strictly defensive (auditing your own code). It's designed for:
- Code review automation
- CI/CD integration
- Shift-left security
- Compliance scanning

For authorized penetration testing, use dedicated tools like Burp Suite, Metasploit, etc.

### Q: What models do you recommend?

**A:** See `docs/CONFIGURATION.md` for detailed model selection. Quick answer:
- **Triage:** `llama3.2:3b` (fast, good)
- **Deep analysis:** `qwen3-coder:30b` (strong code reasoning)
- **Skeptic:** `gpt-oss:20b` (critical thinking)

**Alternative (memory-constrained):** `phi3:3.8b`, `qwen2:7b`, `neural-chat:7b`

### Q: How do I integrate with GitHub Actions?

**A:** See `docs/CI-CD.md` for full integration guide. Quick example:
```yaml
- name: Scan with Citadel
  run: |
    pip install citadel-local
    citadel scan . --out scan-results/

- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: citadel-findings
    path: scan-results/
```

### Q: Can I exclude specific files from scan?

**A:** Yes, use `.ignore` patterns in config:
```yaml
ignore:
  - tests/fixtures/*.py
  - docs/examples/
  - vendor/
```

### Q: How do I report a bug?

**A:** See `docs/SECURITY.md` for bug reporting policy. Quick answer:
- Report to this repository's issues
- Do NOT include sensitive findings publicly
- Use responsible disclosure (private issues if available)

### Q: What file types are supported?

**A:** Deterministic detectors work on any text file (source code, configs, docs). LLM models best with:
- Python, JavaScript, Java, Go, Rust, C/C++
- YAML, JSON, XML configs
- Shell scripts

LLM may struggle with:
- Binary files
- Very large functions (> 1000 lines)
- Unfamiliar languages

### Q: How do I add a custom detector?

**A:** See `docs/CONTRIBUTING.md` for step-by-step guide. Quick overview:
1. Create `src/citadel_local/detectors/my_detector.py`
2. Register in `src/citadel_local/detectors/__init__.py`
3. Add tests in `tests/`
4. Document in `rules/*.yaml`

### Q: Can Citadel detect all vulnerabilities?

**A:** No. It catches:
- **High-signal patterns:** secrets, obvious injection, insecure crypto
- **Common misconfigs:** Docker, GitHub Actions, Kubernetes

It doesn't catch:
- Logic bugs
- Complex authentication flaws
- Advanced exploitation techniques
- Race conditions

Use Citadel as one layer in defense-in-depth.

### Q: How do I baseline known findings?

**A:**
```bash
# Record current findings as accepted
citadel baseline /path/to/repo

# Future scans show only NEW findings
citadel scan /path/to/repo
```

This creates `.citadel-baseline.json` to track approved issues.

### Q: Can I run Citadel in a container?

**A:** Yes:
```dockerfile
FROM python:3.11-slim
RUN pip install citadel-local

# Also need Ollama
RUN apt-get update && apt-get install -y ollama

ENTRYPOINT ["citadel"]
```

Then:
```bash
docker run --rm -v /path/to/repo:/scan citadel scan /scan
```

For Ollama on separate container:
```bash
docker run --rm -v /path/to/repo:/scan \
  -e CITADEL_OLLAMA_BASE_URL=http://ollama-service:11434 \
  citadel scan /scan
```
