# FMS200-Vision-Quality-System

Sistema de control de calidad por visión artificial para las estaciones de ensamblaje de la célula didáctica SMC FMS-200 (FMS-201, FMS-202, FMS-205 y FMS-206). Desarrollado como Trabajo Fin de Grado en Ingeniería Electrónica, Robótica y Mecatrónica (Universidad de Málaga).

El sistema combina una cámara web y un aro de luz difusa con cuatro algoritmos de visión artificial clásica programados en Python con OpenCV, y se comunica con los PLC Beckhoff de cada estación mediante el protocolo ADS (librería PyADS). Un orquestador atiende las solicitudes de inspección de las cuatro estaciones y muestra el resultado en una interfaz de supervisión en tiempo real.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `src/` | Código del sistema: orquestador (`main.py`), configuración de estaciones, cliente ADS, interfaz de supervisión y algoritmos de visión |
| `data/Imagenes_FMS/` | Imágenes de muestra etiquetadas de cada estación |
| `scripts/` | Herramientas auxiliares, entre ellas `probar_cliente_ads.py` |
| `hardware/cad/` | Diseño de los soportes mecánicos de la cámara y el aro de luz |
| `docs/memoria/` | Figuras empleadas en la memoria del proyecto |
| `tests/` | Pruebas del proyecto |

## Instalación y ejecución

Estos pasos permiten ejecutar el proyecto en cualquier equipo, sin necesidad de disponer del hardware del laboratorio.

### 1. Comprobar los requisitos previos

El equipo debe tener instalados Git y Python 3.11 o superior (que ya incluye `pip`). Pueden comprobarse desde cualquier terminal:

```bash
git --version
python --version
pip --version
```

Si algún comando no se reconoce, el programa correspondiente no está instalado o no es accesible desde la terminal. Git puede descargarse desde <https://git-scm.com/> y Python desde <https://www.python.org/>. Durante la instalación de Python en Windows, conviene marcar la opción **Add python.exe to PATH**.

### 2. Abrir una terminal en la carpeta donde se quiere alojar el proyecto

Elige una carpeta cualquiera del equipo (por ejemplo, el Escritorio) y abre una terminal en ella. En Windows, la forma más directa es abrir la carpeta en el explorador de archivos, escribir `powershell` en la barra de direcciones y pulsar Intro. También puede usarse la terminal integrada de Visual Studio Code (**Terminal > Nueva terminal**).

### 3. Clonar el repositorio

```bash
git clone https://github.com/EnriqueGF10/FMS200-Vision-Quality-System.git
cd FMS200-Vision-Quality-System
```

Todos los pasos siguientes se ejecutan dentro de esta carpeta.

### 4. Crear el entorno virtual

Las dependencias se instalan en un entorno virtual dedicado, aislado del Python del sistema:

```bash
python -m venv Entorno_TFG
```

### 5. Activar el entorno virtual

```bash
# Windows (PowerShell)
Entorno_TFG\Scripts\Activate.ps1

# Linux / macOS
source Entorno_TFG/bin/activate
```

En Windows, PowerShell bloquea por defecto la ejecución de scripts locales, por lo que la activación falla la primera vez. Antes de activar el entorno hay que habilitar la ejecución de scripts para la sesión actual:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
```

El parámetro `-Scope Process` limita el permiso a la ventana de terminal actual, sin modificar la configuración del equipo, por lo que este comando debe repetirse cada vez que se abra una terminal nueva. Con el entorno activado, su nombre aparece entre paréntesis al inicio de la línea de comandos: `(Entorno_TFG)`.

### 6. Instalar las dependencias

El fichero `requirements.txt` enumera las librerías del proyecto con su versión mínima compatible:

```
opencv-python>=4.8.0
numpy>=1.24.0
pyads>=3.3.9
```

Con el entorno activado, se instalan de una sola vez:

```bash
pip install -r requirements.txt
```

La instalación termina con un mensaje `Successfully installed`.

### 7. Ejecutar el sistema

Desde la raíz del repositorio:

```bash
python -m src.main
```

Si no hay ninguna cámara conectada, el sistema recurre automáticamente a las imágenes de muestra del proyecto. Si ningún PLC está disponible, cada estación puede dispararse manualmente con el teclado:

| Tecla | Acción |
|---|---|
| `1` | Inspeccionar FMS-201 |
| `2` | Inspeccionar FMS-202 |
| `3` | Inspeccionar FMS-205 |
| `4` | Inspeccionar FMS-206 |
| `q` | Salir |

### 8. (Opcional) Probar la comunicación ADS sin hardware

Para validar únicamente la capa de comunicación ADS sin un PLC real, el repositorio incluye un script que levanta un servidor ADS simulado en local:

```bash
python scripts/probar_cliente_ads.py
```

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el fichero `LICENSE` para más detalles.
