# Python Sandbox HTTP API

Every god-damn python sandbox is too complicated. SimpleSandbox keeps it, well, simple.

A minimal HTTP API to execute arbitrary Python code and install packages in a single global environment. No VMs or per-request containers—runs on Python 3 slim with FastAPI.

**Note:** No authentication is included. Intended for local or trusted environments only.

## Build

```bash
docker build -t python-sandbox .
```

## Run

```bash
docker run -p 8000:8000 python-sandbox
```

To use a different port (e.g. 9000):

```bash
docker run -p 9000:9000 -e PORT=9000 python-sandbox
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP server port. |
| `EXECUTE_TIMEOUT` | `5` | Default execution timeout in seconds for `/execute` (clamped to 0.1–60). Request-level `timeout_seconds` still overrides per call. |

## API

### Execute Python code

**POST** `/execute`

Request body:

```json
{
  "code": "print(1 + 1)",
  "timeout_seconds": 5
}
```

- `code` (required): Python code to run.
- `timeout_seconds` (optional): Max execution time in seconds (default: 5, max: 60).

Response:

```json
{
  "stdout": "2\n",
  "stderr": "",
  "exit_code": 0,
  "timeout": false,
  "error": null
}
```

Example:

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2 ** 10)"}'
```

### Install packages

**POST** `/install`

Request body:

```json
{
  "packages": ["requests", "numpy"]
}
```

- `packages` (required): Non-empty list of pip package names.

Response:

```json
{
  "success": true,
  "stdout": "...",
  "stderr": ""
}
```

Example:

```bash
curl -X POST http://localhost:8000/install \
  -H "Content-Type: application/json" \
  -d '{"packages": ["requests"]}'
```

Installed packages are available to subsequent `/execute` calls in the same container. They are not persisted across container restarts.

## OpenAPI docs

With the server running, open:

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  
