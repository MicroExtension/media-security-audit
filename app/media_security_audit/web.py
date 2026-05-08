"""Local read-only web interface for the audit workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from media_security_audit.reports import render_html
from media_security_audit.storage import JsonStore
from media_security_audit.web_auth import (
    WebAuthSettings,
    valid_credentials,
    web_auth_settings_from_env,
)
from media_security_audit.web_ui import (
    build_dashboard_view,
    build_mission_view,
    html_escape,
    severity_class,
)


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "web_templates"
STATIC_DIR = PACKAGE_DIR / "web_static"


def template_environment():
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "missing jinja2; install the project dependencies before running the UI"
        ) from error

    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
    )
    environment.filters["severity_class"] = severity_class
    environment.filters["html_escape"] = html_escape
    return environment


def render_template(environment: Any, name: str, context: dict[str, Any]) -> str:
    return environment.get_template(name).render(**context)


def create_web_app(data_dir: Path = Path("data"), auth_settings: WebAuthSettings | None = None):
    try:
        from fastapi import Depends, FastAPI, HTTPException, Request
        from fastapi.responses import HTMLResponse, RedirectResponse
        from fastapi.security import HTTPBasic, HTTPBasicCredentials
        from fastapi.staticfiles import StaticFiles
    except ModuleNotFoundError as error:
        missing = error.name or "web dependency"
        raise RuntimeError(
            f"missing {missing}; install the project with web dependencies before running the UI"
        ) from error

    store = JsonStore(data_dir)
    templates = template_environment()
    settings = auth_settings or web_auth_settings_from_env()
    app = FastAPI(title="MEDIA Security Audit Platform")
    security = HTTPBasic(auto_error=False)

    def require_web_auth(credentials: HTTPBasicCredentials | None = Depends(security)) -> None:
        username = credentials.username if credentials else None
        password = credentials.password if credentials else None
        if valid_credentials(settings, username, password):
            return
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": f'Basic realm="{settings.realm}"'},
        )

    protected = [Depends(require_web_auth)]

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse, dependencies=protected)
    def dashboard(request: Request) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "dashboard.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_dashboard_view(store),
                },
            )
        )

    @app.get("/missions/{mission_id}", response_class=HTMLResponse, dependencies=protected)
    def mission_detail(request: Request, mission_id: str) -> HTMLResponse:
        try:
            view = build_mission_view(store, mission_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        return HTMLResponse(
            render_template(
                templates,
                "mission.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": view,
                },
            )
        )

    @app.get("/missions/{mission_id}/report.html", response_class=HTMLResponse, dependencies=protected)
    def mission_report(mission_id: str) -> HTMLResponse:
        try:
            mission = store.get_mission(mission_id)
            findings = store.list_findings(mission_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return HTMLResponse(render_html(mission, findings))

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/missions", dependencies=protected)
    def missions_redirect() -> RedirectResponse:
        return RedirectResponse(url="/")

    return app


def run_web_server(data_dir: Path = Path("data"), host: str = "127.0.0.1", port: int = 8080) -> None:
    try:
        import uvicorn
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "missing uvicorn; install the project dependencies before running the UI"
        ) from error

    uvicorn.run(create_web_app(data_dir=data_dir), host=host, port=port)


def main() -> None:
    run_web_server()


if __name__ == "__main__":
    main()
