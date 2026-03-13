import os
import subprocess
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Python Sandbox API", description="Execute code and install packages.")

def _parse_execute_timeout() -> float:
    raw = os.environ.get("EXECUTE_TIMEOUT", "5")
    try:
        val = float(raw)
        return max(0.1, min(60.0, val))
    except (ValueError, TypeError):
        return 5.0

EXECUTE_TIMEOUT_DEFAULT = _parse_execute_timeout()
INSTALL_TIMEOUT = 120


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    timeout_seconds: Optional[float] = Field(default=EXECUTE_TIMEOUT_DEFAULT, ge=0.1, le=60)


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timeout: bool = False
    error: Optional[str] = None


class InstallRequest(BaseModel):
    packages: list[str] = Field(..., min_length=1, description="Package names to install")


class InstallResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str


@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest) -> ExecuteResponse:
    timeout = request.timeout_seconds or EXECUTE_TIMEOUT_DEFAULT
    try:
        result = subprocess.run(
            [sys.executable, "-c", request.code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecuteResponse(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.returncode,
            timeout=False,
        )
    except subprocess.TimeoutExpired:
        return ExecuteResponse(
            stdout="",
            stderr="",
            exit_code=-1,
            timeout=True,
            error=f"Execution timed out after {timeout}s",
        )
    except Exception as e:
        return ExecuteResponse(
            stdout="",
            stderr="",
            exit_code=-1,
            timeout=False,
            error=str(e),
        )


@app.post("/install", response_model=InstallResponse)
async def install(request: InstallRequest) -> InstallResponse:
    if not request.packages:
        raise HTTPException(status_code=400, detail="packages list must not be empty")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", *request.packages],
            capture_output=True,
            text=True,
            timeout=INSTALL_TIMEOUT,
        )
        return InstallResponse(
            success=result.returncode == 0,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
        )
    except subprocess.TimeoutExpired:
        return InstallResponse(
            success=False,
            stdout="",
            stderr=f"pip install timed out after {INSTALL_TIMEOUT}s",
        )
    except Exception as e:
        return InstallResponse(
            success=False,
            stdout="",
            stderr=str(e),
        )
