from app.ui import build_usage_instructions


def test_usage_instructions_contains_expected_steps():
    text = build_usage_instructions()

    assert "Procedimento para Digitacao de Lotes" in text
    assert "Acesso" in text
    assert "Importacao" in text
    assert "Execucao" in text
    assert "Passo 2" in text
