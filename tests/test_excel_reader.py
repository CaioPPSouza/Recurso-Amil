from pathlib import Path

from openpyxl import Workbook
import pytest

from app.excel_reader import load_spreadsheet_index


def test_read_csv_builds_index(tmp_path: Path):
    source = tmp_path / "glosas.csv"
    source.write_text(
        (
            "numero_guia,senha,valor_glosa,justificativa,codigo_da_glosa_da_guia\n"
            "123,999,10.5,Sem cobertura,3052\n"
        ),
        encoding="utf-8",
    )

    index = load_spreadsheet_index(source)

    assert "123|999" in index
    assert index["123|999"].valor_glosa == 10.5
    assert index["123|999"].justificativa == "Sem cobertura"
    assert index["123|999"].codigo_glosa == "3052"


def test_raises_error_when_required_column_is_missing(tmp_path: Path):
    source = tmp_path / "glosas.csv"
    source.write_text("numero_guia,senha,justificativa\n123,999,Teste\n", encoding="utf-8")

    with pytest.raises(ValueError, match="colunas obrigatorias"):
        load_spreadsheet_index(source)


def test_raises_error_for_duplicate_keys(tmp_path: Path):
    source = tmp_path / "glosas.csv"
    source.write_text(
        (
            "numero_guia,senha,valor_glosa,justificativa\n"
            "123,999,10.5,Primeira\n"
            "123,999,12.0,Duplicada\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="chave duplicada"):
        load_spreadsheet_index(source)


def test_accepts_portuguese_friendly_headers(tmp_path: Path):
    source = tmp_path / "glosas.csv"
    source.write_text(
        "Numero da Guia,Senha,Valor da Glosa,Justificativa\n123,999,10,Sem cobertura\n",
        encoding="utf-8",
    )

    index = load_spreadsheet_index(source)

    assert "123|999" in index
    assert index["123|999"].valor_glosa == 10.0


def test_missing_columns_error_includes_found_headers(tmp_path: Path):
    source = tmp_path / "glosas.csv"
    source.write_text(
        "Guia,Senha,Justificativa\n123,999,Sem cobertura\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        load_spreadsheet_index(source)

    message = str(exc.value)
    assert "colunas obrigatorias" in message
    assert "Encontrado" in message


def test_accepts_real_amil_xlsx_headers_with_trailing_empty_columns(tmp_path: Path):
    source = tmp_path / "glosas_consolidadas_amil.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "Número do Protocolo",
            "Número do Lote",
            "Código do Beneficiário",
            "Número da Guia no Prestador",
            "Número da Guia Atribuído pela Operadora",
            "Senha",
            "Data Realização",
            "Código Procedimento",
            "Descrição Procedimento",
            "Código da Glosa da Guia",
            "Descrição Glosa",
            "Definições da glosa",
            "Valor Glosa (R$)",
            "Justificativa para recurso.",
            None,
            None,
        ]
    )
    ws.append(
        [
            "P100",
            "L200",
            "B300",
            "G123",
            "O999",
            "S456",
            "2026-02-26",
            "PROC1",
            "Descricao",
            "GL001",
            "Glosa",
            "Definicao",
            150.25,
            "Texto do recurso",
            None,
            None,
        ]
    )
    wb.save(source)
    wb.close()

    index = load_spreadsheet_index(source)

    assert "G123|S456" in index
    assert index["G123|S456"].valor_glosa == 150.25
    assert index["G123|S456"].justificativa == "Texto do recurso"
    assert index["G123|S456"].codigo_glosa == "GL001"
