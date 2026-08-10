"""
Genera las figuras "curadas" para la memoria del TFG: un subconjunto pequeño
y representativo de imágenes (no el volcado en bruto de outputs/), en el
mismo orden en que se fueron tomando las decisiones descritas en
docs/bitacora_algoritmos.txt, con nombres descriptivos.

Por qué un script y no copiar archivos a mano: si más adelante se ajusta
algún umbral o paso del algoritmo, basta con volver a ejecutar este script
para regenerar las figuras actualizadas, en vez de rehacer el trabajo a mano.

Uso:
    python scripts/generar_figuras_memoria.py
"""

import sys
from pathlib import Path

import cv2 as cv

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.vision.utils.preprocesamiento import (
    convertir_a_grises,
    suavizar,
    binarizar,
    encontrar_contornos,
    encontrar_hueco_principal,
)
from src.vision.fms201 import fms201
from src.vision.fms202 import fms202
from src.vision.fms205 import fms205
from src.vision.fms206 import fms206

CARPETA_FIGURAS = RAIZ_REPO / "docs" / "memoria" / "figuras"


def _texto(imagen, texto, y=25, color=(0, 255, 0), escala=0.8):
    cv.putText(imagen, texto, (10, y), cv.FONT_HERSHEY_SIMPLEX, escala, color, 2)
    return imagen


# ---------------------------------------------------------------------------
# FMS-201
# ---------------------------------------------------------------------------

def generar_figuras_fms201():
    carpeta = CARPETA_FIGURAS / "fms201"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagenes = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS201"
    indice = []

    # 01-02: imágenes de referencia usadas para entender el criterio OK/NOK.
    ok_ref = cv.imread(str(imagenes / "Pieza OK.jpeg"))
    cv.imwrite(str(carpeta / "01_referencia_pieza_ok.jpg"), ok_ref)
    indice.append("01_referencia_pieza_ok.jpg: Imagen de referencia: pieza colocada correctamente.")

    nok_ref = cv.imread(str(imagenes / "Pieza NOK.jpeg"))
    cv.imwrite(str(carpeta / "02_referencia_pieza_nok.jpg"), nok_ref)
    indice.append("02_referencia_pieza_nok.jpg: Imagen de referencia: pieza colocada al reves.")

    # 03: Paso 1, ROI.
    ok = cv.imread(str(imagenes / "captura_1.jpg"))
    roi_ok = fms201.recortar_roi(ok, fms201.ROI)
    cv.imwrite(str(carpeta / "03_paso1_roi_recorte.png"), roi_ok)
    indice.append("03_paso1_roi_recorte.png: Recorte fijo (ROI) sobre captura_1 (Paso 1).")

    # 04: Paso 1 (conversion a grises), sobre el recorte.
    grises_ok = convertir_a_grises(roi_ok)
    cv.imwrite(str(carpeta / "04_paso1_conversion_grises.png"), grises_ok)
    indice.append("04_paso1_conversion_grises.png: Resultado de convertir_a_grises sobre el ROI (Paso 1).")

    # 05-07: Paso 2 (binarizado Otsu) en los 3 casos: OK, invertida, vacia.
    invertida = cv.imread(str(imagenes / "captura_20.jpg"))
    vacia = cv.imread(str(imagenes / "captura_35.jpg"))

    bin_ok = binarizar(suavizar(grises_ok))
    cv.imwrite(str(carpeta / "05_paso2_binarizado_otsu_ok.png"), bin_ok)
    indice.append("05_paso2_binarizado_otsu_ok.png: Binarizado Otsu de la pieza OK (Paso 2).")

    bin_inv = binarizar(suavizar(convertir_a_grises(fms201.recortar_roi(invertida, fms201.ROI))))
    cv.imwrite(str(carpeta / "06_paso2_binarizado_otsu_invertida.png"), bin_inv)
    indice.append("06_paso2_binarizado_otsu_invertida.png: Binarizado Otsu de la pieza invertida (Paso 2).")

    bin_vac = binarizar(suavizar(convertir_a_grises(fms201.recortar_roi(vacia, fms201.ROI))))
    cv.imwrite(str(carpeta / "07_paso2_binarizado_otsu_vacia.png"), bin_vac)
    indice.append("07_paso2_binarizado_otsu_vacia.png: Binarizado Otsu de la estacion vacia dentro del ROI: solo ruido pequeno, sin pieza (Paso 2).")

    # 08: Paso 3, todos los contornos detectados dentro del ROI.
    contornos_ok, _ = encontrar_contornos(bin_ok)
    con_dibujo = roi_ok.copy()
    for cnt in contornos_ok:
        if cv.contourArea(cnt) < 50:
            continue
        cv.drawContours(con_dibujo, [cnt], -1, (0, 0, 255), 2)
    cv.imwrite(str(carpeta / "08_paso3_todos_los_contornos.png"), con_dibujo)
    indice.append("08_paso3_todos_los_contornos.png: Todos los contornos detectados dentro del ROI (Paso 3).")

    # 09-11: Paso 4/5, resultado final (pieza + hueco + estado) en los 3 casos
    # del ambiente ideal (sin manos ni oclusiones).
    def resultado_final(imagen_bgr, nombre_archivo, descripcion):
        estado = fms201.procesar(imagen_bgr)
        recorte = fms201.recortar_roi(imagen_bgr, fms201.ROI)
        dibujo = recorte.copy()
        contornos, jerarquia = encontrar_contornos(binarizar(suavizar(convertir_a_grises(recorte))))
        pieza = fms201.encontrar_contorno_pieza(contornos)
        if pieza is not None:
            cv.drawContours(dibujo, [pieza], -1, (255, 255, 0), 2)
            hueco = encontrar_hueco_principal(contornos, jerarquia, pieza)
            if hueco is not None:
                cv.drawContours(dibujo, [hueco], -1, (0, 0, 255), 2)
        _texto(dibujo, f"ESTADO: {estado}")
        cv.imwrite(str(carpeta / nombre_archivo), dibujo)
        indice.append(f"{nombre_archivo}: {descripcion} (resultado: {estado}).")

    resultado_final(ok, "09_paso4_resultado_final_ok.png", "Resultado final sobre captura_1 (pieza OK)")
    resultado_final(invertida, "10_paso4_resultado_final_invertida.png", "Resultado final sobre captura_20 (pieza invertida)")
    resultado_final(vacia, "11_paso4_resultado_final_vacia.png", "Resultado final sobre captura_35 (estacion vacia)")

    (carpeta / "00_indice.txt").write_text(
        "Figuras de FMS-201, en el orden de docs/bitacora_algoritmos.txt\n"
        "=================================================================\n\n"
        + "\n".join(indice) + "\n",
        encoding="utf-8",
    )
    print(f"FMS-201: {len(indice)} figuras generadas en {carpeta}")


