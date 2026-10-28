import pytest

from pisentinel.config import ConfigError, load_config, read_env_file
from tests.conftest import REPO_ROOT

SECRET = "hunter2-SuperSecretValue-9f8e7d"


def test_defaults_load_without_environment():
    cfg = load_config({})
    assert cfg.case_id == "CASE-0001" and cfg.max_record_bytes == 16384
    assert cfg.log_level == "INFO"


def test_env_example_loads_and_contains_no_secret_settings():
    path = REPO_ROOT / ".env.example"
    values = read_env_file(path)
    assert all(k.startswith("PISENTINEL_") for k in values)
    assert not any(w in k for k in values for w in ("PASSWORD", "TOKEN", "SECRET", "KEY"))
    cfg = load_config({}, env_file=path)
    assert cfg.case_id == "CASE-0001"


def test_environment_overrides_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("PISENTINEL_CASE_ID=FROM-FILE\n", encoding="utf-8")
    assert load_config({}, env_file=env_file).case_id == "FROM-FILE"
    assert load_config({"PISENTINEL_CASE_ID": "FROM-ENV"}, env_file=env_file).case_id == "FROM-ENV"


@pytest.mark.parametrize(
    "name,value",
    [
        ("PISENTINEL_MAX_RECORD_BYTES", "16385"),
        ("PISENTINEL_MAX_RECORD_BYTES", "1023"),
        ("PISENTINEL_MAX_RECORD_BYTES", "-5"),
        ("PISENTINEL_MAX_RECORD_BYTES", "1e4"),
        ("PISENTINEL_MAX_RECORD_BYTES", "NaN"),
        ("PISENTINEL_SQLITE_BUSY_TIMEOUT_MS", "99"),
        ("PISENTINEL_MIN_FREE_BYTES", "99999999999999"),
        ("PISENTINEL_CASE_ID", ""),
        ("PISENTINEL_CASE_ID", "../etc"),
        ("PISENTINEL_CASE_ID", "x" * 65),
        ("PISENTINEL_CASE_ID", "caf\u00e9"),
        ("PISENTINEL_LOG_LEVEL", "TRACE"),
        ("PISENTINEL_DB_PATH", ":memory:"),
        ("PISENTINEL_DB_PATH", "file:x.db?mode=memory"),
        ("PISENTINEL_DB_PATH", ""),
        ("PISENTINEL_DB_PATH", "a\x00b"),
        ("PISENTINEL_DB_PATH", "x" * 2000),
        ("PISENTINEL_TYPO_SETTING", "1"),
    ],
)
def test_invalid_settings_are_rejected(name, value):
    with pytest.raises(ConfigError) as info:
        load_config({name: value})
    assert name in info.value.problems


@pytest.mark.parametrize(
    "name",
    [
        "PISENTINEL_MAX_RECORD_BYTES",
        "PISENTINEL_CASE_ID",
        "PISENTINEL_LOG_LEVEL",
        "PISENTINEL_DB_PATH",
        "PISENTINEL_API_TOKEN",
    ],
)
def test_errors_never_echo_values(name):
    with pytest.raises(ConfigError) as info:
        load_config({name: SECRET + "\x00"})
    assert SECRET not in str(info.value)
    assert SECRET not in repr(info.value.problems)


def test_env_file_errors_do_not_echo_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"not a valid line {SECRET}\nPISENTINEL_CASE_ID=A\nPISENTINEL_CASE_ID=B\n")
    with pytest.raises(ConfigError) as info:
        read_env_file(env_file)
    assert SECRET not in str(info.value)
    assert "PISENTINEL_CASE_ID" in info.value.problems


def test_oversized_env_file_rejected(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"#" * (64 * 1024 + 1))
    with pytest.raises(ConfigError):
        read_env_file(env_file)


def test_unrelated_environment_variables_ignored():
    cfg = load_config({"HOME": "/x", "OPENAI_API_KEY": SECRET})
    assert cfg.case_id == "CASE-0001"


def test_importing_config_does_not_bind_environment(monkeypatch):
    import importlib

    import pisentinel.config as config_module

    monkeypatch.setenv("PISENTINEL_CASE_ID", "../bad")
    importlib.reload(config_module)  # import must not read or validate the environment
    with pytest.raises(config_module.ConfigError):
        config_module.load_config()
