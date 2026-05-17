import pyads

def clasificar_variable(symbol):
    """
    Determina si la variable es:
    - Entrada (%I)
    - Salida (%Q)
    - Local (resto)
    """
    if symbol.index_group == pyads.constants.ADSIGRP_IOIMAGE_RWIB:  # Inputs
        return "%I (Input)"
    elif symbol.index_group == pyads.constants.ADSIGRP_IOIMAGE_RWOB:  # Outputs
        return "%Q (Output)"
    else:
        return "Local"

def main():
    # Cambia estos valores
    AMS_NET_ID = "10.60.186.36.1.1"
    AMS_PORT = 851  # típico para TwinCAT PLC Runtime 1

    plc = pyads.Connection(AMS_NET_ID, AMS_PORT)

    try:
        plc.open()
        print("Conectado al servidor ADS\n")

        symbols = plc.get_all_symbols()

        print(f"{'Nombre':40} {'Tipo':20} {'Clase'}")
        print("-" * 80)

        for sym in symbols:
            clase = clasificar_variable(sym)
            print(f"{sym.name:40} {sym.symbol_type:20} {clase}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        plc.close()
        print("\nConexion cerrada")


if __name__ == "__main__":
    main()