import cv2
import os
import numpy as np

class VisionSystem:
    def __init__(self, camera_index=0, dev_mode=True):
        self.camera_index = camera_index    # ID de la cámara (0 = integrada)
        self.dev_mode = dev_mode            # Modo de simulación para cuando no tenga cámara
        self.cap = None
        self.test_image_path = ""

    # Intenta conectarse a la cámara C922 o a la del PC por defecto
    def conectar_camara(self):
        self.cap = cv2.VideoCapture(self.camera_index)  # Conecta el HW de la cámara
        if not self.cap.isOpened():                     # Si la cámara no se conecta...
            print("No se detecta cámara física.")
            return False
        print("Cámara conectada correctamente")
        return True

# Obtiene una imágen de la cámara o del archivo de simulación
    def tomar_imagen(self):
        if self.cap and self.cap.isOpened():            # Si la conexión va bien
            ret, imagen = self.cap.read()               # ret es un booleano que almacena si la imagen se ha tomado o no
            if ret:
                return imagen
            
        # Si falla la cámara o no hay, lee la imagen de la ruta que hayamos pasado
        if self.dev_mode and os.path.exists(self.test_image_path):
            return cv2.imread(self.test_image_path)
        
        return None
    
    # Lógica de la decisión de si la pieza es OK o KO
    # 
    def analizar_pieza(self, imagen):
        if imagen is None:
            return False, "Error: Sin Imagen"
        
        # En caso de que se haya tomado una imagen
