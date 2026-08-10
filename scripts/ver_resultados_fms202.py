"""
Ejecuta el algoritmo de FMS-202 sobre TODAS las imágenes etiquetadas
(data/Imagenes_FMS/FMS202/labels.csv) y muestra una tabla comparando el
resultado esperado (ground truth) con el que da el algoritmo.

Uso:
    python scripts/ver_resultados_fms202.py
"""

import csv
import sys
from pathlib import Path

import cv2 as cv

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.fms202.fms202 import procesar

RUTA_IMAGENES = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS202"
RUTA_LABELS = RUTA_IMAGENES / "labels.csv"


def main():
    with open(RUTA_LABELS, newline="") as f:
        filas = list(csv.DictReader(f))

    aciertos = 0
    print(f"{'imagen':<16} {'esperado':<24} {'obtenido':<24} resultado")
    print("-" * 78)

    for fila in filas:
        nombre = fila["filename"]
        esperado = fila["estado_terreno"]

        imagen = cv.imread(str(RUTA_IMAGENES / nombre))
        obtenido = procesar(imagen)

        acierto = obtenido == esperado
        aciertos += acierto
        marca = "OK" if acierto else "FALLO"
        print(f"{nombre:<16} {esperado:<24} {obtenido!s:<24} {marca}")

    print("-" * 78)
    print(f"Aciertos: {aciertos}/{len(filas)}")


if __name__ == "__main__":
    main()
