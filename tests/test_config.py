"""Pruebas de validación de configuración (no requieren navegador)."""

import pytest

from a11y_audit.config import ConfigError, load_config


def write(tmp_path, text):
    p = tmp_path / "sites.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_config_valida_con_valores_por_defecto(tmp_path):
    cfg = load_config(write(tmp_path, "sites:\n  - {name: A, en: 'https://a.gov', es: 'https://a.gov/es'}\n"))
    assert cfg.sites[0].en == "https://a.gov"
    assert cfg.settings.delay_s == 2.0
    assert cfg.settings.min_score is None


def test_rutas_locales_se_convierten_a_file_uri(tmp_path):
    (tmp_path / "en.html").write_text("<html></html>")
    (tmp_path / "es.html").write_text("<html></html>")
    cfg = load_config(write(tmp_path, "sites:\n  - {name: A, en: en.html, es: es.html}\n"), base_dir=tmp_path)
    assert cfg.sites[0].en.startswith("file://")


@pytest.mark.parametrize(
    ("text", "mensaje"),
    [
        ("sites: []\n", "no tiene sitios"),
        ("sites:\n  - {name: A, en: 'https://a.gov'}\n", "es"),
        (
            "sites:\n  - {name: A, en: 'https://a', es: 'https://b'}\n  - {name: A, en: 'https://c', es: 'https://d'}\n",
            "repetido",
        ),
        ("sites:\n  - {name: A, en: no-existe.html, es: 'https://b'}\n", "No existe"),
        ("settings: {min_score: 150}\nsites:\n  - {name: A, en: 'https://a', es: 'https://b'}\n", "min_score"),
        ("sites: [\n", "YAML"),
    ],
)
def test_errores_de_configuracion_son_claros(tmp_path, text, mensaje):
    with pytest.raises(ConfigError, match=mensaje):
        load_config(write(tmp_path, text), base_dir=tmp_path)


def test_archivo_inexistente(tmp_path):
    with pytest.raises(ConfigError, match="No existe el archivo de configuración"):
        load_config(tmp_path / "nada.yaml")
