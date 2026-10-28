"""Genera los reportes: HTML (para el cliente), JSON y CSV (para análisis)."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .scanner import axe_version
from .scoring import SiteComparison

IMPACT_LABELS = {"critical": "Crítico", "serious": "Grave", "moderate": "Moderado", "minor": "Menor"}


def write_json(comparisons: list[SiteComparison], out: Path) -> Path:
    path = out / "resultados.json"
    data = [
        {
            "sitio": c.name,
            "puntaje_en": c.en_score,
            "puntaje_es": c.es_score,
            "brecha": c.gap,
            "reglas_solo_es": c.es_only_rules,
            "en": asdict(c.en),
            "es": asdict(c.es),
        }
        for c in comparisons
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_csv(comparisons: list[SiteComparison], out: Path) -> Path:
    path = out / "hallazgos.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig abre bien en Excel
        w = csv.writer(f)
        w.writerow(["sitio", "idioma", "url", "regla", "severidad", "criterios_wcag", "elementos", "descripcion"])
        for c in comparisons:
            for lang, res in (("en", c.en), ("es", c.es)):
                for v in res.violations:
                    w.writerow([c.name, lang, res.url, v.rule_id, v.impact, " ".join(v.wcag), v.nodes, v.description])
    return path


def write_html(comparisons: list[SiteComparison], out: Path, tags: list[str]) -> Path:
    env = Environment(loader=PackageLoader("a11y_audit", "templates"), autoescape=select_autoescape(["html"]))
    env.filters["impact_label"] = lambda i: IMPACT_LABELS.get(i, i)
    template = env.get_template("report.html")

    scored = [c for c in comparisons if c.gap is not None]
    summary = {
        "sitios": len(comparisons),
        "es_peor": sum(1 for c in scored if c.gap > 0),
        "brecha_promedio": round(sum(c.gap for c in scored) / len(scored), 1) if scored else None,
    }

    html = template.render(
        comparisons=comparisons,
        summary=summary,
        tags=", ".join(tags),
        axe=axe_version(),
        generated=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
    path = out / "reporte.html"
    path.write_text(html, encoding="utf-8")
    return path
