import pytest
from pydantic import ValidationError

from wsqfai.domain.evidence import AIAssessment, AnalyzerMetadata, Evidence, Finding, Severity, SourceLocation
from wsqfai.domain.quality_model import QualityCharacteristic


def _evidence(path: str = "src/app.py", line: int = 10) -> Evidence:
    return Evidence(
        location=SourceLocation(file_path=path, start_line=line, end_line=line),
        snippet="os.system(f'ping {host}')",
        analyzer=AnalyzerMetadata(analyzer="ast_scan", rule_id="shell_exec.os_system"),
    )


def test_finding_requires_at_least_one_evidence_item():
    with pytest.raises(ValidationError):
        Finding(
            title="Command injection",
            description="...",
            characteristic=QualityCharacteristic.SECURITY,
            sub_characteristic_key="integrity",
            severity=Severity.HIGH,
            evidence=[],
        )


def test_finding_rejects_absolute_file_paths():
    with pytest.raises(ValidationError):
        Evidence(
            location=SourceLocation(file_path="/etc/passwd", start_line=1),
            snippet="x",
            analyzer=AnalyzerMetadata(analyzer="ast_scan"),
        )


def test_finding_rejects_sub_characteristic_from_a_different_characteristic():
    # "confidentiality" belongs to SECURITY, not MAINTAINABILITY
    with pytest.raises(ValidationError):
        Finding(
            title="Mismatched characteristic",
            description="...",
            characteristic=QualityCharacteristic.MAINTAINABILITY,
            sub_characteristic_key="confidentiality",
            severity=Severity.LOW,
            evidence=[_evidence()],
        )


def test_finding_rejects_unknown_sub_characteristic_key():
    with pytest.raises(ValidationError):
        Finding(
            title="Bogus key",
            description="...",
            characteristic=QualityCharacteristic.SECURITY,
            sub_characteristic_key="not_a_real_sub_characteristic",
            severity=Severity.LOW,
            evidence=[_evidence()],
        )


def test_valid_finding_round_trips_through_json():
    finding = Finding(
        title="Command injection via os.system",
        description="Unsanitized host interpolated into a shell string.",
        characteristic=QualityCharacteristic.SECURITY,
        sub_characteristic_key="integrity",
        severity=Severity.HIGH,
        evidence=[_evidence()],
        ai_assessment=AIAssessment(model="groq:llama", summary="Plausible real injection.", confidence=0.8),
    )
    restored = Finding.model_validate_json(finding.model_dump_json())
    assert restored.finding_id == finding.finding_id
    assert restored.evidence[0].location.file_path == "src/app.py"
    assert restored.ai_assessment is not None
    assert restored.ai_assessment.confidence == 0.8


def test_ai_assessment_confidence_must_be_a_probability():
    with pytest.raises(ValidationError):
        AIAssessment(model="x", summary="x", confidence=1.5)
