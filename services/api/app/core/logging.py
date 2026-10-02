import logging
import re

# Sensitive patterns to redact in logs (PRD 9.6, FR-SEC-03)
# Format: (regex, replacement)
SENSITIVE_REPLACEMENTS = [
    (re.compile(r'(api[-_]?key["\']?\s*[:=]\s*["\']?)([^"\'\s&]{4,})', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(secret[-_]?key["\']?\s*[:=]\s*["\']?)([^"\'\s&]{4,})', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s&]{4,})', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(bearer\s+)([A-Za-z0-9\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'0x[a-fA-F0-9]{64}', re.IGNORECASE), '[REDACTED]'),  # Private keys
]


def redact_sensitive_data(message: str) -> str:
    """Redacts potential secrets, keys, or passwords from string."""
    redacted = message
    for pattern, replacement in SENSITIVE_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted



class SecretRedactionFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials before emitting."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (redact_sensitive_data(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_data(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    root_logger = logging.getLogger()
    redaction_filter = SecretRedactionFilter()
    root_logger.addFilter(redaction_filter)
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)
