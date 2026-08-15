import sys
import subprocess
from pathlib import Path

import studio_command
from studio_command.service import (
    FRONTEND_DIST,
    SNAPSHOT_PATH,
    app,
)

ROOT = Path(__file__).resolve().parent

subprocess.run(
    [
        sys.executable,
        "-c",
        (
            "import sys; "
            "import studio_command; "
            "from studio_command.service import app; "
            "assert 'studio_command.agent' not in sys.modules; "
            "assert 'root_agent' in studio_command.__all__; "
            "assert app.title == 'Kevaro Studio Command'"
        ),
    ],
    cwd=ROOT,
    check=True,
)

assert "root_agent" in studio_command.__all__

assert app.title == "Kevaro Studio Command"
assert app.version == "23.0"

routes = {
    route.path: getattr(route, "methods", set())
    for route in app.routes
}

assert "/health" in routes
assert "/ready" in routes
assert "/api/studio-snapshot" in routes
assert "/{full_path:path}" in routes

assert "GET" in routes["/health"]
assert "GET" in routes["/ready"]
assert "GET" in routes["/api/studio-snapshot"]

frontend_methods = routes["/{full_path:path}"]
assert "GET" in frontend_methods
assert "HEAD" in frontend_methods

assert (ROOT / "Dockerfile").exists()
assert (ROOT / ".dockerignore").exists()

requirements = (ROOT / "requirements.txt").read_text()
assert "fastapi" in requirements
assert "uvicorn" in requirements

assert FRONTEND_DIST.name == "dist"
assert SNAPSHOT_PATH.name == "studio-snapshot.json"

print("MILESTONE 23 LIGHTWEIGHT SERVICE BOOTSTRAP: PASS")
print("MILESTONE 23 HEALTH AND READINESS CONTRACT: PASS")
print("MILESTONE 23 STUDIO SNAPSHOT API CONTRACT: PASS")
print("MILESTONE 23 FRONTEND GET/HEAD CONTRACT: PASS")
print("MILESTONE 23 CONTAINER DEPLOYMENT CONTRACT: PASS")
print("MILESTONE 1-23 DEPLOYABLE PRODUCT PATH: PASS")
