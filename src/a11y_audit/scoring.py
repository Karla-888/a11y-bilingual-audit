"""Puntaje de accesibilidad y comparación EN vs ES."""

from __future__ import annotations

from dataclasses import dataclass

from .scanner import PageResult

# Peso por severidad de axe-core. Se multiplica por el número de elementos afectados.
IMPACT_WEIGHTS = {"critical": 10, "serious": 5, "moderate": 2, "minor": 1}
LANG_MISMATCH_PENALTY = 10  # lang incorrecto: el lector de pantalla pronuncia mal todo


def penalty(result: PageResult) -> int:
    total = sum(IMPACT_WEIGHTS.get(v.impact, 1) * v.nodes for v in result.violations)
    if not result.lang_ok:
        total += LANG_MISMATCH_PENALTY
    return total


def score(result: PageResult) -> int | None:
    """0 a 100, donde 100 es sin hallazgos. None si la página no cargó."""
    if result.error:
        return None
    return max(0, 100 - penalty(result))


@dataclass
class SiteComparison:
    name: str
    en: PageResult
    es: PageResult

    @property
    def en_score(self) -> int | None:
        return score(self.en)

    @property
    def es_score(self) -> int | None:
        return score(self.es)

    @property
    def gap(self) -> int | None:
        """Positivo = el español está peor que el inglés."""
        if self.en_score is None or self.es_score is None:
            return None
        return self.en_score - self.es_score

    @property
    def es_only_rules(self) -> list[str]:
        en_ids = {v.rule_id for v in self.en.violations}
        return sorted({v.rule_id for v in self.es.violations} - en_ids)
