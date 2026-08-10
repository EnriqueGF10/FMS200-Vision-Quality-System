"""
src/main.py: orquestador de las 4 estaciones FMS-200.

Solo hay una cámara y un aro de luz físicos para las 4 estaciones, así que
la captura + inspección es forzosamente secuencial: una cola productor-consumidor
con un único hilo trabajador es quien toca la cámara/aro de luz, evitando
condiciones de carrera sobre ese recurso compartido.

Cada estación dispara una tarea de dos formas posibles, indistintas para el
hilo trabajador:
  - Disparo real: notificación ADS de bTrigger en su PLC (src/comunicacion/cliente_ads.py).
  - Disparo manual (teclas 1-4): para poder probar sin tener las 4 PLCs
    conectadas a la vez, que es la situación real ahora mismo.

Si una estación no tiene ams_net_id en src/config_estaciones.py (todavía no
hay PLC asignada), simplemente no se crea su ConexionEstacion: se puede
seguir disparando esa estación a mano y ver el resultado, solo que no se
escribe nada por ADS.

Si no hay cámara conectada, se cae a leer la primera imagen de muestra de
data/Imagenes_FMS/<estación>/, así se puede probar todo el flujo (cola,
hilo, algoritmo, overlay) sin ningún hardware.

Uso:
    python -m src.main

    Teclas: 1-4 simula el trigger de FMS201/202/205/206, q sale.
"""

import queue
import threading
import time
from pathlib import Path

import cv2 as cv
import numpy as np

from src.config_estaciones import ESTACIONES, ESTACION_DUEÑA_DE_LA_LUZ
from src.comunicacion.cliente_ads import ConexionEstacion
from src.hmi.panel import dibujar_overlay

RAIZ_REPO = Path(__file__).resolve().parents[1]

TECLAS_ESTACION = {
    ord("1"): "FMS201",
    ord("2"): "FMS202",
    ord("3"): "FMS205",
    ord("4"): "FMS206",
}


def abrir_camara():
    """Intenta abrir la cámara del sistema. Devuelve None si no hay ninguna."""
    camara = cv.VideoCapture(0)
    if not camara.isOpened():
        return None
    return camara


def leer_imagen_de_respaldo(id_estacion):
    """
    Sin cámara conectada, se usa la primera imagen de muestra de esa
    estación (mismas imágenes con las que se validó el algoritmo), para
    poder probar el flujo completo sin hardware.
    """
    carpeta = RAIZ_REPO / "data" / "Imagenes_FMS" / id_estacion
    imagenes = sorted(carpeta.glob("captura_*.jpg"))
    if not imagenes:
        raise FileNotFoundError(f"No hay imágenes de respaldo para {id_estacion} en {carpeta}")
    return cv.imread(str(imagenes[0]))


def capturar_frame(camara, id_estacion):
    if camara is not None and camara.isOpened():
        ok, frame = camara.read()
        if ok:
            return frame
    return leer_imagen_de_respaldo(id_estacion)


def crear_conexiones_activas(cola):
    """
    Crea una ConexionEstacion por cada estación que ya tiene ams_net_id
    asignado en config_estaciones.py, y suscribe su trigger para que
    encole tareas igual que el disparo manual (mismo camino de cola/hilo
    para ambos orígenes de disparo).
    """
    conexiones = {}
    for id_estacion, datos in ESTACIONES.items():
        if datos["ams_net_id"] is None:
            continue
        conexion = ConexionEstacion(
            id_estacion,
            datos["ams_net_id"],
            datos["ams_port"],
            datos["nombre_gvl"],
            datos["resultados"],
            es_dueña_de_la_luz=(id_estacion == ESTACION_DUEÑA_DE_LA_LUZ),
        )
        conexion.conectar()
        conexion.suscribir_trigger(lambda id_estacion=id_estacion: cola.put(id_estacion))
        conexiones[id_estacion] = conexion
    return conexiones


def procesar_tarea(id_estacion, camara, conexiones, estado, lock):
    datos = ESTACIONES[id_estacion]
    conexion = conexiones.get(id_estacion)
    conexion_luz = conexiones.get(ESTACION_DUEÑA_DE_LA_LUZ)

    if conexion is not None:
        conexion.marcar_inspeccionando(True)
    if conexion_luz is not None:
        conexion_luz.controlar_aro_luz(True)

    frame = capturar_frame(camara, id_estacion)

    if conexion_luz is not None:
        conexion_luz.controlar_aro_luz(False)

    resultado = datos["modulo"].procesar(frame)

    if conexion is not None:
        conexion.escribir_resultado(resultado)
        conexion.limpiar_ciclo()

    with lock:
        estado["estacion_actual"] = id_estacion
        estado["ultimo_resultado"] = resultado
        estado["historial"].append((id_estacion, resultado))


def hilo_trabajador(cola, camara, conexiones, estado, lock, detener):
    """
    Único hilo que toca la cámara/aro de luz. Consume la cola en orden de
    llegada, así que dos triggers casi simultáneos de estaciones distintas
    se procesan uno detrás de otro, nunca a la vez.
    """
    while not detener.is_set():
        try:
            id_estacion = cola.get(timeout=0.2)
        except queue.Empty:
            continue
        try:
            procesar_tarea(id_estacion, camara, conexiones, estado, lock)
        except Exception as error:
            print(f"[ERROR] fallo procesando {id_estacion}: {error}")
        cola.task_done()


def main():
    camara = abrir_camara()
    cola = queue.Queue()
    lock = threading.Lock()
    detener = threading.Event()
    estado = {"estacion_actual": None, "ultimo_resultado": None, "historial": []}

    conexiones = crear_conexiones_activas(cola)

    hilo = threading.Thread(
        target=hilo_trabajador, args=(cola, camara, conexiones, estado, lock, detener), daemon=True
    )
    hilo.start()

    if conexiones:
        print(f"Conectado por ADS a: {', '.join(conexiones)}")
    else:
        print("Sin ninguna PLC conectada (ams_net_id sin asignar en config_estaciones.py).")
    if camara is None:
        print("Sin cámara detectada: se usará una imagen de muestra por estación.")
    print("Teclas: 1=FMS201  2=FMS202  3=FMS205  4=FMS206  q=salir\n")

    ultimo_tiempo = time.time()
    try:
        while True:
            if camara is not None and camara.isOpened():
                ok, frame_en_vivo = camara.read()
                if not ok:
                    frame_en_vivo = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                frame_en_vivo = np.zeros((480, 640, 3), dtype=np.uint8)

            ahora = time.time()
            fps = 1.0 / (ahora - ultimo_tiempo) if ahora > ultimo_tiempo else 0.0
            ultimo_tiempo = ahora

            with lock:
                frame_anotado = dibujar_overlay(
                    frame_en_vivo,
                    estado["estacion_actual"],
                    estado["ultimo_resultado"],
                    list(estado["historial"]),
                    fps,
                )

            cv.imshow("FMS-200 - Supervision", frame_anotado)
            tecla = cv.waitKey(1) & 0xFF
            if tecla == ord("q"):
                break
            if tecla in TECLAS_ESTACION:
                cola.put(TECLAS_ESTACION[tecla])
    finally:
        detener.set()
        hilo.join(timeout=2)
        for conexion in conexiones.values():
            conexion.desconectar()
        if camara is not None:
            camara.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    main()
