"""Support and detection status enumerations."""

from enum import StrEnum


class SupportStatus(StrEnum):
    """Reflects whether a detected file format is extractable, planned, or unprocessable."""

    DETECTED_AND_SUPPORTED = "detected_and_supported"
    DETECTED_BUT_NOT_IMPLEMENTED = "detected_but_not_implemented"
    DETECTED_BUT_UNSUPPORTED = "detected_but_unsupported"
    UNKNOWN_FORMAT = "unknown_format"
    INVALID_FILE = "invalid_file"
    CORRUPTED_FILE = "corrupted_file"
    SUSPICIOUS_FILE = "suspicious_file"
    AMBIGUOUS_FORMAT = "ambiguous_format"


class ConfidenceLevel(StrEnum):
    """Categorical confidence level of the detection analysis."""

    HIGH = "high"  # Multiple independent signals agree (magic + mime + container)
    MEDIUM = "medium"  # One strong signature or structural signal present
    LOW = "low"  # Only weak heuristics or extension-only hints
    UNKNOWN = "unknown"  # No reliable identification possible
