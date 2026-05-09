"""File-based storage for the V1 local workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from media_security_audit.models import (
    ActivityEvent,
    Client,
    Finding,
    FindingStatus,
    Mission,
    MissionStatus,
    ScanRun,
    ScopeItem,
    utc_now,
)
from media_security_audit.findings import FindingEngine

ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonStore:
    """Small JSON repository used before SQLite is introduced."""

    def __init__(self, data_dir: Path = Path("data")) -> None:
        self.data_dir = data_dir
        self.clients_dir = self.data_dir / "clients"
        self.missions_dir = self.data_dir / "missions"
        self.findings_dir = self.data_dir / "findings"
        self.events_dir = self.data_dir / "events"
        self.runs_dir = self.data_dir / "runs"

    def ensure(self) -> None:
        self.clients_dir.mkdir(parents=True, exist_ok=True)
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.findings_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_client(self, client: Client) -> Client:
        self.ensure()
        self._write_model(self.clients_dir / f"{client.id}.json", client)
        return client

    def list_clients(self) -> list[Client]:
        self.ensure()
        return self._list_models(self.clients_dir, Client)

    def get_client(self, client_id: str) -> Client:
        return self._read_model(
            self.clients_dir / f"{client_id}.json",
            Client,
            missing_message=f"client not found: {client_id}",
        )

    def create_mission(self, mission: Mission) -> Mission:
        self.ensure()
        self.get_client(mission.client_id)
        mission.status = compute_mission_status(mission)
        self._write_model(self.missions_dir / f"{mission.id}.json", mission)
        return mission

    def list_missions(self) -> list[Mission]:
        self.ensure()
        return self._list_models(self.missions_dir, Mission)

    def get_mission(self, mission_id: str) -> Mission:
        return self._read_model(
            self.missions_dir / f"{mission_id}.json",
            Mission,
            missing_message=f"mission not found: {mission_id}",
        )

    def save_mission(self, mission: Mission) -> Mission:
        self.ensure()
        mission.status = compute_mission_status(mission)
        self._write_model(self.missions_dir / f"{mission.id}.json", mission)
        return mission

    def add_scope_item(self, mission_id: str, scope_item: ScopeItem) -> Mission:
        mission = self.get_mission(mission_id)
        mission.scope.append(scope_item)
        return self.save_mission(mission)

    def update_scope_item(self, mission_id: str, scope_item: ScopeItem) -> Mission:
        mission = self.get_mission(mission_id)
        updated_scope = []
        found = False
        for existing in mission.scope:
            if existing.id == scope_item.id:
                updated_scope.append(scope_item)
                found = True
            else:
                updated_scope.append(existing)
        if not found:
            raise FileNotFoundError(f"scope item not found: {scope_item.id}")
        updated = mission.model_copy(update={"scope": updated_scope})
        return self.save_mission(updated)

    def add_finding(self, mission_id: str, finding: Finding) -> Finding:
        self.get_mission(mission_id)

        engine = FindingEngine()
        engine.add_many(self.list_findings(mission_id))
        stored = engine.add(finding)
        self._write_findings(mission_id, engine.list())
        return stored

    def add_findings(self, mission_id: str, findings: list[Finding]) -> list[Finding]:
        return [self.add_finding(mission_id, finding) for finding in findings]

    def list_findings(self, mission_id: str) -> list[Finding]:
        self.get_mission(mission_id)
        directory = self._mission_findings_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        return self._list_models(directory, Finding)

    def get_finding(self, mission_id: str, finding_id: str) -> Finding:
        self.get_mission(mission_id)
        return self._read_model(
            self._mission_findings_dir(mission_id) / f"{finding_id}.json",
            Finding,
            missing_message=f"finding not found: {finding_id}",
        )

    def save_finding(self, mission_id: str, finding: Finding) -> Finding:
        self.get_mission(mission_id)
        self._write_model(self._mission_findings_dir(mission_id) / f"{finding.id}.json", finding)
        return finding

    def update_finding_status(
        self,
        mission_id: str,
        finding_id: str,
        status: FindingStatus,
        review_note: str | None = None,
    ) -> Finding:
        finding = self.get_finding(mission_id, finding_id)
        metadata = dict(finding.metadata)
        if review_note is not None:
            cleaned_note = review_note.strip()
            if cleaned_note:
                metadata["review_note"] = cleaned_note
            else:
                metadata.pop("review_note", None)
        metadata["reviewed_at"] = utc_now().isoformat()
        updated = finding.model_copy(update={"status": status, "metadata": metadata})
        return self.save_finding(mission_id, updated)

    def add_activity_event(self, event: ActivityEvent) -> ActivityEvent:
        self.get_mission(event.mission_id)
        self._write_model(self._mission_events_dir(event.mission_id) / f"{event.id}.json", event)
        return event

    def list_activity_events(self, mission_id: str) -> list[ActivityEvent]:
        self.get_mission(mission_id)
        directory = self._mission_events_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        return sorted(
            self._list_models(directory, ActivityEvent),
            key=lambda item: item.created_at,
            reverse=True,
        )

    def add_scan_run(self, run: ScanRun) -> ScanRun:
        self.get_mission(run.mission_id)
        self._write_model(self._mission_runs_dir(run.mission_id) / f"{run.id}.json", run)
        return run

    def list_scan_runs(self, mission_id: str) -> list[ScanRun]:
        self.get_mission(mission_id)
        directory = self._mission_runs_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        return sorted(
            self._list_models(directory, ScanRun),
            key=lambda item: item.started_at,
            reverse=True,
        )

    def _write_model(self, path: Path, model: ModelT) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _read_model(
        self,
        path: Path,
        model_type: type[ModelT],
        missing_message: str | None = None,
    ) -> ModelT:
        if not path.exists():
            raise FileNotFoundError(missing_message or f"not found: {path}")
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def _list_models(self, directory: Path, model_type: type[ModelT]) -> list[ModelT]:
        return sorted(
            (self._read_model(path, model_type) for path in directory.glob("*.json")),
            key=lambda item: getattr(item, "created_at", ""),
        )

    def _mission_findings_dir(self, mission_id: str) -> Path:
        return self.findings_dir / mission_id

    def _mission_events_dir(self, mission_id: str) -> Path:
        return self.events_dir / mission_id

    def _mission_runs_dir(self, mission_id: str) -> Path:
        return self.runs_dir / mission_id

    def _write_findings(self, mission_id: str, findings: list[Finding]) -> None:
        directory = self._mission_findings_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        for finding in findings:
            self._write_model(directory / f"{finding.id}.json", finding)


def compute_mission_status(mission: Mission) -> MissionStatus:
    if mission.has_approved_scope and mission.is_authorized and mission.selected_checks:
        return MissionStatus.READY_TO_SCAN
    if mission.has_approved_scope:
        return MissionStatus.SCOPE_DEFINED
    if mission.is_authorized:
        return MissionStatus.AUTHORIZED
    return MissionStatus.DRAFT
