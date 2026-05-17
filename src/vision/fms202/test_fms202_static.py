import cv2 as cv
import os
import fms202

def comprobar_algoritmo_202():
    print("1. Iniciando el procesador...")
    processor = fms202.FMS202_Processor()

    # Lista de imágenes que tengo para probar
    imagenes_test = [
        "FMS202_rodamiento_alto.jpg",
        "data/Imagenes_FMS/FMS202/FMS202_rodamiento_bajo.jpg",
        "data/Imagenes_FMS/FMS202/FMS202_vacio.jpg",
        "data/Imagenes_FMS/FMS202/rodamientos_superior.jpg"
    ]

    for nombre in imagenes_test:
        if os.path.exists(nombre):
            frame = cv.imread(nombre)

            # Ejecutamos la lógica de la FMS202
            estado, img_resultado = processor.procesar(frame)

            print(f"Resultado: {estado}")

            print(f"--- Análisis de {nombre} ---")
            print(f"RESULTADO: {estado}")
            print("-----------------------------\n")

            # Mostramos el resultado visual
            # Redimensionamos para que quepa en pantalla
            h, w = img_resultado.shape[:2]
            img_show = cv.resize(img_resultado, (int(w*0.7), int(h*0.7)))

            cv.imshow(f"Test FMS202 - {nombre}", img_show)
            print("Pulsa cualquier tecla para ver la siguiente imagen...")
            cv.waitKey(0)
        else:
            print(f"No se encuentra el archivo: {nombre}")
    
    cv.destroyAllWindows()

if __name__ == "__main__":
    print("Ejecutando")
    comprobar_algoritmo_202()