from app.config import AppSettings
from app.portal_client import PortalClient


class PortalClientSpy(PortalClient):
    def __init__(self, settings: AppSettings):
        super().__init__(settings)
        self.calls: list[tuple[str, str]] = []
        self.fail_primary_justificativa = False

    def _fill(self, selector: str, value: str) -> None:
        if (
            self.fail_primary_justificativa
            and selector == self.settings.selectors.justificativa
        ):
            raise RuntimeError("campo principal indisponivel")
        self.calls.append((selector, value))


def test_fill_1702_uses_secondary_justification_and_skips_value():
    settings = AppSettings()
    client = PortalClientSpy(settings)

    client.fill_current_guide(valor_glosa=10.0, justificativa="Texto", codigo_glosa="1702")

    assert client.calls == [(settings.selectors.justificativa_3052, "Texto")]


def test_fill_regular_glosa_uses_primary_and_value():
    settings = AppSettings()
    client = PortalClientSpy(settings)

    client.fill_current_guide(valor_glosa=10.0, justificativa="Texto", codigo_glosa="3030")

    assert client.calls == [
        (settings.selectors.justificativa, "Texto"),
        (settings.selectors.valor_glosa, "10,00"),
    ]


def test_fill_regular_glosa_falls_back_to_secondary_and_skips_value_when_primary_unavailable():
    settings = AppSettings()
    client = PortalClientSpy(settings)
    client.fail_primary_justificativa = True

    client.fill_current_guide(valor_glosa=10.0, justificativa="Texto", codigo_glosa="3030")

    assert client.calls == [(settings.selectors.justificativa_3052, "Texto")]
