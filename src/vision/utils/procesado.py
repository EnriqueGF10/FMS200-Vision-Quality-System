import cv2 as cv
import os

def probar_filtros(nombre_foto):
    # 1. Construimos la ruta de la imagen
    ruta_imagen = os.path.join("data/Imagenes_FMS/FMS201/", nombre_foto)

    # 2. Cargamos la imagen del disco
    imagen = cv.imread(ruta_imagen)

    if imagen is None:
        print(f"No se encuentra la foto: {ruta_imagen}")
        return
    
    # --- INICIO DEL PROCESADO ---

    # A. Convertir a escala de GRISES
    # Eliminamos el color para quedarnos solo con la intensidad de luz
    imagen_gris = cv.cvtColor(imagen, cv.COLOR_BGR2GRAY)

    # B. Aplicar BLUR (Dsenfoque)
    # (5, 5) es el tamaño del filtro. A mayor tamaño, más borroso
    # Sirve para limpiar la imagen de "ruido metálico" y pequeños reflejos
    imagen_blur = cv.GaussianBlur(imagen_gris, (5, 5), 0)

    # C. Canny (Detección de bordes)
    # 50 y 150 son los umbrales
    # Si la diferencia de contraste es > 150, es un borde seguro
    imagen_bordes = cv.Canny(imagen_blur, 50, 150)

    # --- MOSTRAR RESULTADOS ---

    # Redimensión de las ventanas para adaptarse a la pantalla
    porcentaje_escala = 0.5 # 50 % del tamaño original
    anchura = int(imagen.shape[1] * porcentaje_escala)
    altura = int(imagen.shape[0] * porcentaje_escala)
    dimension = (anchura, altura)

    cv.imshow('1. Original', cv.resize(imagen, dimension))
    cv.imshow('2. Gris', cv.resize(imagen_gris, dimension))
    cv.imshow('3. Blur', cv.resize(imagen_blur, dimension))
    cv.imshow('4. Bordes (Canny)', cv.resize(imagen_bordes, dimension))

    print("Mostrando procesado. Pulsa cualquier tecla para cerrar.")
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":
    # Adaptar el nombre de cada una de las fotos de la carpeta
    muestra = "FMS201_con_base_nook.jpg"
    probar_filtros(muestra)