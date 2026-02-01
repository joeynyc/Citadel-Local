# CI/CD Integration Guide

Run Citadel Local in your CI/CD pipeline for automated security scanning.

## Overview

**Goals:**
- Scan on every PR/commit
- Fail builds on critical findings
- Track remediation over time
- Integrate with existing security tools

**Key considerations:**
- Ollama should run on a dedicated machine (scanning + LLM)
- Use baseline to track known issues
- Fail fast on critical findings, warn on medium/low
- Cache Ollama models to speed up scans

## GitHub Actions

### Basic setup (detectors only, no LLM)

```yaml
# .github/workflows/security-scan.yml
name: Citadel Security Scan

on:
  pull_request:
    paths:
      - 'src/**'
      - '.citadel-local.yaml'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Citadel
        run: pip install citadel-local

      - name: Scan repository
        run: |
          citadel scan . --out scan-results/

      - name: Upload findings
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: citadel-findings
          path: scan-results/

      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const findings = JSON.parse(fs.readFileSync('scan-results/findings.json'));
            const critical = findings.filter(f => f.severity === 'critical');

            if (critical.length > 0) {
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: `⚠️ **Critical findings found**: ${critical.length}\n\nSee artifacts for details.`
              });
            }
```

### With Ollama (self-hosted runner)

If you have a self-hosted runner with Ollama:

```yaml
# .github/workflows/security-scan-with-llm.yml
name: Citadel Security Scan (with LLM)

on:
  pull_request:
    paths:
      - 'src/**'
      - 'config/**'

jobs:
  scan:
    runs-on: [self-hosted, linux, ollama]  # custom runner with Ollama
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache Ollama models
        uses: actions/cache@v3
        with:
          path: ~/.ollama/models
          key: ollama-models-${{ runner.os }}

      - name: Install Citadel
        run: pip install citadel-local

      - name: Check Ollama
        run: |
          curl -s http://127.0.0.1:11434/api/tags | jq .

      - name: Scan with LLM council
        run: |
          citadel scan . --out scan-results/ --config .citadel-local.yaml

      - name: Parse findings
        if: always()
        run: |
          python scripts/parse_findings.py scan-results/findings.json

      - name: Check for critical findings
        run: |
          python scripts/check_severity.py scan-results/findings.json critical
```

### Scan only changed files (faster)

```yaml
# .github/workflows/security-diff.yml
name: Security Scan (diff)

on:
  pull_request:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Citadel
        run: pip install citadel-local

      - name: Scan changed files
        run: |
          citadel diff . --out scan-results/

      - name: Upload findings
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: citadel-findings
          path: scan-results/

      - name: Fail on critical
        run: |
          python -c "
          import json
          with open('scan-results/findings.json') as f:
            findings = json.load(f)
          critical = [f for f in findings if f.get('severity') == 'critical']
          if critical:
            print(f'Found {len(critical)} critical findings')
            exit(1)
          "
```

### With baseline tracking

```yaml
# .github/workflows/security-scan-with-baseline.yml
name: Citadel Scan (with baseline)

on:
  pull_request:
    paths:
      - 'src/**'
  push:
    branches:
      - main
    paths:
      - 'src/**'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Citadel
        run: pip install citadel-local

      - name: Load baseline
        run: |
          if [ -f .citadel-baseline.json ]; then
            echo "Using baseline: .citadel-baseline.json"
          fi

      - name: Scan
        run: citadel scan . --out scan-results/

      - name: Compare to baseline
        run: |
          python scripts/compare_baselines.py \
            .citadel-baseline.json \
            scan-results/findings.json

      - name: Update baseline (main only)
        if: github.ref == 'refs/heads/main'
        run: |
          citadel baseline .
          git config user.email "security@company.com"
          git config user.name "Citadel Bot"
          git add .citadel-baseline.json
          git commit -m "Update security baseline" || true
          git push
```

## GitLab CI

### Basic setup

```yaml
# .gitlab-ci.yml
security:scan:
  stage: scan
  image: python:3.11
  script:
    - pip install citadel-local
    - citadel scan . --out scan-results/
  artifacts:
    paths:
      - scan-results/
    reports:
      sast: scan-results/findings.json
    expire_in: 30 days
  allow_failure: true
  only:
    - merge_requests
    - main
```

