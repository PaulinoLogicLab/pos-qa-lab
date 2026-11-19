from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.db import init_db
from src.api.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "api.db"
    monkeypatch.setenv("POS_QA_DB", str(db_file))
    init_db()
    with TestClient(app) as test_client:
        yield test_client
