"""
Ejecuta el algoritmo de FMS-205 sobre TODAS las imágenes etiquetadas
(data/Imagenes_FMS/FMS205/labels.csv) y muestra una tabla comparando el
resultado esperado (ground truth) con el que da el algoritmo.

Uso:
    python scripts/ver_resultados_fms205.py
"""

import csv
import sys
from pathlib import Path

import cv2 as cv

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.fms205.fms205 import procesar

RUTA_IMAGENES = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS205"
RUTA_LABELS = RUTA_IMAGENES / "labels.csv"


def main():
    with open(RUTA_LABELS, newline="") as f:
        filas = list(csv.DictReader(f))

    aciertos = 0
    fallos = []

    for fila in filas:
        nombre = fila["filename"]
        esperado = fila["estado_terreno"]

        imagen = cv.imread(str(RUTA_IMAGENES / nombre))
        obtenido = procesar(imagen)

        acierto = obtenido == esperado
        aciertos += acierto
        if not acierto:
            fallos.append((nombre, esperado, obtenido))

    print(f"Aciertos: {aciertos}/{len(filas)}")
    if fallos:
        print("\nFallos:")
        for nombre, esperado, obtenido in fallos:
            print(f"  {nombre}: esperado={esperado} obtenido={obtenido}")


if __name__ == "__main__":
    main()
