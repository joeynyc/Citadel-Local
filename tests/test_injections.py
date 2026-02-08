from pathlib import Path
from citadel_local.detectors.injections import scan_injections

CFG = {"context_lines": 3}


def _make_file(tmp_path, name, content):
    f = tmp_path / name
    f.write_text(content)
    return f


# --- shell calls ---

def test_os_system(tmp_path):
    f = _make_file(tmp_path, "run.py", 'os.system("ls -la")\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


def test_subprocess_run(tmp_path):
    f = _make_file(tmp_path, "run.py", 'subprocess.run(["ls"], shell=True)\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


def test_subprocess_call(tmp_path):
    f = _make_file(tmp_path, "run.py", "subprocess.call(cmd)\n")
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


def test_subprocess_popen(tmp_path):
    f = _make_file(tmp_path, "run.py", "subprocess.popen(cmd)\n")
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


def test_exec(tmp_path):
    f = _make_file(tmp_path, "run.py", "exec(user_input)\n")
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


def test_eval(tmp_path):
    f = _make_file(tmp_path, "run.js", "eval(data)\n")
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.shell_call" for h in findings)


# --- SQL concatenation ---

def test_select_concat(tmp_path):
    f = _make_file(tmp_path, "db.py", 'q = "SELECT " + col + " FROM users"\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.sql_concat" for h in findings)


def test_insert_concat(tmp_path):
    f = _make_file(tmp_path, "db.py", 'q = "INSERT INTO t " + vals\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.sql_concat" for h in findings)


def test_update_concat(tmp_path):
    f = _make_file(tmp_path, "db.py", 'q = "UPDATE t SET " + vals\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.sql_concat" for h in findings)


def test_delete_concat(tmp_path):
    f = _make_file(tmp_path, "db.py", 'q = "DELETE " + condition\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert any(h["rule_id"] == "injection.sql_concat" for h in findings)


# --- extension filtering ---

def test_py_scanned(tmp_path):
    f = _make_file(tmp_path, "x.py", "os.system('cmd')\n")
    assert len(scan_injections(tmp_path, [f], CFG)) > 0


def test_js_scanned(tmp_path):
    f = _make_file(tmp_path, "x.js", "eval(data)\n")
    assert len(scan_injections(tmp_path, [f], CFG)) > 0


def test_ts_scanned(tmp_path):
    f = _make_file(tmp_path, "x.ts", "eval(data)\n")
    assert len(scan_injections(tmp_path, [f], CFG)) > 0


def test_tsx_scanned(tmp_path):
    f = _make_file(tmp_path, "x.tsx", "eval(data)\n")
    assert len(scan_injections(tmp_path, [f], CFG)) > 0


def test_sh_scanned(tmp_path):
    f = _make_file(tmp_path, "x.sh", "eval(data)\n")
    assert len(scan_injections(tmp_path, [f], CFG)) > 0


def test_txt_skipped(tmp_path):
    f = _make_file(tmp_path, "x.txt", "os.system('cmd')\n")
    assert len(scan_injections(tmp_path, [f], CFG)) == 0


def test_go_skipped(tmp_path):
    f = _make_file(tmp_path, "x.go", "exec(cmd)\n")
    assert len(scan_injections(tmp_path, [f], CFG)) == 0


# --- clean file ---

def test_clean_file(tmp_path):
    f = _make_file(tmp_path, "safe.py", 'x = 42\nprint("hello")\n')
    assert len(scan_injections(tmp_path, [f], CFG)) == 0


# --- finding structure ---

def test_finding_structure(tmp_path):
    f = _make_file(tmp_path, "r.py", 'os.system("ls")\n')
    findings = scan_injections(tmp_path, [f], CFG)
    assert len(findings) >= 1
    hit = findings[0]
    for key in ("id", "rule_id", "category", "severity", "confidence",
                "title", "description", "evidence", "recommendation", "references"):
        assert key in hit, f"missing key: {key}"
    assert hit["category"] == "injection"
    assert hit["evidence"]["start_line"] == 1
