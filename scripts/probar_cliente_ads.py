"""
scripts/probar_cliente_ads.py: verifica el protocolo de ConexionEstacion
sin ningún PLC real ni servidor de red.

Por qué no un pyads.testserver.AdsTestServer real: en esta máquina ya hay
un router ADS de TwinCAT instalado y escuchando en el puerto 48898 (el mismo
puerto fijo que usa el protocolo AMS/TCP), así que un AdsTestServer local no
puede levantar su propio socket ahí (conflicto de puerto) ni pyads llega a
alcanzarlo por otro puerto (el router siempre habla por el 48898). En su
lugar, se sustituye pyads.Connection por una PLC falsa en memoria que
implementa el mismo protocolo (open/close/write_by_name/add_device_notification):
así se comprueba la LÓGICA de ConexionEstacion (nombres de variable, mapeo
resultado -> índice, aviso de trigger, aro de luz) de forma aislada, igual
que los algoritmos de visión se comprueban contra imágenes sin cámara.

Uso:
    python scripts/probar_cliente_ads.py
"""

import sys
from pathlib import Path
from unittest.mock import patch

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO))

from src.comunicacion import cliente_ads


class PLCFalsa:
    """
    Sustituto en memoria de pyads.Connection: guarda lo que se escribe y
    permite simular un cambio de bTrigger desde el "PLC", sin abrir ningún
    socket real.
    """

    def __init__(self, *args, **kwargs):
        self.abierta = False
        self.escrituras = {}
        self._callback_notificacion = None

    def open(self):
        self.abierta = True

    def close(self):
        self.abierta = False

    def write_by_name(self, nombre, valor, tipo=None):
        self.escrituras[nombre] = valor

    def notification(self, plc_datatype=None, timestamp_as_filetime=False):
        def decorador(func):
            def envoltura(handle=1, name="", timestamp=None, value=None):
                return func(handle, name, timestamp, value)

            return envoltura

        return decorador

    def add_device_notification(self, nombre, atributos, callback):
        self._callback_notificacion = callback
        return (1, 2)

    def del_device_notification(self, handle, user_handle):
        self._callback_notificacion = None

    def simular_trigger(self):
        """Ayuda de test: simula que el PLC ha puesto bTrigger a TRUE."""
        self._callback_notificacion(value=True)


RESULTADOS_FMS201 = ["PIEZA_OK", "PIEZA_NOK", "ESTACION_VACIA"]


def main():
    with patch.object(cliente_ads.pyads, "Connection", PLCFalsa):
        # --- estación dueña del aro de luz ---
        estacion = cliente_ads.ConexionEstacion(
            "FMS201", None, None, "GVL_FMS201", RESULTADOS_FMS201, es_dueña_de_la_luz=True
        )
        estacion.conectar()
        assert estacion._plc.abierta, "conectar() no abrió la conexión"

        # 1. notificación de trigger
        recibidos = []
        estacion.suscribir_trigger(lambda id_estacion: recibidos.append(id_estacion))
        estacion._plc.simular_trigger()
        assert recibidos == ["FMS201"], f"el trigger no llegó al callback: {recibidos}"
        print("[OK] suscribir_trigger dispara el callback con el id de estación")

        # 2. marcar_inspeccionando
        estacion.marcar_inspeccionando(True)
        assert estacion._plc.escrituras["GVL_FMS201.bInspeccionando"] is True
        print("[OK] marcar_inspeccionando escribe bInspeccionando")

        # 3. escribir_resultado: índice + texto
        estacion.escribir_resultado("ESTACION_VACIA")
        assert estacion._plc.escrituras["GVL_FMS201.iResultado"] == 2
        assert estacion._plc.escrituras["GVL_FMS201.sResultado"] == "ESTACION_VACIA"
        assert estacion._plc.escrituras["GVL_FMS201.bResultadoListo"] is True
        print("[OK] escribir_resultado mapea el string al índice correcto")

        # 4. limpiar_ciclo
        estacion.limpiar_ciclo()
        assert estacion._plc.escrituras["GVL_FMS201.bInspeccionando"] is False
        assert estacion._plc.escrituras["GVL_FMS201.bResultadoListo"] is False
        print("[OK] limpiar_ciclo baja bInspeccionando y bResultadoListo")

        # 5. aro de luz: esta instancia SÍ es la dueña
        estacion.controlar_aro_luz(True)
        assert estacion._plc.escrituras["GVL_Iluminacion.bAroLuzOn"] is True
        print("[OK] controlar_aro_luz escribe cuando la estación es la dueña")

        # 6. aro de luz: una estación que NO es la dueña no debe escribir nada
        otra = cliente_ads.ConexionEstacion(
            "FMS202", None, None, "GVL_FMS202", ["ERROR"], es_dueña_de_la_luz=False
        )
        otra.conectar()
        otra.controlar_aro_luz(True)
        assert "GVL_Iluminacion.bAroLuzOn" not in otra._plc.escrituras
        print("[OK] controlar_aro_luz no hace nada si la estación no es la dueña")

    print("\nProtocolo ADS verificado correctamente (sin hardware real).")


if __name__ == "__main__":
    main()
