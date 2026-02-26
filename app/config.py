from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class PortalSelectors:
    numero_guia: str = "//*[@id='num_guia_operadora_recurso']"
    senha: str = "//*[@id='senha']"
    lote: str = ""
    protocolo: str = ""
    total_guias: str = "//*[@id='guia_final']"
    valor_glosa: str = "//*[@id='valor_recursado']"
    justificativa: str = "//*[@id='justificativa_prestador_procedimento']"
    justificativa_3052: str = "//*[@id='justificativa_guia']"
    proxima_guia: str = "//*[@id='btn_guia_posterior']"


@dataclass
class AppSettings:
    debug_port: int = 9222
    timeout_ms: int = 15000
    chrome_binary: str | None = None
    portal_url: str = "https://credenciado.amil.com.br/"
    selectors: PortalSelectors = field(default_factory=PortalSelectors)

    @property
    def cdp_url(self) -> str:
        return f"http://127.0.0.1:{self.debug_port}"


def load_settings(path: Path | None = None) -> AppSettings:
    if not path or not path.exists():
        return AppSettings()

    content = json.loads(path.read_text(encoding="utf-8"))
    base = AppSettings()

    if "debug_port" in content:
        base.debug_port = int(content["debug_port"])
    if "timeout_ms" in content:
        base.timeout_ms = int(content["timeout_ms"])
    if "chrome_binary" in content:
        base.chrome_binary = content["chrome_binary"]
    if "portal_url" in content:
        base.portal_url = str(content["portal_url"])

    selectors_payload = content.get("selectors")
    if isinstance(selectors_payload, dict):
        selectors_data = asdict(base.selectors)
        selectors_data.update(
            {k: str(v) for k, v in selectors_payload.items() if k in selectors_data}
        )
        base.selectors = PortalSelectors(**selectors_data)

    return base
