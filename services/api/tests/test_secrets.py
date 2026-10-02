import logging

from app.core.logging import SecretRedactionFilter, redact_sensitive_data


def test_redact_api_key():
    message = "Request with api_key=AIzaSyD-1234567890abcdef and status=200"
    redacted = redact_sensitive_data(message)
    assert "AIzaSyD-1234567890abcdef" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_private_key():
    message = "Signer key 0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d provided"
    redacted = redact_sensitive_data(message)
    assert "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_bearer_token():
    message = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
    redacted = redact_sensitive_data(message)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID" not in redacted
    assert "[REDACTED]" in redacted


def test_logging_filter():
    record = logging.LogRecord(

        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connecting with secret_key=my_super_secret_password_12345",
        args=(),
        exc_info=None,
    )
    redaction_filter = SecretRedactionFilter()
    redaction_filter.filter(record)
    assert "my_super_secret_password_12345" not in record.msg
    assert "[REDACTED]" in record.msg
