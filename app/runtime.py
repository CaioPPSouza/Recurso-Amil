from __future__ import annotations

from typing import Callable, Dict

from app.config import AppSettings
from app.models import GuideStatusRecord, SpreadsheetRow
from app.orchestrator import AutomationOrchestrator, OrchestratorConfig
from app.portal_client import PortalClient


def run_automation_job(
    settings: AppSettings | None,
    spreadsheet_index: Dict[str, SpreadsheetRow],
    on_log: Callable[[str], None],
    on_status: Callable[[GuideStatusRecord], None],
    config: OrchestratorConfig | None = None,
    on_ready: Callable[[AutomationOrchestrator], None] | None = None,
    portal_client_factory=PortalClient,
) -> AutomationOrchestrator:
    portal_client = portal_client_factory(settings)
    orchestrator: AutomationOrchestrator | None = None

    try:
        portal_client.connect()
        on_log(
            "Conexao com o Chrome estabelecida. "
            "Confirme que a aba atual esta no lote desejado."
        )
        orchestrator = AutomationOrchestrator(
            portal_client=portal_client,
            spreadsheet_index=spreadsheet_index,
            config=config or OrchestratorConfig(),
            on_log=on_log,
            on_status=on_status,
        )
        if on_ready:
            on_ready(orchestrator)
        orchestrator.run()
        return orchestrator
    finally:
        close = getattr(portal_client, "close", None)
        if callable(close):
            close()
