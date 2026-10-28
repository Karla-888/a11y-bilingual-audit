"""Línea de comandos.

Uso:  a11y-audit --config config/sites.yaml

Códigos de salida (útiles en CI):
  0  auditoría completa y todos los puntajes cumplen min_score
  1  algún puntaje quedó abajo de min_score o alguna página no cargó
  2  error de configuración
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from . import __version__
from .config import AuditConfig, ConfigError, load_config
from .report import write_csv, write_html, write_json
from .scanner import scan_page
from .scoring import SiteComparison

log = logging.getLogger("a11y_audit")

EXIT_OK, EXIT_FAIL, EXIT_CONFIG = 0, 1, 2
USER_AGENT = f"a11y-bilingual-audit/{__version__} (+https://github.com/Karla-888/a11y-bilingual-audit)"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="a11y-audit", description="Auditoría de accesibilidad WCAG que compara EN vs ES.")
    p.add_argument("--config", default="config/sites.yaml", help="archivo YAML con los sitios")
    p.add_argument("--out", default="reports", help="carpeta donde se guardan los reportes")
    p.add_argument("--min-score", type=int, help="puntaje mínimo aceptado (sobrescribe el YAML)")
    p.add_argument("--headed", action="store_true", help="mostrar el navegador (para depurar)")
    p.add_argument("-v", "--verbose", action="store_true", help="mostrar más detalle")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p.parse_args(argv)


def audit(cfg: AuditConfig, headed: bool = False) -> list[SiteComparison]:
    s = cfg.settings
    comparisons: list[SiteComparison] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        try:
            # bypass_csp: permite inyectar axe en sitios con Content-Security-Policy estricta
            context = browser.new_context(
                bypass_csp=True, user_agent=USER_AGENT, viewport={"width": 1280, "height": 900}
            )
            for i, site in enumerate(cfg.sites, start=1):
                log.info("[%d/%d] %s", i, len(cfg.sites), site.name)
                en = scan_page(context, site.en, "en", s.wcag_tags, s.timeout_ms)
                time.sleep(s.delay_s)
                es = scan_page(context, site.es, "es", s.wcag_tags, s.timeout_ms)
                c = SiteComparison(site.name, en, es)
                comparisons.append(c)
                for res in (en, es):
                    if res.error:
                        log.warning("  No cargó %s: %s", res.url, res.error)
                log.info("  EN %s | ES %s | brecha %s", c.en_score, c.es_score, c.gap)
                if i < len(cfg.sites):
                    time.sleep(s.delay_s)
        finally:
            browser.close()
    return comparisons


def failures(comparisons: list[SiteComparison], min_score: int | None) -> list[str]:
    out = []
    for c in comparisons:
        for lang, res, sc in (("EN", c.en, c.en_score), ("ES", c.es, c.es_score)):
            if res.error:
                out.append(f"{c.name} {lang}: la página no cargó")
            elif min_score is not None and sc < min_score:
                out.append(f"{c.name} {lang}: {sc} < {min_score}")
    return out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        log.error("Error de configuración: %s", exc)
        return EXIT_CONFIG

    try:
        comparisons = audit(cfg, args.headed)
    except PlaywrightError as exc:
        log.error("No se pudo iniciar el navegador. ¿Ya corriste 'python -m playwright install chromium'?\n%s", exc)
        return EXIT_FAIL

    out = Path(args.out) / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    for path in (
        write_html(comparisons, out, cfg.settings.wcag_tags),
        write_json(comparisons, out),
        write_csv(comparisons, out),
    ):
        log.info("Generado: %s", path)

    min_score = args.min_score if args.min_score is not None else cfg.settings.min_score
    problems = failures(comparisons, min_score)
    for p in problems:
        log.warning("FALLA %s", p)
    return EXIT_FAIL if problems else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
