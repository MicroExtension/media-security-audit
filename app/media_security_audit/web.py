"""Local read-only web interface for the audit workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pydantic import ValidationError

from media_security_audit.models import AuditType, FindingStatus, ScopeEnvironment, ScopeType
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
from media_security_audit.web_forms import (
    add_scope_from_form,
    create_client_from_form,
    create_mission_from_form,
    new_form_token,
    parse_urlencoded_form,
    update_finding_status_from_form,
    validate_form_token,
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


def redirect_with_status(path: str, message: str | None = None, error: str | None = None):
    from fastapi.responses import RedirectResponse

    query = {key: value for key, value in {"message": message, "error": error}.items() if value}
    separator = "&" if "?" in path else "?"
    target = f"{path}{separator}{urlencode(query)}" if query else path
    return RedirectResponse(url=target, status_code=303)


def format_web_error(error: Exception) -> str:
    if isinstance(error, ValidationError):
        messages = [item["msg"] for item in error.errors()]
        return "validation failed: " + "; ".join(messages)
    return str(error)


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
    form_token = new_form_token()
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
    def dashboard(
        request: Request,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "dashboard.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_dashboard_view(store),
                    "audit_types": [item.value for item in AuditType],
                    "form_token": form_token,
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.post("/clients", dependencies=protected)
    async def client_create(request: Request):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            create_client_from_form(store, form)
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status("/", error=format_web_error(error))
        return redirect_with_status("/", message="client created")

    @app.post("/missions", dependencies=protected)
    async def mission_create(request: Request):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            mission = create_mission_from_form(store, form)
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status("/", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission.id}", message="mission created")

    @app.get("/missions/{mission_id}", response_class=HTMLResponse, dependencies=protected)
    def mission_detail(
        request: Request,
        mission_id: str,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
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
                    "scope_types": [item.value for item in ScopeType],
                    "scope_environments": [item.value for item in ScopeEnvironment],
                    "finding_statuses": [item.value for item in FindingStatus],
                    "form_token": form_token,
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.post("/missions/{mission_id}/scope", dependencies=protected)
    async def scope_create(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            add_scope_from_form(store, mission_id, form)
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="scope item added")

    @app.post("/missions/{mission_id}/findings/{finding_id}/status", dependencies=protected)
    async def finding_status_update(request: Request, mission_id: str, finding_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            update_finding_status_from_form(store, mission_id, finding_id, form)
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="finding status updated")

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
