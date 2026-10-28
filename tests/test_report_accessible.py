"""El reporte de accesibilidad debe ser accesible: lo auditamos con su propio motor."""

from a11y_audit.report import write_html
from a11y_audit.scanner import PageResult, Violation, scan_page
from a11y_audit.scoring import SiteComparison

TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]


def test_reporte_html_sin_violaciones(tmp_path, context):
    en = PageResult(url="https://a.gov", expected_lang="en", declared_lang="en")
    es = PageResult(
        url="https://a.gov/es",
        expected_lang="es",
        declared_lang="en",
        violations=[
            Violation("image-alt", "critical", "Las imágenes deben tener texto alternativo", "#", ["1.1.1"], 2)
        ],
    )
    failed = PageResult(url="https://b.gov", expected_lang="en", declared_lang="", error="timeout")
    comparisons = [SiteComparison("Ciudad A", en, es), SiteComparison("Ciudad B", failed, es)]

    report = write_html(comparisons, tmp_path, TAGS)
    # Abre los <details> para que axe audite también las tablas de hallazgos
    report.write_text(report.read_text(encoding="utf-8").replace("<details>", "<details open>"), encoding="utf-8")

    result = scan_page(context, report.as_uri(), "es", TAGS)
    assert result.violations == [], [v.rule_id for v in result.violations]
    assert result.lang_ok
