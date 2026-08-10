"""
Script de apoyo para VER paso a paso qué le hace el algoritmo de FMS-201 a
una imagen concreta. No forma parte del sistema final: es una herramienta de
desarrollo para ir comprobando cada paso del algoritmo mientras lo construimos.

Uso:
    python scripts/ver_procesamiento_fms201.py captura_1.jpg
"""

import sys
from pathlib import Path

import cv2 as cv

# Añadimos la raíz del repo al path para poder importar "src...." aunque
# este script no esté dentro del paquete src/.
RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.utils.preprocesamiento import (
    convertir_a_grises,
    suavizar,
    binarizar,
    encontrar_contornos,
    encontrar_hueco_principal,
)
from src.vision.fms201.fms201 import (
    ROI,
    recortar_roi,
    encontrar_contorno_pieza,
    procesar,
)

CARPETA_IMAGENES = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS201"
CARPETA_SALIDA = RAIZ_REPO / "outputs" / "fms201"


def procesar_una_imagen(nombre_imagen):
    ruta_imagen = CARPETA_IMAGENES / nombre_imagen
    imagen = cv.imread(str(ruta_imagen))
    if imagen is None:
        print(f"No se pudo leer la imagen: {ruta_imagen}")
        return None

    recorte = recortar_roi(imagen, ROI)
    grises = convertir_a_grises(recorte)
    suave = suavizar(grises)
    binaria = binarizar(suave)
    contornos, jerarquia = encontrar_contornos(binaria)

    # Subcarpeta por imagen para no mezclar resultados al probar varias.
    prefijo = Path(nombre_imagen).stem
    carpeta = CARPETA_SALIDA / prefijo
    carpeta.mkdir(parents=True, exist_ok=True)

    cv.imwrite(str(carpeta / "1_original.png"), imagen)
    cv.imwrite(str(carpeta / "2_grises.png"), grises)
    cv.imwrite(str(carpeta / "3_binaria.png"), binaria)

    # El estado se calcula con procesar() (la funcion "oficial" del
    # algoritmo), no reimplementando la decision aqui: asi este script y el
    # algoritmo real nunca pueden acabar dando respuestas distintas.
    estado = procesar(imagen)

    # Volvemos a buscar pieza/hueco solo para DIBUJARLOS en la imagen de
    # depuracion (procesar() ya hizo este mismo trabajo por dentro, pero no
    # devuelve los contornos: su interfaz de cara al resto del sistema debe
    # ser solo "imagen -> estado").
    resultado = recorte.copy()
    pieza = encontrar_contorno_pieza(contornos)
    if pieza is not None:
        cv.drawContours(resultado, [pieza], -1, (255, 255, 0), 2)
        hueco = encontrar_hueco_principal(contornos, jerarquia, pieza)
        if hueco is not None:
            cv.drawContours(resultado, [hueco], -1, (0, 0, 255), 2)
            perimetro = cv.arcLength(hueco, True)
            cv.putText(resultado, f"perimetro hueco: {perimetro:.0f}", (10, 70),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv.putText(resultado, f"ESTADO: {estado}", (10, 30),
               cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv.imwrite(str(carpeta / "5_resultado.png"), resultado)

    return estado


def main():
    if len(sys.argv) > 1:
        nombres = sys.argv[1:]
    else:
        # Por defecto probamos un caso de cada tipo: OK, invertida y vacia.
        nombres = ["captura_1.jpg", "captura_20.jpg", "captura_35.jpg"]

    for nombre in nombres:
        estado = procesar_una_imagen(nombre)
        print(f"[{nombre}] estado detectado: {estado}")
        print(f"[{nombre}] resultados guardados en: {CARPETA_SALIDA / Path(nombre).stem}")


if __name__ == "__main__":
    main()
