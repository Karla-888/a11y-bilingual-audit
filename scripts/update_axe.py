"""Actualiza axe-core en src/a11y_audit/vendor desde el registro de npm.

Uso:  python scripts/update_axe.py 4.10.2
Después corre las pruebas: algunas reglas cambian entre versiones.
"""

import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / "src" / "a11y_audit" / "vendor"
FILES = {
    "package/axe.min.js": "axe.min.js",
    "package/locales/es.json": "axe-es.json",
    "package/LICENSE": "LICENSE-axe-core.txt",
}


def main(version: str) -> None:
    meta = json.load(urllib.request.urlopen(f"https://registry.npmjs.org/axe-core/{version}"))
    data = urllib.request.urlopen(meta["dist"]["tarball"]).read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member, target in FILES.items():
            (VENDOR / target).write_bytes(tar.extractfile(member).read())
            print(f"Actualizado {target}")
    print(f"axe-core {version} listo. Corre: python -m pytest")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/update_axe.py <versión>   (ej. 4.10.2)")
    main(sys.argv[1])
