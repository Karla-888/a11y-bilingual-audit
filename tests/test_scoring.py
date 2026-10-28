"""Pruebas del puntaje y la comparación EN vs ES (no requieren navegador)."""

from a11y_audit.scanner import PageResult, Violation
from a11y_audit.scoring import SiteComparison, score


def make(lang, declared, violations=()):
    return PageResult(url="x", expected_lang=lang, declared_lang=declared, violations=list(violations))


def v(rule, impact, nodes=1):
    return Violation(rule, impact, "desc", "url", ["1.1.1"], nodes)


def test_sin_hallazgos_es_100():
    assert score(make("en", "en")) == 100


def test_penaliza_por_severidad_y_elementos():
    assert score(make("en", "en", [v("image-alt", "critical", 2), v("region", "moderate")])) == 78


def test_penaliza_lang_incorrecto():
    assert score(make("es", "en")) == 90
    assert score(make("es", "es-MX")) == 100


def test_puntaje_nunca_es_negativo():
    assert score(make("en", "en", [v("x", "critical", 50)])) == 0


def test_error_de_carga_no_tiene_puntaje():
    r = make("en", "")
    r.error = "timeout"
    assert score(r) is None


def test_brecha_y_reglas_solo_en_espanol():
    c = SiteComparison(
        "demo",
        make("en", "en", [v("region", "moderate")]),
        make("es", "es", [v("region", "moderate"), v("image-alt", "critical")]),
    )
    assert c.gap == 10
    assert c.es_only_rules == ["image-alt"]
