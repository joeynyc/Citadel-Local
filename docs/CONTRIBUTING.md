# Contributing Guide

## Development Setup

### Prerequisites
- Python 3.11+
- Git
- Ollama (for testing LLM council features)

### Local development

```bash
# Clone repository
git clone https://github.com/anthropics/Citadel-Local.git
cd Citadel-Local

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev tools
pip install -e .[dev]
```

### Verify setup

```bash
# Run tests
pytest -q

# Check code style
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

## Design Principles

### 1. Evidence first, models second
- **Deterministic detectors** find grounded evidence (file path, line number, snippet)
- **LLM models** analyze that evidence and provide context/remediation
- Never rely on LLM to discover vulnerabilities; detectors must provide proof

### 2. High-signal rules over noise
- Aim for <10% false positives
- Entropy-based secrets detection (avoid pure regex)
- Context matters (is this code path reachable?)
- When in doubt, let skeptic model reduce false positives

### 3. Defensive only
- Detect vulnerabilities in code you own or have permission to test
- Never generate exploit payloads or weaponized guidance
- Focus on "what's wrong and how to fix it"

## Adding a New Detector

### Overview

A detector is a Python function that:
1. Takes file content + metadata
2. Finds patterns matching rules
3. Returns list of findings with evidence

### Step 1: Create the detector module

Create `src/citadel_local/detectors/my_detector.py`:

```python
"""
Detector for [vulnerability type].

Examples:
- [finding type 1]
- [finding type 2]
"""

import re
from pathlib import Path


def find_vulnerable_patterns(
    file_path: str,
    content: str,
    context_lines: int = 40
) -> list[dict]:
    """
    Find [vulnerability type] in [file_type] files.

    Args:
        file_path: Path to file being scanned
        content: File contents
        context_lines: Lines of context around finding

    Returns:
        List of finding dictionaries with keys:
        - file: str (file path)
        - line_start: int (line number of finding)
        - line_end: int (line number of finding)
        - snippet: str (code snippet with finding)
        - detector_id: str (e.g., "detector_my_detector")
        - rule_id: str (e.g., "MY_VULN_001")
    """
    findings = []
    lines = content.split('\n')

    # Example: search for hardcoded API keys
    # Pattern should be specific to avoid false positives
    pattern = r'API_KEY\s*=\s*["\']([^"\']{32,})["\']'

    for line_num, line in enumerate(lines, 1):
        if re.search(pattern, line):
            # Skip if in comment
            if line.strip().startswith('#'):
                continue

            # Calculate context window
            context_start = max(0, line_num - context_lines)
            context_end = min(len(lines), line_num + context_lines)
            snippet = '\n'.join(lines[context_start:context_end])

            findings.append({
                'file': file_path,
                'line_start': line_num,
                'line_end': line_num,
                'snippet': snippet,
                'detector_id': 'detector_my_detector',
                'rule_id': 'MY_VULN_001',
            })

    return findings
```

### Step 2: Register the detector

Edit `src/citadel_local/detectors/__init__.py`:

```python
from . import my_detector  # Add import

def run_detectors(
    file_path: str,
    content: str,
    context_lines: int = 40,
    file_type: str = None
) -> list[dict]:
    """Run all detectors on a file."""
    all_findings = []

    # ... existing detectors ...

    # Add your detector
    all_findings.extend(
        my_detector.find_vulnerable_patterns(
            file_path, content, context_lines
        )
    )

    return all_findings
```

### Step 3: Add rules to YAML

Edit `rules/insecure_patterns.yaml` or create `rules/my_detector.yaml`:

```yaml
# Rules metadata for detector
detectors:
  detector_my_detector:
    name: "My Vulnerability Detector"
    description: "Detects [vulnerability type]"
    enabled: true

    rules:
      MY_VULN_001:
        name: "Hardcoded API Key"
        description: "API key found in source code"
        severity: "critical"
        category: "secrets"
        cwe: "CWE-798"  # Hardcoded credentials
        remediation: |
          1. Remove the hardcoded key
          2. Use environment variables or secrets manager
          3. Rotate the exposed key
          4. Add to .gitignore