# ---------------------------------------------------------------------------
# FMS-202
# ---------------------------------------------------------------------------

def generar_figuras_fms202():
    carpeta = CARPETA_FIGURAS / "fms202"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagenes = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS202"
    indice = []

    # 01: imagen de referencia (bolas vs sellado, lado a lado).
    ref = cv.imread(str(imagenes / "rodamientos_superior.jpg"))
    cv.imwrite(str(carpeta / "01_referencia_bolas_vs_sellado.jpg"), ref)
    indice.append("01_referencia_bolas_vs_sellado.jpg: Rodamiento sellado (izq.) vs. de bolas (dcha.), imagen de referencia.")

    # 02-03: Paso 1, ROI.
    sin_pieza = cv.imread(str(imagenes / "captura_1.jpg"))
    cv.imwrite(str(carpeta / "02_paso1_imagen_original_sin_pieza.png"), sin_pieza)
    indice.append("02_paso1_imagen_original_sin_pieza.png: captura_1.jpg, pieza de FMS-201 sin rodamiento (Paso 1).")

    negro_bajo = cv.imread(str(imagenes / "captura_35.jpg"))
    roi_negro_bajo = fms202.recortar_roi(negro_bajo, fms202.ROI)
    cv.imwrite(str(carpeta / "03_paso1_roi_recorte.png"), roi_negro_bajo)
    indice.append("03_paso1_roi_recorte.png: Recorte fijo (ROI) sobre captura_35, elimina fondo/railes (Paso 1).")

    # 04-05: Paso 3 vs Paso 5, binarizado sin y con cierre morfologico.
    grises_bajo = convertir_a_grises(roi_negro_bajo)
    bin_sin_cierre = binarizar(suavizar(grises_bajo))
    cv.imwrite(str(carpeta / "04_paso3_binarizado_sin_cierre.png"), bin_sin_cierre)
    indice.append("04_paso3_binarizado_sin_cierre.png: Binarizado Otsu sin cierre morfologico (Paso 3), borde con ruido.")

    bin_con_cierre = fms202.limpiar_binaria(bin_sin_cierre)
    cv.imwrite(str(carpeta / "05_paso5_binarizado_con_cierre.png"), bin_con_cierre)
    indice.append("05_paso5_binarizado_con_cierre.png: Mismo binarizado tras el cierre morfologico (Paso 5), borde estabilizado.")

    # 06-07: Paso 4, zoom x4 comparando captura_35 (limpia) con captura_43 (ruido de Otsu).
    def zoom_hueco(imagen_bgr):
        recorte = fms202.recortar_roi(imagen_bgr, fms202.ROI)
        grises = convertir_a_grises(recorte)
        binaria = fms202.limpiar_binaria(binarizar(suavizar(grises)))
        contornos, jerarquia = encontrar_contornos(binaria)
        bloque = fms202.encontrar_bloque(contornos)
        hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
        x, y, w, h = cv.boundingRect(hueco)
        margen = 15
        zoom = recorte[max(0, y - margen):y + h + margen, max(0, x - margen):x + w + margen]
        return cv.resize(zoom, None, fx=4, fy=4, interpolation=cv.INTER_NEAREST)

    zoom_35 = zoom_hueco(negro_bajo)
    cv.imwrite(str(carpeta / "06_paso4_zoom_captura35_limpia.png"), zoom_35)
    indice.append("06_paso4_zoom_captura35_limpia.png: Zoom x4 del hueco, captura_35 (negro_bajo limpia, Paso 4).")

    captura_43 = cv.imread(str(imagenes / "captura_43.jpg"))
    zoom_43 = zoom_hueco(captura_43)
    cv.imwrite(str(carpeta / "07_paso4_zoom_captura43_ruido_otsu.png"), zoom_43)
    indice.append("07_paso4_zoom_captura43_ruido_otsu.png: Zoom x4 del hueco, captura_43 (visualmente identica a 06, la diferencia era ruido de Otsu, Paso 4).")

    # 08-11: Paso 6, resultado final (bloque + hueco + estado) en las 4 categorias.
    def resultado_final(imagen_bgr, nombre_archivo, descripcion):
        estado = fms202.procesar(imagen_bgr)
        recorte = fms202.recortar_roi(imagen_bgr, fms202.ROI)
        dibujo = recorte.copy()
        grises = convertir_a_grises(recorte)
        binaria = fms202.limpiar_binaria(binarizar(suavizar(grises)))
        contornos, jerarquia = encontrar_contornos(binaria)
        bloque = fms202.encontrar_bloque(contornos)
        cv.drawContours(dibujo, [bloque], -1, (255, 255, 0), 2)
        hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
        if hueco is not None:
            cv.drawContours(dibujo, [hueco], -1, (0, 0, 255), 2)
        _texto(dibujo, f"ESTADO: {estado}", escala=0.5)
        cv.imwrite(str(carpeta / nombre_archivo), dibujo)
        indice.append(f"{nombre_archivo}: {descripcion} (resultado: {estado}).")

    negro_alto = cv.imread(str(imagenes / "captura_54.jpg"))
    bolas = cv.imread(str(imagenes / "captura_78.jpg"))

    resultado_final(negro_bajo, "08_paso6_resultado_final_negro_bajo.png", "Resultado final sobre captura_35 (rodamiento negro bajo)")
    resultado_final(negro_alto, "09_paso6_resultado_final_negro_alto.png", "Resultado final sobre captura_54 (rodamiento negro alto)")
    resultado_final(bolas, "10_paso6_resultado_final_bolas.png", "Resultado final sobre captura_78 (rodamiento de bolas)")
    resultado_final(sin_pieza, "11_paso6_resultado_final_error_sin_pieza.png", "Resultado final sobre captura_1 (sin rodamiento -> ERROR)")

    (carpeta / "00_indice.txt").write_text(
        "Figuras de FMS-202, en el orden de docs/bitacora_algoritmos.txt\n"
        "=================================================================\n\n"
        + "\n".join(indice) + "\n",
        encoding="utf-8",
    )
    print(f"FMS-202: {len(indice)} figuras generadas en {carpeta}")


