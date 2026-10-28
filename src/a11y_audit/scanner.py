"""Escanea una página con axe-core dentro de Playwright.

Además de las reglas WCAG de axe, agrega una verificación propia:
que el atributo lang del <html> coincida con el idioma esperado de la página.

axe-core (MPL-2.0) viene incluido en vendor/, así que no se necesita Node.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files

from playwright.sync_api import BrowserContext

IMPACT_ORDER = ["critical", "serious", "moderate", "minor"]


@dataclass
class Violation:
    rule_id: str
    impact: str
    description: str
    help_url: str
    wcag: list[str]
    nodes: int


@dataclass
class PageResult:
    url: str
    expected_lang: str
    declared_lang: str
    violations: list[Violation] = field(default_factory=list)
    passes: int = 0
    error: str | None = None

    @property
    def lang_ok(self) -> bool:
        return self.declared_lang.lower().split("-")[0] == self.expected_lang


def wcag_criteria(tags: list[str]) -> list[str]:
    """Convierte tags de axe como 'wcag143' en criterios legibles como '1.4.3'."""
    out = []
    for t in tags:
        digits = t[4:]
        if t.startswith("wcag") and digits.isdigit() and len(digits) >= 3:
            out.append(f"{digits[0]}.{digits[1]}.{digits[2:]}")
    return out


@lru_cache(maxsize=1)
def load_axe_source() -> str:
    """Código de axe-core + configuración en español. Se lee una sola vez."""
    vendor = files("a11y_audit").joinpath("vendor")
    source = vendor.joinpath("axe.min.js").read_text(encoding="utf-8")
    locale = json.loads(vendor.joinpath("axe-es.json").read_text(encoding="utf-8"))
    return f"{source}\naxe.configure({{locale: {json.dumps(locale, ensure_ascii=False)}}});"


def axe_version() -> str:
    head = files("a11y_audit").joinpath("vendor", "axe.min.js").read_text(encoding="utf-8")[:200]
    marker = "axe v"
    return head.split(marker, 1)[1].split()[0] if marker in head else "desconocida"


def _parse(raw: dict) -> list[Violation]:
    violations = [
        Violation(
            rule_id=v["id"],
            impact=v.get("impact") or "minor",
            description=v["help"],
            help_url=v["helpUrl"],
            wcag=wcag_criteria(v["tags"]),
            nodes=len(v["nodes"]),
        )
        for v in raw["violations"]
    ]
    rank = {imp: i for i, imp in enumerate(IMPACT_ORDER)}
    return sorted(violations, key=lambda v: (rank.get(v.impact, 99), -v.nodes, v.rule_id))


def scan_page(
    context: BrowserContext,
    url: str,
    expected_lang: str,
    tags: list[str],
    timeout_ms: int = 45_000,
) -> PageResult:
    """Abre una pestaña nueva por escaneo para que no se arrastre estado entre sitios."""
    page = context.new_page()
    page.on("dialog", lambda d: d.dismiss())  # cierra alert/confirm que bloquearían la carga
    try:
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.add_script_tag(content=load_axe_source())
        raw = page.evaluate(
            "async (tags) => await axe.run(document, {runOnly: {type: 'tag', values: tags}})",
            tags,
        )
        declared = page.evaluate("document.documentElement.getAttribute('lang') || ''")
    except Exception as exc:  # noqa: BLE001 - se reporta como error de la página, no detiene la auditoría
        return PageResult(url=url, expected_lang=expected_lang, declared_lang="", error=str(exc).splitlines()[0])
    finally:
        page.close()

    return PageResult(
        url=url,
        expected_lang=expected_lang,
        declared_lang=declared,
        violations=_parse(raw),
        passes=len(raw["passes"]),
    )
