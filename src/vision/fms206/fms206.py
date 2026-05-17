import cv2 as cv
import numpy as np

class InspectorFMS206:
    def __init__(self):
        # ROI de la base (Ajustado a tu encuadre de trabajo)
        self.roi_base = (200, 180, 200, 200) 
        
        # TUS COORDENADAS FINALES ACTUALIZADAS
        self.puntos = [
            (18, 90),   # Punto 1 (Izquierda)
            (195, 90),  # Punto 2 (Derecha)
            (108, 10),  # Punto 3 (Arriba)
            (101, 178)  # Punto 4 (Abajo)
        ]
        
        self.radio = 12 
        self.umbral_deteccion = 85 
        
        # Filtro interno para estabilidad de contraste
        self.clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

    def procesar(self, frame):
        xb, yb, wb, hb = self.roi_base
        
        # Procesamiento de imagen interno (Gris + CLAHE)
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # Aplicamos el filtro solo en el área de interés para mayor velocidad
        roi_gray = gray[yb:yb+hb, xb:xb+wb]
        roi_filt = self.clahe.apply(roi_gray)
        
        bits = []
        for i, (px, py) in enumerate(self.puntos):
            # Crear máscara para el tornillo i
            mask = np.zeros(roi_filt.shape, dtype="uint8")
            cv.circle(mask, (px, py), self.radio, 255, -1)
            
            # Medir brillo en la zona filtrada
            brillo = cv.mean(roi_filt, mask=mask)[0]
            detectado = brillo > self.umbral_deteccion
            bits.append(1 if detectado else 0)
            
            # Dibujar círculos y números directamente sobre el frame original
            # Coordenadas absolutas: (xb + px, yb + py)
            color = (0, 255, 0) if detectado else (0, 0, 255)
            centro = (xb + px, yb + py)
            
            cv.circle(frame, centro, self.radio, color, 2)
            cv.putText(frame, str(i+1), (centro[0]-5, centro[1]+5), 
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Dashboard de resultados
        total = sum(bits)
        self.dibujar_interfaz(frame, total, xb, yb, wb)
        
        return frame

    def dibujar_interfaz(self, frame, total, x, y, w):
        # Determinar texto de estado
        if total == 4:
            estado = "ESTADO: COMPLETO"
            color_ui = (0, 255, 0)
        elif total == 0:
            estado = "ESTADO: VACIO"
            color_ui = (0, 0, 255)
        else:
            estado = f"PARCIAL - {total}/4"
            color_ui = (0, 255, 255) # Amarillo para estados intermedios

        # Dibujar fondo del panel de texto
        cv.rectangle(frame, (x, y-40), (x+w, y), (40, 40, 40), -1)
        cv.putText(frame, estado, (x+10, y-12), 
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color_ui, 2)
        
        # Opcional: Recuadro del área de inspección
        cv.rectangle(frame, (x, y), (x+w, y+w), (255, 255, 255), 1)

# --- Bucle de ejecución ---
if __name__ == "__main__":
    cap = cv.VideoCapture(0)
    inspector = InspectorFMS206()

    while True:
        ret, frame = cap.read()
        if not ret: break

        resultado = inspector.procesar(frame)
        cv.imshow("Control de Calidad FMS-206", resultado)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()