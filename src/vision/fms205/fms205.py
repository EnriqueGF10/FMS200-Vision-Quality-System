import cv2 as cv
import numpy as np

class FMS205_Final_Fix:
    def __init__(self):
        # Tus coordenadas corregidas
        self.roi_base = (200, 180, 200, 200) 
        
        # AJUSTE CRÍTICO: Reducimos el radio de inspección de material
        # para que NO toque el metal de la base.
        self.centro_inspeccion = (300, 280) # Ajustar para que caiga en el centro de la tapa
        self.radio_inspeccion = 40          # Radio pequeño = Lectura pura
        
        # Umbrales basados en tus fotos
        self.v_negra_max = 80
        self.v_blanca_min = 180

    def procesar(self, frame):
        # 1. Dibujar la ROI Base (Tu referencia)
        xb, yb, wb, hb = self.roi_base
        cv.rectangle(frame, (xb, yb), (xb+wb, yb+hb), (255, 255, 0), 2)
        
        # 2. Análisis de Material (ROI interna pequeña)
        mask_mat = np.zeros(frame.shape[:2], dtype="uint8")
        cv.circle(mask_mat, self.centro_inspeccion, self.radio_inspeccion, 255, -1)
        
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        v_canal = hsv[:,:,2]
        avg_v = cv.mean(v_canal, mask=mask_mat)[0]
        _, std_v = cv.meanStdDev(v_canal, mask=mask_mat)
        textura = std_v[0][0]

        # 3. Lógica de Material Robusta
        if avg_v < self.v_negra_max:
            material = "NEGRA"
        elif textura > 25: # El metal brilla de forma irregular
            material = "METALICA"
        else:
            material = "BLANCA"

        # 4. Detección de Altura (Círculo externo)
        gris = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gris = cv.GaussianBlur(gris, (7, 7), 0)
        circles = cv.HoughCircles(gris, cv.HOUGH_GRADIENT, 1.2, 100, 
                                  param1=100, param2=35, minRadius=50, maxRadius=90)
        
        res_alt = "---"
        radio_r = 0
        if circles is not None:
            circles = np.uint16(np.around(circles))
            c = circles[0, 0]
            radio_r = c[2]
            cv.circle(frame, (c[0], c[1]), radio_r, (0, 255, 0), 2)
            res_alt = "ALTA" if radio_r > 70 else "BAJA"

        # Dashboard UI
        cv.rectangle(frame, (0, 0), (450, 100), (0,0,0), -1)
        cv.putText(frame, f"MAT: {material} | ALT: {res_alt}", (15, 40), 2, 0.8, (0, 255, 0), 2)
        cv.putText(frame, f"V-Pureza: {int(avg_v)} | R-Altura: {int(radio_r)}", (15, 80), 1, 1, (255, 255, 255), 1)
        # Dibujar el punto de mira de material (el secreto de la robustez)
        cv.circle(frame, self.centro_inspeccion, self.radio_inspeccion, (255, 0, 255), 1)
        
        return frame

# Ejecución
cap = cv.VideoCapture(0)
sistema = FMS205_Final_Fix()
while True:
    ret, frame = cap.read()
    if not ret: break
    cv.imshow("FMS-205: CALIBRACION FINAL", sistema.procesar(frame))
    if cv.waitKey(1) & 0xFF == ord('q'): break
cap.release()
cv.destroyAllWindows()