# ---------------------------------------------------------------------------
# FMS-205
# ---------------------------------------------------------------------------

def generar_figuras_fms205():
    carpeta = CARPETA_FIGURAS / "fms205"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagenes = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS205"
    indice = []

    # 01-07: las 7 imagenes de referencia (los 3 materiales x 2 alturas + vacio).
    referencias = [
        ("FMS205_vacio.jpg", "01_referencia_vacio.jpg", "Referencia: sin tapon."),
        ("FMS205_metal_baja.jpg", "02_referencia_metal_baja.jpg", "Referencia: tapon metalico bajo."),
        ("FMS205_metal_alta.jpg", "03_referencia_metal_alta.jpg", "Referencia: tapon metalico alto."),
        ("FMS205_negra_baja.jpg", "04_referencia_negra_baja.jpg", "Referencia: tapon negro bajo."),
        ("FMS205_negra_alta.jpg", "05_referencia_negra_alta.jpg", "Referencia: tapon negro alto."),
        ("FMS205_blanca_baja.jpg", "06_referencia_blanca_baja.jpg", "Referencia: tapon blanco bajo."),
        ("FMS205_blanca_alta.jpg", "07_referencia_blanca_alta.jpg", "Referencia: tapon blanco alto."),
    ]
    for origen, destino, descripcion in referencias:
        img = cv.imread(str(imagenes / origen))
        cv.imwrite(str(carpeta / destino), img)
        indice.append(f"{destino}: {descripcion}")

    # 08: Paso 1, ROI.
    sin_tapon = cv.imread(str(imagenes / "captura_1.jpg"))
    roi_sin_tapon = fms205.recortar_roi(sin_tapon, fms205.ROI)
    cv.imwrite(str(carpeta / "08_paso1_roi_recorte.png"), roi_sin_tapon)
    indice.append("08_paso1_roi_recorte.png: Recorte fijo (ROI) sobre captura_1 (Paso 1).")

    # 09-11: Paso 2, comparacion del binarizado: el hueco significa algo
    # distinto segun el material (hallazgo clave del diseno).
    def binaria_de(nombre_imagen):
        img = cv.imread(str(imagenes / nombre_imagen))
        recorte = fms205.recortar_roi(img, fms205.ROI)
        grises = convertir_a_grises(recorte)
        return fms205.limpiar_binaria(binarizar(suavizar(grises))), recorte

    bin_metal, roi_metal = binaria_de("captura_10.jpg")
    cv.imwrite(str(carpeta / "09_paso2_binarizado_metal_bajo.png"), bin_metal)
    indice.append("09_paso2_binarizado_metal_bajo.png: captura_10 (metal bajo): el hueco detectado es pequeno (Paso 2).")

    bin_negro, roi_negro = binaria_de("captura_60.jpg")
    cv.imwrite(str(carpeta / "10_paso2_binarizado_negro_bajo.png"), bin_negro)
    indice.append("10_paso2_binarizado_negro_bajo.png: captura_60 (negro bajo): todo el tapon se lee como 'hueco' por ser oscuro (Paso 2).")

    bin_blanco, roi_blanco = binaria_de("captura_90.jpg")
    cv.imwrite(str(carpeta / "11_paso2_binarizado_blanco_bajo.png"), bin_blanco)
    indice.append("11_paso2_binarizado_blanco_bajo.png: captura_90 (blanco bajo): el hueco detectado es pequeno, igual que el metalico (Paso 2).")

    # 12-13: Paso 6, tecnica del gradiente Sobel para separar SIN_TAPON de
    # TAPON_METALICO_ALTO (el desempate mas dificil de todo el proyecto).
    def visualizar_gradiente(nombre_imagen, nombre_archivo, descripcion):
        img = cv.imread(str(imagenes / nombre_imagen))
        recorte = fms205.recortar_roi(img, fms205.ROI)
        grises = convertir_a_grises(recorte)
        binaria = fms205.limpiar_binaria(binarizar(suavizar(grises)))
        contornos, jerarquia = encontrar_contornos(binaria)
        bloque = fms205.encontrar_bloque(contornos)
        hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
        gradiente = fms205.medir_gradiente_interior(grises, hueco)

        dibujo = recorte.copy()
        cv.drawContours(dibujo, [hueco], -1, (0, 0, 255), 2)
        _texto(dibujo, f"gradiente interior: {gradiente:.1f}", y=25, escala=0.55, color=(0, 255, 255))
        cv.imwrite(str(carpeta / nombre_archivo), dibujo)
        indice.append(f"{nombre_archivo}: {descripcion} (gradiente medido: {gradiente:.1f}, Paso 6).")

    visualizar_gradiente("captura_1.jpg", "12_paso6_gradiente_sin_tapon.png", "SIN_TAPON: cavidad hueca, gradiente interior alto")
    visualizar_gradiente("captura_27.jpg", "13_paso6_gradiente_metal_alto.png", "TAPON_METALICO_ALTO: tapa plana, gradiente interior bajo")

    # 14-20: Paso 6, resultado final (bloque + hueco + estado) en las 7
    # categorias.
    def resultado_final(imagen_bgr, nombre_archivo, descripcion):
        estado = fms205.procesar(imagen_bgr)
        recorte = fms205.recortar_roi(imagen_bgr, fms205.ROI)
        dibujo = recorte.copy()
        grises = convertir_a_grises(recorte)
        binaria = fms205.limpiar_binaria(binarizar(suavizar(grises)))
        contornos, jerarquia = encontrar_contornos(binaria)
        bloque = fms205.encontrar_bloque(contornos)
        cv.drawContours(dibujo, [bloque], -1, (255, 255, 0), 2)
        hueco = encontrar_hueco_principal(contornos, jerarquia, bloque)
        if hueco is not None:
            cv.drawContours(dibujo, [hueco], -1, (0, 0, 255), 2)
        _texto(dibujo, f"ESTADO: {estado}", escala=0.45)
        cv.imwrite(str(carpeta / nombre_archivo), dibujo)
        indice.append(f"{nombre_archivo}: {descripcion} (resultado: {estado}).")

    resultado_final(sin_tapon, "14_paso6_resultado_final_sin_tapon.png", "Resultado final sobre captura_1 (sin tapon)")
    resultado_final(cv.imread(str(imagenes / "captura_10.jpg")), "15_paso6_resultado_final_metal_bajo.png", "Resultado final sobre captura_10 (tapon metalico bajo)")
    resultado_final(cv.imread(str(imagenes / "captura_27.jpg")), "16_paso6_resultado_final_metal_alto.png", "Resultado final sobre captura_27 (tapon metalico alto)")
    resultado_final(cv.imread(str(imagenes / "captura_60.jpg")), "17_paso6_resultado_final_negro_bajo.png", "Resultado final sobre captura_60 (tapon negro bajo)")
    resultado_final(cv.imread(str(imagenes / "captura_70.jpg")), "18_paso6_resultado_final_negro_alto.png", "Resultado final sobre captura_70 (tapon negro alto)")
    resultado_final(cv.imread(str(imagenes / "captura_90.jpg")), "19_paso6_resultado_final_blanco_bajo.png", "Resultado final sobre captura_90 (tapon blanco bajo)")
    resultado_final(cv.imread(str(imagenes / "captura_110.jpg")), "20_paso6_resultado_final_blanco_alto.png", "Resultado final sobre captura_110 (tapon blanco alto)")

    (carpeta / "00_indice.txt").write_text(
        "Figuras de FMS-205, en el orden de docs/bitacora_algoritmos.txt\n"
        "=================================================================\n\n"
        + "\n".join(indice) + "\n",
        encoding="utf-8",
    )
    print(f"FMS-205: {len(indice)} figuras generadas en {carpeta}")


