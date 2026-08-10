"""
FMS-202: inspección del rodamiento insertado.

FMS-202 recibe la pieza que deja lista FMS-201 (el bloque cuadrado) y le
inserta un rodamiento en el hueco central. A diferencia de FMS-201, aquí
SIEMPRE debe haber un rodamiento: no encontrarlo es en sí mismo un error,
no un estado válido.

La estación puede presentar cuatro situaciones:
  - RODAMIENTO_NEGRO_ALTO -> rodamiento sellado, insertado "alto"
  - RODAMIENTO_NEGRO_BAJO -> rodamiento sellado, insertado "bajo"
  - RODAMIENTO_BOLAS      -> rodamiento abierto (bolas metálicas visibles)
  - ERROR                 -> no hay rodamiento insertado

(Inicialmente se pensó en fusionar alto/bajo en un solo estado porque no
parecían distinguibles a simple vista, pero al medir con datos reales sí se
separan con margen amplio)

Este fichero solo contiene el algoritmo de visión (funciones puras: entra
una imagen, sale un resultado). No abre cámara ni ventanas.
"""

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
# Por qué un ROI aquí y no en FMS-201: la cámara de esta estación está fija
# y la pieza siempre aparece en la misma zona (medido sobre varias imágenes
# de las 3 categorías: el bloque cae siempre en x=186-190, y=127-364 aprox.,
# con margen extra por el cable que a veces se funde con el contorno).
# Recortar antes de procesar resuelve dos problemas a la vez:
#   - Descarta directamente los raíles metálicos del fondo (que en FMS-201
#     obligaban a filtrar contornos por área Y distancia al centro).
#   - Descarta la mano cuando solo aparece en el borde del encuadre (varias
#     imágenes de este dataset la tienen ahí sin llegar a tapar la pieza).
ROI = (150, 90, 490, 410)


def encontrar_bloque(contornos):
    """
    Devuelve el contorno del bloque: dentro del ROI, siempre es el contorno
    de mayor área (a diferencia de FMS-201, aquí no hace falta filtrar por
    distancia al centro ni por rango de área, porque el ROI ya descarta
    todo lo que no sea la pieza).
    """
    return max(contornos, key=cv.contourArea)


# Umbrales de área del hueco (en píxeles², tras limpiar_binaria), medidos
# sobre las 76 imágenes reales de FMS-202 (ver docs/bitacora_algoritmos.txt):
#   - ERROR (sin rodamiento):    433 - 686
#   - RODAMIENTO_NEGRO_BAJO:     1706 - 1859
#   - RODAMIENTO_BOLAS:          2713 - 2892
#   - RODAMIENTO_NEGRO_ALTO:     4300 - 4620
# Los 4 grupos quedan separados por márgenes muy amplios (cientos de px²),
# así que los cortes se ponen a mitad de camino entre cada dos grupos.
AREA_MAX_SIN_RODAMIENTO = 1200
AREA_MAX_NEGRO_BAJO = 2300
AREA_MAX_BOLAS = 3600
# area >= AREA_MAX_BOLAS -> RODAMIENTO_NEGRO_ALTO


def decidir_tipo_rodamiento(hueco):
    """
    Clasifica el tipo de rodamiento (o su ausencia) a partir del área del
    hueco central.
    """
    area = cv.contourArea(hueco)
    if area < AREA_MAX_SIN_RODAMIENTO:
        return "ERROR"
    if area < AREA_MAX_NEGRO_BAJO:
        return "RODAMIENTO_NEGRO_BAJO"
    if area < AREA_MAX_BOLAS:
        return "RODAMIENTO_BOLAS"
    return "RODAMIENTO_NEGRO_ALTO"


def procesar(imagen_bgr):
    """
    Punto de entrada único del algoritmo de FMS-202: recibe una imagen (tal
    cual la da la cámara, en color BGR) y devuelve el estado de la estación.

    Devuelve un string: "RODAMIENTO_NEGRO_ALTO", "RODAMIENTO_NEGRO_BAJO",
    "RODAMIENTO_BOLAS" o "ERROR".
    """
    recorte = recortar_roi(imagen_bgr, ROI)
    grises = convertir_a_grises(recorte)
    suave = suavizar(grises)
    binaria = limpiar_binaria(binarizar(suave))
    contornos, jerarquia = encontrar_contornos(binaria)

    bloque = encontrar_bloque(contornos)
    hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
    return decidir_tipo_rodamiento(hueco)
