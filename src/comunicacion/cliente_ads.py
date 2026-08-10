"""
src/comunicacion/cliente_ads.py: cliente PyADS de una estación.

Envuelve una única conexión ADS (una PLC) y expone el protocolo acordado en
src/config_estaciones.py: notificación de bTrigger, escritura del resultado
como (índice entero + texto), y control del aro de luz cuando la estación es
la dueña de esa salida.

No abre cámara ni ventanas: solo habla con el PLC. Se prueba de forma
aislada con scripts/probar_cliente_ads.py contra un pyads.testserver.AdsTestServer
local, sin necesitar ningún PLC real.
"""

import pyads


class ConexionEstacion:
    """
    Conexión ADS a la PLC de una estación concreta.

    Cada instancia habla con UNA PLC. El orquestador (src/main.py) crea una
    instancia por cada fila de config_estaciones.ESTACIONES.
    """

    def __init__(self, id_estacion, ams_net_id, ams_port, nombre_gvl, resultados, es_dueña_de_la_luz=False):
        self.id_estacion = id_estacion
        self.nombre_gvl = nombre_gvl
        self.resultados = resultados
        self.es_dueña_de_la_luz = es_dueña_de_la_luz
        self._plc = pyads.Connection(ams_net_id, ams_port)
        self._handle_notificacion = None

    def conectar(self):
        self._plc.open()

    def desconectar(self):
        if self._handle_notificacion is not None:
            self._plc.del_device_notification(*self._handle_notificacion)
            self._handle_notificacion = None
        self._plc.close()

    def suscribir_trigger(self, callback):
        """
        Registra una notificación ADS sobre bTrigger: cuando el PLC lo pone a
        TRUE, PyADS llama a `callback(id_estacion)` en su propio hilo, sin que
        el orquestador tenga que hacer polling.

        El callback se envuelve con `self._plc.notification(...)`: sin ese
        decorador, add_device_notification entrega el dato crudo de ADS en
        vez del valor Python ya convertido (bool en este caso).
        """

        @self._plc.notification(pyads.PLCTYPE_BOOL)
        def _al_cambiar_trigger(handle, name, timestamp, value):
            if value:
                callback(self.id_estacion)

        atributos = pyads.NotificationAttrib(length=1)
        self._handle_notificacion = self._plc.add_device_notification(
            f"{self.nombre_gvl}.bTrigger", atributos, _al_cambiar_trigger
        )

    def marcar_inspeccionando(self, activo):
        self._plc.write_by_name(f"{self.nombre_gvl}.bInspeccionando", activo, pyads.PLCTYPE_BOOL)

    def escribir_resultado(self, resultado_str):
        """
        Escribe el resultado en el PLC: código entero (índice en la lista de
        resultados de esta estación), el mismo texto, y el pulso de
        bResultadoListo que indica al PLC que ya puede leerlo.
        """
        codigo = self.resultados.index(resultado_str)
        self._plc.write_by_name(f"{self.nombre_gvl}.iResultado", codigo, pyads.PLCTYPE_INT)
        self._plc.write_by_name(f"{self.nombre_gvl}.sResultado", resultado_str, pyads.PLCTYPE_STRING)
        self._plc.write_by_name(f"{self.nombre_gvl}.bResultadoListo", True, pyads.PLCTYPE_BOOL)

    def limpiar_ciclo(self):
        """Baja bInspeccionando y bResultadoListo: la estación queda lista para el próximo trigger."""
        self.marcar_inspeccionando(False)
        self._plc.write_by_name(f"{self.nombre_gvl}.bResultadoListo", False, pyads.PLCTYPE_BOOL)

    def controlar_aro_luz(self, encendido):
        """
        Enciende/apaga el aro de luz físico. Solo tiene efecto si esta
        instancia es la dueña de esa salida (config_estaciones.ESTACION_DUEÑA_DE_LA_LUZ);
        las demás no hacen nada, así el orquestador no necesita preguntar
        "quién soy" antes de llamar a este método.
        """
        if not self.es_dueña_de_la_luz:
            return
        from src.config_estaciones import VARIABLE_ARO_LUZ

        self._plc.write_by_name(VARIABLE_ARO_LUZ, encendido, pyads.PLCTYPE_BOOL)
