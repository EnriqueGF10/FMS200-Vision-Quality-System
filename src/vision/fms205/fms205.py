"""
FMS-205: inspección del tapón insertado.

FMS-205 recibe la pieza de las estaciones anteriores y le inserta un tapón
en el hueco central. Hay 3 materiales posibles (metálico, negro, blanco)
insertados a 2 alturas posibles (alta/baja), más el caso sin tapón:

  - SIN_TAPON
  - TAPON_METALICO_BAJO / TAPON_METALICO_ALTO
  - TAPON_NEGRO_BAJO    / TAPON_NEGRO_ALTO
  - TAPON_BLANCO_BAJO   / TAPON_BLANCO_ALTO

Este fichero solo contiene el algoritmo de visión (funciones puras: entra
una imagen, sale un resultado). No abre cámara ni ventanas.
"""

import numpy as np
import cv2 as cv

from src.vision.utils.preprocesamiento import (
    recortar_roi,
    convertir_a_grises,
    suavizar,
    binarizar,
    encontrar_contornos,
    encontrar_hueco_principal,
    limpiar_binaria,
)


# Región de interés (ROI) fija: x1, y1, x2, y2 en píxeles.
#
# Medido sobre varias imágenes de las 7 categorías: el bloque cae siempre en
# x=181-182, ancho~264-265; el borde inferior del bloque es muy estable
# (~352-361). Se recorta con margen amplio arriba para no perder el propio
# tapón cuando está "alto".
ROI = (150, 60, 470, 380)


def encontrar_bloque(contornos):
    """
    Devuelve el contorno del bloque: dentro del ROI, el contorno de mayor
    área (igual que en FMS-202).
    """
    return max(contornos, key=cv.contourArea)


# Umbrales de área del hueco (en píxeles², tras limpiar_binaria), medidos
# sobre las 120 imágenes reales de FMS-205 excluyendo interferencias de mano
# (ver docs/bitacora_algoritmos.txt para el detalle completo):
#   - TAPON_BLANCO (alto o bajo):        área 324 - 402
#   - SIN_TAPON o TAPON_METALICO_ALTO:   área 658 - 1098   (se resuelven
#     entre sí con el gradiente interior, ver decidir_tipo_y_altura)
#   - TAPON_METALICO_BAJO:               área 1599 - 1966
#   - TAPON_NEGRO (bajo o alto):         área 13836 - 15018
# Los cuatro grupos están separados por márgenes de cientos de píxeles², así
# que los cortes se ponen a mitad de camino entre cada dos grupos.
AREA_MAX_BLANCO = 525
AREA_MAX_SIN_TAPON_O_METALICO_ALTO = 1350
AREA_MAX_METALICO_BAJO = 8000
AREA_MAX_NEGRO_BAJO = 14750

# Perímetro del hueco, solo para separar TAPON_BLANCO_ALTO de
# TAPON_BLANCO_BAJO (el área es prácticamente igual en ambos):
#   - TAPON_BLANCO_ALTO: perímetro 75.9 - 78.8
#   - TAPON_BLANCO_BAJO: perímetro 88.6 - 90.6
PERIMETRO_MAX_BLANCO_ALTO = 84

# Gradiente interior (ver medir_gradiente_interior), solo para separar
# SIN_TAPON de TAPON_METALICO_ALTO (su área se solapa: ambos son aluminio
# liso a ras, muy parecidos en bruto):
#   - SIN_TAPON (cavidad hueca):        gradiente 40.4 - 42.8
#   - TAPON_METALICO_ALTO (tapa plana): gradiente 20.3 - 37.5
# Se investigó esta técnica a partir de literatura de "shape from shading" /
# el operador D_arg (Tankus & Yeshurun) para distinguir superficies cóncavas
# de planas del mismo color: una cavidad tiene una pared curva que genera
# un gradiente de brillo continuo (sombreado), mientras que una tapa plana
# instalada a ras es uniforme por dentro, con el gradiente concentrado solo
# en el borde exterior (que se excluye erosionando la máscara).
GRADIENTE_MIN_SIN_TAPON = 39
_KERNEL_EROSION_GRADIENTE = np.ones((7, 7), np.uint8)


def medir_gradiente_interior(grises, hueco):
    """
    Mide el gradiente de intensidad (Sobel) dentro del hueco, excluyendo su
    borde exterior (que siempre tiene gradiente alto, sea cual sea la forma
    3D real del interior).

    Por qué: una cavidad hueca real (SIN_TAPON) tiene una pared curva que
    refleja la luz de forma gradual según la inclinación de la superficie
    (más clara arriba, más oscura al fondo) -> gradiente interior alto y
    continuo. Una tapa plana instalada al ras (TAPON_METALICO_ALTO) es
    prácticamente uniforme por dentro -> gradiente interior bajo. Es la
    misma idea que las técnicas de "shape from shading" para distinguir
    superficies cóncavas de planas del mismo color.
    """
    mascara = np.zeros(grises.shape, np.uint8)
    cv.drawContours(mascara, [hueco], -1, 255, -1)
    mascara_interior = cv.erode(mascara, _KERNEL_EROSION_GRADIENTE)

    sobel_x = cv.Sobel(grises, cv.CV_64F, 1, 0, ksize=3)
    sobel_y = cv.Sobel(grises, cv.CV_64F, 0, 1, ksize=3)
    magnitud = cv.magnitude(sobel_x, sobel_y)

    if mascara_interior.sum() == 0:
        return 0.0
    return float(magnitud[mascara_interior == 255].mean())


def decidir_tipo_y_altura(hueco, grises):
    """
    Clasifica el estado del tapón (o su ausencia) a partir del área del
    hueco, con dos desempates puntuales (perímetro para blanco, gradiente
    para sin_tapon/metálico_alto) donde el área por sí sola no basta.
    """
    area = cv.contourArea(hueco)

    if area < AREA_MAX_BLANCO:
        perimetro = cv.arcLength(hueco, True)
        if perimetro < PERIMETRO_MAX_BLANCO_ALTO:
            return "TAPON_BLANCO_ALTO"
        return "TAPON_BLANCO_BAJO"

    if area < AREA_MAX_SIN_TAPON_O_METALICO_ALTO:
        gradiente = medir_gradiente_interior(grises, hueco)
        if gradiente >= GRADIENTE_MIN_SIN_TAPON:
            return "SIN_TAPON"
        return "TAPON_METALICO_ALTO"

    if area < AREA_MAX_METALICO_BAJO:
        return "TAPON_METALICO_BAJO"

    if area < AREA_MAX_NEGRO_BAJO:
        return "TAPON_NEGRO_BAJO"

    return "TAPON_NEGRO_ALTO"


def procesar(imagen_bgr):
    """
    Punto de entrada único del algoritmo de FMS-205: recibe una imagen (tal
    cual la da la cámara, en color BGR) y devuelve el estado de la estación.
    """
    recorte = recortar_roi(imagen_bgr, ROI)
    grises = convertir_a_grises(recorte)
    suave = suavizar(grises)
    binaria = limpiar_binaria(binarizar(suave))
    contornos, jerarquia = encontrar_contornos(binaria)

    bloque = encontrar_bloque(contornos)
    hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
    return decidir_tipo_y_altura(hueco, grises)
