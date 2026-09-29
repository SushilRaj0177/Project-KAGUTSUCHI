from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.portability import compute_portability_findings


def _language_for(path: str) -> str | None:
    if path.endswith(".toml"):
        return "TOML"
    if path.endswith(".json"):
        return "JSON"
    return None


def _file(path: str, content: str) -> RepositorySnapshot:
    f = FileRecord(path=path, language=_language_for(path), size_bytes=len(content), line_count=content.count("\n"), content=content)
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=[f])


def test_requirements_txt_with_unpinned_dependency_is_flagged():
    content = "requests\nflask==2.3.0\n"
    findings = compute_portability_findings(_file("requirements.txt", content))
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "installability"
    assert "requests" in findings[0].evidence[0].snippet
    assert "flask" not in findings[0].evidence[0].snippet


def test_requirements_txt_with_multiple_unpinned_dependencies_gets_one_finding_each():
    content = "requests\nflask==2.3.0\nnumpy\n"
    findings = compute_portability_findings(_file("requirements.txt", content))
    assert len(findings) == 2
    by_line = {f.evidence[0].location.start_line: f.evidence[0].snippet for f in findings}
    assert by_line == {1: "requests", 3: "numpy"}


def test_fully_pinned_requirements_txt_has_no_finding():
    content = "requests==2.31.0\nflask~=2.3\n"
    assert compute_portability_findings(_file("requirements.txt", content)) == []


def test_requirements_txt_skips_comments_blank_lines_and_options():
    content = "# a comment\n\n-r base.txt\nrequests==2.31.0\n"
    assert compute_portability_findings(_file("requirements.txt", content)) == []


def test_pyproject_toml_with_unpinned_dependency_is_flagged():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests", "flask==2.3.0"]\n'
    )
    findings = compute_portability_findings(_file("pyproject.toml", content))
    assert len(findings) == 1
    assert "requests" in findings[0].evidence[0].snippet


def test_pyproject_toml_fully_pinned_has_no_finding():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests==2.31.0", "flask~=2.3"]\n'
    )
    assert compute_portability_findings(_file("pyproject.toml", content)) == []


def test_pyproject_toml_dependency_with_environment_marker_is_checked_correctly():
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["requests==2.31.0 ; python_version >= \\"3.11\\""]\n'
    )
    assert compute_portability_findings(_file("pyproject.toml", content)) == []


def test_malformed_pyproject_toml_is_skipped_not_crashed():
    assert compute_portability_findings(_file("pyproject.toml", "not valid [[[ toml")) == []


def test_pyproject_toml_multiline_array_gets_one_finding_per_line():
    content = (
        "[project]\n"
        'name = "proj"\n'
        "dependencies = [\n"
        '    "requests",\n'
        '    "flask==2.3.0",\n'
        '    "numpy",\n'
        "]\n"
    )
    findings = compute_portability_findings(_file("pyproject.toml", content))
    assert len(findings) == 2
    by_line = {f.evidence[0].location.start_line: f.evidence[0].snippet for f in findings}
    assert by_line == {4: "requests", 6: "numpy"}
    assert all(f.evidence[0].analyzer.rule_id == "unpinned_dependency_pyproject" for f in findings)


def test_pyproject_toml_duplicate_declaration_gets_distinct_lines():
    content = (
        "[project]\n"
        'name = "proj"\n'
        "dependencies = [\n"
        '    "requests",\n'
        '    "requests",\n'
        "]\n"
    )
    findings = compute_portability_findings(_file("pyproject.toml", content))
    assert sorted(f.evidence[0].location.start_line for f in findings) == [4, 5]


def test_pyproject_toml_escaped_content_falls_back_to_aggregated_finding():
    # tomllib decodes the ! escape to "!"; the raw-text scan captures the
    # literal source text instead, so the two disagree on this entry's exact
    # string - the scan can't safely place a line for it, so it must fall back
    # to one aggregated Finding rather than guessing wrong.
    content = (
        "[project]\n"
        'name = "proj"\n'
        'dependencies = ["numpy\\u0021"]\n'
    )
    findings = compute_portability_findings(_file("pyproject.toml", content))
    assert len(findings) == 1
    assert findings[0].evidence[0].analyzer.rule_id == "unpinned_dependency_pyproject"
    assert findings[0].evidence[0].location.start_line is None


def test_package_json_with_fully_unconstrained_dependency_is_flagged():
    content = '{"dependencies": {"lodash": "*", "left-pad": "1.3.0"}}'
    findings = compute_portability_findings(_file("package.json", content))
    assert len(findings) == 1
    assert "lodash" in findings[0].evidence[0].snippet
    assert "left-pad" not in findings[0].evidence[0].snippet


def test_package_json_caret_and_tilde_ranges_are_not_flagged():
    # npm's own convention (npm install writes a caret range by default) -
    # unlike Python's bare-version-means-unconstrained convention, these
    # already constrain to at least a major/minor version.
    content = '{"dependencies": {"react": "^18.2.0", "next": "~14.1.0"}}'
    assert compute_portability_findings(_file("package.json", content)) == []


def test_package_json_workspace_and_git_specifiers_are_not_flagged():
    content = (
        '{"dependencies": {'
        '"shared-utils": "workspace:*", '
        '"patched-lib": "git+https://github.com/example/patched-lib.git", '
        '"local-dep": "file:../local-dep"'
        "}}"
    )
    assert compute_portability_findings(_file("package.json", content)) == []


def test_package_json_flags_dev_dependencies_too():
    content = '{"devDependencies": {"eslint": "latest"}}'
    findings = compute_portability_findings(_file("package.json", content))
    assert len(findings) == 1
    assert findings[0].evidence[0].analyzer.rule_id == "unpinned_dependency_package_json"


def test_package_json_reports_a_real_line_number():
    content = (
        "{\n"
        '  "dependencies": {\n'
        '    "left-pad": "1.3.0",\n'
        '    "lodash": "*"\n'
        "  }\n"
        "}\n"
    )
    findings = compute_portability_findings(_file("package.json", content))
    assert len(findings) == 1
    assert findings[0].evidence[0].location.start_line == 4


def test_malformed_package_json_is_skipped_not_crashed():
    assert compute_portability_findings(_file("package.json", "not valid { json")) == []


def test_package_json_with_no_dependencies_key_has_no_finding():
    assert compute_portability_findings(_file("package.json", '{"name": "proj"}')) == []


def test_unrelated_files_are_ignored():
    assert compute_portability_findings(_file("README.md", "requests\n")) == []


def test_every_finding_cites_portability_and_a_real_sub_characteristic():
    from wsqfai.domain.quality_model import QualityCharacteristic, sub_characteristic

    findings = compute_portability_findings(_file("requirements.txt", "requests\n"))
    assert findings
    for finding in findings:
        assert finding.characteristic == QualityCharacteristic.PORTABILITY
        sc = sub_characteristic(finding.sub_characteristic_key)
        assert sc.characteristic == QualityCharacteristic.PORTABILITY
