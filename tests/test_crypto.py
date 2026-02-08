from pathlib import Path
from citadel_local.detectors.crypto import scan_crypto

CFG = {"context_lines": 3}


def _make_file(tmp_path, name, content):
    f = tmp_path / name
    f.write_text(content)
    return f


# --- weak hash ---

def test_md5(tmp_path):
    f = _make_file(tmp_path, "h.py", "hashlib.md5(data)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.weak_hash" for h in findings)


def test_sha1(tmp_path):
    f = _make_file(tmp_path, "h.py", "hashlib.sha1(data)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.weak_hash" for h in findings)


def test_md5_case_insensitive(tmp_path):
    f = _make_file(tmp_path, "h.py", "MD5(data)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.weak_hash" for h in findings)


def test_sha256_no_match(tmp_path):
    f = _make_file(tmp_path, "h.py", "hashlib.sha256(data)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    weak = [f for f in findings if f["rule_id"] == "crypto.weak_hash"]
    assert len(weak) == 0


# --- insecure random ---

def test_math_random(tmp_path):
    f = _make_file(tmp_path, "r.js", "let x = Math.random();\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.insecure_random" for h in findings)


def test_python_random(tmp_path):
    f = _make_file(tmp_path, "r.py", "x = random.random()\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.insecure_random" for h in findings)


def test_rand_call(tmp_path):
    f = _make_file(tmp_path, "r.go", "x := rand()\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "crypto.insecure_random" for h in findings)


def test_secrets_token_no_match(tmp_path):
    f = _make_file(tmp_path, "s.py", "secrets.token_hex(32)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert len(findings) == 0


# --- extension filtering ---

def test_py_scanned(tmp_path):
    f = _make_file(tmp_path, "x.py", "md5(data)\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) > 0


def test_js_scanned(tmp_path):
    f = _make_file(tmp_path, "x.js", "Math.random()\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) > 0


def test_go_scanned(tmp_path):
    f = _make_file(tmp_path, "x.go", "md5(data)\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) > 0


def test_java_scanned(tmp_path):
    f = _make_file(tmp_path, "x.java", "md5(data)\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) > 0


def test_sh_skipped(tmp_path):
    f = _make_file(tmp_path, "x.sh", "md5sum file\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) == 0


def test_txt_skipped(tmp_path):
    f = _make_file(tmp_path, "x.txt", "md5(data)\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) == 0


# --- clean file ---

def test_clean_file(tmp_path):
    f = _make_file(tmp_path, "safe.py", "x = 42\nprint('hello')\n")
    assert len(scan_crypto(tmp_path, [f], CFG)) == 0


# --- finding structure ---

def test_finding_structure(tmp_path):
    f = _make_file(tmp_path, "h.py", "hashlib.md5(data)\n")
    findings = scan_crypto(tmp_path, [f], CFG)
    assert len(findings) >= 1
    hit = findings[0]
    for key in ("id", "rule_id", "category", "severity", "confidence",
                "title", "description", "evidence", "recommendation", "references"):
        assert key in hit, f"missing key: {key}"
    assert hit["category"] == "crypto"
    assert hit["severity"] == "medium"
