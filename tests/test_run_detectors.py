from pathlib import Path
from citadel_local.detectors import run_detectors

CFG = {"context_lines": 3}


def test_combines_all_detectors(tmp_path):
    """A .py file with a secret, an injection, and a crypto issue produces findings from all three."""
    f = tmp_path / "bad.py"
    f.write_text(
        'api_key = "abcdefghij1234567890"\n'
        'os.system(cmd)\n'
        'hashlib.md5(data)\n'
    )
    findings = run_detectors(tmp_path, [f], CFG)
    categories = {f["category"] for f in findings}
    assert "secrets" in categories
    assert "injection" in categories
    assert "crypto" in categories


def test_empty_file_list(tmp_path):
    findings = run_detectors(tmp_path, [], CFG)
    assert findings == []


def test_clean_files_no_findings(tmp_path):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\ny = 2\n")
    findings = run_detectors(tmp_path, [f], CFG)
    assert findings == []
