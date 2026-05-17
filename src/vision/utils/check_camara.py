import cv2 as cv

def verificar_conexion():
    # 1. Intentamos abrir la cámara con índice 0
    # Si tengo conectada la C922 podría ser el índice 1
    cap = cv.VideoCapture(0)

    while (cap.isOpened()):
        # 2. Capturamos frame a frame
        ret, frame = cap.read()

        if ret == True:
            # 3. Mostramos la imagen sin ningún proceso
            cv.imshow('Verificacion C922 - Pulsa Q para salir', frame)
            # 4. Si pulsamos la tecla 'q' salimos del bucle
            if cv.waitKey(1) & 0xFF == ord('q'):    # Esta línea según la documentación de OpenCV es para máquinas de 64 bits
                break

    # 5. Al terminar, liberamos la cámara y cerramos ventanas
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    verificar_conexion()