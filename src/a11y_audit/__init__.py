"""Auditor de accesibilidad bilingüe (EN/ES) basado en Playwright + axe-core."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("a11y-bilingual-audit")  # única fuente de verdad: pyproject.toml
except PackageNotFoundError:  # corriendo sin instalar
    __version__ = "0.0.0-dev"
