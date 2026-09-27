from wsqfai.ingestion.repository import FileRecord, RepositorySnapshot
from wsqfai.measurement.ml_patterns import compute_ml_pattern_findings, is_ml_repository


def _snapshot(*files: FileRecord) -> RepositorySnapshot:
    return RepositorySnapshot(owner="me", repo="proj", ref=None, files=list(files))


def _py(path: str, content: str) -> FileRecord:
    return FileRecord(path=path, language="Python", size_bytes=len(content), line_count=content.count("\n"), content=content)


def test_repo_without_ml_imports_is_not_an_ml_repository():
    snapshot = _snapshot(_py("app.py", "import os\n\ndef f():\n    return 1\n"))
    assert is_ml_repository(snapshot) is False
    assert compute_ml_pattern_findings(snapshot) == []


def test_repo_with_sklearn_import_is_an_ml_repository():
    snapshot = _snapshot(_py("train.py", "from sklearn.linear_model import LogisticRegression\n"))
    assert is_ml_repository(snapshot) is True


def test_repo_with_torch_import_is_an_ml_repository():
    snapshot = _snapshot(_py("model.py", "import torch\nimport torch.nn as nn\n"))
    assert is_ml_repository(snapshot) is True


def test_plain_numpy_pandas_repo_is_not_an_ml_repository():
    # numpy/pandas alone aren't a strong enough signal - see module docstring.
    snapshot = _snapshot(_py("analysis.py", "import numpy as np\nimport pandas as pd\n"))
    assert is_ml_repository(snapshot) is False


def test_ml_repository_without_versioning_signal_flags_a_finding():
    snapshot = _snapshot(_py("train.py", "import sklearn\nmodel = sklearn.linear_model.LogisticRegression()\n"))
    findings = compute_ml_pattern_findings(snapshot)
    assert len(findings) == 1
    assert findings[0].sub_characteristic_key == "modifiability"
    assert findings[0].evidence[0].location.file_path == "train.py"


def test_ml_repository_with_dvc_yaml_has_no_versioning_finding():
    snapshot = _snapshot(
        _py("train.py", "import sklearn\n"),
        FileRecord(path="dvc.yaml", language="YAML", size_bytes=20, line_count=2, content="stages:\n  train: {}\n"),
    )
    assert compute_ml_pattern_findings(snapshot) == []


def test_ml_repository_with_mlflow_usage_has_no_versioning_finding():
    snapshot = _snapshot(_py("train.py", "import sklearn\nimport mlflow\nmlflow.log_model(model, 'model')\n"))
    assert compute_ml_pattern_findings(snapshot) == []


def test_ml_repository_with_versioned_artifact_filename_has_no_versioning_finding():
    snapshot = _snapshot(
        _py("train.py", "import sklearn\n"),
        FileRecord(path="models/model_v3.pkl", language=None, size_bytes=1000, line_count=0, content=None),
    )
    assert compute_ml_pattern_findings(snapshot) == []


def test_dead_experimental_codepath_is_flagged():
    content = (
        "import sklearn\n"
        "import mlflow\n"
        "mlflow.log_model(None, 'm')\n"
        "if False:\n"
        "    old_model = sklearn.linear_model.LinearRegression()\n"
        "    old_model.fit(x, y)\n"
    )
    snapshot = _snapshot(_py("train.py", content))
    findings = compute_ml_pattern_findings(snapshot)
    dead = [f for f in findings if f.evidence[0].analyzer.rule_id == "dead_experimental_codepath"]
    assert len(dead) == 1
    assert dead[0].sub_characteristic_key == "analysability"
    assert dead[0].evidence[0].location.start_line == 4


def test_if_zero_dead_codepath_is_also_flagged():
    content = (
        "import sklearn\nimport mlflow\nmlflow.log_model(None, 'm')\n"
        "if 0:\n    legacy_train()\n"
    )
    snapshot = _snapshot(_py("train.py", content))
    dead = [f for f in compute_ml_pattern_findings(snapshot) if f.evidence[0].analyzer.rule_id == "dead_experimental_codepath"]
    assert len(dead) == 1


def test_trivial_if_false_body_is_not_flagged():
    # `if False: pass` (or a docstring-only body) has no accumulated debt
    # to report - nothing real is hidden behind it.
    content = "import sklearn\nimport mlflow\nmlflow.log_model(None, 'm')\nif False:\n    pass\n"
    snapshot = _snapshot(_py("train.py", content))
    dead = [f for f in compute_ml_pattern_findings(snapshot) if f.evidence[0].analyzer.rule_id == "dead_experimental_codepath"]
    assert dead == []


def test_dead_codepath_check_does_not_apply_to_non_ml_repos():
    content = "if False:\n    do_something_real()\n"
    snapshot = _snapshot(_py("app.py", content))
    assert compute_ml_pattern_findings(snapshot) == []  # not an ML repo at all


def test_every_ml_pattern_finding_cites_a_real_sub_characteristic():
    from wsqfai.domain.quality_model import sub_characteristic

    snapshot = _snapshot(_py("train.py", "import torch\n"))
    for finding in compute_ml_pattern_findings(snapshot):
        sc = sub_characteristic(finding.sub_characteristic_key)
        assert sc.characteristic == finding.characteristic
