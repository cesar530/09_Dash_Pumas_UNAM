"""
utils.py - Funciones auxiliares para Pumas Dashboard ETL

Este módulo contiene funciones de utilidad para el procesamiento,
transformación y análisis de datos de rendimiento futbolístico.

Autor: César Adrián Delgado Díaz
Portfolio: https://tu-portfolio.com
LinkedIn: https://www.linkedin.com/in/cesar-delgado-diaz
GitHub: https://github.com/cesar530

Licencia: MIT
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

# Dimensiones del campo de fútbol (en metros)
FIELD_LENGTH = 105
FIELD_WIDTH = 68

# Zonas del campo
ZONES = {
    'defensive_third': (0, 35),
    'middle_third': (35, 70),
    'attacking_third': (70, 105)
}

# Colores del equipo Pumas UNAM
PUMAS_COLORS = {
    'primary': '#003366',      # Azul marino
    'secondary': '#FFD700',    # Dorado
    'accent': '#FFFFFF'        # Blanco
}


# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Valida que un DataFrame contenga las columnas requeridas.
    
    Args:
        df: DataFrame a validar
        required_columns: Lista de columnas requeridas
        
    Returns:
        True si el DataFrame es válido, False en caso contrario
    """
    if df is None or df.empty:
        logger.error("DataFrame vacío o nulo")
        return False
    
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        logger.error(f"Columnas faltantes: {missing_cols}")
        return False
    
    return True


def validate_coordinates(x: float, y: float) -> bool:
    """
    Valida que las coordenadas estén dentro del campo de juego.
    
    Args:
        x: Coordenada X (largo del campo)
        y: Coordenada Y (ancho del campo)
        
    Returns:
        True si las coordenadas son válidas
    """
    return 0 <= x <= FIELD_LENGTH and 0 <= y <= FIELD_WIDTH


# =============================================================================
# FUNCIONES DE CÁLCULO DE MÉTRICAS
# =============================================================================

def calculate_possession(team_passes: int, opponent_passes: int) -> float:
    """
    Calcula el porcentaje de posesión del equipo.
    
    Args:
        team_passes: Número de pases completados por el equipo
        opponent_passes: Número de pases completados por el rival
        
    Returns:
        Porcentaje de posesión (0-100)
    """
    total_passes = team_passes + opponent_passes
    if total_passes == 0:
        return 0.0
    
    return round((team_passes / total_passes) * 100, 2)


def calculate_xg(
    x: float,
    y: float,
    shot_type: str = 'shot',
    body_part: str = 'foot',
    is_header: bool = False
) -> float:
    """
    Calcula el Expected Goals (xG) basado en la ubicación y tipo de tiro.
    
    Este es un modelo simplificado. Para mayor precisión, se recomienda
    usar modelos entrenados con datos históricos reales.
    
    Args:
        x: Coordenada X del tiro (0-105)
        y: Coordenada Y del tiro (0-68)
        shot_type: Tipo de tiro ('shot', 'penalty', 'free_kick', 'header')
        body_part: Parte del cuerpo ('foot', 'head', 'other')
        is_header: Si es un cabezazo
        
    Returns:
        Valor xG entre 0 y 1
    """
    # Casos especiales
    if shot_type == 'penalty':
        return 0.76
    
    # Calcular distancia a la portería (centro de la portería en x=105, y=34)
    goal_center_x = FIELD_LENGTH
    goal_center_y = FIELD_WIDTH / 2
    
    distance = np.sqrt((goal_center_x - x)**2 + (goal_center_y - y)**2)
    
    # Calcular ángulo hacia la portería
    goal_width = 7.32  # Ancho de la portería en metros
    angle = np.arctan2(goal_width, distance) * (180 / np.pi)
    
    # Modelo simplificado de xG
    base_xg = 0.0
    
    # Factor distancia (exponencial decreciente)
    distance_factor = np.exp(-distance / 20)
    
    # Factor ángulo
    angle_factor = angle / 45  # Normalizado
    
    # Calcular xG base
    base_xg = distance_factor * angle_factor
    
    # Ajustes por tipo de tiro
    if is_header or body_part == 'head':
        base_xg *= 0.7  # Cabezazos tienen menor conversión
    
    if shot_type == 'free_kick':
        base_xg = min(base_xg, 0.08)  # Tiros libres tienen xG bajo
    
    # Limitar entre 0 y 1
    return round(min(max(base_xg, 0.01), 0.95), 3)


