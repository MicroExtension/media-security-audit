"""Local web interface for the audit workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pydantic import ValidationError

from media_security_audit.models import (
    ActivityEvent,
    AuditType,
    FindingStatus,
    ReportFormat,
    ScopeEnvironment,
    ScopeType,
    Severity,
)
from media_security_audit.reports import render_html
from media_security_audit.storage import JsonStore
from media_security_audit.web_authorization import (
    AuthorizationBriefFormat,
    authorization_brief_file,
    generate_authorization_brief,
)
from media_security_audit.web_auth import (
    WebAuthSettings,
    valid_credentials,
    web_auth_settings_from_env,
)
from media_security_audit.web_activity import (
    build_activity_log_export,
    build_activity_log_view,
)
from media_security_audit.web_audit_templates import build_audit_template_library_view
from media_security_audit.web_backup import generate_workspace_backup, workspace_backup_file
from media_security_audit.web_remediations import (
    build_remediation_library_export,
    build_remediation_library_view,
)
from media_security_audit.web_ui import (
    build_dashboard_view,
    build_mission_view,
    html_escape,
    severity_class,
    scope_status,
)
from media_security_audit.web_forms import (
    add_manual_finding_from_form,
    add_scope_from_form,
    create_client_from_form,
    create_mission_from_form,
    new_form_token,
    parse_urlencoded_form,
    update_finding_status_from_form,
    update_manual_finding_from_form,
    update_mission_checks_from_form,
    update_mission_from_form,
    update_scope_from_form,
    validate_form_token,
)
from media_security_audit.web_exports import generate_mission_export, mission_export_file
from media_security_audit.web_reports import generate_web_reports, generated_report_file
from media_security_audit.web_system import build_system_status


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


def create_web_app(
    data_dir: Path = Path("data"),
    reports_dir: Path = Path("reports"),
    auth_settings: WebAuthSettings | None = None,
):
    try:
        from fastapi import Depends, FastAPI, HTTPException, Request
        from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
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

    def record_activity(
        mission_id: str,
        action: str,
        summary: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission_id,
                action=action,
                summary=summary,
                metadata=metadata or {},
            )
        )

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
                    "audit_templates": build_audit_template_library_view().templates,
                    "form_token": form_token,
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.get("/system", response_class=HTMLResponse, dependencies=protected)
    def system_status(
        request: Request,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "system.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_system_status(data_dir, reports_dir, settings),
                    "form_token": form_token,
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.get("/activity", response_class=HTMLResponse, dependencies=protected)
    def activity_log(
        request: Request,
        q: str | None = None,
        action: str | None = None,
        client_id: str | None = None,
        mission_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "activity.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_activity_log_view(
                        store,
                        query=q,
                        action=action,
                        client_id=client_id,
                        mission_id=mission_id,
                        date_from=date_from,
                        date_to=date_to,
                    ),
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.get("/activity/export/{export_format}", dependencies=protected)
    def activity_log_export(
        export_format: ReportFormat,
        q: str | None = None,
        action: str | None = None,
        client_id: str | None = None,
        mission_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Response:
        export = build_activity_log_export(
            store,
            export_format,
            query=q,
            action=action,
            client_id=client_id,
            mission_id=mission_id,
            date_from=date_from,
            date_to=date_to,
        )
        return Response(
            content=export.content,
            media_type=export.media_type,
            headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
        )

    @app.get("/remediations", response_class=HTMLResponse, dependencies=protected)
    def remediation_library(
        request: Request,
        q: str | None = None,
        category: str | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "remediations.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_remediation_library_view(query=q, category=category),
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.get("/templates", response_class=HTMLResponse, dependencies=protected)
    def audit_templates(
        request: Request,
        q: str | None = None,
        audit_type: str | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_template(
                templates,
                "audit_templates.html",
                {
                    "request": request,
                    "data_dir": data_dir,
                    "view": build_audit_template_library_view(query=q, audit_type=audit_type),
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.get("/remediations/export/{export_format}", dependencies=protected)
    def remediation_library_export(
        export_format: ReportFormat,
        q: str | None = None,
        category: str | None = None,
    ) -> Response:
        export = build_remediation_library_export(
            export_format=export_format,
            query=q,
            category=category,
        )
        return Response(
            content=export.content,
            media_type=export.media_type,
            headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
        )

    @app.post("/system/backup", dependencies=protected)
    async def workspace_backup_generate(request: Request):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            generate_workspace_backup(data_dir, reports_dir)
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status("/system", error=format_web_error(error))
        return redirect_with_status("/system", message="workspace backup generated")

    @app.get("/system/backup", dependencies=protected)
    def workspace_backup_download() -> FileResponse:
        try:
            path = workspace_backup_file(reports_dir)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return FileResponse(path)

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
            record_activity(mission.id, "mission.created", f"Mission created: {mission.name}")
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
            view = build_mission_view(store, mission_id, reports_dir=reports_dir)
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
                    "audit_types": [item.value for item in AuditType],
                    "scope_types": [item.value for item in ScopeType],
                    "scope_environments": [item.value for item in ScopeEnvironment],
                    "finding_statuses": [item.value for item in FindingStatus],
                    "severities": [item.value for item in Severity],
                    "form_token": form_token,
                    "message": message,
                    "error": error,
                },
            )
        )

    @app.post("/missions/{mission_id}/details", dependencies=protected)
    async def mission_update(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            mission = update_mission_from_form(store, mission_id, form)
            record_activity(mission_id, "mission.updated", f"Mission setup updated: {mission.name}")
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="mission updated")

    @app.post("/missions/{mission_id}/checks", dependencies=protected)
    async def mission_checks_update(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            mission = update_mission_checks_from_form(store, mission_id, form)
            selected_checks = ", ".join(check.value for check in mission.selected_checks) or "none"
            record_activity(
                mission_id,
                "check_selection.updated",
                f"Check selection updated: {selected_checks}",
                {
                    "selected_checks": selected_checks,
                    "selected_count": str(len(mission.selected_checks)),
                },
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="check selection updated")

    @app.post("/missions/{mission_id}/scope", dependencies=protected)
    async def scope_create(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            mission = add_scope_from_form(store, mission_id, form)
            scope_item = mission.scope[-1]
            record_activity(
                mission_id,
                "scope.added",
                f"Scope added: {scope_item.value}",
                {"scope_id": scope_item.id, "scope_type": scope_item.type.value},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="scope item added")

    @app.post("/missions/{mission_id}/scope/{scope_id}", dependencies=protected)
    async def scope_update(request: Request, mission_id: str, scope_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            mission = update_scope_from_form(store, mission_id, scope_id, form)
            scope_item = next(item for item in mission.scope if item.id == scope_id)
            record_activity(
                mission_id,
                "scope.updated",
                f"Scope updated: {scope_item.value}",
                {"scope_id": scope_item.id, "scope_status": scope_status(scope_item)},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="scope item updated")

    @app.post("/missions/{mission_id}/findings", dependencies=protected)
    async def finding_create(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            finding = add_manual_finding_from_form(store, mission_id, form)
            record_activity(
                mission_id,
                "finding.added",
                f"Manual finding added: {finding.title}",
                {"finding_id": finding.id, "severity": finding.severity.value},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="finding added")

    @app.post("/missions/{mission_id}/findings/{finding_id}/details", dependencies=protected)
    async def finding_update(request: Request, mission_id: str, finding_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            finding = update_manual_finding_from_form(store, mission_id, finding_id, form)
            record_activity(
                mission_id,
                "finding.updated",
                f"Manual finding updated: {finding.title}",
                {"finding_id": finding.id, "severity": finding.severity.value},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="finding updated")

    @app.post("/missions/{mission_id}/findings/{finding_id}/status", dependencies=protected)
    async def finding_status_update(request: Request, mission_id: str, finding_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            finding = update_finding_status_from_form(store, mission_id, finding_id, form)
            record_activity(
                mission_id,
                "finding.status_updated",
                f"Finding status updated: {finding.title} -> {finding.status.value}",
                {"finding_id": finding.id, "status": finding.status.value},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="finding status updated")

    @app.post("/missions/{mission_id}/reports", dependencies=protected)
    async def report_generate(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            paths = generate_web_reports(store, mission_id, reports_dir)
            record_activity(
                mission_id,
                "reports.generated",
                f"Generated {len(paths)} report export(s)",
                {"report_count": str(len(paths))},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="reports generated")

    @app.post("/missions/{mission_id}/authorization-brief", dependencies=protected)
    async def authorization_brief_generate(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            paths = generate_authorization_brief(store, mission_id, reports_dir)
            record_activity(
                mission_id,
                "authorization_brief.generated",
                f"Generated {len(paths)} authorization brief export(s)",
                {"brief_count": str(len(paths))},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="authorization brief generated")

    @app.get("/missions/{mission_id}/authorization-brief/{brief_format}", dependencies=protected)
    def authorization_brief_download(
        mission_id: str,
        brief_format: AuthorizationBriefFormat,
    ) -> FileResponse:
        try:
            store.get_mission(mission_id)
            path = authorization_brief_file(reports_dir, mission_id, brief_format)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return FileResponse(path)

    @app.post("/missions/{mission_id}/export", dependencies=protected)
    async def mission_export_generate(request: Request, mission_id: str):
        try:
            form = parse_urlencoded_form(await request.body())
            validate_form_token(form, form_token)
            path = generate_mission_export(store, mission_id, reports_dir)
            record_activity(
                mission_id,
                "mission.exported",
                f"Mission export package generated: {path.name}",
                {"filename": path.name},
            )
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            return redirect_with_status(f"/missions/{mission_id}", error=format_web_error(error))
        return redirect_with_status(f"/missions/{mission_id}", message="mission export generated")

    @app.get("/missions/{mission_id}/export", dependencies=protected)
    def mission_export_download(mission_id: str) -> FileResponse:
        try:
            store.get_mission(mission_id)
            path = mission_export_file(reports_dir, mission_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return FileResponse(path)

    @app.get("/missions/{mission_id}/reports/{report_format}", dependencies=protected)
    def report_download(mission_id: str, report_format: ReportFormat) -> FileResponse:
        try:
            store.get_mission(mission_id)
            path = generated_report_file(reports_dir, mission_id, report_format)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return FileResponse(path)

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


def run_web_server(
    data_dir: Path = Path("data"),
    reports_dir: Path = Path("reports"),
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    try:
        import uvicorn
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "missing uvicorn; install the project dependencies before running the UI"
        ) from error

    uvicorn.run(create_web_app(data_dir=data_dir, reports_dir=reports_dir), host=host, port=port)


def main() -> None:
    run_web_server()


if __name__ == "__main__":
    main()
