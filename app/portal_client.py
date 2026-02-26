from __future__ import annotations

from pathlib import Path
import re
import time
from typing import Any

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    sync_playwright,
)

from app.config import AppSettings
from app.models import GuideContext


def resolve_selector(selector: str) -> str:
    normalized = str(selector or "").strip()
    if normalized.startswith("/") or normalized.startswith("("):
        return f"xpath={normalized}"
    return normalized


def normalize_glosa_code(codigo_glosa: str | None) -> str:
    text = str(codigo_glosa or "").strip()
    if not text:
        return ""
    numeric = re.sub(r"\D+", "", text)
    return numeric or text


def is_glosa_3052(codigo_glosa: str | None) -> bool:
    return normalize_glosa_code(codigo_glosa) == "3052"


def resolve_justificativa_selector(codigo_glosa: str | None, settings: AppSettings) -> str:
    if is_glosa_3052(codigo_glosa) and settings.selectors.justificativa_3052:
        return settings.selectors.justificativa_3052
    return settings.selectors.justificativa


def find_locator_in_pages(pages: list[Any], selector: str) -> tuple[Any | None, Any | None]:
    # Prioriza a ultima aba/pagina aberta.
    for page in reversed(pages):
        locator = find_locator_in_page_frames(page, selector)
        if locator is not None:
            return locator, page
    return None, None


def find_locator_in_page_frames(page: Any, selector: str) -> Any | None:
    frames = list(getattr(page, "frames", []) or [])
    if not frames and hasattr(page, "main_frame"):
        frames = [page.main_frame]

    for frame in frames:
        try:
            locator = frame.locator(selector).first
            if _safe_locator_count(locator) > 0:
                return locator
        except Exception:
            continue
    return None


def _safe_locator_count(locator: Any) -> int:
    try:
        return int(locator.count())
    except Exception:
        return 0


class PortalClient:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("PortalClient ainda nao conectado.")
        return self._page

    def connect(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(self.settings.cdp_url)

        contexts = self._browser.contexts
        if contexts:
            self._context = contexts[0]
        else:
            self._context = self._browser.new_context()

        if self._context.pages:
            self._page = self._context.pages[-1]
        else:
            self._page = self._context.new_page()

    def close(self) -> None:
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
            self._browser = None
            self._context = None
            self._page = None

    def get_total_guides(self) -> int:
        raw = self._read_text_or_value(self.settings.selectors.total_guias)
        matches = [int(value) for value in re.findall(r"\d+", raw)]
        if not matches:
            raise RuntimeError(
                "Nao foi possivel identificar o total de guias no portal. "
                f"Valor capturado: {raw!r}"
            )
        return matches[-1]

    def read_current_context(self) -> GuideContext:
        selectors = self.settings.selectors
        return GuideContext(
            numero_guia=self._read_text_or_value(selectors.numero_guia),
            senha=self._read_text_or_value(selectors.senha),
            lote=self._read_optional_text_or_value(selectors.lote),
            protocolo=self._read_optional_text_or_value(selectors.protocolo),
        )

    def fill_current_guide(
        self,
        valor_glosa: float,
        justificativa: str,
        codigo_glosa: str | None = None,
    ) -> None:
        selectors = self.settings.selectors
        if not is_glosa_3052(codigo_glosa):
            valor_text = f"{valor_glosa:.2f}".replace(".", ",")
            self._fill(selectors.valor_glosa, valor_text)
        justificativa_selector = resolve_justificativa_selector(codigo_glosa, self.settings)
        self._fill(justificativa_selector, justificativa)

    def click_next_guide(self) -> None:
        locator = self._find_locator(self.settings.selectors.proxima_guia)
        locator.wait_for(state="visible", timeout=self.settings.timeout_ms)
        locator.click(timeout=self.settings.timeout_ms)
        self.page.wait_for_load_state("domcontentloaded", timeout=self.settings.timeout_ms)

    def capture_screenshot(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(output_path), full_page=True)
        return output_path

    def _fill(self, selector: str, value: str) -> None:
        locator = self._find_locator(selector)
        locator.wait_for(state="visible", timeout=self.settings.timeout_ms)
        locator.fill(value, timeout=self.settings.timeout_ms)

    def _read_text_or_value(self, selector: str) -> str:
        locator = self._find_locator(selector)
        locator.wait_for(state="attached", timeout=self.settings.timeout_ms)

        value = self._safe_input_value(locator)
        if value is not None and str(value).strip():
            return str(value).strip()

        text = self._safe_inner_text(locator)
        if not text:
            text = (locator.text_content(timeout=self.settings.timeout_ms) or "").strip()
        if not text:
            raise RuntimeError(f"Campo do portal sem valor para seletor: {selector}")
        return text

    def _read_optional_text_or_value(self, selector: str) -> str:
        if not str(selector or "").strip():
            return ""
        try:
            return self._read_text_or_value(selector)
        except Exception:
            return ""

    def _locator(self, selector: str) -> Locator:
        resolved = resolve_selector(selector)
        if not resolved:
            raise ValueError("Seletor vazio nao pode ser usado.")
        return self.page.locator(resolved)

    def _find_locator(self, selector: str) -> Locator:
        resolved = resolve_selector(selector)
        if not resolved:
            raise ValueError("Seletor vazio nao pode ser usado.")

        timeout_seconds = self.settings.timeout_ms / 1000
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            pages = self._candidate_pages()
            locator, selected_page = find_locator_in_pages(pages, resolved)
            if locator is not None and selected_page is not None:
                self._page = selected_page
                return locator
            time.sleep(0.2)

        pages_info = " | ".join(self._describe_pages())
        raise RuntimeError(
            "Seletor nao encontrado no tempo limite. "
            f"Seletor: {selector} | Paginas/frames: {pages_info}"
        )

    def _candidate_pages(self) -> list[Page]:
        if self._context and self._context.pages:
            return list(self._context.pages)
        return [self.page]

    def _describe_pages(self) -> list[str]:
        result = []
        for page in self._candidate_pages():
            frames = list(getattr(page, "frames", []) or [])
            frame_urls = ", ".join(
                frame.url for frame in frames if getattr(frame, "url", None)
            )
            page_url = getattr(page, "url", "<sem-url>")
            result.append(f"page={page_url};frames=[{frame_urls}]")
        return result or ["<nenhuma pagina>"]

    @staticmethod
    def _safe_input_value(locator: Any) -> str | None:
        try:
            return locator.input_value(timeout=400)
        except Exception:
            return None

    @staticmethod
    def _safe_inner_text(locator: Any) -> str:
        try:
            return locator.inner_text(timeout=400).strip()
        except Exception:
            return ""
