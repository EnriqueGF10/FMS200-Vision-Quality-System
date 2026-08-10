import cv2 as cv
import os
import time

def ejecutar_fotomaton():
    # 1. Configuramos la ruta donde guardamos las capturas
    # Hay que asegurarse de que existe la carpeta
    ruta_imagenes = "data/FMS201/Muestras"
    if not os.path.exists(ruta_imagenes):
        os.makedirs(ruta_imagenes)

    cap = cv.VideoCapture(0)

    print("Instrucciones:")
    print("- Pulsa 's' para Guardar (Save) una foto")
    print("- Pulsa 'q' para Salir")

    while cap.isOpened():
        ret, frame = cap.read()

        if ret == True:

            # Mostramos el vídeo
            cv.imshow('Captura de Muestras', frame)

            key = cv.waitKey (1) & 0xFF

            # Si pulsamos 's'
            if key == ord ('s'):
                # Generamos un nombre único basado en la hora actual
                nombre_archivo = f"pieza_{int(time.time())}.jpg"
                ruta_final = os.path.join(ruta_imagenes, nombre_archivo)

                # Guardamos la imagen en el disco
                cv.imwrite(ruta_final, frame)
                print(f"Foto guardad en: {ruta_final}")

            elif key == ord('q'):
                break
    
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    ejecutar_fotomaton()