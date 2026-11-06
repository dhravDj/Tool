"""Security audit and vulnerability analysis report generator."""

import json

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveSecurityReportGenerator:
    """Generates detailed security report for path traversal, bombs, symlinks, and encryption."""

    def generate(self, doc: ArchiveDocument) -> str:
        sr = doc.safety_report
        is_safe = (
            sr.path_traversal_blocked == 0
            and sr.symlink_entries_blocked == 0
            and sr.suspicious_entries == 0
            and not sr.compression_ratio_exceeded
            and not sr.size_limit_exceeded
            and not sr.timeout_exceeded
        )

        security_data = {
            "archive_id": doc.archive_id,
            "security_assessment": "PASSED" if is_safe else "FLAGGED",
            "safety_summary": {
                "path_traversals_blocked": sr.path_traversal_blocked,
                "symlinks_blocked": sr.symlink_entries_blocked,
                "suspicious_device_files": sr.suspicious_entries,
                "archive_bomb_ratio_exceeded": sr.compression_ratio_exceeded,
                "size_quota_exceeded": sr.size_limit_exceeded,
                "entry_limit_exceeded": sr.entry_limit_exceeded,
                "nesting_limit_exceeded": sr.nesting_limit_exceeded,
                "timeout_exceeded": sr.timeout_exceeded,
                "encryption_detected": sr.encryption_detected,
                "corruption_detected": sr.corruption_detected,
                "total_blocked_entries": sr.blocked_entry_count,
            },
            "blocked_entry_details": doc.blocked_entries,
            "security_warnings": sr.warnings,
        }
        return json.dumps(security_data, indent=2)
