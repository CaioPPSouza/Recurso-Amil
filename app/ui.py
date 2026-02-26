from __future__ import annotations

import threading
from pathlib import Path
from tempfile import gettempdir
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from app.chrome_launcher import launch_chrome_debug
from app.config import AppSettings, load_settings
from app.excel_reader import load_spreadsheet_index
from app.models import GuideStatusRecord, SpreadsheetRow
from app.orchestrator import AutomationOrchestrator, OrchestratorConfig
from app.reporting import export_status_report
from app.runtime import run_automation_job


def build_usage_instructions() -> str:
    return (
        "Procedimento para Digitacao de Lotes\n\n"
        "1. Acesso:\n"
        "Inicie o Google Chrome clicando no botao correspondente dentro do sistema. "
        "Em seguida, navegue ate o lote que sera processado.\n\n"
        "2. Importacao:\n"
        "Selecione a planilha que contem a base de informacoes.\n\n"
        "3. Execucao:\n"
        "Clique no botao [Iniciar] para comecar o processamento.\n\n"
        "Importante:\n"
        "Caso existam outros lotes para recurso, selecione o lote desejado manualmente "
        "e repita o processo a partir do Passo 2."
    )


class AutomationApp:
    def __init__(self, root: tk.Tk, settings: AppSettings | None = None) -> None:
        self.root = root
        self.root.title("Automacao de Glosas - Amil")
        self.root.geometry("980x640")

        self.settings = settings or load_settings(Path("settings.json"))
        self.profile_dir = Path(gettempdir()) / "amil-glosa-chrome-profile"
        self.reports_dir = Path("reports")

        self.orchestrator: AutomationOrchestrator | None = None
        self.worker: threading.Thread | None = None
        self.status_records: list[GuideStatusRecord] = []
        self.spreadsheet_index: dict[str, SpreadsheetRow] | None = None
        self._pending_stop_request = False

        self.file_var = tk.StringVar()
        self.state_var = tk.StringVar(value="IDLE")

        self._build_layout()
        self._apply_button_state()

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self.root, padding=12)
        root_frame.pack(fill="both", expand=True)

        top = ttk.LabelFrame(root_frame, text="Entrada de Dados", padding=8)
        top.pack(fill="x", padx=2, pady=2)

        ttk.Entry(top, textvariable=self.file_var).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(top, text="Selecionar Planilha", command=self._choose_file).pack(
            side="left"
        )

        controls = ttk.LabelFrame(root_frame, text="Controles", padding=8)
        controls.pack(fill="x", padx=2, pady=8)

        self.open_chrome_btn = ttk.Button(
            controls, text="Abrir Chrome (Depuracao)", command=self._open_debug_chrome
        )
        self.start_btn = ttk.Button(controls, text="Iniciar", command=self._start)
        self.pause_btn = ttk.Button(controls, text="Pausar", command=self._pause)
        self.resume_btn = ttk.Button(controls, text="Retomar", command=self._resume)
        self.skip_btn = ttk.Button(
            controls, text="Pular Guia Atual", command=self._skip_current
        )
        self.stop_btn = ttk.Button(controls, text="Encerrar", command=self._stop)
        self.how_to_use_btn = ttk.Button(
            controls, text="Como usar o sistema", command=self._show_how_to_use
        )

        self.open_chrome_btn.pack(side="left", padx=(0, 6))
        self.start_btn.pack(side="left", padx=6)
        self.pause_btn.pack(side="left", padx=6)
        self.resume_btn.pack(side="left", padx=6)
        self.skip_btn.pack(side="left", padx=6)
        self.stop_btn.pack(side="left", padx=6)
        self.how_to_use_btn.pack(side="left", padx=6)
        ttk.Label(controls, textvariable=self.state_var).pack(side="right")

        status_frame = ttk.LabelFrame(root_frame, text="Guias Concluidas", padding=8)
        status_frame.pack(fill="both", expand=True, padx=2, pady=8)

        self.tree = ttk.Treeview(
            status_frame,
            columns=("idx", "guia", "senha", "status", "msg"),
            show="headings",
            height=12,
        )
        self.tree.heading("idx", text="#")
        self.tree.heading("guia", text="Numero Guia")
        self.tree.heading("senha", text="Senha")
        self.tree.heading("status", text="Status")
        self.tree.heading("msg", text="Mensagem")

        self.tree.column("idx", width=50, anchor="center")
        self.tree.column("guia", width=120, anchor="center")
        self.tree.column("senha", width=120, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("msg", width=480)

        self.tree.pack(fill="both", expand=True)

        log_frame = ttk.LabelFrame(root_frame, text="Log de Operacoes", padding=8)
        log_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.log_widget = ScrolledText(log_frame, height=10, wrap="word")
        self.log_widget.pack(fill="both", expand=True)
        self.log_widget.configure(state="disabled")

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar planilha",
            filetypes=[("Planilhas", "*.xlsx *.csv"), ("Todos", "*.*")],
        )
        if path:
            self.file_var.set(path)
            self._log(f"Planilha selecionada: {path}")

    def _show_how_to_use(self) -> None:
        messagebox.showinfo("Como usar o sistema", build_usage_instructions())

    def _open_debug_chrome(self) -> None:
        try:
            process = launch_chrome_debug(
                port=self.settings.debug_port,
                profile_dir=self.profile_dir,
                chrome_binary=self.settings.chrome_binary,
                start_url=self.settings.portal_url,
            )
            if process is None:
                self._log(
                    f"Chrome em depuracao ja ativo na porta {self.settings.debug_port}."
                )
            else:
                self._log(
                    f"Chrome iniciado em modo depuracao na porta {self.settings.debug_port}."
                )
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao abrir Chrome em depuracao:\n{exc}")
            self._log(f"Falha ao abrir Chrome: {exc}")

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            self._log("Automacao ja esta em execucao.")
            return

        file_path = Path(self.file_var.get().strip())
        if not file_path.exists():
            messagebox.showwarning("Planilha", "Selecione um arquivo .xlsx ou .csv valido.")
            return

        try:
            spreadsheet_index = load_spreadsheet_index(file_path)
        except Exception as exc:
            messagebox.showerror("Erro na planilha", str(exc))
            self._log(f"Erro ao ler planilha: {exc}")
            return

        self._clear_table()
        self.status_records.clear()
        self.spreadsheet_index = spreadsheet_index
        self.orchestrator = None
        self._pending_stop_request = False
        self._log(
            f"Planilha carregada com {len(spreadsheet_index)} linhas indexadas por guia|senha."
        )
        self._set_state("INICIALIZANDO")
        self._log("Inicializando automacao e conectando ao Chrome em depuracao...")
        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()
        self._apply_button_state()

    def _run_worker(self) -> None:
        assert self.spreadsheet_index is not None
        try:
            orchestrator = run_automation_job(
                settings=self.settings,
                spreadsheet_index=self.spreadsheet_index,
                config=OrchestratorConfig(
                    pause_on_missing=True,
                    wait_for_manual_action=True,
                    delay_after_next_seconds=0.35,
                    capture_screenshot_on_error=True,
                    error_artifacts_dir=self.reports_dir / "screenshots",
                ),
                on_log=lambda message: self.root.after(0, self._log, message),
                on_status=lambda item: self.root.after(0, self._push_status, item),
                on_ready=lambda item: self.root.after(0, self._on_orchestrator_ready, item),
            )
            self.orchestrator = orchestrator
        except Exception as exc:
            self.root.after(0, self._handle_runtime_error, str(exc))
            self.root.after(0, self._log, f"Erro critico na automacao: {exc}")
        finally:
            state = self.orchestrator.state if self.orchestrator else "ERRO"
            self.root.after(0, self._set_state, state)
            self.root.after(0, self._apply_button_state)
            self.root.after(0, self._notify_finish)

    def _pause(self) -> None:
        if not self.orchestrator:
            self._log("Aguardando inicializacao da automacao para pausar.")
            return
        self.orchestrator.pause()
        self._set_state(self.orchestrator.state)
        self._apply_button_state()

    def _resume(self) -> None:
        if not self.orchestrator:
            self._log("Aguardando inicializacao da automacao para retomar.")
            return
        self.orchestrator.resume()
        self._set_state(self.orchestrator.state)
        self._apply_button_state()

    def _skip_current(self) -> None:
        if not self.orchestrator:
            self._log("Aguardando inicializacao da automacao para pular guia.")
            return
        self.orchestrator.skip_current_guide()
        self._set_state(self.orchestrator.state)
        self._apply_button_state()

    def _stop(self) -> None:
        if self.orchestrator:
            self.orchestrator.stop()
            self._set_state(self.orchestrator.state)
            self._apply_button_state()
            return

        if self.worker and self.worker.is_alive():
            self._pending_stop_request = True
            self._log("Encerramento solicitado. Aguardando inicializacao para interromper.")
            self._apply_button_state()

    def _push_status(self, status: GuideStatusRecord) -> None:
        self.status_records.append(status)
        self.tree.insert(
            "",
            "end",
            values=(
                f"{status.processed_index}/{status.total_guides}",
                status.numero_guia,
                status.senha,
                status.status,
                status.message,
            ),
        )
        self.tree.see(self.tree.get_children()[-1])
        if self.orchestrator:
            self._set_state(self.orchestrator.state)
            self._apply_button_state()

    def _on_orchestrator_ready(self, orchestrator: AutomationOrchestrator) -> None:
        self.orchestrator = orchestrator
        if self._pending_stop_request:
            self._pending_stop_request = False
            self.orchestrator.stop()
        self._set_state(self.orchestrator.state)
        self._apply_button_state()

    def _handle_runtime_error(self, error_text: str) -> None:
        normalized = error_text.lower()
        if any(
            token in normalized
            for token in ("connect_over_cdp", "econnrefused", "127.0.0.1", "cdp")
        ):
            messagebox.showerror(
                "Conexao com Chrome",
                (
                    "Nao foi possivel conectar ao Chrome em depuracao.\n"
                    f"Detalhe: {error_text}\n"
                    "Abra o Chrome pelo botao 'Abrir Chrome (Depuracao)' e tente novamente."
                ),
            )
            return
        messagebox.showerror(
            "Erro de execucao", f"Ocorreu um erro durante a automacao:\n{error_text}"
        )

    def _notify_finish(self) -> None:
        if not self.orchestrator:
            return
        state = self.orchestrator.state
        if state not in {"FINALIZADO", "PARADO"}:
            return

        summary = self.orchestrator.summary()
        report_file = export_status_report(self.status_records, self.reports_dir)
        self._log(f"Relatorio CSV exportado em: {report_file}")
        self.root.bell()
        messagebox.showinfo(
            "Lote finalizado",
            (
                f"Estado: {summary['state']}\n"
                f"Processadas: {summary['processed']}\n"
                f"Sucessos: {summary['successes']}\n"
                f"Erros: {summary['errors']}\n"
                f"Relatorio: {report_file}"
            ),
        )

    def _apply_button_state(self) -> None:
        running = bool(self.worker and self.worker.is_alive())
        paused = self.orchestrator is not None and self.orchestrator.state == "PAUSADO"
        can_start = not running

        self.start_btn.configure(state="normal" if can_start else "disabled")
        self.open_chrome_btn.configure(state="normal" if can_start else "disabled")

        self.pause_btn.configure(
            state="normal"
            if running and self.orchestrator and self.orchestrator.state == "RUNNING"
            else "disabled"
        )
        self.resume_btn.configure(state="normal" if paused else "disabled")
        self.skip_btn.configure(state="normal" if paused else "disabled")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def _set_state(self, state: str) -> None:
        self.state_var.set(f"Estado: {state}")

    def _clear_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", f"{message}\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")
        if self.orchestrator:
            self._set_state(self.orchestrator.state)
            self._apply_button_state()
