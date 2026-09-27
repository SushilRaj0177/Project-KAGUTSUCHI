from wsqfai.domain.quality_model import (
    ALL_SUB_CHARACTERISTICS,
    QualityCharacteristic,
    sub_characteristic,
    sub_characteristics_for,
)


def test_every_iso_25010_characteristic_has_at_least_one_sub_characteristic():
    for characteristic in QualityCharacteristic:
        subs = sub_characteristics_for(characteristic)
        assert subs, f"{characteristic} has no sub-characteristics registered"


def test_sub_characteristic_keys_are_unique():
    keys = [sc.key for sc in ALL_SUB_CHARACTERISTICS]
    assert len(keys) == len(set(keys))


def test_lookup_by_key_returns_the_right_characteristic():
    sc = sub_characteristic("confidentiality")
    assert sc.characteristic == QualityCharacteristic.SECURITY
    assert sc.ai_specific is False


def test_ai_specific_filter_only_returns_25059_additions():
    ai_subs = sub_characteristics_for(QualityCharacteristic.USABILITY, ai_only=True)
    assert {sc.key for sc in ai_subs} == {"user_controllability", "transparency", "intervenability"}
    for sc in ai_subs:
        assert sc.source == "ISO/IEC 25059:2023"


def test_functional_adaptability_is_the_iso_25059_functional_suitability_addition():
    sc = sub_characteristic("functional_adaptability")
    assert sc.characteristic == QualityCharacteristic.FUNCTIONAL_SUITABILITY
    assert sc.ai_specific is True


def test_unknown_key_raises():
    import pytest
    with pytest.raises(KeyError):
        sub_characteristic("not_a_real_key")
