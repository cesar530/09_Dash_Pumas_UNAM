"""
pumas_dashboard_etl.py - ETL Principal para Dashboard de Rendimiento Pumas UNAM

Este módulo implementa el pipeline ETL completo para procesar datos de
rendimiento futbolístico y preparar métricas avanzadas para dashboards
en Power BI / Tableau.

Autor: César Adrián Delgado Díaz
Portfolio: https://tu-portfolio.com
LinkedIn: https://www.linkedin.com/in/cesar-delgado-diaz
GitHub: https://github.com/cesar530

Licencia: MIT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import json

# Importar funciones de utilidad
from utils import (
    calculate_possession,
    calculate_xg,
    calculate_ppda,
    calculate_build_up_speed,
    calculate_progression,
    get_zone,
    aggregate_match_metrics,
    prepare_for_powerbi,
    export_to_csv,
    generate_sample_data,
    PUMAS_COLORS,
    FIELD_LENGTH,
    FIELD_WIDTH
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/etl.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class PumasDashboardETL:
    """
    Clase principal para el pipeline ETL del Dashboard de Pumas UNAM.
    
    Esta clase maneja todo el proceso de:
    - Extracción de datos (CSV, API, etc.)
    - Transformación y cálculo de métricas
    - Carga/Exportación para herramientas BI
    
    Attributes:
        data_path: Ruta base para los datos
        output_path: Ruta para los archivos exportados
        raw_data: DataFrame con datos crudos
        processed_data: DataFrame con datos procesados
        metrics: Diccionario con métricas calculadas
    """
    
    def __init__(
        self,
        data_path: str = "data/raw",
        output_path: str = "output"
    ):
        """
        Inicializa el ETL con las rutas de datos.
        
        Args:
            data_path: Ruta a los datos crudos
            output_path: Ruta para exportar resultados
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        
        # Crear directorios si no existen
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # DataFrames
        self.raw_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None
        self.metrics: Dict = {}
        
        logger.info("PumasDashboardETL inicializado")
    
    # =========================================================================
    # EXTRACCIÓN DE DATOS
    # =========================================================================
    
    def load_data(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Carga datos desde un archivo CSV.
        
        Args:
            filepath: Ruta al archivo CSV. Si es None, usa datos de ejemplo.
            
        Returns:
            DataFrame con los datos cargados
        """
        try:
            if filepath and Path(filepath).exists():
                self.raw_data = pd.read_csv(filepath)
                logger.info(f"Datos cargados desde {filepath}: {len(self.raw_data)} registros")
            else:
                logger.warning("Archivo no encontrado. Generando datos de ejemplo...")
                self.raw_data = generate_sample_data(n_matches=17)  # Medio torneo
                logger.info(f"Datos de ejemplo generados: {len(self.raw_data)} partidos")
            
            return self.raw_data
            
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            raise
    
    def load_from_api(self, api_url: str, api_key: Optional[str] = None) -> pd.DataFrame:
        """
        Carga datos desde una API externa.
        
        Args:
            api_url: URL de la API
            api_key: Clave de API opcional
            
        Returns:
            DataFrame con los datos de la API
        """
        # Placeholder para integración con APIs de datos futbolísticos
        # Ejemplos: StatsBomb, Opta, WhoScored
        logger.info("Carga desde API no implementada. Usando datos de ejemplo.")
        return self.load_data()
    
    # =========================================================================
    # TRANSFORMACIÓN DE DATOS
    # =========================================================================
    
    def transform_data(self) -> pd.DataFrame:
        """
        Aplica transformaciones a los datos crudos.
        
        Returns:
            DataFrame transformado
        """
        if self.raw_data is None:
            raise ValueError("No hay datos cargados. Ejecuta load_data() primero.")
        
        df = self.raw_data.copy()
        
        # Convertir fecha
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['week'] = df['date'].dt.isocalendar().week
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
        
        # Calcular métricas derivadas
        df['goal_difference'] = df['pumas_goals'] - df['opponent_goals']
        df['xg_difference'] = df['pumas_xg'] - df['opponent_xg']
        df['xg_overperformance'] = df['pumas_goals'] - df['pumas_xg']
        
        # Categorizar rendimiento
        df['performance_category'] = pd.cut(
            df['possession'],
            bins=[0, 45, 55, 100],
            labels=['Baja', 'Equilibrada', 'Alta']
        )
        
        # Categorizar PPDA (pressing)
        df['pressing_intensity'] = pd.cut(
            df['ppda'],
            bins=[0, 8, 12, float('inf')],
            labels=['Alto', 'Medio', 'Bajo']
        )
        
        # Puntos obtenidos
        df['points'] = df['result'].map({'W': 3, 'D': 1, 'L': 0})
        
        # Acumulados
        df['cumulative_points'] = df['points'].cumsum()
        df['cumulative_goals'] = df['pumas_goals'].cumsum()
        df['cumulative_xg'] = df['pumas_xg'].cumsum()
        
        # Medias móviles (últimos 5 partidos)
        df['possession_rolling'] = df['possession'].rolling(5, min_periods=1).mean()
        df['xg_rolling'] = df['pumas_xg'].rolling(5, min_periods=1).mean()
        df['ppda_rolling'] = df['ppda'].rolling(5, min_periods=1).mean()
        
        self.processed_data = df
        logger.info(f"Datos transformados: {len(df)} registros, {len(df.columns)} columnas")
        
        return df
    
    def calculate_all_metrics(self) -> Dict:
        """
        Calcula todas las métricas agregadas del equipo.
        
        Returns:
            Diccionario con métricas calculadas
        """
        if self.processed_data is None:
            self.transform_data()
        
        df = self.processed_data
        
        self.metrics = {
            # Métricas generales
            'total_matches': len(df),
            'wins': (df['result'] == 'W').sum(),
            'draws': (df['result'] == 'D').sum(),
            'losses': (df['result'] == 'L').sum(),
            'total_points': df['points'].sum(),
            'points_per_match': round(df['points'].mean(), 2),
            
            # Métricas de goles
            'total_goals_scored': df['pumas_goals'].sum(),
            'total_goals_conceded': df['opponent_goals'].sum(),
            'goal_difference': df['pumas_goals'].sum() - df['opponent_goals'].sum(),
            'goals_per_match': round(df['pumas_goals'].mean(), 2),
            'goals_conceded_per_match': round(df['opponent_goals'].mean(), 2),
            
            # xG
            'total_xg': round(df['pumas_xg'].sum(), 2),
            'total_xga': round(df['opponent_xg'].sum(), 2),
            'xg_per_match': round(df['pumas_xg'].mean(), 2),
            'xga_per_match': round(df['opponent_xg'].mean(), 2),
            'xg_overperformance_total': round(
                df['pumas_goals'].sum() - df['pumas_xg'].sum(), 2
            ),
            
            # Posesión
            'avg_possession': round(df['possession'].mean(), 2),
            'max_possession': df['possession'].max(),
            'min_possession': df['possession'].min(),
            
            # Pressing
            'avg_ppda': round(df['ppda'].mean(), 2),
            'best_ppda': df['ppda'].min(),  # Menor es mejor
            
            # Velocidad de construcción
            'avg_build_up_speed': round(df['build_up_speed'].mean(), 2),
            
            # Tiros
            'avg_shots': round(df['pumas_shots'].mean(), 2),
            'total_shots': df['pumas_shots'].sum(),
            
            # Localía vs Visitante
            'home_points': df[df['is_home']]['points'].sum(),
            'away_points': df[~df['is_home']]['points'].sum(),
            'home_wins': ((df['is_home']) & (df['result'] == 'W')).sum(),
            'away_wins': ((~df['is_home']) & (df['result'] == 'W')).sum(),
        }
        
        # Agregar tendencias
        last_5 = df.tail(5)
        self.metrics['last_5_matches'] = {
            'wins': (last_5['result'] == 'W').sum(),
            'draws': (last_5['result'] == 'D').sum(),
            'losses': (last_5['result'] == 'L').sum(),
            'points': last_5['points'].sum(),
            'avg_possession': round(last_5['possession'].mean(), 2),
            'avg_xg': round(last_5['pumas_xg'].mean(), 2),
            'form': ''.join(last_5['result'].tolist())
        }
        
        logger.info("Métricas calculadas exitosamente")
        return self.metrics
    
    def create_metrics_summary(self) -> pd.DataFrame:
        """
        Crea un resumen de métricas en formato tabular.
        
        Returns:
            DataFrame con resumen de métricas
        """
        if not self.metrics:
            self.calculate_all_metrics()
        
        # Crear DataFrame plano excluyendo diccionarios anidados
        flat_metrics = {k: v for k, v in self.metrics.items() 
                       if not isinstance(v, dict)}
        
        summary = pd.DataFrame([flat_metrics])
        summary = summary.T.reset_index()
        summary.columns = ['metric', 'value']
        
        return summary
    
    # =========================================================================
    # EXPORTACIÓN DE DATOS
    # =========================================================================
    
    def export_to_powerbi(self, filename: str = "pumas_metrics.csv") -> str:
        """
        Exporta datos procesados para Power BI.
        
        Args:
            filename: Nombre del archivo de salida
            
        Returns:
            Ruta del archivo exportado
        """
        if self.processed_data is None:
            self.transform_data()
        
        # Preparar datos para Power BI
        export_df = prepare_for_powerbi(self.processed_data)
        
        # Exportar
        filepath = self.output_path / filename
        export_to_csv(export_df, str(filepath))
        
        logger.info(f"Datos exportados para Power BI: {filepath}")
        return str(filepath)
    
    def export_metrics_summary(self, filename: str = "metrics_summary.csv") -> str:
        """
        Exporta resumen de métricas.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo exportado
        """
        summary = self.create_metrics_summary()
        filepath = self.output_path / filename
        export_to_csv(summary, str(filepath))
        
        return str(filepath)
    
    def export_all(self) -> Dict[str, str]:
        """
        Exporta todos los archivos necesarios para el dashboard.
        
        Returns:
            Diccionario con rutas de archivos exportados
        """
        exports = {}
        
        # Datos procesados
        exports['processed_data'] = self.export_to_powerbi("pumas_processed_data.csv")
        
        # Resumen de métricas
        exports['metrics_summary'] = self.export_metrics_summary("pumas_metrics_summary.csv")
        
        # Datos por partido para time series
        if self.processed_data is not None:
            match_data = self.processed_data[[
                'match_id', 'date', 'opponent', 'is_home',
                'possession', 'pumas_xg', 'opponent_xg', 'ppda',
                'pumas_goals', 'opponent_goals', 'result', 'points'
            ]].copy()
            
            filepath = self.output_path / "pumas_match_timeline.csv"
            export_to_csv(match_data, str(filepath))
            exports['match_timeline'] = str(filepath)
        
        # Exportar métricas como JSON para APIs
        if self.metrics:
            json_path = self.output_path / "pumas_metrics.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            exports['metrics_json'] = str(json_path)
        
        logger.info(f"Exportación completa: {len(exports)} archivos")
        return exports
    
    # =========================================================================
    # PIPELINE COMPLETO
    # =========================================================================
    
    def run_pipeline(self, input_file: Optional[str] = None) -> Dict:
        """
        Ejecuta el pipeline ETL completo.
        
        Args:
            input_file: Archivo de entrada opcional
            
        Returns:
            Diccionario con resultados del pipeline
        """
        logger.info("=" * 60)
        logger.info("Iniciando Pipeline ETL Pumas Dashboard")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # 1. Extracción
        logger.info("Paso 1: Extracción de datos...")
        self.load_data(input_file)
        
        # 2. Transformación
        logger.info("Paso 2: Transformación de datos...")
        self.transform_data()
        
        # 3. Cálculo de métricas
        logger.info("Paso 3: Cálculo de métricas...")
        self.calculate_all_metrics()
        
        # 4. Exportación
        logger.info("Paso 4: Exportación de datos...")
        exports = self.export_all()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"Pipeline completado en {duration:.2f} segundos")
        logger.info("=" * 60)
        
        return {
            'status': 'success',
            'duration_seconds': duration,
            'records_processed': len(self.processed_data),
            'exports': exports,
            'metrics': self.metrics
        }


def main():
    """Función principal para ejecutar el ETL."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║      🦁 Dashboard de Rendimiento Pumas UNAM - ETL 🦁        ║
    ║                                                              ║
    ║  Autor: César Adrián Delgado Díaz                           ║
    ║  GitHub: github.com/cesar530                                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar ETL
    etl = PumasDashboardETL()
    
    # Ejecutar pipeline
    results = etl.run_pipeline()
    
    # Mostrar resumen
    print("\n📊 Resumen del ETL:")
    print(f"   - Partidos procesados: {results['records_processed']}")
    print(f"   - Tiempo de ejecución: {results['duration_seconds']:.2f}s")
    print(f"   - Archivos exportados: {len(results['exports'])}")
    
    print("\n📈 Métricas clave del equipo:")
    metrics = results['metrics']
    print(f"   - Puntos totales: {metrics['total_points']}")
    print(f"   - Record: {metrics['wins']}W - {metrics['draws']}D - {metrics['losses']}L")
    print(f"   - Posesión promedio: {metrics['avg_possession']}%")
    print(f"   - xG por partido: {metrics['xg_per_match']}")
    print(f"   - PPDA promedio: {metrics['avg_ppda']}")
    
    print("\n📁 Archivos exportados:")
    for name, path in results['exports'].items():
        print(f"   - {name}: {path}")
    
    print("\n✅ ETL completado exitosamente!")
    print("   Los archivos están listos para importar en Power BI / Tableau")
    
    return results


if __name__ == "__main__":
    main()
