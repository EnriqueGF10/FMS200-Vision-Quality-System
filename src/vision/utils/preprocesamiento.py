"""
Pasos de preprocesado de imagen compartidos por las 4 estaciones del FMS-200.

Por qué un módulo aparte: las 4 estaciones usan la misma cámara y el mismo
encuadre (la pieza base siempre aparece igual), así que los primeros pasos
del pipeline (pasar a grises, suavizar, binarizar y buscar contornos) son
técnicas 100% genéricas, sin nada específico de ninguna estación en concreto.
Se extrajeron aquí al empezar FMS-202, al comprobar que iban a ser una copia
exacta de las mismas funciones ya escritas para FMS-201 (ver
docs/bitacora_algoritmos.txt).

Lo que SÍ sigue siendo específico de cada estación (y por tanto no vive
aquí) son los umbrales de área/distancia para encontrar la pieza y toda la
lógica de decisión final: cada fms20X.py mantiene lo suyo.
"""

import cv2 as cv
import numpy as np


def recortar_roi(imagen_bgr, roi):
    """
    Recorta la imagen a una región de interés (ROI) fija: x1, y1, x2, y2 en
    píxeles.

    Por qué es genérica y no específica de una estación: la cámara está fija
    en las 4 estaciones y la pieza cae siempre en la misma zona del
    encuadre, así que el recorte en sí es idéntico en las 4; lo único que
    cambia es la propia región (definida como constante ROI en cada
    fms20X.py, medida por separado para cada estación).
    """
    x1, y1, x2, y2 = roi
    return imagen_bgr[y1:y2, x1:x2]


def convertir_a_grises(imagen_bgr):
    """
    Convierte la imagen (en color, formato BGR de OpenCV) a un único canal
    de grises.

    Por qué: en ninguna de las estaciones la decisión depende del color de
    la pieza (siempre es el mismo aluminio/metal), sino de su FORMA y sus
    SOMBRAS. Trabajar en grises simplifica todo lo que viene después
    (umbralizado, contornos) porque pasamos de 3 canales a 1, sin perder la
    información que realmente se necesita.
    """
    return cv.cvtColor(imagen_bgr, cv.COLOR_BGR2GRAY)


def suavizar(grises):
    """
    Aplica un desenfoque gaussiano suave antes de umbralizar.

    Por qué: el sensor de la cámara introduce ruido de alta frecuencia
    (grano, pequeñas motas) que puede generar contornos falsos diminutos al
    binarizar. Un desenfoque gaussiano pequeño (5x5) promedia esos píxeles
    sueltos con sus vecinos sin llegar a borrar los contornos reales, mucho
    más grandes que el ruido.
    """
    return cv.GaussianBlur(grises, (5, 5), 0)


def binarizar(grises_suavizados):
    """
    Convierte la imagen en grises a blanco/negro puro usando el método de
    Otsu.

    Por qué Otsu y no un umbral fijo: Otsu analiza el histograma de la
    imagen y elige automáticamente el punto de corte que mejor separa dos
    poblaciones de brillo (fondo/plataforma oscura frente a la pieza
    metálica clara). Un valor fijo a ojo se rompería en cuanto cambiara
    ligeramente la iluminación del laboratorio; Otsu se recalcula en cada
    imagen y es más robusto a esos cambios sin tener que tocar código.

    Devuelve una imagen binaria donde la pieza (más clara que el fondo)
    queda en blanco (255) y el resto en negro (0).
    """
    _, binaria = cv.threshold(
        grises_suavizados, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU
    )
    return binaria


def encontrar_contornos(binaria):
    """
    Busca las siluetas (contornos) de las zonas blancas de la imagen binaria,
    incluyendo la relación padre-hijo entre ellas (qué contorno es un
    "agujero" dentro de otro).

    Por qué RETR_CCOMP: varias estaciones necesitan analizar agujeros
    interiores de la pieza (huecos, rebajes), que son contornos "hijos" del
    contorno exterior. RETR_CCOMP organiza los contornos en dos niveles
    (exteriores y agujeros) y da además, para cada uno, el índice de su
    padre.

    Por qué CHAIN_APPROX_SIMPLE: en vez de guardar todos los puntos del
    borde, comprime segmentos rectos a solo sus extremos. El resultado es
    el mismo contorno con muchos menos puntos -> más rápido y con menos
    memoria, sin perder la forma real.

    Devuelve (contornos, jerarquia) tal cual los da OpenCV. jerarquia[0][i]
    es [siguiente, anterior, primer_hijo, padre] del contorno i.
    """
    contornos, jerarquia = cv.findContours(binaria, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    return contornos, jerarquia


def encontrar_hueco_principal(contornos, jerarquia, contorno_padre):
    """
    De entre los "agujeros" (contornos hijos) de un contorno dado, devuelve
    el más grande. Útil para quedarse con el hueco/rebaje central de una
    pieza descartando automáticamente agujeros más pequeños (p. ej. los de
    tornillo en las esquinas).

    Por qué es genérica y no específica de una estación: no asume ningún
    tamaño ni forma concreta, solo la relación estructural "hijo de este
    contorno" que da RETR_CCOMP -> sirve igual para el hueco de FMS-201 que
    para el de cualquier otra estación con un rebaje central.

    Devuelve None si el contorno dado no tiene ningún hijo detectado.
    """
    idx_padre = next(i for i, cnt in enumerate(contornos) if cnt is contorno_padre)

    mejor_hijo = None
    mejor_area = 0
    for i, cnt in enumerate(contornos):
        es_hijo = jerarquia[0][i][3] == idx_padre
        if es_hijo:
            area = cv.contourArea(cnt)
            if area > mejor_area:
                mejor_area = area
                mejor_hijo = cnt

    return mejor_hijo


# Kernel para el cierre morfológico (ver limpiar_binaria).
_KERNEL_CIERRE = np.ones((5, 5), np.uint8)


def limpiar_binaria(binaria):
    """
    Aplica un cierre morfológico (dilatar y luego erosionar) a la imagen
    binaria, para suavizar pequeñas irregularidades del borde de un hueco.

    Por qué hace falta esto: Otsu no siempre umbraliza el borde en
    exactamente el mismo píxel de una foto a otra, aunque la escena sea
    idéntica a simple vista: ese ruido de un par de píxeles cambia el
    área/perímetro medido más de lo esperado, y cuando el margen entre dos
    categorías es estrecho (visto por primera vez en FMS-202, y de nuevo en
    FMS-205) ese ruido basta para confundirlas. El cierre morfológico
    rellena esas pequeñas muescas/salientes del borde antes de medir.

    Por qué es genérica y no específica de una estación: es una operación
    de limpieza de imagen sin ningún parámetro propio de una pieza concreta;
    se usa igual en FMS-202 y FMS-205 (ver docs/bitacora_algoritmos.txt).
    """
    return cv.morphologyEx(binaria, cv.MORPH_CLOSE, _KERNEL_CIERRE)
