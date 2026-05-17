"""
MÁQUINA FMS201 - CONTROL DE CALIDAD POR VISIÓN
--------------
La FMS201 es la primera máquina del Sistema didáctico modular de ensamblaje flexible FMS-200.
Su funcionamiento es el más simple y sencillo de todas las que componen el sistema.
Su lógica de funcionamiento se basa en detectar si hay una pieza y si esta es correcta.
Las posibilidades son las siguientes:
- Sin pieza --> Error.
- Pieza en posición invertida --> Error.
- Pieza en posición correcta --> Correcto.

En este script se describen todos los parámetros necesarios para detectar estas piezas.
Para ello se ha observado que la pieza colocada en una posición correcta cuenta en su centro con una circunferencia semi perfecta de
x radio, dato que ninguna de las otras dos posibilidades alberga.

La implementación más óptima ha sido el uso de la Transformada de Hough para Círculos, un algoritmo de visión artificial
que permite identificar patrones circulares mediante una votación matemática en el espacio de parámetros. Al filtrar por radio
específico, el sistema es capaz de ignorar el ruido visual y los elementos metálicos de la base de transporte, validando únicamente
la presencia del rebaje central característico de la pieza en su posición correcta.
"""

import cv2 as cv
import numpy as np

class FMS201_Processor:
    def __init__(self):
        # --- CALIBRACIÓN REFINADA ---
        self.umbral_bloque = 11
        self.umbral_c = 2
        
        # Basado en tu imagen, ajustamos los rangos de área
        self.area_min = 5000          
        self.area_max = 10000        # Bajamos drásticamente para evitar elipses gigantes
        self.ratio_aspecto = (0.4, 0.95)
        
        # Estos valores los ajustarás viendo el nuevo área corregida
        self.umbral_pieza_ok = 8000  
        self.umbral_pieza_ko = 7000   

    def procesar(self, frame):
        if frame is None: return "ERROR", None, None, None, 0

        h, w = frame.shape[:2]
        img_final = frame.copy()
        
        # 1. PRE-PROCESADO CON CIERRE MORFOLÓGICO
        gris = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gris, (7, 7), 0)
        
        # Máscara adaptativa
        binary = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv.THRESH_BINARY_INV, self.umbral_bloque, self.umbral_c)
        
        # --- MEJORA: Rellenar huecos para que el agujero sea una mancha sólida ---
        kernel = np.ones((5,5), np.uint8)
        binary = cv.morphologyEx(binary, cv.MORPH_CLOSE, kernel)
        
        bordes = cv.Canny(blur, 50, 150)

        # 2. DETECCIÓN FILTRADA POR PROXIMIDAD AL CENTRO
        contornos, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        mejor_elipse = None
        area_detectada = 0
        distancia_minima = float('inf')

        for cnt in contornos:
            area_cnt = cv.contourArea(cnt)
            if self.area_min < area_cnt < self.area_max:
                if len(cnt) >= 5:
                    elp = cv.fitEllipse(cnt)
                    (x, y), (MA, ma), ang = elp
                    
                    # Distancia al centro exacto de la imagen
                    dist_al_centro = np.sqrt((x - w/2)**2 + (y - h/2)**2)
                    
                    # Solo aceptamos si está en el tercio central de la pantalla
                    if dist_al_centro < (w / 4): 
                        ratio = MA / ma
                        if self.ratio_aspecto[0] < ratio < self.ratio_aspecto[1]:
                            # Nos quedamos con la elipse que esté MÁS CERCA del centro
                            if dist_al_centro < distancia_minima:
                                distancia_minima = dist_al_centro
                                mejor_elipse = elp
                                area_detectada = (np.pi * MA * ma) / 4

        # 3. LÓGICA DE DECISIÓN
        estado = "ESTACION_VACIA"
        color = (255, 0, 0)

        if mejor_elipse:
            if area_detectada > self.umbral_pieza_ok:
                estado = "PIEZA_OK"
                color = (0, 255, 0)
            elif area_detectada > self.umbral_pieza_ko:
                estado = "PIEZA_KO_INVERTIDA"
                color = (0, 0, 255)
            else:
                estado = "PIEZA_KO_PEQUEÑA"
                color = (0, 165, 255)
            
            cv.ellipse(img_final, mejor_elipse, (255, 255, 0), 3)
        
        # Limpiamos el texto para que no se solape
        cv.rectangle(img_final, (0,0), (400, 110), (0,0,0), -1) # Fondo negro para texto
        cv.putText(img_final, f"ST: {estado}", (10, 40), cv.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv.putText(img_final, f"Area: {int(area_detectada)}", (10, 80), cv.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)

        return estado, img_final, binary, bordes, area_detectada

if __name__ == "__main__":
    proc = FMS201_Processor()
    cap = cv.VideoCapture(0) # Cambiar índice si tienes varias cámaras

    print("Iniciando Dashboard FMS-201... Pulsa 'q' para salir.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        estado, res_final, res_binary, res_bordes, area_val = proc.procesar(frame)

        # --- MONTAJE DEL DASHBOARD 2x2 ---
        w_d, h_d = 640, 360
        
        # Cuadrante 1: Original
        v1 = cv.resize(frame, (w_d, h_d))
        cv.putText(v1, "1. VISTA REAL", (20, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        # Cuadrante 2: Máscara Adaptativa (Para ver si el blanco es sólido)
        v2 = cv.cvtColor(cv.resize(res_binary, (w_d, h_d)), cv.COLOR_GRAY2BGR)
        cv.putText(v2, "2. MASCARA (Adaptativa)", (20, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        
        # Cuadrante 3: Bordes
        v3 = cv.cvtColor(cv.resize(res_bordes, (w_d, h_d)), cv.COLOR_GRAY2BGR)
        cv.putText(v3, "3. BORDES CANNY", (20, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        
        # Cuadrante 4: Resultado final con datos
        v4 = cv.resize(res_final, (w_d, h_d))
        cv.putText(v4, "4. ANALISIS DE AREA", (20, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        # Unión
        mosaico = np.vstack((np.hstack((v1, v2)), np.hstack((v3, v4))))
        
        cv.imshow("CONTROL CALIDAD FMS-201", mosaico)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()