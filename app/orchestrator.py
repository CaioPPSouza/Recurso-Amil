from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict

from app.models import GuideContext, GuideStatusRecord, SpreadsheetRow


@dataclass
class OrchestratorConfig:
    pause_on_missing: bool = True
    wait_for_manual_action: bool = True
    delay_after_next_seconds: float = 0.3
    capture_screenshot_on_error: bool = True
    error_artifacts_dir: Path = Path("reports") / "screenshots"


class AutomationOrchestrator:
    def __init__(
        self,
        portal_client,
        spreadsheet_index: Dict[str, SpreadsheetRow],
        config: OrchestratorConfig | None = None,
        on_log: Callable[[str], None] | None = None,
        on_status: Callable[[GuideStatusRecord], None] | None = None,
    ) -> None:
        self.portal_client = portal_client
        self.spreadsheet_index = spreadsheet_index
        self.config = config or OrchestratorConfig()
        self.on_log = on_log or (lambda _: None)
        self.on_status = on_status or (lambda _: None)

        self.state = "IDLE"
        self.processed = 0
        self.successes = 0
        self.errors = 0

        self._stop_event = threading.Event()
        self._resume_event = threading.Event()
        self._resume_event.set()
        self._skip_current = False
        self._lock = threading.Lock()

    def run(self) -> None:
        if self.state == "RUNNING":
            return

        self._set_state("RUNNING")
        total = self.portal_client.get_total_guides()
        self._log(f"Total de guias no lote: {total}")

        while self.processed < total:
            if self._stop_event.is_set():
                self._set_state("PARADO")
                return

            self._resume_event.wait()
            if self._stop_event.is_set():
                self._set_state("PARADO")
                return

            context = self.portal_client.read_current_context()
            self._log(
                f"Processando guia {self.processed + 1} de {total} - chave {context.key}"
            )

            row = self.spreadsheet_index.get(context.key)
            if row is None:
                self.errors += 1
                screenshot = self._capture_error_screenshot(context)
                self._emit_status(
                    total=total,
                    context=context,
                    status="ERRO",
                    message=self._build_error_message(
                        "Guia/senha nao encontrada na planilha", screenshot
                    ),
                )
                self._log(
                    f"Guia nao encontrada na planilha: {context.key}. "
                    "Execucao pausada para acao manual."
                )
                if self.config.pause_on_missing:
                    self.pause()
                    if not self.config.wait_for_manual_action:
                        return
                    action = self._wait_for_manual_action()
                    if action == "STOP":
                        self._set_state("PARADO")
                        return
                    if action == "SKIP":
                        self._advance_to_next_guide(total)
                    continue

                self._advance_to_next_guide(total)
                continue

            try:
                self.portal_client.fill_current_guide(
                    valor_glosa=row.valor_glosa,
                    justificativa=row.justificativa,
                    codigo_glosa=row.codigo_glosa,
                )
                self.successes += 1
                self._emit_status(
                    total=total,
                    context=context,
                    status="SUCESSO",
                    message="Guia preenchida com sucesso",
                )
                self._advance_to_next_guide(total)
            except Exception as exc:
                self.errors += 1
                screenshot = self._capture_error_screenshot(context)
                self._emit_status(
                    total=total,
                    context=context,
                    status="ERRO",
                    message=self._build_error_message(
                        f"Falha no preenchimento: {exc}", screenshot
                    ),
                )
                self._log(f"Erro no preenchimento da guia {context.key}: {exc}")
                self.pause()
                if not self.config.wait_for_manual_action:
                    return
                action = self._wait_for_manual_action()
                if action == "STOP":
                    self._set_state("PARADO")
                    return
                if action == "SKIP":
                    self._advance_to_next_guide(total)

        self._set_state("FINALIZADO")
        self._log(
            f"Processamento finalizado. Sucessos: {self.successes} | Erros: {self.errors}"
        )

    def pause(self) -> None:
        with self._lock:
            if self.state == "RUNNING":
                self._set_state("PAUSADO")
                self._resume_event.clear()
                self._log("Execucao pausada.")

    def resume(self) -> None:
        with self._lock:
            if self.state == "PAUSADO":
                self._set_state("RUNNING")
                self._resume_event.set()
                self._log("Execucao retomada.")

    def skip_current_guide(self) -> None:
        with self._lock:
            self._skip_current = True
            self._log("Guia atual marcada para pulo.")
        self.resume()

    def stop(self) -> None:
        self._stop_event.set()
        self._resume_event.set()
        self._set_state("PARADO")
        self._log("Execucao encerrada manualmente.")

    def summary(self) -> dict[str, int | str]:
        return {
            "state": self.state,
            "processed": self.processed,
            "successes": self.successes,
            "errors": self.errors,
        }

    def _wait_for_manual_action(self) -> str:
        while True:
            if self._stop_event.is_set():
                return "STOP"
            if self._resume_event.wait(timeout=0.2):
                if self._consume_skip():
                    return "SKIP"
                return "RETRY"

    def _advance_to_next_guide(self, total: int) -> None:
        if self.processed < total - 1:
            self.portal_client.click_next_guide()
            if self.config.delay_after_next_seconds > 0:
                time.sleep(self.config.delay_after_next_seconds)
        self.processed += 1

    def _consume_skip(self) -> bool:
        with self._lock:
            if self._skip_current:
                self._skip_current = False
                return True
        return False

    def _emit_status(
        self, total: int, context: GuideContext, status: str, message: str
    ) -> None:
        self.on_status(
            GuideStatusRecord(
                processed_index=self.processed + 1,
                total_guides=total,
                numero_guia=context.numero_guia,
                senha=context.senha,
                status=status,
                message=message,
            )
        )

    def _log(self, message: str) -> None:
        self.on_log(message)

    def _set_state(self, new_state: str) -> None:
        self.state = new_state

    def _capture_error_screenshot(self, context: GuideContext) -> Path | None:
        if not self.config.capture_screenshot_on_error:
            return None

        capture = getattr(self.portal_client, "capture_screenshot", None)
        if not callable(capture):
            return None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        guia = self._safe_slug(context.numero_guia)
        senha = self._safe_slug(context.senha)
        self.config.error_artifacts_dir.mkdir(parents=True, exist_ok=True)
        output = self.config.error_artifacts_dir / f"{timestamp}-{guia}-{senha}.png"
        try:
            capture(output)
            self._log(f"Screenshot de erro salva em: {output}")
            return output
        except Exception as exc:
            self._log(f"Falha ao capturar screenshot de erro: {exc}")
            return None

    @staticmethod
    def _safe_slug(value: str) -> str:
        text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip())
        return text.strip("_") or "vazio"

    @staticmethod
    def _build_error_message(base: str, screenshot: Path | None) -> str:
        if screenshot is None:
            return base
        return f"{base} | screenshot={screenshot.name}"
