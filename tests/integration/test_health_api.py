import shutil
import sqlite3
from collections import namedtuple

import pytest
from fastapi.testclient import TestClient

from pisentinel.edge.api.app import create_app
from pisentinel.edge.evidence.writer import EvidenceWriteError, EvidenceWriter
from pisentinel.edge.health import check_health
from tests.conftest import observation


def get(config, writer):
    with TestClient(create_app(config, writer)) as client:
        return client.get("/health")


def test_healthy_after_open(writer, config):
    response = get(config, writer)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["components"]["database"]["schema_version"] == 1
    assert response.headers["cache-control"] == "no-store"
    assert str(config.db_path) not in response.text


def test_unavailable_without_writer_or_database(config):
    response = get(config, None)
    assert response.status_code == 503
    body = response.json()
    assert body["components"]["database"]["reason"] == "database_missing"
    assert body["components"]["writer"]["reason"] == "writer_not_attached"


def test_unavailable_after_writer_closed(config):
    w = EvidenceWriter(config).open()
    w.close()
    assert get(config, w).json()["components"]["writer"]["reason"] == "writer_not_open"


def test_write_failure_visible_then_recovers(writer, config):
    def fail(point):
        raise sqlite3.OperationalError("disk I/O error")

    writer._fault_hook = fail
    with pytest.raises(EvidenceWriteError):
        writer.append_observation(observation(1))
    response = get(config, writer)
    assert response.status_code == 503
    comp = response.json()["components"]["writer"]
    assert comp["reason"] == "last_write_failed" and comp["failed"] == 1
    writer._fault_hook = None
    writer.append_observation(observation(1))
    assert get(config, writer).status_code == 200


def test_rejections_do_not_make_writer_unhealthy(writer, config):
    with pytest.raises(Exception):
        writer.append_observation(observation(1, source_ip="bad"))
    body = get(config, writer).json()
    assert body["status"] == "healthy" and body["components"]["writer"]["rejected"] == 1


def test_schema_mismatch_unavailable(writer, config):
    conn = sqlite3.connect(str(config.db_path))
    conn.execute("INSERT INTO schema_migrations VALUES (2, 'future', 'x')")
    conn.commit()
    conn.close()
    db = check_health(config, writer)["components"]["database"]
    assert db["status"] == "unavailable" and db["reason"] == "schema_mismatch"


def test_low_storage_is_degraded(writer, config, monkeypatch):
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda p: usage(100, 99, 1))
    cfg = config.__class__(**{**config.__dict__, "min_free_bytes": 1024})
    response = get(cfg, writer)
    assert response.status_code == 200 and response.json()["status"] == "degraded"


def test_no_docs_or_other_routes(writer, config):
    with TestClient(create_app(config, writer)) as client:
        for path in ("/docs", "/openapi.json", "/redoc", "/events"):
            assert client.get(path).status_code == 404
        assert client.post("/health").status_code == 405
