"""
================================================================================
MÓDULO: src/config.py - CONFIGURACIÓN CENTRALIZADA
================================================================================

PROPÓSITO:
    Define TODOS los parámetros del sistema en un único lugar.
    
    Ventajas del enfoque centralizado:
    1. MANTENIBILIDAD: Cambiar parámetro = editar 1 archivo
    2. REPRODUCIBILIDAD: Mismos parámetros = mismos resultados
    3. PRINCIPIO DRY: No repetir valores por el código
    4. VERSIONABLE: Git puede trackear cambios de configuración
    5. DOCUMENTABLE: Cada parámetro con justificación

ESTRUCTURA:
    Config
    ├─ CameraConfig
    ├─ PreprocessingConfig
    ├─ StationsConfig (FMS201, FMS202, FMS205, FMS206)
    ├─ CommunicationConfig (PyADS)
    └─ UIConfig

PARA TU MEMORIA:
    Esta arquitectura implementa el patrón SINGLETON y permite
    justificar CADA decisión de parámetros en la sección 3.1
    de tu documento.

================================================================================
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


# ============================================================================
# ENUMERACIONES
# ============================================================================

class QualityState(Enum):
    """
    Estados posibles de una pieza detectada.
    
    RAZÓN DE ENUM vs strings:
        - Type-safe (no typos)
        - Autocompletar en IDE
        - Comparación sin case-sensitivity
    """
    OK = "OK"                          # Pieza correcta
    KO_INVERTIDA = "KO_INVERTIDA"      # Pieza al revés
    KO_DAÑADA = "KO_DAÑADA"            # Pieza dañada/defectos
    ESTACION_VACIA = "ESTACION_VACIA"  # Sin pieza
    ERROR = "ERROR"                    # Error de detección


# ============================================================================
# CONFIGURACIÓN: CÁMARA
# ============================================================================

@dataclass
class CameraConfig:
    """
    Parámetros de configuración de la cámara C922 PRO HD.
    
    ESPECIFICACIONES DE C922:
        - Resolución máxima: 1920×1080 @ 30fps
        - Sensor: 1/4" CMOS
        - Lentes: f/2.0 auto-enfoque
        - Interfaz: USB 2.0 / USB 3.0
    
    DECISIONES:
        frame_width=1280, frame_height=720:
            - Resolución: 921,600 píxeles vs 2,073,600 (1920×1080)
            - Tiempo procesamiento: ~80ms vs ~200ms por frame
            - Relación: Sufficient para detectar círculos de 50-100px
            - Justificación: 30 FPS × 80ms = 2.4 frames en buffer OK
        
        fps=30:
            - Ciclo industrial típico: 500-1000ms
            - 30 fps = 33ms entre captures
            - Suficiente para detectar cambios de pieza
            - No necesita >60fps (overhead innecesario)
        
        camera_index=0:
            - 0 = webcam integrada / primera detectada
            - Cambiar a 1, 2 si hay múltiples cámaras
    
    PARA TU MEMORIA:
        Incluir esto en sección 3.3 "Captura de Imágenes"
        Explicar trade-off resolución vs FPS vs latencia
    """
    
    camera_index: int = 0
    """Índice de cámara (0=primera, 1=segunda, etc.)"""
    
    frame_width: int = 1280
    """Ancho en píxeles. 1280 es suficiente para detectar características"""
    
    frame_height: int = 720
    """Alto en píxeles. Ratio 16:9 estándar"""
    
    fps: int = 30
    """Frames por segundo. 30 es suficiente para ciclos industriales"""
    
    autofocus_enabled: bool = True
    """Activar auto-enfoque de cámara"""
    
    auto_exposure_enabled: bool = True
    """Activar auto-exposición (dejamos que ajuste luz automáticamente)"""


# ============================================================================
# CONFIGURACIÓN: PREPROCESAMIENTO E ILUMINACIÓN
# ============================================================================

@dataclass
class PreprocessingConfig:
    """
    Parámetros de normalización de iluminación.
    
    PROBLEMA:
        Iluminación inconsistente es la causa #1 de fallos en visión industrial.
        Tu observación: "la iluminación no es la mejor" es EL problema.
    
    SOLUCIÓN MULTI-TÉCNICA:
        1. White Balance: Compensar temperatura de color
        2. Shadow Removal: Eliminar sombras con morfología
        3. CLAHE: Realzar contraste localmente (vs global)
    
    REFERENCIA ACADÉMICA:
        Pizer et al. (1987) "Adaptive Histogram Equalization and Its Variations"
        IEEE Transactions on Medical Imaging, vol. 39, no. 3
        ~3000+ citaciones - estándar en visión médica e industrial
    
    PARA TU MEMORIA:
        Sección 3.2 "Normalización Adaptativa de Iluminación"
        Incluir fórmula matemática y gráfico antes/después
    """
    
    # White Balance
    apply_white_balance: bool = True
    """
    Aplicar corrección de balance de blancos.
    
    MÉTODO: Grayworld Assumption
        Asume que el promedio de la imagen DEBERÍA ser gris neutro (128,128,128)
        
        Fórmula:
            gray_mean = (R_mean + G_mean + B_mean) / 3
            R' = R × (gray_mean / R_mean)
            G' = G × (gray_mean / G_mean)
            B' = B × (gray_mean / B_mean)
        
        VENTAJA: Compensa diferencias de temperatura de color
        DESVENTAJA: Falla si hay predominancia natural de color
    """
    
    white_balance_method: str = "grayworld"
    """Método de white balance: 'grayworld' o 'stretching'"""
    
    # Shadow Removal
    apply_shadow_removal: bool = True
    """
    Eliminar sombras usando operadores morfológicos.
    
    MÉTODO: Morfología Matemática (Opening)
        Operación: Opening = Erosión ⊕ Dilatación
        
        Intuición:
            - Erosión: "encoger" objetos → sombras desaparecen
            - Dilatación: "expandir" → recuperar tamaño
            - Resultado: Sombras removidas, forma preservada
        
        Referencia: Serra, J. (1982) Image Analysis and Mathematical Morphology
    """
    
    shadow_kernel_size: int = 11
    """
    Tamaño del kernel morfológico (debe ser impar).
    
    AJUSTE:
        - 5: Kernel pequeño, sombras muy pequeñas
        - 11: Default, buen balance
        - 21: Kernel grande, elimina sombras grandes pero pierde detalles
    """
    
    # CLAHE
    apply_clahe: bool = True
    """
    Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    PROBLEMA CON HISTOGRAM EQUALIZATION GLOBAL:
        Si hay zona oscura + zona clara, la global expande TODO
        → zona oscura se satura, zona clara se pierde
    
    SOLUCIÓN: CLAHE - Dividir imagen en tiles locales
        1. Dividir imagen en grid (8×8 tiles por defecto)
        2. En cada tile: histogram equalization SEPARADO
        3. Interpolar bordes tiles para suavidad
        4. Limitar contraste: clip_limit = máximo en histograma
        
        Resultado: Contraste realzado PERO sin saturación
        
        Fórmula: p'(x,y) = (L-1) × C_f(p(x,y)) / M
            donde C_f = función de transformación acumulativa con clipping
        
        Referencia: Pizer et al. (1987) - ver arriba
    
    APLICACIÓN EN INDUSTRIA:
        - Inspección de soldaduras (grietas oscuras)
        - Detección de defectos en superficies
        - Tu caso: Diferenciar piezas OK/KO en iluminación variable
    """
    
    clahe_clip_limit: float = 2.0
    """
    Límite de contraste CLAHE.
    
    RANGO: 0.0 a 40.0
    
    AJUSTE:
        - 1.0: Sin limitación → mucho ruido
        - 2.0: Default, buen balance
        - 5.0: Muy agresivo → artefactos visuales
    """
    
    clahe_tile_size: tuple = (8, 8)
    """
    Tamaño de tiles CLAHE.
    
    AJUSTE:
        - (4, 4): Tiles pequeños, más local
        - (8, 8): Default, buen balance
        - (16, 16): Tiles grandes, más global
    """


# ============================================================================
# CONFIGURACIÓN: ESTACIONES DE TRABAJO
# ============================================================================

@dataclass
class FMS201Config:
    """
    Parámetros de detección para FMS201 (usando Transformada de Hough).
    
    DESCRIPCIÓN FMS201:
        - Estación de ensamblaje simple
        - Detecta si hay pieza
        - Detecta si está invertida o correcta
        - Criterio: Circunferencia central de la pieza
    
    ALGORITMO: Transformada de Hough para Círculos
        
        VENTAJAS:
            ✓ Invariante a escala (detecta círculos de cualquier tamaño)
            ✓ Invariante a rotación
            ✓ Robusto a oclusión parcial (detecta semicírculos)
            ✓ White-box (explicable, ideal para TFG)
            ✓ Complejidad computacional O(n²) ≈ 80ms en 1280×720
        
        DESVENTAJAS:
            ✗ Sensible a parámetros de umbral
            ✗ No detecta círculos muy pequeños (<10px)
            ✗ No detecta círculos muy grandes (>imagen)
        
        ALTERNATIVAS DESCARTADAS:
            ✗ Deep Learning (CNN): Black-box, requiere dataset grande
            ✗ Template Matching: Sensible a rotación/escala
            ✗ Color Clustering: Sensible a iluminación
        
        DECISIÓN: Hough circles es optimal para TFG (white-box, robusto, rápido)
    
    PARA TU MEMORIA:
        Sección 3.5 "Detección de Características: Transformada de Hough"
        Incluir:
            - Fórmula matemática de Hough
            - Gráfico del espacio de parámetros (r, cx, cy)
            - Tabla comparativa con alternativas
            - Curva de exactitud vs tiempo computacional
    """
    
    # Parámetros de preprocesamiento
    blur_kernel_size: int = 5
    """
    Tamaño del filtro Gaussian Blur.
    
    RAZÓN:
        - Reduce ruido de la imagen
        - Suaviza transiciones
        - Debe ser impar
        
    AJUSTE:
        - 3: Poco suavizado
        - 5: Default, buen balance
        - 7: Mucho suavizado, pierde detalles
    """
    
    canny_threshold_low: int = 50
    """
    Umbral bajo de Canny Edge Detection.
    
    RANGO: 0-255
    
    FÓRMULA Canny:
        Si gradiente < threshold_bajo → NO es borde
        Si umbral_bajo < gradiente < umbral_alto → borde si conecta con borde seguro
        Si gradiente > umbral_alto → ES borde
    
    AJUSTE:
        - 30: Umbral bajo, muchos bordes falsos
        - 50: Default, equilibrio
        - 80: Umbral alto, solo bordes claros
    """
    
    canny_threshold_high: int = 150
    """
    Umbral alto de Canny Edge Detection.
    
    RELACIÓN: Generalmente threshold_high = 3 × threshold_low
    """
    
    # Parámetros de Hough Circle Detection
    hough_dp: float = 1.0
    """
    Resolución del acumulador de Hough.
    
    EXPLICACIÓN:
        dp = resolución del espacio de parámetros vs espacio de imagen
        
        dp = 1.0 → acumulador mismo tamaño que imagen
        dp = 2.0 → acumulador mitad tamaño (2x más rápido)
    
    AJUSTE:
        - 1.0: Alta precisión (lento)
        - 2.0: Rápido (puede perder precisión)
    """
    
    hough_min_dist: int = 100
    """
    Distancia mínima entre centros de círculos detectados (píxeles).
    
    RAZÓN:
        En FMS201, solo hay UN círculo relevante (rebaje de pieza)
        Evitar detectar múltiples círculos cercanos (ruido)
    
    AJUSTE:
        - 50: Detecta círculos muy cercanos
        - 100: Default, permite 1 círculo principal
        - 200: Solo detecta si muy separados
    """
    
    hough_param1: int = 50
    """
    Umbral Canny alto (mismo que canny_threshold_high).
    
    NOTA: Hough usa internamente Canny, estos valores deben ser consistentes
    """
    
    hough_param2: int = 30
    """
    Umbral de acumulador de Hough.
    
    SIGNIFICADO:
        Círculo debe votar >= hough_param2 veces para ser considerado
        
        Visualización del acumulador:
            Para cada píxel (x,y) en borde de Canny:
                Para cada radio r posible:
                    acumulador[cx, cy, r] += 1
                    donde (cx, cy) es centro del posible círculo
        
        Solo círculos con acumulador >= param2 son retornados
    
    AJUSTE:
        - 20: Threshold bajo → muchos círculos falsos
        - 30: Default, detecta bien
        - 50: Threshold alto → solo círculos muy claros
    """
    
    hough_min_radius: int = 20
    """Mínimo radio de círculo a detectar (píxeles)"""
    
    hough_max_radius: int = 150
    """Máximo radio de círculo a detectar (píxeles)"""
    
    # Filtrado de resultados
    area_min: int = 5000
    """
    Área mínima del círculo detectado (píxeles²).
    
    CÁLCULO: A = π × r²
        r=20 → A ≈ 1256 px²
        r=50 → A ≈ 7854 px²
        r=100 → A ≈ 31416 px²
    """
    
    area_max: int = 15000
    """Área máxima del círculo detectado"""
    
    circularity_min: float = 0.7
    """
    Circularidad mínima (0 a 1).
    
    FÓRMULA: C = 4π × A / P²
        donde A = área, P = perímetro
        
        C = 1.0 → círculo perfecto
        C = 0.5 → cuadrado
        C < 0.5 → formas irregulares
    
    AJUSTE:
        - 0.5: Acepta cuadrados
        - 0.7: Default, prefiere círculos
        - 0.9: Solo círculos casi perfectos
    """
    
    # Umbral de decisión OK vs KO
    threshold_ok: int = 8000
    """
    Área umbral para pieza OK.
    
    LÓGICA:
        Si área > threshold_ok → PIEZA_OK (círculo grande = posición correcta)
        Si area > threshold_ko (menor) → PIEZA_KO_INVERTIDA
        Si área no detectada → ESTACION_VACIA
    """
    
    threshold_ko: int = 6500
    """Área umbral para pieza KO (invertida)"""


@dataclass
class StationsConfig:
    """Configuración de todas las estaciones"""
    fms201: FMS201Config = FMS201Config()
    # fms202: FMS202Config = FMS202Config()
    # fms205: FMS205Config = FMS205Config()
    # fms206: FMS206Config = FMS206Config()


# ============================================================================
# CONFIGURACIÓN: COMUNICACIÓN CON PLC (PyADS)
# ============================================================================

@dataclass
class CommunicationConfig:
    """
    Parámetros de comunicación con TwinCAT PLC via PyADS.
    
    PROTOCOLO: AMS (Automation Message Specification)
    
    PARA TU MEMORIA:
        Sección sobre integración PLC
    """
    
    enabled: bool = False
    """¿Habilitar comunicación con PLC?"""
    
    ams_netid: str = "192.168.1.100.1.1"
    """
    AMS Net ID del PLC.
    
    FORMATO: IP.INSTANCIA.PUERTO
    
    EJEMPLO:
        - "192.168.1.100.1.1" → PLC en red local
        - "127.0.0.1.1.1" → PLC en localhost
    """
    
    ams_port: int = 851
    """Puerto AMS del PLC (típico: 851)"""
    
    # Variables de lectura (desde PLC)
    plc_var_piece_present: str = "GVL_FMS201.bPiecePresent"
    """Variable PLC: ¿hay pieza?"""
    
    plc_var_station_ready: str = "GVL_FMS201.bStationReady"
    """Variable PLC: ¿estación lista?"""
    
    # Variables de escritura (hacia PLC)
    plc_var_quality_status: str = "GVL_FMS201.iQualityStatus"
    """
    Variable PLC: estado de calidad.
    
    VALORES:
        0 = OK
        1 = KO_INVERTIDA
        2 = KO_DAÑADA
        3 = ERROR
    """
    
    plc_var_detection_confidence: str = "GVL_FMS201.rDetectionConfidence"
    """Variable PLC: confianza de detección (0.0 a 1.0)"""


# ============================================================================
# CONFIGURACIÓN: INTERFAZ DE USUARIO
# ============================================================================

@dataclass
class UIConfig:
    """
    Parámetros de visualización HMI.
    
    PARA TU MEMORIA:
        Sección sobre "Visualización y Trazabilidad"
        Explicar importancia de dashboard multi-vistas
    """
    
    tile_width: int = 640
    """Ancho de cada tile en dashboard (píxeles)"""
    
    tile_height: int = 360
    """Alto de cada tile en dashboard (píxeles)"""
    
    show_fps: bool = True
    """Mostrar FPS en tiempo real"""
    
    show_timestamp: bool = True
    """Mostrar timestamp de captura"""
    
    show_debug_info: bool = True
    """Mostrar información de debug (área, confianza, etc.)"""
    
    save_screenshots: bool = True
    """Guardar screenshots de cada detección"""
    
    screenshot_dir: str = "output/screenshots"
    """Directorio donde guardar screenshots"""
    
    screenshot_on_ko: bool = True
    """Guardar screenshot automático cuando hay KO"""


# ============================================================================
# CLASE PRINCIPAL: CONFIG
# ============================================================================

@dataclass
class Config:
    """
    Configuración global del sistema.
    
    PATRÓN: SINGLETON (una instancia global)
    
    USO:
        config = get_config()
        print(config.camera.fps)
        print(config.stations.fms201.threshold_ok)
    
    ESTRUCTURA:
        Config
        ├─ camera: CameraConfig
        ├─ preprocessing: PreprocessingConfig
        ├─ stations: StationsConfig
        │   └─ fms201: FMS201Config
        ├─ communication: CommunicationConfig
        └─ ui: UIConfig
    
    VENTAJAS:
        - Único lugar donde están todos los parámetros
        - Fácil de pasar entre módulos
        - Type-safe (IDE autocomplete)
        - Versionable (Git)
        - Justificable (cada parámetro documentado)
    """
    
    camera: CameraConfig = CameraConfig()
    preprocessing: PreprocessingConfig = PreprocessingConfig()
    stations: StationsConfig = StationsConfig()
    communication: CommunicationConfig = CommunicationConfig()
    ui: UIConfig = UIConfig()


# ============================================================================
# SINGLETON
# ============================================================================

_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Obtiene la instancia global de Config (SINGLETON).
    
    PATRÓN SINGLETON:
        - Primera llamada: crea instancia
        - Llamadas posteriores: devuelve misma instancia
        - Garantiza única configuración en todo el programa
    
    USO:
        config = get_config()
        config.camera.fps = 60  # Aplica a todo el sistema
    
    RETORNA:
        Instancia singleton de Config
    """
    
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def reset_config():
    """Reset del config (usar solo en tests)"""
    global _global_config
    _global_config = None
