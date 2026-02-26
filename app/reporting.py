from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.models import GuideStatusRecord


def export_status_report(
    records: Iterable[GuideStatusRecord],
    output_dir: Path,
    lot_id: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    lot = _safe_lot(lot_id)
    file_name = f"relatorio-glosas-{lot}-{stamp}.csv"
    target = output_dir / file_name

    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "timestamp",
                "indice",
                "total_guias",
                "numero_guia",
                "senha",
                "status",
                "mensagem",
            ]
        )
        for item in records:
            writer.writerow(
                [
                    item.timestamp,
                    item.processed_index,
                    item.total_guides,
                    item.numero_guia,
                    item.senha,
                    item.status,
                    item.message,
                ]
            )

    return target


def _safe_lot(lot_id: str | None) -> str:
    if not lot_id:
        return "sem-lote"
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in lot_id)
    return safe.strip("_") or "sem-lote"

