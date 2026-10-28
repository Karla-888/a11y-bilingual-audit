"""Carga y valida la configuración (config/sites.yaml).

Todos los errores de configuración se lanzan como ConfigError con un mensaje claro,
para que la CLI los muestre sin traceback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]


class ConfigError(ValueError):
    """La configuración no es válida."""


@dataclass(frozen=True)
class Site:
    name: str
    en: str
    es: str


@dataclass(frozen=True)
class Settings:
    wcag_tags: list[str] = field(default_factory=lambda: list(DEFAULT_TAGS))
    timeout_ms: int = 45_000  # tiempo máximo de carga por página
    delay_s: float = 2.0  # pausa entre páginas para no saturar al servidor
    min_score: int | None = None  # si se define, la CLI falla cuando un puntaje queda abajo


@dataclass(frozen=True)
class AuditConfig:
    sites: list[Site]
    settings: Settings = field(default_factory=Settings)


def to_url(target: str, base_dir: Path) -> str:
    """Convierte rutas locales en file:// y deja las URLs http(s) igual."""
    if target.startswith(("http://", "https://", "file://")):
        return target
    path = (base_dir / target).resolve()
    if not path.exists():
        raise ConfigError(f"No existe el archivo local: {path}")
    return path.as_uri()


def _settings(raw: dict) -> Settings:
    if not isinstance(raw, dict):
        raise ConfigError("'settings' debe ser un objeto con claves.")
    s = Settings(
        wcag_tags=raw.get("wcag_tags") or list(DEFAULT_TAGS),
        timeout_ms=int(raw.get("timeout_ms", 45_000)),
        delay_s=float(raw.get("delay_s", 2.0)),
        min_score=None if raw.get("min_score") is None else int(raw["min_score"]),
    )
    if s.timeout_ms <= 0 or s.delay_s < 0:
        raise ConfigError("timeout_ms debe ser mayor a 0 y delay_s no puede ser negativo.")
    if s.min_score is not None and not 0 <= s.min_score <= 100:
        raise ConfigError("min_score debe estar entre 0 y 100.")
    return s


def load_config(path: str | Path, base_dir: Path | None = None) -> AuditConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"No existe el archivo de configuración: {path}")
    base_dir = base_dir or Path.cwd()

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} no es un YAML válido: {exc}") from exc

    raw_sites = data.get("sites") or []
    if not raw_sites:
        raise ConfigError(f"{path} no tiene sitios en la clave 'sites'.")

    sites: list[Site] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_sites, start=1):
        missing = [k for k in ("name", "en", "es") if not (raw or {}).get(k)]
        if missing:
            raise ConfigError(f"Sitio #{i} sin campos obligatorios: {', '.join(missing)}")
        if raw["name"] in seen:
            raise ConfigError(f"Nombre de sitio repetido: {raw['name']}")
        seen.add(raw["name"])
        sites.append(Site(name=raw["name"], en=to_url(raw["en"], base_dir), es=to_url(raw["es"], base_dir)))

    return AuditConfig(sites=sites, settings=_settings(data.get("settings") or {}))
