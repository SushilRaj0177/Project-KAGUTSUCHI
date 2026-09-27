from system.sandbox.docker_runner import _bucket_filesystem_diff


def test_buckets_docker_diff_kinds_correctly():
    raw = [
        {"Path": "/tmp/kagutsuchi_pwned", "Kind": 1},
        {"Path": "/etc/hosts", "Kind": 0},
        {"Path": "/tmp/old_file", "Kind": 2},
    ]
    result = _bucket_filesystem_diff(raw)
    assert result == {
        "created": ["/tmp/kagutsuchi_pwned"],
        "modified": ["/etc/hosts"],
        "deleted": ["/tmp/old_file"],
    }


def test_empty_diff_yields_empty_buckets():
    assert _bucket_filesystem_diff([]) == {"created": [], "modified": [], "deleted": []}
