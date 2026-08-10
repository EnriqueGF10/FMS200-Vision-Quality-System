import cv2

# Abrir la cámara
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Error: No se pudo abrir la cámara.")
    exit()

print("Pulsa 'c' para capturar una imagen.")
print("Pulsa 'q' para salir.")

contador = 1

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error al leer la cámara.")
        break

    # Mostrar el vídeo en tiempo real
    cv2.imshow("Camara", frame)

    tecla = cv2.waitKey(1) & 0xFF

    # Capturar imagen
    if tecla == ord('c'):
        nombre = f"captura_{contador}.jpg"
        cv2.imwrite(nombre, frame)
        print(f"Imagen guardada: {nombre}")
        contador += 1

    # Salir
    elif tecla == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()