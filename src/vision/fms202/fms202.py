"""
MÁQUINA FMS202 - CONTROL DE CALIDAD POR VISIÓN
--------------
La FMS202 es la segunda máquina del Sistema didáctico modular de ensamblaje flexible FMS-200.
Su funcionamiento es un poco más complejo que el anterior, ya que se añade un requisito.
En este caso, se encarga de la inserción de rodamientos sobre la base proveniente de la estación anterior. En esta fase, el sistema de
visión debe realizar una doble validación: presencia del rodamiento y clasificación del tipo insertado.

Las posibilidades son las siguientes:
- Sin rodamiento --> Error.
- Rodamiento Cerrado (Sellado) --> Presenta de superficie metálica o plástica uniforme.
- Rodamiento Abierto (Bolas) --> Presenta una geometría compleja con bolas de acero.

La implementación técnica combina dos estrategias de visión artificial:
1. Localización Geométrica:
Se utiliza la Transformada de Hough para Círculos para aislar la región exacta donde se aloja el rodamiento.
2. Análisis de Textura por Desviación Estándar:
Una vez localizado el rodamiento, se calcula la varianza de la intensidad de píxeles dentro del círculo detectado. Un rodamiento abierto
genera un valor elevado debido al contraste entre los brillos de las bolas y las sombras de los huecos, mientras que el cerrado
arroja valores bajos por su homogeneidad superficial.
"""

import cv2 as cv
import numpy as np

class FMS202_Processor:
    def __init__(self):
        # --- PARÁMETROS DE CALIBRACIÓN ---
        self.radio_rodamiento = 50
        self.umbral_varianza = 30   # Punto de corte entre Cerrado y Abierto

    def procesar(self, img):
        if img is None:
            return "ERROR", None
        
        # 1. Pre-procesado
        gris = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = cv.medianBlur(gris, 5)

        # 2. Localización del rodamiento (Hough)
        circulos = cv.HoughCircles(
            blur,
            cv.HOUGH_GRADIENT,
            dp = 1.2,
            minDist = 100,
            param1 = 50,
            param2 = 30,
            minRadius = 40,
            maxRadius = 70
        )

        estado = "VACIO"
        img_visual = img.copy()

        if circulos is not None:
            circulos = np.uint1(np.around(circulos))
            for i in circulos[0, :]:
                # Creamos una "MÁSCARA" para mirar solo dentro del rodamiento
                mascara = np.zeros(gris.shape, np.uint8)
                cv.circle(mascara, (i[0], i[1]), i[2], 255, -1)

                # Calculamos la desviación estándar de los píxeles dentro del círculo
                media, desviacion = cv.meanStdDev(gris, mask = mascara)
                valor_desv = desviacion[0][0]

                # 2. Lógica de clasificación por textura
                if valor_desv > self.umbral_varianza:
                    estado = "RODAMIENTO_ABIERTO"
                    color = (0, 255, 255)   # Amarillo

                else:
                    estado = "RODAMIENTO_CERRADO"
                    color = (255, 255, 0)   # Cian
                
                # Dibujamos para ver qué ocurre
                cv.circle(img_visual, (i[0], i[1]), i[2], color, 3)
                cv.putText(img_visual, f"SD: {valor_desv:.2f}", (i[0]-20, i[1]-10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return estado, img_visual