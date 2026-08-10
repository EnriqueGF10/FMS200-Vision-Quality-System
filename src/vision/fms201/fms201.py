"""
FMS-201: inspección de posición de la pieza.

La estación FMS-201 puede presentar tres situaciones:
  - PIEZA_OK            -> Pieza colocada correctamente
  - PIEZA_NOK           -> Pieza colocada al revés
  - ESTACION_VACIA      -> No hay pieza

Este fichero solo contiene el algoritmo de visión (funciones puras: entra una
imagen, sale un resultado). No abre cámara ni ventanas: eso vive en
scripts/ver_procesamiento_fms201.py, para poder testear el algoritmo contra
imágenes ya guardadas sin depender de hardware.
"""

import cv2 as cv

from src.vision.utils.preprocesamiento import (
    recortar_roi,
    convertir_a_grises,
    suavizar,
    binarizar,
    encontrar_contornos,
    encontrar_hueco_principal,
)


# Región de interés (ROI) fija: x1, y1, x2, y2 en píxeles.
#
# Igual que en el resto de estaciones: la cámara está fija y la pieza cae
# siempre en la misma zona (medido sobre varias imágenes: bloque en
# x=190-192, ancho~260-266, borde inferior estable ~360-367). Recortar antes
# de procesar evita tener que filtrar contornos de fondo por distancia al
# centro, como se hacía en la versión original de este fichero.
ROI = (150, 0, 470, 390)


# Área mínima (en píxeles²) para considerar que el contorno más grande
# dentro del ROI es la pieza, medida sobre las imágenes reales de FMS-201
# (excluyendo 3 capturas con interferencia de una mano sobre la pieza,
# ver docs/bitacora_algoritmos.txt, situación estudiada aparte por no ser
# controlable durante el funcionamiento normal de la estación):
#   - Pieza real (OK o invertida): área 53331 - 56802
#   - Estación vacía (ruido de fondo dentro del ROI): área 8887 - 8951
# El margen entre ambos casos es muy amplio (~44400 px²), así que basta un
# único umbral simple. Con interferencia de mano el margen puede reducirse
# drásticamente (hasta ~1000 px² en el peor caso observado, ver memoria),
# aunque la clasificación siguió siendo correcta en todos los casos.
AREA_MIN_PIEZA = 40000


def encontrar_contorno_pieza(contornos):
    """
    Devuelve el contorno de mayor área dentro del ROI si supera el umbral
    esperado para la pieza real, o None si no lo supera (estación vacía).

    Por qué no hace falta ya filtrar por distancia al centro: al trabajar
    sobre el ROI (no la imagen completa), el fondo/raíles que antes podían
    generar contornos grandes quedan fuera del recorte: el contorno más
    grande que puede aparecer aquí es la pieza, o nada.
    """
    mejor_contorno = max(contornos, key=cv.contourArea, default=None)
    if mejor_contorno is None or cv.contourArea(mejor_contorno) < AREA_MIN_PIEZA:
        return None
    return mejor_contorno


# Perímetro (en píxeles) del hueco central, medido sobre las imágenes con
# pieza real de FMS-201, excluyendo las mismas 3 capturas con interferencia
# de mano (ver docs/bitacora_algoritmos.txt):
#   - PIEZA_OK:           perímetro 141.3 - 146.1  (hueco pequeño, ovalado)
#   - PIEZA_NOK:          perímetro 236.9 - 267.6  (hueco en forma de "sonrisa")
# Los dos grupos no se solapan en ningún punto (hueco de ~90 px entre ambos),
# a diferencia del área del hueco, que sí solapaba ligeramente. Por eso se
# usa el perímetro y no el área para esta decisión.
PERIMETRO_MAX_PIEZA_OK = 200


def decidir_orientacion(hueco):
    """
    Decide si la pieza está bien colocada o invertida a partir de la forma
    de su hueco central, usando el perímetro del contorno.

    Por qué el perímetro y no el área: el área del hueco solapaba entre OK e
    invertida (una imagen OK y dos invertidas caían en la misma franja). El
    perímetro, en cambio, separa los dos grupos con un margen amplio: un
    hueco pequeño y ovalado (OK) tiene mucho menos perímetro que uno grande
    y con forma de "sonrisa" (invertida), aunque sus áreas sean parecidas.
    """
    perimetro = cv.arcLength(hueco, True)
    if perimetro < PERIMETRO_MAX_PIEZA_OK:
        return "PIEZA_OK"
    return "PIEZA_NOK"


def procesar(imagen_bgr):
    """
    Punto de entrada único del algoritmo de FMS-201: recibe una imagen (tal
    cual la da la cámara, en color BGR) y devuelve el estado de la estación.

    Devuelve un string con el estado: "PIEZA_OK", "PIEZA_NOK" o
    "ESTACION_VACIA".
    """
    recorte = recortar_roi(imagen_bgr, ROI)
    grises = convertir_a_grises(recorte)
    suave = suavizar(grises)
    binaria = binarizar(suave)
    contornos, jerarquia = encontrar_contornos(binaria)

    pieza = encontrar_contorno_pieza(contornos)
    if pieza is None:
        return "ESTACION_VACIA"

    hueco = encontrar_hueco_principal(contornos, jerarquia, pieza)
    return decidir_orientacion(hueco)
