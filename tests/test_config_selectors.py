from app.config import AppSettings


def test_default_selectors_match_amil_portal_ids():
    selectors = AppSettings().selectors

    assert selectors.numero_guia == "//*[@id='num_guia_operadora_recurso']"
    assert selectors.senha == "//*[@id='senha']"
    assert selectors.total_guias == "//*[@id='guia_final']"
    assert selectors.valor_glosa == "//*[@id='valor_recursado']"
    assert selectors.justificativa == "//*[@id='justificativa_prestador_procedimento']"
    assert selectors.justificativa_3052 == "//*[@id='justificativa_guia']"
    assert selectors.proxima_guia == "//*[@id='btn_guia_posterior']"


def test_lote_and_protocolo_are_optional_by_default():
    selectors = AppSettings().selectors
    assert selectors.lote == ""
    assert selectors.protocolo == ""


def test_default_portal_url_is_amil_credenciado():
    settings = AppSettings()
    assert settings.portal_url == "https://credenciado.amil.com.br/"
