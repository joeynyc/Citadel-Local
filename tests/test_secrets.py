from citadel_local.detectors.secrets import scan_secrets, shannon_entropy

CFG = {"context_lines": 3}


def _make_file(tmp_path, name, content):
    f = tmp_path / name
    f.write_text(content)
    return f


# --- shannon_entropy ---

def test_entropy_empty():
    assert shannon_entropy("") == 0.0


def test_entropy_low():
    assert shannon_entropy("aaaa") == 0.0


def test_entropy_high():
    assert shannon_entropy("aB3$xZ9!") > 2.5


# --- AWS access key ---

def test_aws_key_detected(tmp_path):
    f = _make_file(tmp_path, "cfg.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "secrets.aws_access_key_id"


def test_aws_key_short_no_match(tmp_path):
    f = _make_file(tmp_path, "cfg.py", 'KEY = "AKIA_SHORT"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    aws = [f for f in findings if f["rule_id"] == "secrets.aws_access_key_id"]
    assert len(aws) == 0


# --- generic API key ---

def test_generic_api_key(tmp_path):
    f = _make_file(tmp_path, "app.py", 'api_key = "abcdefghij1234567890"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.generic_api_key" for f in findings)


def test_generic_secret(tmp_path):
    f = _make_file(tmp_path, "app.py", 'secret = "xyzXYZ012345678901"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.generic_api_key" for f in findings)


def test_generic_token(tmp_path):
    f = _make_file(tmp_path, "app.py", 'token = "abcdefghijklmnop1234"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.generic_api_key" for f in findings)


def test_short_value_no_match(tmp_path):
    f = _make_file(tmp_path, "app.py", 'api_key = "short"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    generic = [f for f in findings if f["rule_id"] == "secrets.generic_api_key"]
    assert len(generic) == 0


# --- private key block ---

def test_rsa_private_key(tmp_path):
    f = _make_file(tmp_path, "key.pem", "-----BEGIN RSA PRIVATE KEY-----\ndata\n-----END RSA PRIVATE KEY-----\n")
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.private_key_block" for f in findings)


def test_ec_private_key(tmp_path):
    f = _make_file(tmp_path, "key.pem", "-----BEGIN EC PRIVATE KEY-----\n")
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.private_key_block" for f in findings)


def test_openssh_private_key(tmp_path):
    f = _make_file(tmp_path, "id_ed25519", "-----BEGIN OPENSSH PRIVATE KEY-----\n")
    findings = scan_secrets(tmp_path, [f], CFG)
    assert any(f["rule_id"] == "secrets.private_key_block" for f in findings)


# --- clean file ---

def test_clean_file(tmp_path):
    f = _make_file(tmp_path, "clean.py", 'x = 42\nprint("hello")\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert len(findings) == 0


# --- finding structure ---

def test_finding_structure(tmp_path):
    f = _make_file(tmp_path, "s.py", 'api_key = "abcdefghij1234567890"\n')
    findings = scan_secrets(tmp_path, [f], CFG)
    assert len(findings) >= 1
    hit = findings[0]
    for key in ("id", "rule_id", "category", "severity", "confidence",
                "title", "description", "evidence", "recommendation", "references"):
        assert key in hit, f"missing key: {key}"
    ev = hit["evidence"]
    for key in ("path", "start_line", "end_line", "snippet", "context"):
        assert key in ev, f"missing evidence key: {key}"
    assert hit["category"] == "secrets"
    assert isinstance(hit["confidence"], float)
    assert isinstance(hit["evidence"]["start_line"], int)
