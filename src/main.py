"""
================================================================================
MÓDULO: src/main.py - PUNTO DE ENTRADA PRINCIPAL
================================================================================

PROPÓSITO:
    Integra TODOS los módulos en un pipeline funcional:
    
    Cámara → Preprocesamiento → Detección → HMI Dashboard
    
    Este es el script que EJECUTAS para iniciar el sistema.

FLUJO GENERAL:
    1. Inicializar configuración
    2. Conectar cámara
    3. En bucle:
        - Capturar frame
        - Normalizar iluminación
        - Detectar con FMS201Detector
        - Mostrar en HMI
        - (Opcional) Integrar con PyADS

USO:
    $ python -m src.main
    
    Presiona 'q' para salir
    Presiona 's' para guardar screenshot
    Presiona 'p' para pausar

================================================================================
"""

import cv2
import time
import sys
from typing import Optional
from pathlib import Path

# Importar módulos propios
from src.config import get_config, QualityState
from src.vision.camera.camera_manager import CameraManager
from src.vision.preprocessing.illumination import IlluminationNormalizer
from src.vision.algorithms.fms201_detector import FMS201Detector
from src.vision.visualization.hmi_dashboard import HMIDashboard


class FMS200VisionSystem:
    """
    Sistema completo de visión para FMS200.
    
    RESPONSABILIDADES:
        1. Orquestar captura, preprocesamiento, detección
        2. Gestionar HMI visualización
        3. Manejo de eventos (teclado)
        4. Logging y estadísticas
    
    ARQUITECTURA:
        FMS200VisionSystem (orquestador)
        ├─ CameraManager
        ├─ IlluminationNormalizer
        ├─ FMS201Detector
        ├─ HMIDashboard
        └─ PyADS (futuro)
    """
    
    def __init__(self):
        """Inicializa el sistema"""
        self.config = get_config()
        
        # Componentes
        self.camera: Optional[CameraManager] = None
        self.normalizer: Optional[IlluminationNormalizer] = None
        self.detector: Optional[FMS201Detector] = None
        self.dashboard: Optional[HMIDashboard] = None
        
        # Estado
        self.running = False
        self.paused = False
        self.fps_history = []
        self.frame_count = 0
        
        # Estadísticas
        self.stats_ok = 0
        self.stats_ko = 0
        self.stats_empty = 0
        self.stats_error = 0
    
    # ========================================================================
    # INICIALIZACIÓN
    # ========================================================================
    
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes del sistema.
        
        RETORNA:
            True si inicialización exitosa, False si error
        """
        
        print("\n" + "="*70)
        print("INICIALIZANDO SISTEMA FMS200 VISION")
        print("="*70 + "\n")
        
        # Paso 1: Conectar cámara
        print("[1/4] Conectando cámara...")
        self.camera = CameraManager(
            camera_index=self.config.camera.camera_index,
            frame_width=self.config.camera.frame_width,
            frame_height=self.config.camera.frame_height,
            fps=self.config.camera.fps
        )
        
        if not self.camera.connect():
            print("[ERROR] Fallo conectar cámara")
            return False
        print("[✓] Cámara conectada exitosamente")
        
        # Paso 2: Inicializar normalizador
        print("\n[2/4] Inicializando normalizador de iluminación...")
        self.normalizer = IlluminationNormalizer(
            config_dict={
                'clahe_clip_limit': self.config.preprocessing.clahe_clip_limit,
                'clahe_tile_size': self.config.preprocessing.clahe_tile_size,
                'shadow_kernel_size': self.config.preprocessing.shadow_kernel_size,
            }
        )
        print("[✓] Normalizador listo")
        
        # Paso 3: Inicializar detector
        print("\n[3/4] Inicializando detector FMS201...")
        self.detector = FMS201Detector(
            config=self.config.stations.fms201.__dict__
        )
        print("[✓] Detector FMS201 listo")
        
        # Paso 4: Inicializar HMI
        print("\n[4/4] Inicializando dashboard HMI...")
        self.dashboard = HMIDashboard(
            tile_width=self.config.ui.tile_width,
            tile_height=self.config.ui.tile_height,
            save_screenshots=self.config.ui.save_screenshots,
            output_dir=self.config.ui.screenshot_dir
        )
        print("[✓] Dashboard HMI listo")
        
        print("\n" + "="*70)
        print("SISTEMA INICIALIZADO CORRECTAMENTE")
        print("="*70 + "\n")
        
        return True
    
    # ========================================================================
    # LOOP PRINCIPAL
    # ========================================================================
    
    def run(self) -> None:
        """
        Inicia el loop principal de ejecución.
        
        ALGORITMO:
            1. Capturar frame de cámara
            2. Si pausado, esperar comando
            3. Si no pausado:
                a. Normalizar iluminación
                b. Detectar con FMS201
                c. Crear mosaico HMI
                d. Mostrar resultado
                e. Actualizar estadísticas
            4. Procesar teclas de control
            5. Repetir hasta comando salida
        """
        
        self.running = True
        
        print("Iniciando captura. Controles:")
        print("  'q' - Salir")
        print("  's' - Guardar screenshot")
        print("  'p' - Pausar/Continuar")
        print("  'r' - Reset estadísticas")
        print("\n" + "="*70 + "\n")
        
        tiempo_inicio = time.time()
        
        while self.running:
            # Capturar frame
            frame = self.camera.read()
            if frame is None:
                print("[ERROR] No se pudo capturar frame")
                break
            
            # Si pausado, solo mostrar último frame
            if self.paused:
                key = cv2.waitKey(1) & 0xFF
                self._handle_keyboard(key)
                continue
            
            # ================================================================
            # PIPELINE PRINCIPAL
            # ================================================================
            
            # Paso 1: Normalizar iluminación
            preprocessed_result = self.normalizer.process(
                frame,
                apply_white_balance=self.config.preprocessing.apply_white_balance,
                apply_shadow_removal=self.config.preprocessing.apply_shadow_removal,
                apply_clahe=self.config.preprocessing.apply_clahe
            )
            
            # Paso 2: Detectar característica (FMS201)
            detection_result = self.detector.detect(preprocessed_result.enhanced)
            
            # Paso 3: Crear mosaico HMI
            mosaic = self.dashboard.create_mosaic(
                original=frame,
                normalized=preprocessed_result.enhanced,
                binary=preprocessed_result.enhanced,  # Para demo, usar enhanced
                annotated=detection_result.image_annotated,
                fps=self.camera.stats.fps_actual,
                timestamp=time.time(),
                debug_data={
                    'Estado': detection_result.state.value,
                    'Area': f"{int(detection_result.metadata['area'])} px²",
                    'Conf': f"{detection_result.confidence:.2f}"
                }
            )
            
            # Paso 4: Mostrar
            cv2.imshow("FMS200 - Control de Calidad", mosaic)
            
            # Paso 5: Actualizar estadísticas
            self._update_statistics(detection_result.state)
            
            self.frame_count += 1
            self.fps_history.append(self.camera.stats.fps_actual)
            
            # ================================================================
            # MANEJO DE TECLADO
            # ================================================================
            
            key = cv2.waitKey(1) & 0xFF
            self._handle_keyboard(key)
            
            # Mostrar estadísticas cada 100 frames
            if self.frame_count % 100 == 0:
                self._print_statistics(tiempo_inicio)
        
        # Finalizar
        self.shutdown()
    
    # ========================================================================
    # MANEJO DE EVENTOS
    # ========================================================================
    
    def _handle_keyboard(self, key: int) -> None:
        """
        Procesa comandos de teclado.
        
        COMANDOS:
            q: Salir
            s: Guardar screenshot
            p: Pausar/Continuar
            r: Reset estadísticas
        """
        
        if key == ord('q'):
            print("\n[INFO] Comando salida (q)")
            self.running = False
        
        elif key == ord('s'):
            print("[INFO] Guardando screenshot...")
            # El dashboard ya lo hace automáticamente si save_screenshots=True
        
        elif key == ord('p'):
            self.paused = not self.paused
            estado = "PAUSADO" if self.paused else "REANUDADO"
            print(f"[INFO] Sistema {estado}")
        
        elif key == ord('r'):
            self._reset_statistics()
            print("[INFO] Estadísticas reseteadas")
    
    # ========================================================================
    # ESTADÍSTICAS
    # ========================================================================
    
    def _update_statistics(self, state: QualityState) -> None:
        """Actualiza contadores de estados"""
        
        if state == QualityState.OK:
            self.stats_ok += 1
        elif state == QualityState.KO_INVERTIDA or state == QualityState.KO_DAÑADA:
            self.stats_ko += 1
        elif state == QualityState.ESTACION_VACIA:
            self.stats_empty += 1
        else:
            self.stats_error += 1
    
    def _reset_statistics(self) -> None:
        """Reset de contadores"""
        self.stats_ok = 0
        self.stats_ko = 0
        self.stats_empty = 0
        self.stats_error = 0
        self.fps_history = []
        self.frame_count = 0
    
    def _print_statistics(self, tiempo_inicio: float) -> None:
        """Imprime estadísticas de ejecución"""
        
        tiempo_transcurrido = time.time() - tiempo_inicio
        
        print("\n" + "="*70)
        print(f"ESTADÍSTICAS (tiempo: {tiempo_transcurrido:.1f}s)")
        print("="*70)
        print(f"Frames procesados: {self.frame_count}")
        print(f"FPS promedio: {sum(self.fps_history)/len(self.fps_history):.1f}")
        print(f"\nResultados:")
        print(f"  ✓ OK:            {self.stats_ok:4d} ({self.stats_ok*100/(self.frame_count or 1):.1f}%)")
        print(f"  ✗ KO:            {self.stats_ko:4d} ({self.stats_ko*100/(self.frame_count or 1):.1f}%)")
        print(f"  ∅ Vacía:         {self.stats_empty:4d} ({self.stats_empty*100/(self.frame_count or 1):.1f}%)")
        print(f"  ! Error:         {self.stats_error:4d} ({self.stats_error*100/(self.frame_count or 1):.1f}%)")
        
        total = self.stats_ok + self.stats_ko + self.stats_empty + self.stats_error
        if total > 0:
            exactitud = self.stats_ok * 100 / total
            print(f"\nExactitud (asumir solo OK es correcto): {exactitud:.1f}%")
        
        print("="*70 + "\n")
    
    # ========================================================================
    # FINALIZACIÓN
    # ========================================================================
    
    def shutdown(self) -> None:
        """Limpia recursos y finaliza"""
        
        print("\n" + "="*70)
        print("FINALIZANDO SISTEMA")
        print("="*70 + "\n")
        
        if self.camera:
            self.camera.print_status()
            self.camera.disconnect()
        
        cv2.destroyAllWindows()
        
        # Estadísticas finales
        if self.frame_count > 0:
            print(f"\nReporteo Final:")
            print(f"  Total frames: {self.frame_count}")
            print(f"  OK: {self.stats_ok} | KO: {self.stats_ko} | Vacía: {self.stats_empty} | Error: {self.stats_error}")
        
        print("\n[OK] Sistema finalizado correctamente")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """
    Punto de entrada principal.
    
    USO:
        python -m src.main
    """
    
    try:
        # Crear sistema
        system = FMS200VisionSystem()
        
        # Inicializar
        if not system.initialize():
            print("[ERROR] No se pudo inicializar sistema")
            return 1
        
        # Ejecutar
        system.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupción del usuario (Ctrl+C)")
        return 1
    
    except Exception as e:
        print(f"\n[ERROR] Excepción no capturada: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
