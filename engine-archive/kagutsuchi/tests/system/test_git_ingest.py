import subprocess

import pytest

from system.analysis import GitIngestError, diff_pair, scan_diff


def _run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def sample_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run("git", "init", "-q", cwd=repo)
    _run("git", "config", "user.email", "test@example.com", cwd=repo)
    _run("git", "config", "user.name", "Test", cwd=repo)

    target = repo / "app.py"
    target.write_text(
        "def run_lookup(hostname):\n"
        "    return 'unchanged'\n"
    )
    _run("git", "add", "app.py", cwd=repo)
    _run("git", "commit", "-q", "-m", "initial", cwd=repo)

    target.write_text(
        "def run_lookup(hostname):\n"
        "    import os\n"
        "    os.system('ping -c 1 ' + hostname)\n"
    )
    _run("git", "add", "app.py", cwd=repo)
    _run("git", "commit", "-q", "-m", "introduce vuln", cwd=repo)

    return repo


def test_diff_pair_reads_both_revisions(sample_repo):
    old, new = diff_pair(str(sample_repo), "app.py")
    assert "unchanged" in old
    assert "os.system" in new


def test_ingested_diff_flags_the_new_vulnerability(sample_repo):
    old, new = diff_pair(str(sample_repo), "app.py")
    findings = scan_diff(old, new, "app.py")
    assert len(findings) == 1
    assert findings[0].symbol == "run_lookup"
    assert findings[0].severity_hint == "high"


def test_missing_file_at_base_raises_clean_error(sample_repo):
    with pytest.raises(GitIngestError):
        from system.analysis import read_file_at_revision

        read_file_at_revision(str(sample_repo), "HEAD", "does_not_exist.py")