### With Ollama service

```yaml
security:scan:full:
  stage: scan
  image: python:3.11
  services:
    - name: ollama/ollama:latest
      alias: ollama
  variables:
    CITADEL_OLLAMA_BASE_URL: "http://ollama:11434"
  before_script:
    - pip install citadel-local
    - apt-get update && apt-get install -y curl
    - |
      # Wait for Ollama to be ready
      for i in {1..30}; do
        if curl -s http://ollama:11434/api/tags > /dev/null; then
          echo "Ollama is ready"
          break
        fi
        echo "Waiting for Ollama... ($i/30)"
        sleep 2
      done
  script:
    - citadel scan . --out scan-results/ --verbose
  artifacts:
    paths:
      - scan-results/
    expire_in: 30 days
  allow_failure: true
```

### Diff scanning (faster)

```yaml
security:scan:diff:
  stage: scan
  image: python:3.11
  script:
    - pip install citadel-local
    - citadel diff . --out scan-results/
  artifacts:
    paths:
      - scan-results/
    expire_in: 7 days
  only:
    - merge_requests
```

## Jenkins

### Declarative pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install citadel-local
                '''
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    . .venv/bin/activate
                    citadel scan . --out scan-results/
                '''
            }
        }

        stage('Parse Results') {
            steps {
                script {
                    def findings = readJSON file: 'scan-results/findings.json'
                    def critical = findings.findAll { it.severity == 'critical' }

                    echo "Total findings: ${findings.size()}"
                    echo "Critical findings: ${critical.size()}"

                    if (critical.size() > 0) {
                        unstable("Found ${critical.size()} critical findings")
                    }
                }
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'scan-results/**', allowEmptyArchive: true
                publishHTML([
                    reportDir: 'scan-results',
                    reportFiles: 'report.md',
                    reportName: 'Security Report'
                ])
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

### Scripted pipeline with Ollama

```groovy
// Jenkinsfile
def scan(path) {
    withEnv(["CITADEL_OLLAMA_BASE_URL=http://localhost:11434"]) {
        sh '''
            . .venv/bin/activate
            citadel scan ${path} --out scan-results/ --verbose
        '''
    }
}

def parseFindings() {
    def findings = readJSON file: 'scan-results/findings.json'
    return findings
}

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install citadel-local
                '''
            }
        }

        stage('Scan') {
            steps {
                script {
                    scan('.')
                }
            }
        }

        stage('Results') {
            steps {
                script {
                    def findings = parseFindings()
                    def critical = findings.findAll { it.severity == 'critical' }
                    def high = findings.findAll { it.severity == 'high' }

                    echo "Findings Summary:"
                    echo "  Critical: ${critical.size()}"
                    echo "  High: ${high.size()}"
                    echo "  Total: ${findings.size()}"

                    if (critical.size() > 0) {
                        currentBuild.result = 'FAILURE'
                        error("Found ${critical.size()} critical security findings")
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'scan-results/**', allowEmptyArchive: true
        }
    }
}
```

## General best practices

### 1) Baseline known findings

```bash
# Create baseline on main branch
citadel baseline .
git add .citadel-baseline.json
git commit -m "Add security baseline"

# PR scans will show only NEW findings
citadel scan . --baseline .citadel-baseline.json
```

### 2) Fail on critical, warn on lower severities

```python
# scripts/check_findings.py
import json
import sys

with open('scan-results/findings.json') as f:
    findings = json.load(f)

critical = [f for f in findings if f['severity'] == 'critical']
high = [f for f in findings if f['severity'] == 'high']

print(f"Critical: {len(critical)}")
print(f"High: {len(high)}")

if critical:
    print("❌ Critical findings detected")
    sys.exit(1)

if high:
    print("⚠️ High-severity findings detected")
    # Warn but don't fail
```

### 3) Comment on PRs with findings

```python
# scripts/github_comment.py
import json
import os
from github import Github

with open('scan-results/findings.json') as f:
    findings = json.load(f)

critical = [f for f in findings if f['severity'] == 'critical']
high = [f for f in findings if f['severity'] == 'high']

if not critical and not high:
    print("✅ No critical/high findings")
    exit(0)

body = f"""
## Security Scan Results

🔍 **Findings detected in this PR:**

- **Critical:** {len(critical)}
- **High:** {len(high)}

**Top findings:**
"""

for finding in (critical + high)[:5]:
    body += f"\n- [{finding['id']}] {finding['file']}:{finding['line_start']}"

g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr = repo.get_pull(int(os.getenv('GITHUB_PR_NUMBER')))
pr.create_issue_comment(body)
```

### 4) Cache Ollama models

In GitHub Actions:
```yaml
- name: Cache Ollama
  uses: actions/cache@v3
  with:
    path: ~/.ollama/models
    key: ollama-models-${{ runner.os }}-${{ hashFiles('.citadel-local.yaml') }}
```

In GitLab CI:
```yaml
cache:
  paths:
    - .ollama/models/
  key: ollama-models
```

In Jenkins:
```groovy
stage('Cache Models') {
    steps {
        script {
            sh 'mkdir -p ~/.ollama/models'
        }
    }
}
```

### 5) Incremental baseline updates

Track remediation over time:

```bash
# On main: update baseline
if [[ "$BRANCH" == "main" ]]; then
    citadel baseline .
    git add .citadel-baseline.json
    git commit -m "Update security baseline" || true
fi

# On PRs: compare to baseline
citadel scan . --baseline .citadel-baseline.json
```

## Performance tips

### 1) Scan only changed files

```bash
# Much faster for large repos
citadel diff . --out scan-results/
```

### 2) Use smaller models in CI

```yaml
# .citadel-local.yaml
ollama:
  triage_model: "phi3:3.8b"      # small, fast
  deep_model: "qwen2:7b"         # smaller, reasonable
  skeptic_model: "neural-chat:7b"  # small
  timeout_s: 60
```

### 3) Run Ollama on separate machine

**Main CI runner:** runs Citadel scanner only
**Separate machine:** runs Ollama, accessed via HTTP

```yaml
# GitHub Actions example
env:
  CITADEL_OLLAMA_BASE_URL: "http://ollama-server.internal:11434"
```

### 4) Parallel scanning

For monorepos, scan each service independently:

```bash
# Scan multiple paths in parallel
citadel scan ./service-a --out scan-results/a/ &
citadel scan ./service-b --out scan-results/b/ &
citadel scan ./service-c --out scan-results/c/ &
wait
```

## Monitoring & alerting

### Export to SIEM

```bash
# Convert to SARIF for integration with code scanning tools
citadel scan . --format sarif --out results.sarif

# Upload to GitHub
gh code-scanning upload results.sarif
```

### Slack notifications

```python
# scripts/notify_slack.py
import json
import os
import requests

with open('scan-results/findings.json') as f:
    findings = json.load(f)

critical = [f for f in findings if f['severity'] == 'critical']

if critical:
    msg = f":warning: {len(critical)} critical findings in {os.getenv('REPO_NAME')}"
    requests.post(os.getenv('SLACK_WEBHOOK'), json={'text': msg})
```

### Metrics dashboard

Track findings over time:

```json
// scan-results/metrics.json
{
  "date": "2026-02-01",
  "total": 15,
  "critical": 2,
  "high": 4,
  "medium": 9,
  "low": 0,
  "scan_time_s": 45,
  "repo": "my-repo"
}
```

Append to time-series DB (InfluxDB, Prometheus, etc.) for trending.

## Troubleshooting CI/CD runs

### Ollama timeout in CI

**Solution:** Use smaller models, increase timeout
```yaml
ollama:
  deep_model: "qwen2:7b"  # smaller
  timeout_s: 120          # longer timeout
```

### "Out of memory" in CI

**Solution:** Use container limits or self-hosted runner with more RAM
```yaml
# GitHub Actions
runs-on: ubuntu-latest  # has ~7GB available
# For larger scans, use self-hosted with more RAM
```

### Models not found in CI

**Solution:** Pull models in setup step
```bash
- name: Setup Ollama
  run: |
    ollama pull llama3.2:3b
    ollama pull qwen2:7b
```

### Slow scans in CI

**Solution:** Use `citadel diff` instead of full scan
```bash
citadel diff . --out scan-results/
# Only scans changed files, much faster
```
