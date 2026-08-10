"""
src/hmi/panel.py: dibujado del overlay de supervisión (HMI).

Funciones puras: reciben un frame (imagen BGR de OpenCV) y datos de estado,
devuelven un frame anotado nuevo. No abren cámara ni ventanas (eso vive en
src/main.py), así se pueden probar con una imagen suelta, sin hardware.
"""

import cv2 as cv

# Resultados que consideramos "no favorables" para pintarlos en rojo en vez
# de en verde. Se basta con mirar si alguna de estas palabras aparece en el
# string de resultado, porque los 4 algoritmos ya usan este vocabulario
# (ESTACION_VACIA, RODAMIENTO_.../ERROR, INCOMPLETO, PIEZA_NOK).
PALABRAS_NO_FAVORABLES = ("ERROR", "KO", "VACIA", "INCOMPLETO")

COLOR_FAVORABLE = (0, 200, 0)  # verde (BGR)
COLOR_NO_FAVORABLE = (0, 0, 220)  # rojo (BGR)
COLOR_TEXTO = (255, 255, 255)
COLOR_FONDO_PANEL = (40, 40, 40)

ALTO_BARRA_SUPERIOR = 40
ALTO_LINEA_HISTORIAL = 22
HISTORIAL_MAX_LINEAS = 6


def es_resultado_favorable(resultado):
    return not any(palabra in resultado for palabra in PALABRAS_NO_FAVORABLES)


def _color_de(resultado):
    return COLOR_FAVORABLE if es_resultado_favorable(resultado) else COLOR_NO_FAVORABLE


def dibujar_overlay(frame, estacion_actual, ultimo_resultado, historial, fps=None):
    """
    Devuelve una copia de `frame` con:
      - una barra superior con la estación activa y su último resultado
        (coloreado en verde/rojo según sea favorable o no)
      - un historial de las últimas inspecciones, más pequeño, debajo

    `estacion_actual`/`ultimo_resultado` pueden ser None (arranque, sin
    ninguna inspección todavía). `historial` es una lista de tuplas
    (id_estacion, resultado), la más reciente al final.
    """
    anotado = frame.copy()
    alto, ancho = anotado.shape[:2]

    cv.rectangle(anotado, (0, 0), (ancho, ALTO_BARRA_SUPERIOR), COLOR_FONDO_PANEL, -1)

    if estacion_actual is None:
        texto = "Esperando disparo (1-4 = simular estacion, q = salir)"
        color = COLOR_TEXTO
    else:
        texto = f"{estacion_actual}: {ultimo_resultado}"
        color = _color_de(ultimo_resultado)

    if fps is not None:
        texto = f"{texto}   |   {fps:.0f} FPS"

    cv.putText(anotado, texto, (10, 27), cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    historial_reciente = historial[-HISTORIAL_MAX_LINEAS:]
    alto_panel = len(historial_reciente) * ALTO_LINEA_HISTORIAL + 10
    y0 = alto - alto_panel
    cv.rectangle(anotado, (0, y0), (220, alto), COLOR_FONDO_PANEL, -1)

    for i, (id_estacion, resultado) in enumerate(historial_reciente):
        y = y0 + 18 + i * ALTO_LINEA_HISTORIAL
        cv.putText(
            anotado,
            f"{id_estacion}: {resultado}",
            (8, y),
            cv.FONT_HERSHEY_SIMPLEX,
            0.45,
            _color_de(resultado),
            1,
        )

    return anotado
