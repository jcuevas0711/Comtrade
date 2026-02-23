# ⚡ Fault Analyzer — Transmission Line COMTRADE Analyzer

Herramienta de análisis exhaustivo de fallas eléctricas en líneas de transmisión, a partir de registros **COMTRADE** (IEEE C37.111-1991/1999/2013).

Desarrollado para operaciones de generación hidroeléctrica con líneas:
- **69 kV** — Cable ACSR HAWK 477 kcmil
- **13.8 kV** — Cable ACSR 266 kcmil (Partridge)

---

## 🚀 Instalación rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/fault-analyzer.git
cd fault-analyzer

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate.bat       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

---

## 📁 Estructura del proyecto

```
fault-analyzer/
│
├── app.py                        # Aplicación Streamlit principal
├── requirements.txt
├── generate_sample_comtrade.py   # Genera archivos COMTRADE de prueba
│
├── utils/
│   ├── line_params.py            # Parámetros Z1/Z0 para cada tipo de línea
│   ├── comtrade_parser.py        # Lectura de archivos .CFG + .DAT / .CFF
│   ├── fault_detector.py         # Clasificación automática del tipo de falla
│   ├── fault_locator.py          # 4 métodos de localización de fallas
│   ├── symmetrical.py            # Componentes simétricas (secuencias 0,1,2)
│   ├── plots.py                  # Gráficas Plotly interactivas
│   └── pdf_report.py             # Generación de reporte PDF (ReportLab)
│
└── sample_data/                  # Archivos COMTRADE de prueba (auto-generados)
    ├── fault_AG_69kV.cfg
    └── fault_AG_69kV.dat
```

---

## 📂 Archivos COMTRADE soportados

| Estándar | Formato | Extensiones |
|----------|---------|-------------|
| IEEE C37.111-1991 | ASCII | `.cfg` + `.dat` |
| IEEE C37.111-1999 | ASCII / Binary | `.cfg` + `.dat` |
| IEEE C37.111-2013 | CFF | `.cff` |

### Convención de nombres de canales
El parser detecta automáticamente los canales por nombre. Patrones reconocidos:

| Canal | Patrones aceptados |
|-------|--------------------|
| Va    | `va`, `v_a`, `ua`, `vpha`, `ea` |
| Vb    | `vb`, `v_b`, `ub`, `vphb`, `eb` |
| Vc    | `vc`, `v_c`, `uc`, `vphc`, `ec` |
| Ia    | `ia`, `i_a`, `ifa`, `ipha` |
| Ib    | `ib`, `i_b`, `ifb`, `iphb` |
| Ic    | `ic`, `i_c`, `ifc`, `iphc` |

---

## ⚙️ Parámetros de línea configurados

### 69 kV — ACSR HAWK 477 kcmil
| Parámetro | Valor |
|-----------|-------|
| Z1 | 0.0841 + j0.3932 Ω/km |
| Z0 | 0.2530 + j1.1796 Ω/km |
| k0 | (Z0-Z1)/(3·Z1) |
| CTR | 400 |
| VTR | 600 |

### 13.8 kV — ACSR 266 kcmil (Partridge)
| Parámetro | Valor |
|-----------|-------|
| Z1 | 0.1710 + j0.3812 Ω/km |
| Z0 | 0.3402 + j1.1436 Ω/km |
| CTR | 200 |
| VTR | 120 |

---

## 🔍 Métodos de localización de fallas

| Método | Descripción | Ventaja | Limitación |
|--------|-------------|---------|------------|
| **Reactancia Simple** | `m = Im(V/I) / Im(Z1)` | Simple, rápido | Error con Rf > 0 |
| **Takagi** | Componente incremental | Cancela Rf | Requiere prefalla limpia |
| **Takagi Modificado** | Usa dV incremental | Más robusto ante Rf | Depende calidad onset |
| **Two-End (estimado)** | Promedio local + remoto | Reduce errores sistemáticos | Estimación del remoto |

**Consenso:** mediana de los 4 métodos.

---

## 📊 Gráficas incluidas

1. **Formas de onda** — Va,Vb,Vc e Ia,Ib,Ic vs tiempo con marcador de onset
2. **Diagrama fasorial** — Phasors pre-falla (transparentes) y durante falla
3. **Componentes simétricas** — Barras comparativas seq-0, seq-1, seq-2
4. **Trayectoria R-X** — Impedancia aparente + zona MHO de referencia

---

## 📄 Reporte PDF

Incluye:
- Encabezado con metadatos del operador y línea
- Resumen ejecutivo (tipo de falla, distancia, duración)
- Tabla de resultados de los 4 métodos de localización
- Magnitudes eléctricas de falla (I, V por fase)
- Componentes simétricas (magnitud y ángulo)
- Parámetros de línea utilizados
- Notas y limitaciones

---

## 🧪 Prueba con datos de ejemplo

```bash
# Generar archivos COMTRADE de prueba
python generate_sample_comtrade.py

# Luego cargar en Streamlit:
# sample_data/fault_AG_69kV.cfg
# sample_data/fault_AG_69kV.dat
```

Simula una falla **AG (Fase A a tierra)** al 60% de una línea de 50 km a los 50 ms de inicio del registro.

---

## 🛠️ Personalización

Para agregar un nuevo tipo de línea, editar `utils/line_params.py`:

```python
LINE_CONFIGS["mi_linea"] = {
    "label":          "34.5 kV — ACSR Hawk 477",
    "cable":          "ACSR HAWK 477",
    "voltage_kv":     34.5,
    "Z1":             complex(0.09, 0.40),   # Ω/km
    "Z0":             complex(0.27, 1.18),   # Ω/km
    "Z1_str":         "0.09 + j0.40 Ω/km",
    "Z0_str":         "0.27 + j1.18 Ω/km",
    "CTR":            300,
    "VTR":            300,
    "default_length": 30.0,
    "freq_hz":        60,
    "I_rated_A":      500,
}
```

---

## 📦 Dependencias

| Librería | Versión mínima | Uso |
|---------|---------------|-----|
| streamlit | 1.32 | UI web |
| comtrade | 0.3 | Parser COMTRADE |
| numpy | 1.26 | Cálculo numérico |
| scipy | 1.12 | Filtros, DSP |
| plotly | 5.20 | Gráficas interactivas |
| reportlab | 4.1 | Generación PDF |
| pandas | 2.2 | Tablas de datos |

---

## 📝 Referencias técnicas

- IEEE Std C37.111™-2013 — Common Format for Transient Data Exchange (COMTRADE)
- IEEE Std C37.114™-2004 — Guide for Determining Fault Location on AC Transmission Lines
- Takagi T. et al., "Development of a New Type Fault Locator Using the One-Terminal Voltage and Current Data", IEEE Trans. PAS, Vol. 101, No. 8, 1982
- Anderson P.M., "Analysis of Faulted Power Systems", IEEE Press, 1995

---

## ⚠️ Limitaciones

- El método Two-End usa estimación del extremo remoto; para mayor precisión se requieren datos reales de ambos extremos.
- Se asume línea homogénea sin derivaciones (tap).
- La resistencia de arco afecta la precisión del método de Reactancia Simple.
- Verificar siempre las razones de transformación CTR/VTR del equipo de campo.

---

*Desarrollado para operaciones de generación hidroeléctrica · Guatemala*
