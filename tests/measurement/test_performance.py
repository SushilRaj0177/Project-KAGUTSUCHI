from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.performance import compute_performance_findings


def _snapshot(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_string_concat_in_for_loop_is_flagged():
    content = (
        "def build(items):\n"
        "    out = ''\n"
        "    for item in items:\n"
        "        out = out + str(item)\n"
        "    return out\n"
    )
    findings = compute_performance_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "time_behaviour"
    assert findings[0].characteristic.value == "performance_efficiency"
    assert findings[0].evidence[0].location.start_line == 4
    assert findings[0].evidence[0].analyzer.rule_id == "quadratic_string_concat_in_loop"


def test_aug_assign_string_concat_in_while_loop_is_flagged():
    content = (
        "def build(n):\n"
        "    out = ''\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        out += f'{i},'\n"
        "        i += 1\n"
        "    return out\n"
    )
    findings = compute_performance_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert findings[0].evidence[0].location.start_line == 5


def test_numeric_accumulation_in_loop_is_not_flagged():
    content = (
        "def total(prices):\n"
        "    total = 0\n"
        "    for price in prices:\n"
        "        total += price\n"
        "    return total\n"
    )
    assert compute_performance_findings(_snapshot("app.py", content)) == []


def test_string_concat_outside_a_loop_is_not_flagged():
    content = "def greet(name):\n    return 'hello ' + name\n"
    assert compute_performance_findings(_snapshot("app.py", content)) == []


def test_multiple_sites_in_the_same_file_are_counted_but_one_finding():
    content = (
        "def build(a, b):\n"
        "    out = ''\n"
        "    for x in a:\n"
        "        out += str(x)\n"
        "    for y in b:\n"
        "        out += str(y)\n"
        "    return out\n"
    )
    findings = compute_performance_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert "2 loop iteration" in findings[0].description
    assert findings[0].evidence[0].location.start_line == 4  # the first site


def test_nested_loop_site_is_counted_once():
    content = (
        "def build(matrix):\n"
        "    out = ''\n"
        "    for row in matrix:\n"
        "        for cell in row:\n"
        "            out += str(cell)\n"
        "    return out\n"
    )
    findings = compute_performance_findings(_snapshot("app.py", content))
    assert len(findings) == 1
    assert "1 loop iteration" in findings[0].description


def test_malformed_python_is_skipped_not_crashed():
    assert compute_performance_findings(_snapshot("app.py", "def f(:\n")) == []


def test_non_python_files_are_ignored():
    f = FileRecord(path="notes.md", language="Markdown", size_bytes=10, line_count=1, content="out += x")
    snapshot = RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])
    assert compute_performance_findings(snapshot) == []
