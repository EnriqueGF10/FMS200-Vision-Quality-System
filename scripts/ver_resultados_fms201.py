"""
Ejecuta el algoritmo de FMS-201 sobre TODAS las imágenes etiquetadas
(data/Imagenes_FMS/FMS201/labels.csv) y muestra una tabla comparando el
resultado esperado (ground truth) con el que da el algoritmo.

También guarda la imagen de resultado de cada una en outputs/fms201/ (vía
procesar_una_imagen), para poder revisarlas todas visualmente si hace falta.

Uso:
    python scripts/ver_resultados_fms201.py
"""

import csv
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from scripts.ver_procesamiento_fms201 import procesar_una_imagen

RUTA_LABELS = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS201" / "labels.csv"


def main():
    with open(RUTA_LABELS, newline="") as f:
        filas = list(csv.DictReader(f))

    aciertos = 0
    print(f"{'imagen':<16} {'esperado':<20} {'obtenido':<20} resultado")
    print("-" * 70)

    for fila in filas:
        nombre = fila["filename"]
        # Las imagenes marcadas como caso_especial (p.ej. oclusion de mano)
        # tienen como resultado esperado ERROR, aunque la pieza este bien
        # colocada (ver decision en docs/bitacora_algoritmos.txt).
        esperado = "ERROR" if fila["caso_especial"] else fila["estado_terreno"]

        obtenido = procesar_una_imagen(nombre)

        acierto = obtenido == esperado
        aciertos += acierto
        marca = "OK" if acierto else "FALLO"
        print(f"{nombre:<16} {esperado:<20} {obtenido!s:<20} {marca}")

    print("-" * 70)
    print(f"Aciertos: {aciertos}/{len(filas)}")


if __name__ == "__main__":
    main()