def calculate_ppda(
    opponent_passes_allowed: int,
    defensive_actions: int
) -> float:
    """
    Calcula el PPDA (Passes Allowed Per Defensive Action).
    
    PPDA bajo = pressing alto y efectivo
    PPDA alto = pressing bajo o inefectivo
    
    Args:
        opponent_passes_allowed: Pases permitidos al rival en su campo
        defensive_actions: Acciones defensivas en campo rival
        
    Returns:
        Valor PPDA
    """
    if defensive_actions == 0:
        return float('inf')
    
    return round(opponent_passes_allowed / defensive_actions, 2)


def calculate_build_up_speed(
    start_time: float,
    end_time: float,
    start_zone: str = 'defensive_third',
    end_zone: str = 'attacking_third'
) -> float:
    """
    Calcula la velocidad de construcción de jugada.
    
    Args:
        start_time: Tiempo de inicio (segundos)
        end_time: Tiempo de fin (segundos)
        start_zone: Zona inicial de la jugada
        end_zone: Zona final de la jugada
        
    Returns:
        Velocidad en segundos
    """
    return round(end_time - start_time, 2)


def calculate_progression(
    start_x: float,
    end_x: float,
    start_y: float,
    end_y: float
) -> Dict[str, float]:
    """
    Calcula la progresión del balón.
    
    Args:
        start_x: Coordenada X inicial
        end_x: Coordenada X final
        start_y: Coordenada Y inicial
        end_y: Coordenada Y final
        
    Returns:
        Diccionario con métricas de progresión
    """
    # Progresión hacia la portería rival
    forward_progression = end_x - start_x
    
    # Distancia total
    total_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    
    # Eficiencia de progresión (qué tan directo fue el avance)
    efficiency = forward_progression / total_distance if total_distance > 0 else 0
    
    return {
        'forward_progression': round(forward_progression, 2),
        'total_distance': round(total_distance, 2),
        'efficiency': round(efficiency, 3)
    }


# =============================================================================
# FUNCIONES DE ZONA
# =============================================================================

def get_zone(x: float) -> str:
    """
    Determina la zona del campo basada en la coordenada X.
    
    Args:
        x: Coordenada X (0-105)
        
    Returns:
        Nombre de la zona ('defensive_third', 'middle_third', 'attacking_third')
    """
    for zone_name, (start, end) in ZONES.items():
        if start <= x < end:
            return zone_name
    return 'attacking_third'  # Por defecto si x >= 105


def get_pitch_sector(x: float, y: float) -> str:
    """
    Determina el sector del campo (combinación de zona y carril).
    
    Args:
        x: Coordenada X
        y: Coordenada Y
        
    Returns:
        Nombre del sector
    """
    zone = get_zone(x)
    
    # Determinar carril
    if y < FIELD_WIDTH / 3:
        lane = 'left'
    elif y < 2 * FIELD_WIDTH / 3:
        lane = 'center'
    else:
        lane = 'right'
    
    return f"{zone}_{lane}"


# =============================================================================
# FUNCIONES DE AGREGACIÓN
# =============================================================================

