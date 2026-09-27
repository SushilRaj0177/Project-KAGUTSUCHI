import time

import pytest
from fastapi.testclient import TestClient

import wsqfai.server.main as server_main
import wsqfai.server.rate_limit as rate_limit_module
from wsqfai.integration.github_pr import GitHubPrError, OpenedPr
from wsqfai.report import RepositoryReport


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    # The rate limiter's hit-tracking dict is process-global (see
    # wsqfai/server/rate_limit.py's own docstring on why - a single
    # always-on process, not distributed serverless) - which means it
    # persists across tests in the same run unless explicitly cleared.
    rate_limit_module._hits.clear()
    yield
    rate_limit_module._hits.clear()


@pytest.fixture
def client():
    return TestClient(server_main.app)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_repo_start_rejects_a_non_github_url(client):
    response = client.post("/api/analyze-repo/start", json={"repo_url": "https://gitlab.com/x/y"})
    assert response.status_code == 400


def test_analyze_repo_start_returns_a_job_id_and_the_job_can_be_polled(client, monkeypatch):
    fake_report = RepositoryReport(
        owner="me", repo="proj", ref=None, total_files=1, total_lines=1, truncated=False,
        language_summary={}, is_ml_repository=False, findings=[], security_hypotheses=[], fixes=[], suggestions=[],
    )
    monkeypatch.setattr(server_main, "_run_analysis", lambda repo_url, ref: fake_report)

    start = client.post("/api/analyze-repo/start", json={"repo_url": "https://github.com/me/proj"})
    assert start.status_code == 200
    job_id = start.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/analyze-repo/jobs/{job_id}")
        if status.json()["status"] != "running":
            break
        time.sleep(0.02)

    body = status.json()
    assert body["status"] == "done"
    assert body["result"]["owner"] == "me"


def test_analyze_repo_job_status_404s_for_an_unknown_job(client):
    response = client.get("/api/analyze-repo/jobs/does-not-exist")
    assert response.status_code == 404


def test_analyze_repo_job_surfaces_a_clone_failure_as_a_job_error(client, monkeypatch):
    def _raise(repo_url, ref):
        raise RuntimeError("git clone failed (repo/branch may be private, deleted, or wrong): fatal error")

    monkeypatch.setattr(server_main, "_run_analysis", _raise)

    start = client.post("/api/analyze-repo/start", json={"repo_url": "https://github.com/me/proj"})
    job_id = start.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/analyze-repo/jobs/{job_id}")
        if status.json()["status"] != "running":
            break
        time.sleep(0.02)

    body = status.json()
    assert body["status"] == "error"
    assert "git clone failed" in body["error"]


def test_open_pr_rejects_an_empty_fix_list(client):
    response = client.post("/api/open-pr", json={"repo_url": "https://github.com/me/proj", "fixes": [], "github_token": "tok"})
    assert response.status_code == 400


def test_open_pr_rejects_a_non_github_url(client):
    fix = {"finding_id": "f1", "file_path": "app.py", "diff": "d", "summary": "s", "patched_content": "x"}
    response = client.post("/api/open-pr", json={"repo_url": "https://gitlab.com/x/y", "fixes": [fix], "github_token": "tok"})
    assert response.status_code == 400


def test_open_pr_returns_the_pr_url_on_success(client, monkeypatch):
    monkeypatch.setattr(server_main, "open_fix_pr", lambda **kwargs: OpenedPr(pr_url="https://github.com/me/proj/pull/1", branch="wsqfai-fix/abc"))

    fix = {"finding_id": "f1", "file_path": "app.py", "diff": "d", "summary": "s", "patched_content": "x"}
    response = client.post("/api/open-pr", json={"repo_url": "https://github.com/me/proj", "fixes": [fix], "github_token": "tok"})
    assert response.status_code == 200
    assert response.json()["pr_url"] == "https://github.com/me/proj/pull/1"


def test_open_pr_surfaces_a_github_error_as_502(client, monkeypatch):
    def _raise(**kwargs):
        raise GitHubPrError("GitHub rejected the token — it's invalid or expired.")

    monkeypatch.setattr(server_main, "open_fix_pr", _raise)

    fix = {"finding_id": "f1", "file_path": "app.py", "diff": "d", "summary": "s", "patched_content": "x"}
    response = client.post("/api/open-pr", json={"repo_url": "https://github.com/me/proj", "fixes": [fix], "github_token": "bad"})
    assert response.status_code == 502
    assert "invalid or expired" in response.json()["detail"]


def test_rate_limit_kicks_in_after_repeated_requests(client):
    for _ in range(5):
        client.post("/api/analyze-repo/start", json={"repo_url": "https://gitlab.com/x/y"})  # fast 400s still count
    response = client.post("/api/analyze-repo/start", json={"repo_url": "https://gitlab.com/x/y"})
    assert response.status_code == 429
