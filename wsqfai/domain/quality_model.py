"""
The ISO/IEC 25010 product quality model (base) and its ISO/IEC 25059 AI
extension, encoded as data rather than left implicit in scoring code.

This is the single most load-bearing design decision in WSQF-AI: every
Finding produced anywhere in this project must attach to one of the
QualityCharacteristics defined here, using the SQuaRE standard's own
vocabulary (ISO/IEC 25000-2) - never an ad hoc "category" string invented
per-detector. See ARCHITECTURE.md for why this traces directly to Prof.
Hironori Washizaki's WSQF/WSQB methodology (ICSE 2019), which concretizes
this same standard into measurable metrics rather than treating it as a
citation of convenience.

ISO/IEC 25010 defines 8 product-quality characteristics, each with several
sub-characteristics (2011 edition; the 2023 revision renames Usability to
"Interaction Capability" and adds Safety as a ninth characteristic - noted
but not yet modeled here, see the TODO at the bottom of this file).

ISO/IEC 25059:2023 is a SQuaRE "Extension Division" standard: it inherits
the base model above and adds/modifies sub-characteristics only where
AI-specific behaviour demands it. The additions modeled here (Functional
Adaptability, User Controllability, Transparency, Intervenability, and
Societal and Ethical Risk Mitigation) are sourced from ISO/IEC 25059:2023's
published summary - see ARCHITECTURE.md's citation list. This is
deliberately a partial mapping: 25059 also introduces broader dimensions
(behavioural quality under operational conditions, model quality, data
quality) that aren't yet reduced to concrete sub-characteristics here -
expanding this honestly, from further primary-source reading, is real M3
work, not something to guess at now.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QualityCharacteristic(str, Enum):
    """The 8 top-level ISO/IEC 25010:2011 product quality characteristics."""

    FUNCTIONAL_SUITABILITY = "functional_suitability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    COMPATIBILITY = "compatibility"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"


@dataclass(frozen=True)
class SubCharacteristic:
    key: str
    name: str
    characteristic: QualityCharacteristic
    description: str
    ai_specific: bool = False
    source: str = "ISO/IEC 25010:2011"


# The base ISO/IEC 25010:2011 sub-characteristics, one entry per
# (characteristic, sub-characteristic) pair. Kept as a flat, queryable list
# rather than nested dicts, since M2's measurement layer needs to look up
# "which sub-characteristics belong to Reliability" and "which
# sub-characteristic does this metric measure" with equal ease.
_BASE: list[SubCharacteristic] = [
    SubCharacteristic("func_completeness", "Functional Completeness", QualityCharacteristic.FUNCTIONAL_SUITABILITY,
                       "Degree to which the set of functions covers all specified tasks and user objectives."),
    SubCharacteristic("func_correctness", "Functional Correctness", QualityCharacteristic.FUNCTIONAL_SUITABILITY,
                       "Degree to which a product provides correct results with the needed degree of precision."),
    SubCharacteristic("func_appropriateness", "Functional Appropriateness", QualityCharacteristic.FUNCTIONAL_SUITABILITY,
                       "Degree to which functions facilitate the accomplishment of specified tasks and objectives."),

    SubCharacteristic("time_behaviour", "Time Behaviour", QualityCharacteristic.PERFORMANCE_EFFICIENCY,
                       "Degree to which response/processing times and throughput meet requirements."),
    SubCharacteristic("resource_utilization", "Resource Utilization", QualityCharacteristic.PERFORMANCE_EFFICIENCY,
                       "Degree to which resources used (CPU, memory, storage, network) meet requirements."),
    SubCharacteristic("capacity", "Capacity", QualityCharacteristic.PERFORMANCE_EFFICIENCY,
                       "Degree to which maximum limits of a parameter meet requirements."),

    SubCharacteristic("co_existence", "Co-existence", QualityCharacteristic.COMPATIBILITY,
                       "Degree to which a product can perform required functions efficiently while sharing an environment with other products."),
    SubCharacteristic("interoperability", "Interoperability", QualityCharacteristic.COMPATIBILITY,
                       "Degree to which two or more systems can exchange information and use it."),

    SubCharacteristic("appropriateness_recognizability", "Appropriateness Recognizability", QualityCharacteristic.USABILITY,
                       "Degree to which users can recognize whether a product is appropriate for their needs."),
    SubCharacteristic("learnability", "Learnability", QualityCharacteristic.USABILITY,
                       "Degree to which a product can be used to achieve learning goals with effectiveness, efficiency and satisfaction."),
    SubCharacteristic("operability", "Operability", QualityCharacteristic.USABILITY,
                       "Degree to which a product has attributes that make it easy to operate and control."),
    SubCharacteristic("user_error_protection", "User Error Protection", QualityCharacteristic.USABILITY,
                       "Degree to which a system protects users against making errors."),
    SubCharacteristic("ui_aesthetics", "User Interface Aesthetics", QualityCharacteristic.USABILITY,
                       "Degree to which a user interface enables pleasing and satisfying interaction."),
    SubCharacteristic("accessibility", "Accessibility", QualityCharacteristic.USABILITY,
                       "Degree to which a product can be used by people with the widest range of characteristics and capabilities."),

    SubCharacteristic("maturity", "Maturity", QualityCharacteristic.RELIABILITY,
                       "Degree to which a system meets reliability needs under normal operation."),
    SubCharacteristic("availability", "Availability", QualityCharacteristic.RELIABILITY,
                       "Degree to which a system is operational and accessible when required for use."),
    SubCharacteristic("fault_tolerance", "Fault Tolerance", QualityCharacteristic.RELIABILITY,
                       "Degree to which a system operates as intended despite hardware or software faults."),
    SubCharacteristic("recoverability", "Recoverability", QualityCharacteristic.RELIABILITY,
                       "Degree to which a system can recover data and re-establish state after an interruption or failure."),

    SubCharacteristic("confidentiality", "Confidentiality", QualityCharacteristic.SECURITY,
                       "Degree to which data is accessible only to those authorized to have access."),
    SubCharacteristic("integrity", "Integrity", QualityCharacteristic.SECURITY,
                       "Degree to which a system prevents unauthorized access to, or modification of, data."),
    SubCharacteristic("non_repudiation", "Non-repudiation", QualityCharacteristic.SECURITY,
                       "Degree to which actions or events can be proven to have taken place, so they can't be denied later."),
    SubCharacteristic("accountability", "Accountability", QualityCharacteristic.SECURITY,
                       "Degree to which actions of an entity can be traced uniquely to that entity."),
    SubCharacteristic("authenticity", "Authenticity", QualityCharacteristic.SECURITY,
                       "Degree to which the identity of a subject or resource can be proved to be the one claimed."),

    SubCharacteristic("modularity", "Modularity", QualityCharacteristic.MAINTAINABILITY,
                       "Degree to which a system is composed of discrete components such that a change to one has minimal impact on others."),
    SubCharacteristic("reusability", "Reusability", QualityCharacteristic.MAINTAINABILITY,
                       "Degree to which an asset can be used in more than one system."),
    SubCharacteristic("analysability", "Analysability", QualityCharacteristic.MAINTAINABILITY,
                       "Degree of effectiveness/efficiency in assessing the impact of an intended change."),
    SubCharacteristic("modifiability", "Modifiability", QualityCharacteristic.MAINTAINABILITY,
                       "Degree to which a product can be modified without introducing defects or degrading quality."),
    SubCharacteristic("testability", "Testability", QualityCharacteristic.MAINTAINABILITY,
                       "Degree of effectiveness/efficiency with which test criteria can be established and tests performed."),

    SubCharacteristic("adaptability", "Adaptability", QualityCharacteristic.PORTABILITY,
                       "Degree to which a product can effectively be adapted for different environments."),
    SubCharacteristic("installability", "Installability", QualityCharacteristic.PORTABILITY,
                       "Degree of effectiveness/efficiency with which a product can be installed in a specified environment."),
    SubCharacteristic("replaceability", "Replaceability", QualityCharacteristic.PORTABILITY,
                       "Degree to which a product can replace another specified product for the same purpose in the same environment."),
]

# ISO/IEC 25059:2023's AI-specific additions/modifications on top of the
# base model above. Deliberately a small, honestly-sourced set - see this
# file's module docstring for what's known to be missing.
_AI_EXTENSION: list[SubCharacteristic] = [
    SubCharacteristic("functional_adaptability", "Functional Adaptability", QualityCharacteristic.FUNCTIONAL_SUITABILITY,
                       "Degree to which an AI system can accurately acquire information from data, or the result of "
                       "previous actions, and use that information in future predictions.",
                       ai_specific=True, source="ISO/IEC 25059:2023"),
    SubCharacteristic("user_controllability", "User Controllability", QualityCharacteristic.USABILITY,
                       "Degree to which a user can appropriately intervene in an AI system's functioning in a timely manner.",
                       ai_specific=True, source="ISO/IEC 25059:2023"),
    SubCharacteristic("transparency", "Transparency", QualityCharacteristic.USABILITY,
                       "Degree to which appropriate information about an AI system is communicated to relevant stakeholders.",
                       ai_specific=True, source="ISO/IEC 25059:2023"),
    SubCharacteristic("intervenability", "Intervenability", QualityCharacteristic.USABILITY,
                       "Degree to which an operator can intervene in an AI system's operation to prevent harm or hazard "
                       "- related to controllability, but framed from the operator's perspective.",
                       ai_specific=True, source="ISO/IEC 25059:2023"),
    SubCharacteristic("societal_ethical_risk_mitigation", "Societal and Ethical Risk Mitigation", QualityCharacteristic.RELIABILITY,
                       "Degree to which a system mitigates societal and ethical risks arising from its use "
                       "(freedom-from-risk dimension, ISO/IEC 25059's AI-specific addition).",
                       ai_specific=True, source="ISO/IEC 25059:2023"),
]

ALL_SUB_CHARACTERISTICS: list[SubCharacteristic] = _BASE + _AI_EXTENSION
_BY_KEY: dict[str, SubCharacteristic] = {sc.key: sc for sc in ALL_SUB_CHARACTERISTICS}


def sub_characteristic(key: str) -> SubCharacteristic:
    return _BY_KEY[key]


def sub_characteristics_for(characteristic: QualityCharacteristic, *, ai_only: bool = False) -> list[SubCharacteristic]:
    return [
        sc for sc in ALL_SUB_CHARACTERISTICS
        if sc.characteristic == characteristic and (not ai_only or sc.ai_specific)
    ]


# TODO (M3): model ISO/IEC 25059:2023's broader AI-specific dimensions
# (behavioural quality under operational conditions, model quality, data
# quality) once reduced to concrete, citable sub-characteristics from a
# primary-source read of the standard - not guessed at here.