# ---------------------------------------------------------------------------
# FMS-206
# ---------------------------------------------------------------------------

def generar_figuras_fms206():
    carpeta = CARPETA_FIGURAS / "fms206"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagenes = RAIZ_REPO / "data" / "Imagenes_FMS" / "FMS206"
    indice = []

    # 01: Paso 1, ROI.
    vacio = cv.imread(str(imagenes / "captura_1.jpg"))
    roi_vacio = fms206.recortar_roi(vacio, fms206.ROI)
    cv.imwrite(str(carpeta / "01_paso1_roi_recorte.png"), roi_vacio)
    indice.append("01_paso1_roi_recorte.png: Recorte fijo (ROI) sobre captura_1, sin tornillos (Paso 1).")

    # 02: Paso 2, las 4 posiciones de tornillo marcadas sobre el hueco vacio.
    dibujo = roi_vacio.copy()
    for nombre_pos, datos in fms206.POSICIONES_TORNILLO.items():
        cv.circle(dibujo, datos["punto"], datos["radio"], (0, 255, 255), 2)
        cv.putText(dibujo, nombre_pos, (datos["punto"][0] - 20, datos["punto"][1] - datos["radio"] - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv.imwrite(str(carpeta / "02_paso2_posiciones_taladros.png"), dibujo)
    indice.append("02_paso2_posiciones_taladros.png: Las 4 posiciones fijas de tornillo, localizadas con Hough Circles (Paso 2).")

    # 03-04: Paso 3, zoom comparando taladro vacio vs tornillo puesto en la
    # posicion "arriba", para ilustrar el desplazamiento por paralaje.
    def zoom_arriba(nombre_imagen):
        img = cv.imread(str(imagenes / nombre_imagen))
        recorte = fms206.recortar_roi(img, fms206.ROI)
        px, py = fms206.POSICIONES_TORNILLO["arriba"]["punto"]
        margen = 35
        zoom = recorte[max(0, py - margen):py + margen, max(0, px - margen):px + margen]
        return cv.resize(zoom, None, fx=5, fy=5, interpolation=cv.INTER_NEAREST)

    cv.imwrite(str(carpeta / "03_paso3_zoom_arriba_vacio.png"), zoom_arriba("captura_1.jpg"))
    indice.append("03_paso3_zoom_arriba_vacio.png: Zoom x5 de la posicion 'arriba' vacia, captura_1 (Paso 3).")

    cv.imwrite(str(carpeta / "04_paso3_zoom_arriba_tornillo.png"), zoom_arriba("captura_44.jpg"))
    indice.append("04_paso3_zoom_arriba_tornillo.png: Zoom x5 de la misma posicion con tornillo, captura_44: se ve desplazado hacia arriba por paralaje (Paso 3).")

    # 05-09: Paso 4, resultado final (las 4 posiciones marcadas en verde/rojo
    # + estado) para 0, 1, 2, 3 y 4 tornillos.
    def resultado_final(nombre_imagen, nombre_archivo, descripcion):
        img = cv.imread(str(imagenes / nombre_imagen))
        recorte = fms206.recortar_roi(img, fms206.ROI)
        grises = suavizar(convertir_a_grises(recorte))
        presencia = fms206.detectar_tornillos(grises)
        estado = "COMPLETO" if all(presencia.values()) else "INCOMPLETO"

        dibujo = recorte.copy()
        for nombre_pos, datos in fms206.POSICIONES_TORNILLO.items():
            color = (0, 255, 0) if presencia[nombre_pos] else (0, 0, 255)
            cv.circle(dibujo, datos["punto"], datos["radio"], color, 2)
        _texto(dibujo, f"ESTADO: {estado}", escala=0.6)
        cv.imwrite(str(carpeta / nombre_archivo), dibujo)
        indice.append(f"{nombre_archivo}: {descripcion} (resultado: {estado}).")

    resultado_final("captura_1.jpg", "05_paso4_resultado_0_tornillos.png", "Resultado final sobre captura_1 (0 tornillos)")
    resultado_final("captura_18.jpg", "06_paso4_resultado_1_tornillo.png", "Resultado final sobre captura_18 (1 tornillo)")
    resultado_final("captura_31.jpg", "07_paso4_resultado_2_tornillos.png", "Resultado final sobre captura_31 (2 tornillos)")
    resultado_final("captura_37.jpg", "08_paso4_resultado_3_tornillos.png", "Resultado final sobre captura_37 (3 tornillos)")
    resultado_final("captura_44.jpg", "09_paso4_resultado_completo.png", "Resultado final sobre captura_44 (4 tornillos, COMPLETO)")

    (carpeta / "00_indice.txt").write_text(
        "Figuras de FMS-206, en el orden de docs/bitacora_algoritmos.txt\n"
        "=================================================================\n\n"
        + "\n".join(indice) + "\n",
        encoding="utf-8",
    )
    print(f"FMS-206: {len(indice)} figuras generadas en {carpeta}")


if __name__ == "__main__":
    generar_figuras_fms201()
    generar_figuras_fms202()
    generar_figuras_fms205()
    generar_figuras_fms206()
