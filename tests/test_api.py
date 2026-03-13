"""Five tests for the Python Sandbox HTTP API (execute + install)."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_execute_simple_code_returns_stdout_and_exit_zero():
    """Execute trivial Python code; expect stdout and exit_code 0."""
    r = client.post("/execute", json={"code": "print(1 + 1)"})
    assert r.status_code == 200
    data = r.json()
    assert data["stdout"].strip() == "2"
    assert data["stderr"] == ""
    assert data["exit_code"] == 0
    assert data["timeout"] is False


def test_execute_capture_stderr():
    """Execute code that writes to stderr; expect it in response."""
    r = client.post(
        "/execute",
        json={"code": "import sys; print('err', file=sys.stderr)"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "err" in data["stderr"]
    assert data["exit_code"] == 0


def test_execute_nonzero_exit():
    """Execute code that exits with non-zero; expect exit_code and stderr."""
    r = client.post("/execute", json={"code": "raise SystemExit(42)"})
    assert r.status_code == 200
    data = r.json()
    assert data["exit_code"] == 42


def test_execute_respects_timeout_seconds():
    """Execute long-running code with short timeout; expect timeout=True or error."""
    r = client.post(
        "/execute",
        json={
            "code": "import time; time.sleep(10)",
            "timeout_seconds": 0.2,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["timeout"] is True or data.get("error")
    assert data["exit_code"] == -1


def test_install_then_execute_arbitrary_code():
    """Install a package then execute code that uses it."""
    r_install = client.post("/install", json={"packages": ["six"]})
    assert r_install.status_code == 200
    inst = r_install.json()
    assert inst["success"] is True

    r_exec = client.post(
        "/execute",
        json={"code": "import six; print(six.__version__)"},
    )
    assert r_exec.status_code == 200
    data = r_exec.json()
    assert data["exit_code"] == 0
    assert data["stdout"].strip() != ""
