"""
Ejecuta el algoritmo de FMS-206 sobre TODAS las imágenes etiquetadas
(data/Imagenes_FMS/FMS206/labels.csv) y muestra una tabla comparando el
resultado esperado (ground truth) con el que da el algoritmo.

Uso:
    python scripts/ver_resultados_fms206.py
"""

import csv
import sys
from pathlib import Path

import cv2 as cv

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.fms206.fms206 import procesar

RUTA_IMAGENES = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS206"
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
            fallos.append((nombre, esperado, obtenido, fila["num_tornillos"]))

    print(f"Aciertos: {aciertos}/{len(filas)}")
    if fallos:
        print("\nFallos:")
        for nombre, esperado, obtenido, num in fallos:
            print(f"  {nombre}: esperado={esperado} (num_tornillos={num}) obtenido={obtenido}")


if __name__ == "__main__":
    main()
