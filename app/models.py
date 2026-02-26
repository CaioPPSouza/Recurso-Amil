from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def build_key(numero_guia: str, senha: str) -> str:
    return f"{str(numero_guia).strip()}|{str(senha).strip()}"


@dataclass(frozen=True)
class SpreadsheetRow:
    numero_guia: str
    senha: str
    valor_glosa: float
    justificativa: str
    codigo_glosa: str | None = None

    @property
    def key(self) -> str:
        return build_key(self.numero_guia, self.senha)


@dataclass(frozen=True)
class GuideContext:
    numero_guia: str
    senha: str
    lote: str
    protocolo: str

    @property
    def key(self) -> str:
        return build_key(self.numero_guia, self.senha)


@dataclass(frozen=True)
class GuideStatusRecord:
    processed_index: int
    total_guides: int
    numero_guia: str
    senha: str
    status: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