def aggregate_match_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas a nivel de partido.
    
    Args:
        df: DataFrame con eventos del partido
        
    Returns:
        DataFrame con métricas agregadas por partido
    """
    required_cols = ['match_id', 'event_type', 'team']
    if not validate_dataframe(df, required_cols):
        return pd.DataFrame()
    
    aggregations = {
        'passes': ('event_type', lambda x: (x == 'pass').sum()),
        'shots': ('event_type', lambda x: (x == 'shot').sum()),
        'tackles': ('event_type', lambda x: (x == 'tackle').sum()),
        'interceptions': ('event_type', lambda x: (x == 'interception').sum())
    }
    
    # Agregar métricas básicas
    match_metrics = df.groupby(['match_id', 'team']).agg(
        passes=('event_type', lambda x: (x == 'pass').sum()),
        shots=('event_type', lambda x: (x == 'shot').sum()),
        tackles=('event_type', lambda x: (x == 'tackle').sum()),
        interceptions=('event_type', lambda x: (x == 'interception').sum())
    ).reset_index()
    
    return match_metrics


def calculate_rolling_metrics(
    df: pd.DataFrame,
    metric_column: str,
    window: int = 5
) -> pd.Series:
    """
    Calcula métricas con media móvil.
    
    Args:
        df: DataFrame con los datos
        metric_column: Columna de la métrica
        window: Tamaño de la ventana
        
    Returns:
        Serie con la media móvil
    """
    return df[metric_column].rolling(window=window, min_periods=1).mean()


# =============================================================================
# FUNCIONES DE EXPORTACIÓN
# =============================================================================

def prepare_for_powerbi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el DataFrame para exportación a Power BI.
    
    - Convierte fechas a formato compatible
    - Renombra columnas para mayor claridad
    - Agrega columnas calculadas útiles
    
    Args:
        df: DataFrame a preparar
        
    Returns:
        DataFrame preparado para Power BI
    """
    df_export = df.copy()
    
    # Convertir columnas de fecha
    date_columns = df_export.select_dtypes(include=['datetime64']).columns
    for col in date_columns:
        df_export[col] = df_export[col].dt.strftime('%Y-%m-%d')
    
    # Redondear números flotantes
    float_columns = df_export.select_dtypes(include=['float64']).columns
    for col in float_columns:
        df_export[col] = df_export[col].round(3)
    
    return df_export


def export_to_csv(
    df: pd.DataFrame,
    filepath: str,
    encoding: str = 'utf-8-sig'
) -> bool:
    """
    Exporta DataFrame a CSV con configuración óptima.
    
    Args:
        df: DataFrame a exportar
        filepath: Ruta del archivo
        encoding: Codificación del archivo
        
    Returns:
        True si la exportación fue exitosa
    """
    try:
        df.to_csv(filepath, index=False, encoding=encoding)
        logger.info(f"Archivo exportado exitosamente: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error al exportar: {e}")
        return False


# =============================================================================
# FUNCIONES DE VISUALIZACIÓN (helpers)
# =============================================================================

def get_color_scale(metric_type: str) -> List[str]:
    """
    Retorna una escala de colores apropiada para el tipo de métrica.
    
    Args:
        metric_type: Tipo de métrica ('positive', 'negative', 'neutral')
        
    Returns:
        Lista de colores para la escala
    """
    scales = {
        'positive': ['#f7fbff', '#08306b'],  # Azul (más es mejor)
        'negative': ['#fff5f0', '#67000d'],  # Rojo (menos es mejor)
        'neutral': ['#f7f7f7', '#252525'],   # Gris
        'pumas': [PUMAS_COLORS['secondary'], PUMAS_COLORS['primary']]
    }
    
    return scales.get(metric_type, scales['neutral'])


def format_metric_display(value: float, metric_type: str) -> str:
    """
    Formatea un valor de métrica para mostrar.
    
    Args:
        value: Valor de la métrica
        metric_type: Tipo de métrica
        
    Returns:
        Cadena formateada
    """
    formats = {
        'percentage': f"{value:.1f}%",
        'xg': f"{value:.2f}",
        'ppda': f"{value:.1f}",
        'time': f"{value:.1f}s",
        'distance': f"{value:.1f}m"
    }
    
    return formats.get(metric_type, f"{value:.2f}")


