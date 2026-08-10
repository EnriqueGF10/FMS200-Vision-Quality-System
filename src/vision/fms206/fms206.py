"""
FMS-206: comprobación de los 4 tornillos.

FMS-206 recibe la pieza de las estaciones anteriores y le inserta hasta 4
tornillos, uno en cada esquina. El objetivo es exclusivamente comprobar que
están los 4: cualquier cantidad inferior se considera no válida.

  - COMPLETO   -> los 4 tornillos presentes
  - INCOMPLETO -> falta al menos uno (independientemente de cuál o cuántos)

Este fichero solo contiene el algoritmo de visión (funciones puras: entra
una imagen, sale un resultado). No abre cámara ni ventanas.
"""

import numpy as np
import cv2 as cv

from src.vision.utils.preprocesamiento import recortar_roi, convertir_a_grises, suavizar


# Región de interés (ROI) fija: x1, y1, x2, y2 en píxeles.
#
# Medido sobre 5 imágenes con distinto número de tornillos: el bloque cae
# siempre en x=170-171, ancho~278-280; el borde inferior es muy estable
# (~318-319), el superior varía por el cable que a veces se funde con el
# contorno. Se recorta con margen amplio para no cortar ningún tornillo que
# sobresalga.
ROI = (140, 0, 470, 370)


# Las 4 posiciones de tornillo, ya dentro del recorte del ROI.
#
# Por qué no basta con el centro del taladro vacío: un tornillo sobresale
# hacia la cámara, y como la cámara mira la pieza en ángulo (no en vertical
# perfecta), un tornillo puesto aparece desplazado en la imagen respecto al
# mismo taladro vacío (~10-18 px hacia arriba, efecto de paralaje). Cada
# punto de aquí está centrado a medio camino entre ambas posiciones, con un
# radio (30 px) generoso para cubrir el taladro vacío Y el tornillo
# desplazado sin necesitar precisión de un solo píxel.
#
# umbral_gradiente: valor de corte entre "vacío" y "con tornillo", medido a
# mitad de camino entre el máximo observado en vacío y el mínimo observado
# con tornillo (ver docs/bitacora_algoritmos.txt para las 13+ imágenes de
# referencia usadas en cada posición):
#   top:    vacío ≤43.4 / tornillo ≥53.3  -> umbral 48
#   right:  vacío ≤47.6 / tornillo ≥63.7  -> umbral 56
#   bottom: vacío ≤49.9 / tornillo ≥69.7  -> umbral 60
#   left:   vacío ≤41.7 / tornillo ≥44.8  -> umbral 43 (margen más ajustado,
#           es la posición más difícil de las 4, ver bitácora)
POSICIONES_TORNILLO = {
    "arriba": {"punto": (171, 65), "radio": 30, "umbral_gradiente": 48},
    "derecha": {"punto": (277, 142), "radio": 30, "umbral_gradiente": 56},
    "abajo": {"punto": (170, 228), "radio": 30, "umbral_gradiente": 60},
    "izquierda": {"punto": (70, 145), "radio": 30, "umbral_gradiente": 43},
}


def medir_gradiente_en_punto(grises, punto, radio):
    """
    Mide la magnitud media del gradiente (Sobel) dentro de un círculo.

    Por qué el gradiente: un taladro vacío es una cavidad curva que refleja
    la luz de forma gradual y suave (gradiente bajo, mismo razonamiento que
    en FMS-205 para distinguir hueco de tapa plana). Un tornillo con cabeza
    hexagonal tiene facetas, aristas y el hueco/sombra entre el tornillo y
    la pared del taladro -> gradiente mucho más alto e irregular.
    """
    mascara = np.zeros(grises.shape, np.uint8)
    cv.circle(mascara, punto, radio, 255, -1)
    sobel_x = cv.Sobel(grises, cv.CV_64F, 1, 0, ksize=3)
    sobel_y = cv.Sobel(grises, cv.CV_64F, 0, 1, ksize=3)
    magnitud = cv.magnitude(sobel_x, sobel_y)
    return float(magnitud[mascara == 255].mean())


def detectar_tornillos(grises_roi):
    """
    Comprueba las 4 posiciones y devuelve un diccionario {posicion: bool}
    indicando si hay tornillo en cada una.
    """
    presencia = {}
    for nombre, datos in POSICIONES_TORNILLO.items():
        gradiente = medir_gradiente_en_punto(grises_roi, datos["punto"], datos["radio"])
        presencia[nombre] = gradiente >= datos["umbral_gradiente"]
    return presencia


def procesar(imagen_bgr):
    """
    Punto de entrada único del algoritmo de FMS-206: recibe una imagen (tal
    cual la da la cámara, en color BGR) y devuelve el estado de la estación.

    Devuelve "COMPLETO" si los 4 tornillos están presentes, o "INCOMPLETO"
    si falta al menos uno (sin distinguir cuál ni cuántos, tal como pidió
    el usuario).
    """
    recorte = recortar_roi(imagen_bgr, ROI)
    grises = suavizar(convertir_a_grises(recorte))

    presencia = detectar_tornillos(grises)
    if all(presencia.values()):
        return "COMPLETO"
    return "INCOMPLETO"
