"""
Genera archivos COMTRADE de prueba (IEEE C37.111-1991 ASCII).
Simula una falla AG (Fase A a tierra) a los 50 ms de inicio del registro.

Uso:
    python generate_sample_comtrade.py
Salida:
    sample_data/fault_AG_69kV.cfg
    sample_data/fault_AG_69kV.dat
"""

import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Parámetros de simulación ──────────────────────────────────────────────────
FS       = 3840          # Hz (64 muestras/ciclo @ 60 Hz)
F0       = 60            # Hz
T_TOTAL  = 0.200         # s (200 ms)
T_FAULT  = 0.050         # s — onset de falla
T_CLEAR  = 0.150         # s — apertura de interruptor

VN_PH    = 69e3 / np.sqrt(3)   # tensión de fase nominal 69 kV (V)
IN_PH    = 100.0                # corriente nominal pre-falla (A primarios)
I_FAULT  = 800.0                # corriente de falla (A)
FAULT_D  = 0.6                  # ubicación falla (60% de la línea)
RF       = 5.0                  # resistencia de arco (Ω)

# ── Generación de señales ─────────────────────────────────────────────────────
N  = int(T_TOTAL * FS)
t  = np.arange(N) / FS
dt = 1 / FS

theta = 2 * np.pi * F0 * t
A120  = np.exp(1j * 2 * np.pi / 3)

# Pre-fault
Va0 = VN_PH * np.sqrt(2) * np.cos(theta)
Vb0 = VN_PH * np.sqrt(2) * np.cos(theta - 2*np.pi/3)
Vc0 = VN_PH * np.sqrt(2) * np.cos(theta + 2*np.pi/3)
Ia0 = IN_PH * np.sqrt(2) * np.cos(theta - np.pi/6)
Ib0 = IN_PH * np.sqrt(2) * np.cos(theta - np.pi/6 - 2*np.pi/3)
Ic0 = IN_PH * np.sqrt(2) * np.cos(theta - np.pi/6 + 2*np.pi/3)

# Fault contribution (AG fault)
Z1  = complex(0.0841, 0.3932)  # Ω/km
Z0  = complex(0.2530, 1.1796)
Zf  = Z1 * FAULT_D * 50        # 50 km línea
mask_fault = (t >= T_FAULT) & (t < T_CLEAR)
mask_post  = t >= T_CLEAR

# Voltage collapse on phase A at fault point
Va = Va0.copy()
Vb = Vb0.copy()
Vc = Vc0.copy()
Ia = Ia0.copy()
Ib = Ib0.copy()
Ic = Ic0.copy()

# Fault phase voltages / currents (simplified)
Va[mask_fault] *= 0.25  # heavy voltage dip on phase A
Ia[mask_fault] = I_FAULT * np.sqrt(2) * np.cos(theta[mask_fault] - np.pi/5)
Ib[mask_fault] *= 1.05  # slight increase Ib, Ic due to coupling
Ic[mask_fault] *= 1.05

# Add DC offset at onset (transient)
n_onset = int(T_FAULT * FS)
dc_decay = np.exp(-np.arange(N - n_onset) / (FS / F0 * 1.5))
Ia[n_onset:] += 300 * np.sqrt(2) * dc_decay * mask_fault[n_onset:].astype(float)

# Noise
rng = np.random.default_rng(42)
for sig in [Va, Vb, Vc]:
    sig += rng.normal(0, VN_PH * 0.002, N)
for sig in [Ia, Ib, Ic]:
    sig += rng.normal(0, IN_PH * 0.01, N)

# ── Escalar a secundarios de TC/TP ────────────────────────────────────────────
CTR = 400
VTR = 600
Va_s = Va / VTR;  Vb_s = Vb / VTR;  Vc_s = Vc / VTR
Ia_s = Ia / CTR;  Ib_s = Ib / CTR;  Ic_s = Ic / CTR

# ── Escribir .CFG ─────────────────────────────────────────────────────────────
BASE_NAME = "fault_AG_69kV"
cfg_path  = os.path.join(OUT_DIR, f"{BASE_NAME}.cfg")
dat_path  = os.path.join(OUT_DIR, f"{BASE_NAME}.dat")

n_analog = 6
n_digital = 0
n_channels = n_analog + n_digital

cfg_lines = []
cfg_lines.append(f"{BASE_NAME},69kV Line,1991")
cfg_lines.append(f"{n_channels},{n_analog}A,{n_digital}D")

# Analog channels: idx,name,phase,ccbm,uu,a,b,skew,min,max,primary,secondary,PS
ch_defs = [
    (1, "Va", "A", "A", "V",  VTR, 0),
    (2, "Vb", "B", "B", "V",  VTR, 0),
    (3, "Vc", "C", "C", "V",  VTR, 0),
    (4, "Ia", "A", "A", "A",  CTR, 0),
    (5, "Ib", "B", "B", "A",  CTR, 0),
    (6, "Ic", "C", "C", "A",  CTR, 0),
]

raw_max_V = np.max(np.abs(np.column_stack([Va_s, Vb_s, Vc_s])))
raw_max_I = np.max(np.abs(np.column_stack([Ia_s, Ib_s, Ic_s])))

for idx, name, ph, ccbm, unit, ratio, skew in ch_defs:
    a = 1.0   # multiply factor
    b = 0.0   # offset
    raw_max = raw_max_V if unit == "V" else raw_max_I
    cfg_lines.append(
        f"{idx},{name},{ph},{ccbm},{unit},{a:.6f},{b:.6f},{skew},\
{-raw_max*1.1:.4f},{raw_max*1.1:.4f},{ratio:.1f},1.0,P"
    )

# Frequency, sample rate
cfg_lines.append(f"{F0}")
cfg_lines.append("1")
cfg_lines.append(f"{FS},{N}")
cfg_lines.append("01/01/2024,00:00:00.000000")
cfg_lines.append("01/01/2024,00:00:00.000000")
cfg_lines.append("ASCII")
cfg_lines.append("1.0")

with open(cfg_path, "w") as f:
    f.write("\n".join(cfg_lines) + "\n")

# ── Escribir .DAT (ASCII) ─────────────────────────────────────────────────────
signals_s = [Va_s, Vb_s, Vc_s, Ia_s, Ib_s, Ic_s]
with open(dat_path, "w") as f:
    for i in range(N):
        t_us = int(round(t[i] * 1e6))
        vals = ",".join(f"{int(round(sig[i] * 1000))}" for sig in signals_s)
        f.write(f"{i+1},{t_us},{vals}\n")

print(f"✅ Archivos generados:")
print(f"   {cfg_path}")
print(f"   {dat_path}")
print(f"   Duración: {T_TOTAL*1000:.0f} ms | Falla AG onset: {T_FAULT*1000:.0f} ms")
print(f"   Muestras: {N} @ {FS} Hz")
