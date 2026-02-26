from app.portal_client import resolve_selector
from app.portal_client import find_locator_in_pages
from app.portal_client import is_glosa_3052
from app.portal_client import is_glosa_1702
from app.portal_client import requires_secondary_justificativa
from app.portal_client import resolve_justificativa_selector
from app.config import AppSettings


def test_resolve_selector_converts_xpath():
    assert (
        resolve_selector("//*[@id='guia_final']")
        == "xpath=//*[@id='guia_final']"
    )


def test_resolve_selector_keeps_css_selector():
    assert resolve_selector("#guia_final") == "#guia_final"


class _FakeLocator:
    def __init__(self, total: int):
        self._total = total
        self.first = self

    def count(self):
        return self._total


class _FakeFrame:
    def __init__(self, selectors):
        self._selectors = selectors

    def locator(self, selector):
        return _FakeLocator(self._selectors.get(selector, 0))


class _FakePage:
    def __init__(self, frames):
        self.frames = frames


def test_find_locator_in_pages_finds_selector_inside_iframe():
    selector = "xpath=//*[@id='guia_final']"
    page = _FakePage(
        frames=[
            _FakeFrame({}),
            _FakeFrame({selector: 1}),
        ]
    )

    locator, selected_page = find_locator_in_pages([page], selector)

    assert locator is not None
    assert selected_page is page


def test_find_locator_in_pages_scans_multiple_pages():
    selector = "xpath=//*[@id='guia_final']"
    page1 = _FakePage(frames=[_FakeFrame({})])
    page2 = _FakePage(frames=[_FakeFrame({selector: 1})])

    locator, selected_page = find_locator_in_pages([page1, page2], selector)

    assert locator is not None
    assert selected_page is page2


def test_is_glosa_3052_accepts_plain_or_formatted_code():
    assert is_glosa_3052("3052")
    assert is_glosa_3052("3052 - divergencia")
    assert not is_glosa_3052("3030")


def test_is_glosa_1702_accepts_plain_or_formatted_code():
    assert is_glosa_1702("1702")
    assert is_glosa_1702("1702 - pacote")
    assert not is_glosa_1702("3030")


def test_requires_secondary_justificativa_for_3052_and_1702():
    assert requires_secondary_justificativa("3052")
    assert requires_secondary_justificativa("1702")
    assert not requires_secondary_justificativa("3030")


def test_resolve_justificativa_selector_uses_special_xpath_for_3052_and_1702():
    settings = AppSettings()
    assert (
        resolve_justificativa_selector("3052", settings)
        == "//*[@id='justificativa_guia']"
    )
    assert (
        resolve_justificativa_selector("1702", settings)
        == "//*[@id='justificativa_guia']"
    )
    assert (
        resolve_justificativa_selector("3030", settings)
        == "//*[@id='justificativa_prestador_procedimento']"
    )
