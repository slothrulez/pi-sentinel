import io
import json
import logging

from pisentinel.safe_logging import REDACTED, configure_logging, log_event, safe_fields

SECRET = "hunter2-SuperSecretValue-9f8e7d"


def capture():
    stream = io.StringIO()
    logger = configure_logging("DEBUG", stream)
    return logger, stream


def test_sensitive_keys_redacted():
    fields = safe_fields(
        {
            "password": SECRET,
            "api_key": SECRET,
            "Authorization": SECRET,
            "nested": {"cookie": SECRET, "ok": "visible"},
            "count": 3,
        }
    )
    assert fields["password"] == fields["api_key"] == fields["Authorization"] == REDACTED
    assert fields["nested"] == {"cookie": REDACTED, "ok": "visible"}
    assert fields["count"] == 3


def test_secret_shaped_values_redacted_and_long_values_truncated():
    fields = safe_fields(
        {
            "msg": f"Bearer {SECRET}",
            "line": "password=" + SECRET,
            "pem": "-----BEGIN RSA PRIVATE KEY-----",
            "big": "x" * 1000,
        }
    )
    dumped = json.dumps(fields)
    assert SECRET not in dumped and "PRIVATE KEY" not in dumped
    assert len(fields["big"]) < 300


def test_log_event_output_is_json_and_secret_free():
    logger, stream = capture()
    log_event(
        logging.getLogger("pisentinel.test"),
        logging.WARNING,
        "rejected",
        password=SECRET,
        reason="invalid",
        error=ValueError(SECRET),
    )
    line = stream.getvalue().strip()
    payload = json.loads(line)
    assert payload["event"] == "rejected" and payload["fields"]["error"] == "ValueError"
    assert SECRET not in line


def test_adhoc_messages_and_exceptions_are_scrubbed():
    logger, stream = capture()
    child = logging.getLogger("pisentinel.adhoc")
    child.warning("login token=%s", SECRET)
    try:
        raise RuntimeError(SECRET)
    except RuntimeError:
        child.exception("failure")
    output = stream.getvalue()
    assert SECRET not in output
    assert '"exception_class": "RuntimeError"' in output
