import pyads

# Local NetID
AMS_NET_ID = '10.60.186.36.1.1'
# Puerto de conexión del PLC
PUERTO_PLC = 851


def probar_conexion():
    #plc = None
    try:
        # 1. Creamos la conexión
        # Al estar en el mismo PC, la IP es 127.0.0.1
        plc = pyads.Connection(AMS_NET_ID, PUERTO_PLC, '127.0.0.1')
        plc.open()

        if plc.is_open:
            print("ÉXITO: Conectado al PLC Beckhoff.")
            print(f"Local Address? : {plc.get_local_address()}")
            print(plc.read_state())

            # 2. Intentamos escribir en la variable del MAIN
            # En este caso declarada en TwinCAT como bPiezaOK: BOOL;
            print("Enviando comando de prueba...")
            plc.write_by_name("Main.bPiezaOK", False)

            # 3. Leemos para confirmar la recepción
            plc.read_by_name('Main.PiezaOK')
            print(f"Confirmación recibida del PLC: {confirmacion}")

        else:
            print("ERROR: No se puedo abrir la conexión.")
    
    except Exception as e:
        print(f"ERROR de sistema: {e}")
        print("\nConsejo: Revisa que TwinCAT 3 esté en modo RUN (icono verde en barra de tareas)")

if __name__ == "__main__":
    probar_conexion()
