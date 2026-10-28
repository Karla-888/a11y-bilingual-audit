"""Pruebas del escáner contra páginas locales con fallas conocidas."""

from a11y_audit.scanner import axe_version, scan_page, wcag_criteria

TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]


def test_wcag_criteria_formatea_tags():
    assert wcag_criteria(["wcag2aa", "wcag143", "wcag1412", "best-practice"]) == ["1.4.3", "1.4.12"]


def test_axe_incluido_en_el_paquete():
    assert axe_version().startswith("4.")


def test_pagina_en_no_tiene_violaciones(context, fixture_url):
    result = scan_page(context, fixture_url("site_en.html"), "en", TAGS)
    assert result.error is None
    assert result.violations == []
    assert result.lang_ok


def test_pagina_es_detecta_fallas_conocidas(context, fixture_url):
    result = scan_page(context, fixture_url("site_es.html"), "es", TAGS)
    rules = {v.rule_id for v in result.violations}
    assert {"image-alt", "label", "button-name", "color-contrast"} <= rules
    assert not result.lang_ok  # declara lang="en" en una página en español


def test_descripciones_en_espanol(context, fixture_url):
    result = scan_page(context, fixture_url("site_es.html"), "es", TAGS)
    alt = next(v for v in result.violations if v.rule_id == "image-alt")
    assert "imágenes" in alt.description.lower()


def test_violaciones_ordenadas_por_severidad(context, fixture_url):
    result = scan_page(context, fixture_url("site_es.html"), "es", TAGS)
    order = ["critical", "serious", "moderate", "minor"]
    ranks = [order.index(v.impact) for v in result.violations]
    assert ranks == sorted(ranks)


def test_url_invalida_no_rompe_la_auditoria(context):
    result = scan_page(context, "http://127.0.0.1:9/no-existe", "en", TAGS, timeout_ms=5_000)
    assert result.error is not None
    assert "\n" not in result.error


def test_cada_escaneo_cierra_su_pestana(context, fixture_url):
    scan_page(context, fixture_url("site_en.html"), "en", TAGS)
    scan_page(context, fixture_url("site_es.html"), "es", TAGS)
    assert context.pages == []
