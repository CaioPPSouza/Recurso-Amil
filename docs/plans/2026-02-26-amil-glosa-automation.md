# Automacao de Glosas Amil Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Construir uma aplicacao desktop em Python para ler planilha de glosas e preencher automaticamente guias no portal Amil via Playwright conectado ao Chrome em modo depuracao.

**Architecture:** A solucao separa GUI, orquestracao de fluxo, leitura de planilha e cliente de portal. A GUI publica eventos (iniciar, pausar, retomar, pular) e o orquestrador controla o loop por guia, emitindo logs e status. O cliente Playwright encapsula seletores e waits explicitos.

**Tech Stack:** Python 3.11+, Playwright (sync API), Tkinter/ttk, pytest.

---

### Task 1: Estrutura base do projeto e modelos

**Files:**
- Create: `main.py`
- Create: `app/__init__.py`
- Create: `app/models.py`
- Create: `app/config.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

```python
from app.models import SpreadsheetRow

def test_spreadsheet_key_normalization():
    row = SpreadsheetRow(numero_guia=" 123 ", senha=" 999 ", valor_glosa=10.5, justificativa="abc")
    assert row.key == "123|999"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_spreadsheet_key_normalization -v`
Expected: FAIL with `ModuleNotFoundError` or missing class.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SpreadsheetRow:
    numero_guia: str
    senha: str
    valor_glosa: float
    justificativa: str

    @property
    def key(self) -> str:
        return f"{self.numero_guia.strip()}|{self.senha.strip()}"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_spreadsheet_key_normalization -v`
Expected: PASS

**Step 5: Commit**

```bash
git add main.py app/__init__.py app/models.py app/config.py tests/test_models.py
git commit -m "feat: bootstrap domain models and config"
```

### Task 2: Leitura e validacao da planilha

**Files:**
- Create: `app/excel_reader.py`
- Test: `tests/test_excel_reader.py`

**Step 1: Write the failing test**

```python
def test_read_csv_builds_index(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("numero_guia,senha,valor_glosa,justificativa\n1,2,10.5,ok\n", encoding="utf-8")
    index = load_spreadsheet_index(p)
    assert "1|2" in index
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_excel_reader.py::test_read_csv_builds_index -v`
Expected: FAIL with missing function.

**Step 3: Write minimal implementation**

```python
def load_spreadsheet_index(path):
    # valida colunas obrigatorias e monta dict por chave numero_guia|senha
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_excel_reader.py -v`
Expected: PASS including testes de coluna ausente e chave duplicada.

**Step 5: Commit**

```bash
git add app/excel_reader.py tests/test_excel_reader.py
git commit -m "feat: add spreadsheet reader with strict validation"
```

### Task 3: Orquestrador do fluxo e estado de pausa

**Files:**
- Create: `app/orchestrator.py`
- Test: `tests/test_orchestrator.py`

**Step 1: Write the failing test**

```python
def test_pauses_when_portal_row_not_in_spreadsheet():
    # portal retorna guia/senha inexistente, orquestrador deve pausar
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py::test_pauses_when_portal_row_not_in_spreadsheet -v`
Expected: FAIL with missing class or wrong state.

**Step 3: Write minimal implementation**

```python
class AutomationOrchestrator:
    # run loop, callbacks de log/status e pause_on_missing
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -v`
Expected: PASS para fluxo de sucesso e fluxo de pausa por ausencia na planilha.

**Step 5: Commit**

```bash
git add app/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: implement automation orchestrator state machine"
```

### Task 4: Cliente do portal e launcher do Chrome

**Files:**
- Create: `app/chrome_launcher.py`
- Create: `app/portal_client.py`
- Test: `tests/test_chrome_launcher.py`

**Step 1: Write the failing test**

```python
def test_debug_chrome_command_contains_remote_port():
    cmd = build_chrome_command(9222, Path("tmp-profile"))
    assert "--remote-debugging-port=9222" in cmd
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_chrome_launcher.py::test_debug_chrome_command_contains_remote_port -v`
Expected: FAIL with missing function.

**Step 3: Write minimal implementation**

```python
def build_chrome_command(port, profile_dir):
    return ["chrome", f"--remote-debugging-port={port}", f"--user-data-dir={profile_dir}"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_chrome_launcher.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/chrome_launcher.py app/portal_client.py tests/test_chrome_launcher.py
git commit -m "feat: add debug chrome launcher and playwright portal client"
```

### Task 5: GUI com log em tempo real e controles de acao manual

**Files:**
- Create: `app/ui.py`
- Modify: `main.py`

**Step 1: Write the failing test**

```python
def test_ui_has_required_actions():
    # smoke test de construcao da janela e botoes principais
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui_smoke.py -v`
Expected: FAIL while UI shell does not exist.

**Step 3: Write minimal implementation**

```python
class AutomationApp:
    # botoes: Abrir Chrome, Iniciar, Pausar, Retomar, Pular, Encerrar
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS for all suite.

**Step 5: Commit**

```bash
git add app/ui.py main.py tests/test_ui_smoke.py
git commit -m "feat: add desktop GUI for amil glosa automation"
```

### Task 6: Documentacao e execucao local

**Files:**
- Create: `README.md`
- Create: `requirements.txt`

**Step 1: Write the failing test**

```python
def test_readme_mentions_required_columns():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "numero_guia" in text and "justificativa" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py -v`
Expected: FAIL while docs do not exist.

**Step 3: Write minimal implementation**

```text
# instrucoes de instalacao, chrome debug, formato da planilha e execucao
```

**Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md requirements.txt tests/test_docs.py
git commit -m "docs: add setup and operation guide for automation"
```
