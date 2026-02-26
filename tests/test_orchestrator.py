from app.models import GuideContext, SpreadsheetRow
from app.orchestrator import AutomationOrchestrator, OrchestratorConfig


class FakePortalClient:
    def __init__(self, guides):
        self.guides = guides
        self.next_clicks = 0
        self.filled = []
        self.screenshots = []

    def get_total_guides(self):
        return len(self.guides)

    def read_current_context(self):
        return self.guides[self.next_clicks]

    def fill_current_guide(self, valor_glosa, justificativa, codigo_glosa=None):
        self.filled.append((valor_glosa, justificativa, codigo_glosa))

    def click_next_guide(self):
        self.next_clicks += 1

    def capture_screenshot(self, output_path):
        self.screenshots.append(output_path)
        return output_path


class FillErrorPortalClient(FakePortalClient):
    def fill_current_guide(self, valor_glosa, justificativa, codigo_glosa=None):
        raise RuntimeError("falha de preenchimento")


def test_processes_all_guides_with_success():
    portal = FakePortalClient(
        guides=[
            GuideContext(numero_guia="1", senha="A", lote="L1", protocolo="P1"),
            GuideContext(numero_guia="2", senha="B", lote="L1", protocolo="P1"),
        ]
    )
    rows = {
        "1|A": SpreadsheetRow(
            numero_guia="1", senha="A", valor_glosa=10.0, justificativa="J1"
        ),
        "2|B": SpreadsheetRow(
            numero_guia="2", senha="B", valor_glosa=11.0, justificativa="J2"
        ),
    }
    statuses = []
    logs = []

    orchestrator = AutomationOrchestrator(
        portal_client=portal,
        spreadsheet_index=rows,
        config=OrchestratorConfig(pause_on_missing=True, wait_for_manual_action=False),
        on_log=logs.append,
        on_status=statuses.append,
    )

    orchestrator.run()

    assert len(portal.filled) == 2
    assert len(statuses) == 2
    assert all(s.status == "SUCESSO" for s in statuses)
    assert portal.filled[0] == (10.0, "J1", None)


def test_pauses_when_guide_not_found():
    portal = FakePortalClient(
        guides=[GuideContext(numero_guia="1", senha="A", lote="L1", protocolo="P1")]
    )
    rows = {}
    statuses = []
    logs = []
    orchestrator = AutomationOrchestrator(
        portal_client=portal,
        spreadsheet_index=rows,
        config=OrchestratorConfig(pause_on_missing=True, wait_for_manual_action=False),
        on_log=logs.append,
        on_status=statuses.append,
    )

    orchestrator.run()

    assert len(statuses) == 1
    assert statuses[0].status == "ERRO"
    assert orchestrator.state == "PAUSADO"
    assert any("nao encontrada" in message.lower() for message in logs)
    assert len(portal.screenshots) == 1


def test_captures_screenshot_on_fill_error():
    portal = FillErrorPortalClient(
        guides=[GuideContext(numero_guia="1", senha="A", lote="L1", protocolo="P1")]
    )
    rows = {
        "1|A": SpreadsheetRow(
            numero_guia="1", senha="A", valor_glosa=10.0, justificativa="J1"
        )
    }
    statuses = []
    logs = []

    orchestrator = AutomationOrchestrator(
        portal_client=portal,
        spreadsheet_index=rows,
        config=OrchestratorConfig(
            pause_on_missing=True,
            wait_for_manual_action=False,
        ),
        on_log=logs.append,
        on_status=statuses.append,
    )

    orchestrator.run()

    assert len(statuses) == 1
    assert statuses[0].status == "ERRO"
    assert "Falha no preenchimento" in statuses[0].message
    assert len(portal.screenshots) == 1


def test_passes_glosa_code_to_portal_fill():
    portal = FakePortalClient(
        guides=[GuideContext(numero_guia="1", senha="A", lote="L1", protocolo="P1")]
    )
    rows = {
        "1|A": SpreadsheetRow(
            numero_guia="1",
            senha="A",
            valor_glosa=10.0,
            justificativa="J1",
            codigo_glosa="3052",
        )
    }

    orchestrator = AutomationOrchestrator(
        portal_client=portal,
        spreadsheet_index=rows,
        config=OrchestratorConfig(pause_on_missing=True, wait_for_manual_action=False),
        on_log=lambda _: None,
        on_status=lambda _: None,
    )

    orchestrator.run()

    assert portal.filled[0] == (10.0, "J1", "3052")
