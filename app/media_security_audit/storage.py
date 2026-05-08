"""File-based storage for the V1 local workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from media_security_audit.models import (
    Client,
    Finding,
    Mission,
    MissionStatus,
    ScopeItem,
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

    def ensure(self) -> None:
        self.clients_dir.mkdir(parents=True, exist_ok=True)
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.findings_dir.mkdir(parents=True, exist_ok=True)

    def create_client(self, client: Client) -> Client:
        self.ensure()
        self._write_model(self.clients_dir / f"{client.id}.json", client)
        return client

    def list_clients(self) -> list[Client]:
        self.ensure()
        return self._list_models(self.clients_dir, Client)

    def get_client(self, client_id: str) -> Client:
        return self._read_model(self.clients_dir / f"{client_id}.json", Client)

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
        return self._read_model(self.missions_dir / f"{mission_id}.json", Mission)

    def save_mission(self, mission: Mission) -> Mission:
        self.ensure()
        mission.status = compute_mission_status(mission)
        self._write_model(self.missions_dir / f"{mission.id}.json", mission)
        return mission

    def add_scope_item(self, mission_id: str, scope_item: ScopeItem) -> Mission:
        mission = self.get_mission(mission_id)
        mission.scope.append(scope_item)
        return self.save_mission(mission)

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

    def _write_model(self, path: Path, model: ModelT) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _read_model(self, path: Path, model_type: type[ModelT]) -> ModelT:
        if not path.exists():
            raise FileNotFoundError(f"not found: {path}")
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def _list_models(self, directory: Path, model_type: type[ModelT]) -> list[ModelT]:
        return sorted(
            (self._read_model(path, model_type) for path in directory.glob("*.json")),
            key=lambda item: getattr(item, "created_at", ""),
        )

    def _mission_findings_dir(self, mission_id: str) -> Path:
        return self.findings_dir / mission_id

    def _write_findings(self, mission_id: str, findings: list[Finding]) -> None:
        directory = self._mission_findings_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        for finding in findings:
            self._write_model(directory / f"{finding.id}.json", finding)


def compute_mission_status(mission: Mission) -> MissionStatus:
    if mission.has_approved_scope and mission.is_authorized:
        return MissionStatus.READY_TO_SCAN
    if mission.has_approved_scope:
        return MissionStatus.SCOPE_DEFINED
    if mission.is_authorized:
        return MissionStatus.AUTHORIZED
    return MissionStatus.DRAFT
