from app.models import SpreadsheetRow


def test_spreadsheet_key_normalization():
    row = SpreadsheetRow(
        numero_guia=" 123 ",
        senha=" 999 ",
        valor_glosa=10.5,
        justificativa="Ajuste",
    )
    assert row.key == "123|999"