# =============================================================================
# GENERADOR DE DATOS DE EJEMPLO
# =============================================================================

def generate_sample_data(n_matches: int = 10) -> pd.DataFrame:
    """
    Genera datos de ejemplo para pruebas y demostración.
    
    Args:
        n_matches: Número de partidos a generar
        
    Returns:
        DataFrame con datos de ejemplo
    """
    np.random.seed(42)  # Para reproducibilidad
    
    opponents = [
        'América', 'Guadalajara', 'Cruz Azul', 'Tigres', 'Monterrey',
        'Santos', 'León', 'Toluca', 'Pachuca', 'Atlas'
    ]
    
    data = []
    base_date = datetime(2024, 1, 15)
    
    for i in range(n_matches):
        match_date = base_date + timedelta(weeks=i)
        opponent = opponents[i % len(opponents)]
        is_home = i % 2 == 0
        
        # Generar métricas con variación realista
        pumas_passes = np.random.randint(350, 550)
        opponent_passes = np.random.randint(300, 500)
        
        possession = calculate_possession(pumas_passes, opponent_passes)
        
        # xG basado en performance del partido
        pumas_shots = np.random.randint(8, 18)
        pumas_xg = sum([
            calculate_xg(
                x=np.random.uniform(70, 105),
                y=np.random.uniform(20, 48)
            ) for _ in range(pumas_shots)
        ])
        
        opponent_shots = np.random.randint(5, 15)
        opponent_xg = sum([
            calculate_xg(
                x=np.random.uniform(70, 105),
                y=np.random.uniform(20, 48)
            ) for _ in range(opponent_shots)
        ])
        
        # PPDA
        ppda = calculate_ppda(
            opponent_passes_allowed=np.random.randint(80, 150),
            defensive_actions=np.random.randint(30, 60)
        )
        
        # Velocidad de construcción
        build_up_speed = np.random.uniform(8, 18)
        
        # Resultado
        pumas_goals = np.random.poisson(pumas_xg)
        opponent_goals = np.random.poisson(opponent_xg)
        
        data.append({
            'match_id': i + 1,
            'date': match_date.strftime('%Y-%m-%d'),
            'opponent': opponent,
            'is_home': is_home,
            'venue': 'Estadio Olímpico Universitario' if is_home else f'Estadio {opponent}',
            'pumas_goals': pumas_goals,
            'opponent_goals': opponent_goals,
            'result': 'W' if pumas_goals > opponent_goals else ('D' if pumas_goals == opponent_goals else 'L'),
            'possession': possession,
            'pumas_passes': pumas_passes,
            'opponent_passes': opponent_passes,
            'pumas_shots': pumas_shots,
            'opponent_shots': opponent_shots,
            'pumas_xg': round(pumas_xg, 2),
            'opponent_xg': round(opponent_xg, 2),
            'ppda': ppda,
            'build_up_speed': round(build_up_speed, 2),
            'tackles': np.random.randint(15, 30),
            'interceptions': np.random.randint(8, 20),
            'aerial_duels_won': np.random.randint(10, 25),
            'progressive_passes': np.random.randint(40, 80)
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Prueba de funciones
    print("=== Test de funciones utils.py ===\n")
    
    # Test posesión
    possession = calculate_possession(450, 350)
    print(f"Posesión (450 vs 350 pases): {possession}%")
    
    # Test xG
    xg = calculate_xg(x=90, y=34)
    print(f"xG desde posición (90, 34): {xg}")
    
    # Test PPDA
    ppda = calculate_ppda(120, 45)
    print(f"PPDA (120 pases, 45 acciones): {ppda}")
    
    # Generar datos de ejemplo
    sample_df = generate_sample_data(5)
    print(f"\nDatos de ejemplo generados: {len(sample_df)} partidos")
    print(sample_df[['date', 'opponent', 'possession', 'pumas_xg', 'ppda']].to_string())