```

### Step 4: Write tests

Create `tests/test_my_detector.py`:

```python
"""Tests for my_detector."""

import pytest
from citadel_local.detectors import my_detector


class TestMyDetector:
    """Test my_detector finds expected vulnerabilities."""

    def test_finds_hardcoded_api_key(self):
        """Should detect hardcoded API key."""
        code = '''
import requests

API_KEY = "AKIAIOSFODNN7EXAMPLE"
response = requests.get(
    "https://api.example.com",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
'''
        findings = my_detector.find_vulnerable_patterns(
            "test.py", code
        )

        assert len(findings) == 1
        assert findings[0]['rule_id'] == 'MY_VULN_001'
        assert findings[0]['line_start'] == 3
        assert 'API_KEY' in findings[0]['snippet']

    def test_ignores_commented_keys(self):
        """Should not flag commented out keys."""
        code = '''
# API_KEY = "AKIAIOSFODNN7EXAMPLE"
def get_key():
    return "safe_value"
'''
        findings = my_detector.find_vulnerable_patterns(
            "test.py", code
        )

        assert len(findings) == 0

    def test_ignores_short_strings(self):
        """Should not flag strings that are too short."""
        code = 'API_KEY = "short"'
        findings = my_detector.find_vulnerable_patterns(
            "test.py", code
        )

        assert len(findings) == 0

    def test_handles_different_quote_styles(self):
        """Should handle both single and double quotes."""
        code_double = '''API_KEY = "AKIAIOSFODNN7EXAMPLE"'''
        code_single = '''API_KEY = 'AKIAIOSFODNN7EXAMPLE2'"""

        findings_double = my_detector.find_vulnerable_patterns(
            "test.py", code_double
        )
        findings_single = my_detector.find_vulnerable_patterns(
            "test.py", code_single
        )

        assert len(findings_double) == 1
        assert len(findings_single) == 1
```

Run tests:
```bash
pytest tests/test_my_detector.py -v
```

## Best Practices

### Pattern design

**Good patterns (low false positive):**
- Entropy-based: requires minimum randomness
- Length-based: matches actual secret formats
- Context-aware: checks surrounding code
- Multi-line: requires pattern in specific context

**Bad patterns (high false positive):**
- `password\s*=` — matches comments, examples, tests
- `secret` — too generic
- Regex without bounds — matches substrings

### Example: Good entropy-based detector

```python
import re
import math

def shannon_entropy(s):
    """Calculate Shannon entropy of string."""
    if not s:
        return 0
    entropy = 0
    for x in set(s):
        p_x = s.count(x) / len(s)
        entropy += -p_x * math.log2(p_x)
    return entropy

def is_likely_secret(s, min_entropy=3.5, min_length=20):
    """Check if string looks like a secret."""
    if len(s) < min_length:
        return False
    return shannon_entropy(s) > min_entropy

# Usage in detector
def find_secrets(file_path, content, context_lines=40):
    findings = []
    lines = content.split('\n')

    # Look for assignment patterns
    pattern = r'[\w_]+\s*=\s*["\']([^"\']{20,})["\']'

    for line_num, line in enumerate(lines, 1):
        for match in re.finditer(pattern, line):
            value = match.group(1)

            # Filter using entropy
            if is_likely_secret(value):
                findings.append({
                    'file': file_path,
                    'line_start': line_num,
                    'line_end': line_num,
                    'snippet': line,
                    'detector_id': 'detector_secrets',
                    'rule_id': 'SECRET_001',
                })

    return findings
```

### Testing patterns

Test your detector against:

```python
# True positives: actual vulnerabilities
TRUE_POSITIVE = """
database_url = "postgresql://user:password@localhost/db"
"""

# True negatives: safe code that looks similar
TRUE_NEGATIVE_COMMENT = """
# Example: postgresql://user:password@localhost/db
"""

TRUE_NEGATIVE_TEST = """
def test_connection():
    url = get_from_config()  # Safe, dynamic
"""

TRUE_NEGATIVE_PLACEHOLDER = """
# TODO: postgresql://user:REDACTED@localhost/db
"""

# Run tests
assert detector.scan(TRUE_POSITIVE) != []
assert detector.scan(TRUE_NEGATIVE_COMMENT) == []
assert detector.scan(TRUE_NEGATIVE_TEST) == []
```

### Common pitfalls

**1. Not handling context correctly**
```python
# ❌ BAD: Includes context even if not set
if finding:
    snippet = get_context(line, lines, context_lines)

# ✅ GOOD: Let the caller decide
findings.append({'snippet': line, 'context_lines': context_lines})
```

**2. Case sensitivity issues**
```python
# ❌ BAD: Only matches lowercase
if 'password' in line:

# ✅ GOOD: Case-insensitive
if re.search(r'password', line, re.IGNORECASE):
```

**3. Skipping file type checks**
```python
# ❌ BAD: Runs detector on all files
def find_patterns(file_path, content):
    # Might crash on binary files

# ✅ GOOD: Check file type first
def find_patterns(file_path, content):
    if file_path.endswith('.pyc'):
        return []
    # Safe to process
```

**4. Not validating line numbers**
```python
# ❌ BAD: May produce invalid line numbers
line_start = match.start() / avg_line_length

# ✅ GOOD: Count actual line breaks
line_num = content[:match.start()].count('\n') + 1
```

## Testing Your Work

### Run full test suite
```bash
pytest -q
pytest -v  # verbose
pytest -k detector_my  # run specific tests
```

### Lint and format
```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Manual testing
```bash
# Create test repo
mkdir test-repo
echo 'API_KEY = "AKIAIOSFODNN7EXAMPLE"' > test-repo/test.py

# Scan it
citadel scan test-repo/

# Check findings
cat out/findings.json | python -m json.tool
```

### Performance testing
```bash
# Time the detector
time citadel scan /large/repo --verbose

# Profile detectors
python -m cProfile -s cumtime -m citadel.cli scan /path
```

## Common Detector Patterns

### Regex-based (simple patterns)
```python
def find_patterns(file_path, content):
    pattern = r'vulnerable_function\s*\('
    findings = []
    for line_num, line in enumerate(content.split('\n'), 1):
        if re.search(pattern, line):
            findings.append({...})
    return findings
```

### Entropy-based (secrets)
```python
def find_secrets(file_path, content):
    # Use Shannon entropy to detect random strings
    for value in extract_strings(content):
        if shannon_entropy(value) > threshold:
            findings.append({...})
    return findings
```

### AST-based (Python only)
```python
def find_patterns(file_path, content):
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for vulnerable function calls
            pass
    return findings
```

### Pattern matching (YAML rules)
```python
def find_patterns(file_path, content, rules):
    findings = []
    for rule in rules:
        pattern = rule['pattern']
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            findings.append({...})
    return findings
```

## Code review checklist

Before submitting a PR with a new detector:

- [ ] Detector module created in `src/citadel_local/detectors/`
- [ ] Detector registered in `detectors/__init__.py`
- [ ] Rules added to `rules/*.yaml`
- [ ] Tests written in `tests/test_*.py`
- [ ] All tests pass: `pytest`
- [ ] Code formatted: `ruff format src/ tests/`
- [ ] No linting issues: `ruff check src/ tests/`
- [ ] Tested manually on real code samples
- [ ] False positive rate documented (estimated %)
- [ ] No high-entropy randomness in patterns (for secrets)
- [ ] No exploitation guidance in findings

## Submitting changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-detector
   ```

2. **Make your changes and test:**
   ```bash
   pytest -q
   ruff check src/ tests/
   ruff format src/ tests/
   ```

3. **Commit with clear message:**
   ```bash
   git add src/ rules/ tests/ docs/
   git commit -m "Add detector for [vulnerability type]

   - Detects [pattern]
   - ~X% false positive rate
   - Covers [file types]
   - Fixes #123"
   ```

4. **Push and open PR:**
   ```bash
   git push origin feature/my-detector
   ```

5. **Address review feedback:**
   - Reduce false positives if needed
   - Add more test cases
   - Improve documentation

## Need help?

- **Questions?** Open a discussion in the repository
- **Found a bug?** Report it in issues (see SECURITY.md)
- **Have ideas?** Share them in discussions
