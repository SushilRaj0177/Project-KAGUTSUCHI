import pytest

import wsqfai.integration.github_pr as github_pr
from wsqfai.integration.github_pr import GitHubPrError, open_fix_pr
from wsqfai.remediation import Fix


def _fix(file_path: str, content: str) -> Fix:
    return Fix(finding_id="f1", file_path=file_path, diff="diff", summary=f"fixed {file_path}", patched_content=content)


class _FakeGitHub:
    """Records every call open_fix_pr makes through _request, and returns
    a plausible response for each real GitHub endpoint it hits - the
    network boundary is mocked, none of open_fix_pr's own logic is."""

    def __init__(self):
        self.calls: list[tuple[str, str, dict | None, dict | None]] = []

    def __call__(self, method, url, token, *, json_body=None, params=None):
        self.calls.append((method, url, json_body, params))
        if url.endswith("/repos/acme/widgets"):
            return {"default_branch": "main"}
        if "/git/ref/heads/main" in url:
            return {"object": {"sha": "base-sha-123"}}
        if "/git/refs" in url and method == "POST":
            return {"ref": f"refs/heads/{json_body['ref']}"}
        if "/contents/" in url and method == "GET":
            return {"sha": "existing-file-sha"}
        if "/contents/" in url and method == "PUT":
            return {"content": {"sha": "new-sha"}}
        if url.endswith("/pulls") and method == "POST":
            return {"html_url": "https://github.com/acme/widgets/pull/42"}
        raise AssertionError(f"unexpected call: {method} {url}")


def test_opens_a_pr_with_a_single_fix(monkeypatch):
    fake = _FakeGitHub()
    monkeypatch.setattr(github_pr, "_request", fake)

    result = open_fix_pr(token="tok", owner="acme", repo="widgets", fixes=[_fix("app.py", "fixed content\n")])

    assert result.pr_url == "https://github.com/acme/widgets/pull/42"
    assert result.branch.startswith("wsqfai-fix/")


def test_commits_every_fix_before_opening_the_pr(monkeypatch):
    fake = _FakeGitHub()
    monkeypatch.setattr(github_pr, "_request", fake)

    open_fix_pr(token="tok", owner="acme", repo="widgets", fixes=[_fix("app.py", "x"), _fix("requirements.txt", "y")])

    put_calls = [c for c in fake.calls if c[0] == "PUT"]
    assert len(put_calls) == 2
    assert {c[1].rsplit("/", 1)[-1] for c in put_calls} == {"app.py", "requirements.txt"}


def test_pr_body_lists_every_fix_summary(monkeypatch):
    fake = _FakeGitHub()
    monkeypatch.setattr(github_pr, "_request", fake)

    open_fix_pr(token="tok", owner="acme", repo="widgets", fixes=[_fix("app.py", "x")])

    pr_call = next(c for c in fake.calls if c[0] == "POST" and c[1].endswith("/pulls"))
    assert "fixed app.py" in pr_call[2]["body"]


def test_uses_explicit_base_branch_when_given(monkeypatch):
    calls = []

    def fake_request(method, url, token, *, json_body=None, params=None):
        calls.append((method, url, params))
        if url.endswith("/repos/x/y"):
            return {"default_branch": "main"}  # would be wrong to use - base_branch overrides it
        if "/git/ref/heads/develop" in url:
            return {"object": {"sha": "sha"}}
        if "/git/refs" in url:
            return {}
        if "/contents/" in url and method == "GET":
            return {"sha": "s"}
        if "/contents/" in url and method == "PUT":
            return {}
        if url.endswith("/pulls"):
            return {"html_url": "https://github.com/x/y/pull/1"}
        raise AssertionError(url)

    import wsqfai.integration.github_pr as mod
    monkeypatch.setattr(mod, "_request", fake_request)

    open_fix_pr(token="tok", owner="x", repo="y", fixes=[_fix("a.py", "z")], base_branch="develop")
    # the base ref lookup must target "develop", never the repo's actual default branch ("main")
    assert any("/git/ref/heads/develop" in url for _, url, _ in calls)
    assert not any("/git/ref/heads/main" in url for _, url, _ in calls)


def test_raises_without_a_token():
    with pytest.raises(GitHubPrError):
        open_fix_pr(token="", owner="acme", repo="widgets", fixes=[_fix("app.py", "x")])


def test_raises_with_no_fixes():
    with pytest.raises(ValueError):
        open_fix_pr(token="tok", owner="acme", repo="widgets", fixes=[])


def test_request_translates_401_to_a_clear_error(monkeypatch):
    import io
    import urllib.error

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(github_pr.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(GitHubPrError, match="invalid or expired"):
        github_pr._request("GET", "https://api.github.com/repos/x/y", "bad-token")


def test_request_never_leaks_the_token_in_an_error_message(monkeypatch):
    import io
    import urllib.error

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 422, "nope", {}, io.BytesIO(b"secret-token-abc123 was rejected"))

    monkeypatch.setattr(github_pr.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(GitHubPrError) as exc_info:
        github_pr._request("GET", "https://api.github.com/x", "secret-token-abc123")
    assert "secret-token-abc123" not in str(exc_info.value)
