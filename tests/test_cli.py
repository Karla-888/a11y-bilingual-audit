"""Prueba de punta a punta: config -> navegador -> reportes -> código de salida."""

import csv
import json
from pathlib import Path

from a11y_audit.cli import EXIT_CONFIG, EXIT_FAIL, EXIT_OK, main

FIXTURES = Path(__file__).parent / "fixtures"


def make_config(tmp_path, min_score="null"):
    p = tmp_path / "sites.yaml"
    p.write_text(
        f"settings: {{delay_s: 0, min_score: {min_score}}}\n"
        f"sites:\n  - {{name: Demo, en: '{(FIXTURES / 'site_en.html').as_uri()}', "
        f"es: '{(FIXTURES / 'site_es.html').as_uri()}'}}\n",
        encoding="utf-8",
    )
    return p


def run(tmp_path, *extra, min_score="null"):
    out = tmp_path / "reports"
    code = main(["--config", str(make_config(tmp_path, min_score)), "--out", str(out), *extra])
    run_dir = next(out.iterdir()) if out.exists() else None
    return code, run_dir


def test_genera_los_tres_reportes(tmp_path):
    code, run_dir = run(tmp_path)
    assert code == EXIT_OK
    assert {p.name for p in run_dir.iterdir()} == {"reporte.html", "resultados.json", "hallazgos.csv"}

    data = json.loads((run_dir / "resultados.json").read_text(encoding="utf-8"))
    assert data[0]["puntaje_en"] == 100
    assert data[0]["brecha"] > 0

    with (run_dir / "hallazgos.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows and all(r["idioma"] == "es" for r in rows)

    html = (run_dir / "reporte.html").read_text(encoding="utf-8")
    assert "la versión en español es menos accesible" in html


def test_min_score_hace_fallar_la_cli(tmp_path):
    code, _ = run(tmp_path, min_score=80)
    assert code == EXIT_FAIL


def test_argumento_min_score_sobrescribe_yaml(tmp_path):
    code, _ = run(tmp_path, "--min-score", "0", min_score=80)
    assert code == EXIT_OK


def test_config_invalida_devuelve_codigo_2(tmp_path):
    assert main(["--config", str(tmp_path / "nada.yaml")]) == EXIT_CONFIG
