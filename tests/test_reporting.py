from pathlib import Path

from app.models import GuideStatusRecord
from app.reporting import export_status_report


def test_export_status_report_creates_csv(tmp_path: Path):
    records = [
        GuideStatusRecord(
            processed_index=1,
            total_guides=2,
            numero_guia="123",
            senha="999",
            status="SUCESSO",
            message="OK",
        ),
        GuideStatusRecord(
            processed_index=2,
            total_guides=2,
            numero_guia="124",
            senha="998",
            status="ERRO",
            message="Nao encontrada",
        ),
    ]

    target = export_status_report(records, output_dir=tmp_path, lot_id="L-100")

    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "numero_guia" in content
    assert "123" in content
    assert "Nao encontrada" in content
