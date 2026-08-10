"""
src/config_estaciones.py: tabla declarativa de las 4 estaciones.

Une cada estación con su algoritmo de visión (src/vision/fmsXXX/fmsXXX.py) y
con los datos necesarios para hablar con su PLC por PyADS. Añadir o quitar
una estación es editar este diccionario, no tocar la lógica de src/main.py.

Convención de variables PLC (una GVL por estación, mismo esquema en las 4):
    bTrigger        BOOL   PLC -> PC   pieza colocada y asentada, lista para inspeccionar
    bInspeccionando BOOL   PC -> PLC   el PC ha tomado el trigger y está procesando
    iResultado      INT    PC -> PLC   índice del resultado en la lista "resultados" de abajo
    sResultado      STRING PC -> PLC   mismo resultado en texto, para trazabilidad
    bResultadoListo BOOL   PC -> PLC   pulso a TRUE cuando iResultado/sResultado son válidos

Protocolo: PLC sube bTrigger -> PC lo detecta -> PC sube bInspeccionando ->
PC captura y procesa -> PC escribe iResultado/sResultado -> PC sube
bResultadoListo -> PLC lee y baja bTrigger -> PC ve bTrigger en FALSE y baja
bInspeccionando/bResultadoListo (listo para el siguiente ciclo).

ams_net_id/ams_port quedan a None hasta que se conecte cada estación a su
PLC real en el laboratorio (el hardware solo permite probar una a la vez).
"""

from src.vision.fms201 import fms201
from src.vision.fms202 import fms202
from src.vision.fms205 import fms205
from src.vision.fms206 import fms206


# Nombre de la variable, en la GVL del PLC dueño de la luz, que enciende el
# aro de luz físico. Solo hay un aro de luz para las 4 estaciones, así que
# vive en una única PLC (fija) y no en cada una de las 4 GVL de estación.
GVL_ILUMINACION = "GVL_Iluminacion"
VARIABLE_ARO_LUZ = f"{GVL_ILUMINACION}.bAroLuzOn"

# Estación cuya PLC controla físicamente el aro de luz. 
# Modificar este valor en función de la máquina que estemos corriendo.
ESTACION_DUEÑA_DE_LA_LUZ = "FMS201"


ESTACIONES = {
    "FMS201": {
        "modulo": fms201,
        "nombre_gvl": "GVL_FMS201",
        # Runtime local de TwinCAT 3 en este mismo PC (proyecto de prueba
        # "PruebaADS"), usado para validar el protocolo ADS sin PLC física
        # ni cámara/aro de luz reales.
        "ams_net_id": "10.60.186.36.1.1",
        "ams_port": 851,
        "resultados": ["PIEZA_OK", "PIEZA_NOK", "ESTACION_VACIA"],
    },
    "FMS202": {
        "modulo": fms202,
        "nombre_gvl": "GVL_FMS202",
        "ams_net_id": None,
        "ams_port": None,
        "resultados": [
            "RODAMIENTO_NEGRO_ALTO",
            "RODAMIENTO_NEGRO_BAJO",
            "RODAMIENTO_BOLAS",
            "ERROR",
        ],
    },
    "FMS205": {
        "modulo": fms205,
        "nombre_gvl": "GVL_FMS205",
        "ams_net_id": None,
        "ams_port": None,
        "resultados": [
            "SIN_TAPON",
            "TAPON_METALICO_ALTO",
            "TAPON_METALICO_BAJO",
            "TAPON_NEGRO_ALTO",
            "TAPON_NEGRO_BAJO",
            "TAPON_BLANCO_ALTO",
            "TAPON_BLANCO_BAJO",
        ],
    },
    "FMS206": {
        "modulo": fms206,
        "nombre_gvl": "GVL_FMS206",
        "ams_net_id": None,
        "ams_port": None,
        "resultados": ["COMPLETO", "INCOMPLETO"],
    },
}
