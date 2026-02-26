import threading

from app.models import GuideContext, SpreadsheetRow
from app.runtime import run_automation_job


class ThreadBoundPortalClient:
    def __init__(self, _settings):
        self.thread_id = None
        self.current = 0
        self.closed = False
        self.guides = [GuideContext(numero_guia="1", senha="A", lote="L1", protocolo="P1")]

    def connect(self):
        self.thread_id = threading.get_ident()

    def close(self):
        self._assert_thread()
        self.closed = True

    def get_total_guides(self):
        self._assert_thread()
        return len(self.guides)

    def read_current_context(self):
        self._assert_thread()
        return self.guides[self.current]

    def fill_current_guide(self, valor_glosa, justificativa, codigo_glosa=None):
        self._assert_thread()
        assert valor_glosa == 10.0
        assert justificativa == "Teste"
        assert codigo_glosa == "3052"

    def click_next_guide(self):
        self._assert_thread()
        self.current += 1

    def _assert_thread(self):
        assert self.thread_id == threading.get_ident(), "portal usado em thread incorreta"


def test_run_automation_job_uses_single_thread_for_portal_calls():
    rows = {
        "1|A": SpreadsheetRow(
            numero_guia="1",
            senha="A",
            valor_glosa=10.0,
            justificativa="Teste",
            codigo_glosa="3052",
        )
    }
    logs = []
    statuses = []

    orchestrator = run_automation_job(
        settings=None,
        spreadsheet_index=rows,
        on_log=logs.append,
        on_status=statuses.append,
        portal_client_factory=ThreadBoundPortalClient,
    )

    assert orchestrator.successes == 1
    assert orchestrator.errors == 0
    assert len(statuses) == 1
