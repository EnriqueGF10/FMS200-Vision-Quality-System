"""
Script de apoyo para VER paso a paso qué le hace el algoritmo de FMS-202 a
una imagen concreta. No forma parte del sistema final: es una herramienta de
desarrollo para ir comprobando cada paso del algoritmo mientras lo construimos.

Uso:
    python scripts/ver_procesamiento_fms202.py captura_35.jpg
"""

import sys
from pathlib import Path

import cv2 as cv

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.fms202.fms202 import ROI, recortar_roi

CARPETA_IMAGENES = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS202"
CARPETA_SALIDA = RAIZ_REPO / "outputs" / "fms202"


def procesar_una_imagen(nombre_imagen):
    ruta_imagen = CARPETA_IMAGENES / nombre_imagen
    imagen = cv.imread(str(ruta_imagen))
    if imagen is None:
        print(f"No se pudo leer la imagen: {ruta_imagen}")
        return None

    recorte = recortar_roi(imagen, ROI)

    prefijo = Path(nombre_imagen).stem
    carpeta = CARPETA_SALIDA / prefijo
    carpeta.mkdir(parents=True, exist_ok=True)

    cv.imwrite(str(carpeta / "1_original.png"), imagen)
    cv.imwrite(str(carpeta / "2_roi.png"), recorte)

    return None  # todavia no hay estado: solo estamos viendo el ROI


def main():
    if len(sys.argv) > 1:
        nombres = sys.argv[1:]
    else:
        # Un caso de cada categoria: sin pieza, negro, bolas.
        nombres = ["captura_1.jpg", "captura_35.jpg", "captura_78.jpg"]

    for nombre in nombres:
        procesar_una_imagen(nombre)
        print(f"[{nombre}] resultados guardados en: {CARPETA_SALIDA / Path(nombre).stem}")


if __name__ == "__main__":
    main()
