# 🦁 Dashboard Avanzado de Rendimiento Pumas UNAM

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Power BI](https://img.shields.io/badge/Power%20BI-Ready-orange.svg)](https://powerbi.microsoft.com/)

> Dashboard analítico avanzado para el análisis del rendimiento del Club Universidad Nacional A.C. (Pumas UNAM) con métricas clave de fútbol moderno.

![Dashboard Preview](docs/dashboard_preview.png)

## 📋 Descripción

Este proyecto implementa un pipeline ETL completo en Python para procesar, transformar y preparar datos de rendimiento futbolístico del equipo Pumas UNAM. Los datos procesados alimentan dashboards interactivos en Power BI/Tableau que permiten:

- **Análisis táctico** basado en métricas avanzadas
- **Comparación histórica** del rendimiento del equipo
- **Identificación de patrones** en la construcción de jugadas
- **Evaluación del pressing** y recuperación de balón

## 📊 Métricas Implementadas

| Métrica | Descripción | Fórmula/Cálculo |
| ------- | ----------- | --------------- |
| **Posesión** | Porcentaje de tiempo con control del balón | Pases propios / (Pases propios + Pases rival) × 100 |
| **xG (Expected Goals)** | Goles esperados basados en calidad de tiros | Modelo probabilístico por ubicación y tipo de tiro |
| **Velocidad de Construcción** | Tiempo promedio del inicio al tercio final | Segundos desde recuperación hasta zona de ataque |
| **PPDA (Pressing)** | Presión alta del equipo | Pases permitidos al rival / Acciones defensivas en campo rival |
| **Progresión** | Avance efectivo del balón | Metros ganados por pase/conducción hacia portería rival |

## 🏗️ Estructura del Proyecto

```
09_Dash_UNAM/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias del proyecto
├── .gitignore                         # Archivos ignorados por git
├── pumas_dashboard_etl.py             # Script principal ETL
├── utils.py                           # Funciones auxiliares
├── Pumas_Performance_Analysis.ipynb   # Notebook de análisis
├── data/
│   ├── raw/                           # Datos crudos
│   │   └── sample_match_data.csv      # Datos de ejemplo
│   └── processed/                     # Datos procesados para BI
├── docs/
│   └── dashboard_preview.png          # Preview del dashboard
└── output/
    └── metrics_export.csv             # Métricas exportadas
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.9 o superior
- Power BI Desktop / Tableau (para visualización)

### Pasos de instalación

1.**Clonar el repositorio**

```bash
git clone https://github.com/cesar530/09_Dash_UNAM.git
cd 09_Dash_UNAM
```

2.**Crear entorno virtual**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3.**Instalar dependencias**

```bash
pip install -r requirements.txt
```

> ⚠️ **Nota**: Las versiones de las librerías están fijadas para evitar errores de incompatibilidad binaria con NumPy.

## 💻 Uso

### Ejecutar el ETL completo

```bash
python pumas_dashboard_etl.py
```

### Usar el notebook interactivo

```bash
jupyter notebook Pumas_Performance_Analysis.ipynb
```

### Ejemplo de uso en Python

```python
from pumas_dashboard_etl import PumasDashboardETL

# Inicializar el ETL
etl = PumasDashboardETL()

# Cargar datos
etl.load_data('data/raw/sample_match_data.csv')

# Calcular métricas
metrics = etl.calculate_all_metrics()

# Exportar para Power BI
etl.export_to_powerbi('output/metrics_export.csv')
```

## 📈 Conexión con Power BI / Tableau

### Power BI

1. Abrir Power BI Desktop
2. Seleccionar "Obtener datos" → "Texto/CSV"
3. Navegar a `output/metrics_export.csv`
4. Crear visualizaciones con las métricas calculadas

### Tableau

1. Abrir Tableau Desktop
2. Conectar a archivo de texto
3. Seleccionar `output/metrics_export.csv`
4. Diseñar dashboard con las métricas disponibles

## 🔧 Tecnologías Utilizadas

- **Python 3.9+**: Lenguaje principal
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos
- **Plotly**: Visualizaciones interactivas
- **Scikit-learn**: Modelos de xG
- **Power BI / Tableau**: Dashboards finales

## 📊 Dashboard Preview

El dashboard incluye las siguientes visualizaciones:

1. **Panel de Posesión**: Evolución por partido y comparativa
2. **Mapa de Calor xG**: Zonas de mayor peligro ofensivo
3. **Análisis de Pressing**: PPDA por zona del campo
4. **Velocidad de Construcción**: Tiempos de transición
5. **Tendencias Temporales**: Evolución de métricas por jornada

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaMetrica`)
3. Commit tus cambios (`git commit -m 'Add: nueva métrica de pressing'`)
4. Push a la rama (`git push origin feature/NuevaMetrica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.
```
MIT License

Copyright (c) 2026 César Adrián Delgado Díaz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👤 Autor

- 👤 Autor : **César Adrián Delgado Díaz**
- 💼 LinkedIn: [linkedin.com/in/cesar-delgado-diaz](linkedin.com/in/cesar-delgado-diaz)
- 🐙 GitHub: [github.com/cesar530](https://github.com/cesar530)

---
