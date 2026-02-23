import streamlit as st
from pathlib import Path
import tempfile
import os

st.set_page_config(
    page_title="Fault Analyzer | Líneas de Transmisión",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size:2rem; font-weight:700; color:#1E3A5F; }
    .sub-header { font-size:1rem; color:#555; margin-bottom:1.5rem; }
    .section-title {
        font-size:1.1rem; font-weight:600; color:#1E3A5F;
        border-left:4px solid #2E6DA4; padding-left:8px; margin:1rem 0 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

from utils.comtrade_parser import parse_comtrade
from utils.fault_detector import detect_fault_type
from utils.fault_locator import locate_fault_all_methods
from utils.signal_analysis import compute_symmetrical_components, compute_phasors
from utils.line_parameters import get_line_parameters
from utils.plots import (plot_waveforms, plot_phasors, plot_symmetrical_components,
                          plot_impedance_trajectory, plot_rms_profile)
from utils.pdf_report import generate_pdf_report

with st.sidebar:
    st.markdown("## ⚡ Fault Analyzer")
    st.markdown("**Análisis de Fallas — Líneas de Transmisión**")
    st.markdown("---")
    line_type = st.selectbox("🔌 Tipo de línea",
        ["69 kV – ACSR HAWK 477", "13.8 kV – ACSR 266"])
    line_length = st.number_input("📏 Longitud de la línea (km)",
        min_value=0.1, max_value=500.0, value=50.0, step=0.5)
    ct_ratio = st.number_input("🔁 Relación TC (A / 1A)",
        min_value=1, max_value=5000, value=600)
    vt_ratio = st.number_input("🔁 Relación TP (V / 115V)",
        min_value=1, max_value=100000, value=600)
    st.markdown("---")
    lp = get_line_parameters(line_type)
    st.markdown("#### ℹ️ Parámetros de línea")
    st.markdown(f"Z1: `{lp['Z1_r']:.4f}+j{lp['Z1_x']:.4f}` Ω/km")
    st.markdown(f"Z0: `{lp['Z0_r']:.4f}+j{lp['Z0_x']:.4f}` Ω/km")
    st.markdown("---")
    st.caption("v1.0 — IEC 60255-24 / IEEE C37.111")

st.markdown('<div class="main-header">⚡ Analizador de Fallas Eléctricas</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Sube archivos COMTRADE para obtener el reporte completo de la falla</div>', unsafe_allow_html=True)

col_up1, col_up2 = st.columns(2)
with col_up1:
    uploaded_cfg = st.file_uploader("📂 Archivo de configuración (.cfg)", type=["cfg"])
with col_up2:
    uploaded_dat = st.file_uploader("📂 Archivo de datos (.dat / .cdat)", type=["dat","cdat"])

if uploaded_cfg and uploaded_dat:
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = os.path.join(tmpdir, "record.cfg")
        dat_path = os.path.join(tmpdir, "record.dat")
        with open(cfg_path,"wb") as f: f.write(uploaded_cfg.read())
        with open(dat_path,"wb") as f: f.write(uploaded_dat.read())

        with st.spinner("⚙️ Procesando COMTRADE..."):
            try:
                data = parse_comtrade(cfg_path, dat_path, ct_ratio, vt_ratio)
            except Exception as e:
                st.error(f"❌ Error parseando COMTRADE: {e}")
                st.stop()

        fault_info = detect_fault_type(data)
        lp = get_line_parameters(line_type)
        location_results = locate_fault_all_methods(data, lp, line_length, fault_info)
        sym_comp = compute_symmetrical_components(data)
        phasors = compute_phasors(data)

        st.markdown("---")
        st.markdown("### 📋 Resumen Ejecutivo")

        fault_colors = {
            "AG":"#E74C3C","BG":"#E67E22","CG":"#F1C40F",
            "AB":"#8E44AD","BC":"#2980B9","CA":"#27AE60",
            "ABG":"#C0392B","BCG":"#1A5276","CAG":"#196F3D",
            "ABC":"#2C3E50","ABCG":"#17202A","Unknown":"#7F8C8D"
        }
        fcolor = fault_colors.get(fault_info["type"],"#7F8C8D")

        c1,c2,c3,c4,c5 = st.columns(5)
        best = location_results.get("takagi", location_results.get("reactance",{}))
        c1.metric("⚡ Tipo de Falla", fault_info["type"])
        c2.metric("📅 Timestamp", data.get("timestamp","N/A"))
        c3.metric("📍 Distancia (Takagi)", f"{best.get('distance_km',0):.2f} km")
        c4.metric("⏱️ Duración falla", f"{fault_info.get('duration_ms',0):.1f} ms")
        c5.metric("📡 Frec. muestreo", f"{data.get('sample_rate',0):.0f} Hz")

        st.markdown(f"""
        <div style="background:{fcolor}22;border-left:5px solid {fcolor};
                    padding:12px 16px;border-radius:6px;margin:8px 0;">
            <span style="color:{fcolor};font-size:1.1rem;font-weight:700;">
            Falla tipo {fault_info['type']}</span> &nbsp;|&nbsp;
            Fase(s): <b>{fault_info.get('phases','N/A')}</b> &nbsp;|&nbsp;
            Confianza: <b>{fault_info.get('confidence','N/A')}</b> &nbsp;|&nbsp;
            Distancia: <b>{best.get('distance_km',0):.3f} km ({best.get('distance_pct',0):.1f}%)</b>
        </div>""", unsafe_allow_html=True)

        tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
            "📈 Formas de Onda","🔵 Fasores","🔄 Comp. Simétricas",
            "📐 Trayectoria Z","📍 Localización","📄 Reporte PDF"])

        with tab1:
            st.markdown('<div class="section-title">Formas de Onda — Tensiones y Corrientes</div>', unsafe_allow_html=True)
            fig_v, fig_i = plot_waveforms(data, fault_info)
            st.plotly_chart(fig_v, use_container_width=True)
            st.plotly_chart(fig_i, use_container_width=True)
            st.plotly_chart(plot_rms_profile(data), use_container_width=True)

        with tab2:
            st.markdown('<div class="section-title">Diagrama Fasorial — Pre-falla vs Durante Falla</div>', unsafe_allow_html=True)
            st.plotly_chart(plot_phasors(phasors), use_container_width=True)

        with tab3:
            st.markdown('<div class="section-title">Componentes Simétricas — Secuencia 0, 1, 2</div>', unsafe_allow_html=True)
            st.plotly_chart(plot_symmetrical_components(sym_comp, data), use_container_width=True)
            sdata = sym_comp.get("fault_magnitudes",{})
            col_a, col_b = st.columns(2)
            with col_a:
                import pandas as pd
                st.dataframe(pd.DataFrame({
                    "Secuencia":["Positiva (1)","Negativa (2)","Cero (0)"],
                    "Tensión (pu)":[f"{sdata.get('V1',0):.4f}",f"{sdata.get('V2',0):.4f}",f"{sdata.get('V0',0):.4f}"],
                    "Corriente (A)":[f"{sdata.get('I1',0):.3f}",f"{sdata.get('I2',0):.3f}",f"{sdata.get('I0',0):.3f}"]
                }), hide_index=True, use_container_width=True)
            with col_b:
                st.metric("Ratio I2/I1", f"{sdata.get('I2_I1_ratio',0):.4f}", help=">0.1 = falla asimétrica")
                st.metric("Ratio I0/I1", f"{sdata.get('I0_I1_ratio',0):.4f}", help=">0.1 = falla a tierra")

        with tab4:
            st.markdown('<div class="section-title">Trayectoria de Impedancia — Plano R-X</div>', unsafe_allow_html=True)
            st.plotly_chart(plot_impedance_trajectory(data, lp, line_length, fault_info), use_container_width=True)

        with tab5:
            st.markdown('<div class="section-title">Comparativa — Todos los Métodos de Localización</div>', unsafe_allow_html=True)
            import pandas as pd
            methods = {"reactance":"Reactancia Simple","takagi":"Takagi",
                       "modified_takagi":"Takagi Modificado","two_end":"Two-End (estimado)"}
            rows = []
            for key,name in methods.items():
                if key in location_results:
                    r = location_results[key]
                    rows.append({"Método":name,
                        "Distancia (km)":f"{r.get('distance_km',0):.3f}",
                        "Distancia (%)":f"{r.get('distance_pct',0):.2f}%",
                        "Zf (Ω)":f"{r.get('Zf_r',0):.3f}+j{r.get('Zf_x',0):.3f}",
                        "Rf (Ω)":f"{r.get('Rf',0):.3f}",
                        "Confianza":r.get("confidence","—")})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 📌 Resultado Recomendado — Método Takagi")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Distancia", f"{best.get('distance_km',0):.3f} km")
            c2.metric("% de línea", f"{best.get('distance_pct',0):.2f}%")
            c3.metric("Rf falla", f"{best.get('Rf',0):.3f} Ω")
            c4.metric("Zf módulo", f"{best.get('Zf_mag',0):.3f} Ω")

        with tab6:
            st.markdown('<div class="section-title">Generar Reporte PDF Completo</div>', unsafe_allow_html=True)
            st.markdown("""
            El PDF incluye: portada, resumen ejecutivo, todas las gráficas,
            tabla de métodos, parámetros de línea y conclusiones automáticas.
            """)
            if st.button("📄 Generar PDF", type="primary", use_container_width=True):
                with st.spinner("Generando reporte..."):
                    try:
                        pdf_bytes = generate_pdf_report(data, fault_info, location_results,
                                                         sym_comp, phasors, lp, line_type, line_length)
                        fname = f"reporte_falla_{fault_info['type']}_{data.get('timestamp','event').replace(':','-').replace(' ','_')}.pdf"
                        st.download_button("⬇️ Descargar PDF", data=pdf_bytes,
                                          file_name=fname, mime="application/pdf",
                                          use_container_width=True)
                        st.success("✅ Reporte generado.")
                    except Exception as e:
                        st.error(f"Error: {e}")
else:
    st.markdown("---")
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown("#### 📁 1. Sube tus archivos\nCarga el `.cfg` y `.dat` de tu oscilógrafo. Compatible con IEC 60255-24 / IEEE C37.111.")
    with col2:
        st.markdown("#### ⚙️ 2. Configura la línea\nSelecciona tipo de línea, longitud y relaciones TC/TP en el panel lateral.")
    with col3:
        st.markdown("#### 📊 3. Obtén el reporte\nGráficas interactivas + PDF descargable con análisis exhaustivo.")
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("**69 kV — ACSR HAWK 477**\nZ1: 0.0839+j0.3927 Ω/km\nZ0: 0.2530+j1.1780 Ω/km\nCapacidad: 659 A")
    with col_b:
        st.info("**13.8 kV — ACSR 266**\nZ1: 0.1712+j0.3810 Ω/km\nZ0: 0.3400+j1.1430 Ω/km\nCapacidad: 340 A")
