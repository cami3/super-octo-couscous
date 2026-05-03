# Pokè To Go! – Dashboard Operativa per Arianna

import io
import json
import random
import urllib.request
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ── COLONNE ───────────────────────────────────────────────────────────────────

POKE_COLS     = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl', 'poke_veggy']
EXTRA_COLS    = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
BIBITE_COLS   = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
SORBETTI_COLS = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']
SORB_PZ_COLS  = ['Sorbetti_venduti']
COST_COLS     = ['Dipendente']
EXCLUDE_COLS  = set(POKE_COLS + EXTRA_COLS + BIBITE_COLS + SORBETTI_COLS + SORB_PZ_COLS + COST_COLS + ['data', 'fatturato'])

CATEGORIE_ING = {
    'Proteine': ['salmone', 'tonno', 'Tonno Saku', 'Polpo', 'Gamberetti', 'Pollo Nuggets', 'Pollo fette', 'Feta', 'Formaggio spalmabile', 'Tofu', 'Uova'],
    'Verdure':  ['edamame', 'ceci', 'mais', 'carote', 'cetrioli', 'pomodori', 'Cavolo viola', 'zucchine', 'cipolle', 'Goma wakame'],
    'Frutta':   ['Avocado', 'Avo Hass', 'mango', 'Lime', 'uva', 'Mele', 'melone', 'Kiwi', 'Ananas', 'Anguria'],
    'Base':     ['iceberg', 'riso_sushi', 'riso_nero', 'Riso integrale'],
    'Topping':  ['Sesamo nero', 'Sesamo bianco', 'Mandorle', 'nocciole', 'Cipolle croccanti', 'Pistacchio', 'Sale grosso'],
    'Salse':    ['Salsa soya', 'Olio Evo', 'Teriyaki', 'Maionese', 'yogurt', 'poke', 'Ponzu', 'Sriracha'],
}
ALL_INGRED_COLS = sum(CATEGORIE_ING.values(), [])

ALL_CSV_COLS = (
    ['data', 'fatturato', 'Dipendente']
    + POKE_COLS + EXTRA_COLS + SORB_PZ_COLS
    + BIBITE_COLS + SORBETTI_COLS
    + ALL_INGRED_COLS
)

WMO_EMOJI = {
    0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
    45: '🌫️', 48: '🌫️',
    51: '🌦️', 53: '🌦️', 55: '🌧️',
    61: '🌧️', 63: '🌧️', 65: '🌧️',
    71: '🌨️', 73: '🌨️', 75: '❄️',
    80: '🌦️', 81: '🌦️', 82: '⛈️',
    95: '⛈️', 96: '⛈️', 99: '⛈️',
}

# ── UTILITY ───────────────────────────────────────────────────────────────────

def safe_pct(cost, rev):
    return cost / rev * 100 if rev > 0 else 0.0

def ols_manuale(x, y):
    n = len(x)
    if n < 2:
        return 0.0, (y[0] if y else 0.0)
    mx, my = sum(x) / n, sum(y) / n
    denom = sum((xi - mx) ** 2 for xi in x)
    if denom == 0:
        return 0.0, my
    slope = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / denom
    return slope, my - slope * mx

# ── DISTRIBUZIONE COSTI INGREDIENTI ──────────────────────────────────────────

def distribuisci_costi(df: pd.DataFrame, ingred_cols: list) -> pd.DataFrame:
    """Spread each restock cost evenly across days until the next restock,
    stopping at year boundaries."""
    dist = pd.DataFrame(0.0, index=df.index, columns=ingred_cols)
    for ing in ingred_cols:
        s = df[['data', ing]].dropna()
        s = s[s[ing] > 0].sort_values('data')
        for i in range(len(s)):
            a, val = s.iloc[i]['data'], s.iloc[i][ing]
            fine_anno = pd.Timestamp(int(a.year), 12, 31)
            if i < len(s) - 1:
                b = s.iloc[i + 1]['data']
                mask = (df['data'] >= a) & (df['data'] < b) if a.year == b.year \
                       else (df['data'] >= a) & (df['data'] <= fine_anno)
            else:
                mask = (df['data'] >= a) & (df['data'] <= fine_anno)
            n = mask.sum()
            if n > 0:
                dist.loc[mask, ing] += val / n
    return dist

# ── METEO ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_meteo():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=42.77&longitude=10.19"
            "&daily=weathercode,temperature_2m_max,precipitation_sum"
            "&timezone=Europe%2FRome&forecast_days=7"
        )
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())['daily']
    except Exception:
        return None

# ── CARICAMENTO DATI ──────────────────────────────────────────────────────────

@st.cache_data
def carica_giornaliero(file_bytes: bytes) -> tuple:
    df = pd.read_csv(io.BytesIO(file_bytes), sep=';').dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data']).sort_values('data').reset_index(drop=True)
    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    ingred_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
    df_dist = distribuisci_costi(df, ingred_cols)
    df['ing_dist']       = df_dist.sum(axis=1)
    df['bib_sorb_costo'] = df[[c for c in BIBITE_COLS + SORBETTI_COLS if c in df.columns]].sum(axis=1)
    df['poke_totali']    = df[[c for c in POKE_COLS if c in df.columns]].sum(axis=1).fillna(0)
    df['extra_totali']   = df[[c for c in EXTRA_COLS if c in df.columns]].sum(axis=1).fillna(0)
    df['Dipendente']     = df['Dipendente'].fillna(0)
    df['utile_lordo']    = df['fatturato'] - df['ing_dist'] - df['bib_sorb_costo'] - df['Dipendente']
    df['pct_ingredienti'] = df.apply(lambda r: safe_pct(r['ing_dist'],   r['fatturato']), axis=1)
    df['pct_dipendenti']  = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
    df['anno']  = df['data'].dt.year
    df['mm_dd'] = df['data'].dt.strftime('%m-%d')
    return df, df_dist, ingred_cols

@st.cache_data
def carica_fornitori(file_bytes: bytes):
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=';').dropna(how='all')
        df['data']     = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df['quantita'] = pd.to_numeric(df['quantita'], errors='coerce')
        df['spesa']    = pd.to_numeric(df['spesa'],    errors='coerce')
        df = df.dropna(subset=['data']).sort_values('data').reset_index(drop=True)
        df['prezzo_unitario'] = df['spesa'] / df['quantita'].replace(0, float('nan'))
        return df
    except Exception:
        return None

# ── GENERATORI DATI DI ESEMPIO ────────────────────────────────────────────────

@st.cache_data
def genera_csv_giornaliero():
    rng = random.Random(42)
    ing_ranges = {
        'salmone': (80,200), 'tonno': (60,150), 'Tonno Saku': (40,100), 'Polpo': (50,120),
        'Gamberetti': (40,90), 'Pollo Nuggets': (20,50), 'Pollo fette': (20,50),
        'Feta': (15,40), 'Formaggio spalmabile': (10,30), 'Tofu': (10,25), 'Uova': (5,15),
        'edamame': (15,35), 'ceci': (5,15), 'mais': (5,12), 'carote': (3,8),
        'cetrioli': (4,10), 'pomodori': (5,15), 'Cavolo viola': (4,10),
        'zucchine': (4,10), 'cipolle': (3,8), 'Goma wakame': (15,35),
        'Avocado': (20,60), 'Avo Hass': (20,60), 'mango': (15,40), 'Lime': (5,15),
        'uva': (5,15), 'Mele': (5,12), 'melone': (8,20), 'Kiwi': (5,15),
        'Ananas': (8,20), 'Anguria': (10,30),
        'iceberg': (8,20), 'riso_sushi': (20,50), 'riso_nero': (15,40), 'Riso integrale': (10,25),
        'Sesamo nero': (5,15), 'Sesamo bianco': (5,15), 'Mandorle': (10,25), 'nocciole': (10,25),
        'Cipolle croccanti': (8,20), 'Pistacchio': (15,35), 'Sale grosso': (2,6),
        'Salsa soya': (10,30), 'Olio Evo': (15,40), 'Teriyaki': (15,35),
        'Maionese': (8,20), 'yogurt': (5,15), 'Ponzu': (10,25), 'Sriracha': (8,20),
    }
    _prot = set(CATEGORIE_ING['Proteine'])
    _freq_breve = {'iceberg','riso_sushi','riso_nero','Riso integrale','Avocado','Avo Hass','mango','Anguria','melone'}
    ing_freq = {
        ing: (2,4) if ing in _prot else (3,5) if ing in _freq_breve else (5,9)
        for ing in ALL_INGRED_COLS
    }
    rows = []
    for year in [2024, 2025]:
        start, end = date(year, 6, 1), date(year, 9, 30)
        n_days = (end - start).days + 1
        next_restock = {ing: 0 for ing in ALL_INGRED_COLS}
        for i in range(n_days):
            day = start + timedelta(days=i)
            m, dom, dow = day.month, day.day, day.weekday()
            if   m == 6:               base = rng.uniform(350, 700)
            elif m == 7 and dom <= 14: base = rng.uniform(600, 1000)
            elif m == 7:               base = rng.uniform(800, 1300)
            elif m == 8 and dom <= 20: base = rng.uniform(900, 1400)
            elif m == 8:               base = rng.uniform(700, 1100)
            elif m == 9 and dom <= 15: base = rng.uniform(500, 800)
            else:                      base = rng.uniform(300, 600)
            if dow >= 5:
                base *= rng.uniform(1.15, 1.25)
            if year == 2025:
                base *= rng.uniform(1.03, 1.10)
            fatturato = round(base, 2)
            tot = max(1, int(fatturato / rng.uniform(11, 15)))
            p_reg   = max(0, int(tot * rng.uniform(0.50, 0.62)))
            p_maxi  = max(0, int(tot * rng.uniform(0.15, 0.25)))
            p_baby  = max(0, int(tot * rng.uniform(0.07, 0.13)))
            p_fruit = max(0, int(tot * rng.uniform(0.03, 0.07)))
            p_veg   = max(0, tot - p_reg - p_maxi - p_baby - p_fruit)
            sc = tot / 60.0
            row = {
                'data': day.strftime('%d/%m/%Y'), 'fatturato': fatturato,
                'Dipendente': float(rng.choice([70, 75, 80, 85, 90])),
                'poke_reglular': p_reg, 'poke_maxi': p_maxi, 'poke_baby': p_baby,
                'fruit_bowl': p_fruit, 'poke_veggy': p_veg,
                'Avocado_venduto':  round(p_reg * rng.uniform(0.25, 0.40) * 1.5, 2),
                'Feta_venduto':     round(p_reg * rng.uniform(0.10, 0.20) * 1.5, 2),
                'Philad_venduto':   round(p_reg * rng.uniform(0.15, 0.25) * 1.5, 2),
                'Gomawak_venduto':  round(p_reg * rng.uniform(0.20, 0.35) * 1.5, 2),
                'Sorbetti_venduti': max(0, int(tot * rng.uniform(0.20, 0.50))),
                'Acqua nat':       round(rng.uniform(0.8, 1.5) * sc * 10, 2),
                'Acqua gas':       round(rng.uniform(0.5, 1.2) * sc * 10, 2),
                'Coca cola':       round(rng.uniform(1.0, 2.0) * sc * 10, 2),
                'Coca zero':       round(rng.uniform(0.5, 1.5) * sc * 10, 2),
                'corona':          round(rng.uniform(0.8, 1.8) * sc * 10, 2),
                'ichnusa':         round(rng.uniform(0.8, 1.5) * sc * 10, 2),
                'fanta':           round(rng.uniform(0.4, 0.9) * sc * 10, 2),
                'Estathe limone':  round(rng.uniform(0.4, 0.8) * sc * 10, 2),
                'Estathe pesca':   round(rng.uniform(0.3, 0.7) * sc * 10, 2),
                'Sorbetto limone': round(rng.uniform(1.0, 2.5) * sc * 8, 2),
                'Sorbetto mela':   round(rng.uniform(0.8, 2.0) * sc * 8, 2),
                'Sorbetto mango':  round(rng.uniform(0.9, 2.2) * sc * 8, 2),
            }
            for ing in ALL_INGRED_COLS:
                if i >= next_restock[ing]:
                    lo, hi = ing_ranges[ing]
                    row[ing] = round(rng.uniform(lo, hi), 2)
                    fmin, fmax = ing_freq[ing]
                    next_restock[ing] = i + rng.randint(fmin, fmax)
                else:
                    row[ing] = ''
            rows.append(row)
    df_fake = pd.DataFrame(rows)[ALL_CSV_COLS]
    buf = io.StringIO()
    df_fake.to_csv(buf, sep=';', index=False)
    return buf.getvalue().encode('utf-8')

@st.cache_data
def genera_csv_fornitori():
    rng = random.Random(99)
    config = {
        'salmone':    ('Mario Pesca',    'kg', 32.0),
        'tonno':      ('Mario Pesca',    'kg', 25.0),
        'Polpo':      ('FruttaMare',     'kg', 18.0),
        'Gamberetti': ('FruttaMare',     'kg', 16.0),
        'Avocado':    ('FruttaElba',     'pz',  1.1),
        'riso_sushi': ('Grossisti Elba', 'kg',  4.2),
        'iceberg':    ('FruttaElba',     'kg',  2.5),
        'Salsa soya': ('Grossisti Elba', 'lt',  6.0),
    }
    freq = {
        'salmone': (2,4), 'tonno': (2,4), 'Polpo': (3,5), 'Gamberetti': (3,5),
        'Avocado': (3,5), 'riso_sushi': (5,8), 'iceberg': (4,6), 'Salsa soya': (7,12),
    }
    rows = []
    for year in [2024, 2025]:
        start, end = date(year, 6, 1), date(year, 9, 30)
        n_days = (end - start).days + 1
        next_order = {ing: 0 for ing in config}
        for i in range(n_days):
            d = start + timedelta(days=i)
            for ing, (fornitore, unita, prezzo_base) in config.items():
                if i >= next_order[ing]:
                    q = round(
                        rng.uniform(1.5, 3.5) if unita == 'kg' else
                        rng.uniform(15, 30)   if unita == 'pz' else
                        rng.uniform(2, 5), 2
                    )
                    prezzo = round(
                        prezzo_base
                        * (1 + (i / n_days) * 0.12)
                        * (1 + (year - 2024) * 0.09)
                        * rng.uniform(0.93, 1.07), 2
                    )
                    rows.append({
                        'data': d.strftime('%d/%m/%Y'), 'ingrediente': ing,
                        'fornitore': fornitore, 'quantita': q,
                        'unita': unita, 'spesa': round(q * prezzo, 2),
                    })
                    fmin, fmax = freq[ing]
                    next_order[ing] = i + rng.randint(fmin, fmax)
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, sep=';', index=False)
    return buf.getvalue().encode('utf-8')

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Pokè To Go!", layout="wide", page_icon="🍱")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fdfcfb; }
h1, h2, h3 { color: #e85d04; }
section[data-testid="stSidebar"] { background-color: #fff8f5; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    try:
        from PIL import Image
        st.image(Image.open("logo.png"), width=130)
    except Exception:
        st.markdown("### 🍱 Pokè To Go!")

    st.markdown("---")
    up_gio  = st.file_uploader("📥 CSV Giornaliero", type=["csv"])
    up_forn = st.file_uploader("📦 CSV Fornitori *(opzionale)*", type=["csv"])

    st.markdown("---")
    costi_fissi_gg = st.number_input(
        "💰 Costi fissi (€/giorno apertura)",
        min_value=0, value=150, step=10,
        help="Affitto, utenze, ecc. divisi per i giorni di apertura stimati"
    )
    obiettivo = st.number_input(
        "🎯 Obiettivo fatturato stagione (€)",
        min_value=0, value=80000, step=1000
    )

    st.markdown("---")
    with st.expander("📋 Template e dati di esempio"):
        template_csv = ';'.join(ALL_CSV_COLS) + '\n' + ';'.join(['gg/mm/aaaa'] + [''] * (len(ALL_CSV_COLS) - 1)) + '\n'
        st.download_button("⬇️ Template giornaliero vuoto",
                           data=template_csv.encode('utf-8'),
                           file_name="template_giornaliero.csv", mime="text/csv",
                           use_container_width=True)
        st.download_button("🎲 Dati esempio giornaliero (2024–2025)",
                           data=genera_csv_giornaliero(),
                           file_name="esempio_giornaliero.csv", mime="text/csv",
                           use_container_width=True)
        st.download_button("🎲 Dati esempio fornitori (2024–2025)",
                           data=genera_csv_fornitori(),
                           file_name="esempio_fornitori.csv", mime="text/csv",
                           use_container_width=True)
        st.markdown("""
**CSV Giornaliero** — separatore `;`, date `gg/mm/aaaa`
Ingredienti: compila solo nei giorni di rifornimento.

**CSV Fornitori** — colonne:
`data ; ingrediente ; fornitore ; quantita ; unita ; spesa`
        """)

# ── GUARDIA ───────────────────────────────────────────────────────────────────

if not up_gio:
    st.title("🍱 Pokè To Go! – Dashboard Operativa")
    st.info("👈 Carica il CSV giornaliero dalla sidebar per iniziare.")
    st.stop()

# ── CARICAMENTO (bytes in session_state per compatibilità con cache) ──────────

if st.session_state.get("gio_name") != up_gio.name:
    st.session_state["gio_bytes"] = up_gio.read()
    st.session_state["gio_name"]  = up_gio.name

df, df_dist, ingred_cols = carica_giornaliero(st.session_state["gio_bytes"])

if up_forn:
    if st.session_state.get("forn_name") != up_forn.name:
        st.session_state["forn_bytes"] = up_forn.read()
        st.session_state["forn_name"]  = up_forn.name
    df_forn = carica_fornitori(st.session_state["forn_bytes"])
else:
    df_forn = None

anni          = sorted(df['anno'].unique())
anno_corrente = int(anni[-1])
anno_prec     = int(anni[-2]) if len(anni) > 1 else None

# ── CONTROLLO QUALITÀ ─────────────────────────────────────────────────────────

with st.expander("🔍 Controllo qualità file", expanded=False):
    campi = [c for c in ['fatturato', 'Dipendente'] + POKE_COLS + EXTRA_COLS if c in df.columns]
    avvisi = 0
    for col in campi:
        nan_dates = df.loc[df[col].isna(), 'data'].dt.strftime('%d/%m/%Y').tolist()
        if nan_dates:
            st.warning(f"⚠️ **{col}** vuoto in {len(nan_dates)} giorni → {', '.join(nan_dates[:5])}")
            avvisi += 1
    _vend = df[[c for c in POKE_COLS + EXTRA_COLS if c in df.columns]].sum(axis=1)
    for cond, msg in [
        ((df['fatturato'] > 0) & (_vend == 0), "💸 Fatturato > 0 ma nessuna vendita registrata"),
        ((df['fatturato'] == 0) & (_vend > 0), "📜 Vendite > 0 ma fatturato = 0"),
    ]:
        if cond.any():
            st.warning(msg + " in: " + ', '.join(df.loc[cond, 'data'].dt.strftime('%d/%m/%Y').tolist()[:5]))
            avvisi += 1
    if avvisi == 0:
        st.success("✅ Nessuna anomalia rilevata.")

# ══════════════════════════════════════════════════════════════════════════════
# SEZIONE 1 — BRIEFING OPERATIVO
# ══════════════════════════════════════════════════════════════════════════════

st.header(f"☀️ Briefing operativo — stagione {anno_corrente}")

# Meteo 7 giorni
meteo = fetch_meteo()
if meteo:
    giorni_it = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    for col, i in zip(st.columns(7), range(7)):
        d       = pd.to_datetime(meteo['time'][i])
        icon    = WMO_EMOJI.get(int(meteo['weathercode'][i]), '❓')
        tmax    = meteo['temperature_2m_max'][i]
        pioggia = meteo['precipitation_sum'][i]
        col.markdown(
            f"<div style='background:#fff5f0;border-radius:10px;padding:8px;"
            f"text-align:center;font-size:.82rem'>"
            f"<b>{giorni_it[d.weekday()]} {d.day}/{d.month}</b><br>"
            f"{icon}<br><b>{tmax:.0f}°C</b><br>💧{pioggia:.0f}mm</div>",
            unsafe_allow_html=True
        )
    st.caption("📍 Procchio, Isola d'Elba — aggiornato ogni ora")
else:
    st.caption("⚠️ Previsioni meteo non disponibili al momento")

st.markdown("")

# KPI ultimi 7 giorni aperti (esclusi giorni chiusi / fatturato=0)
df_open = df[(df['anno'] == anno_corrente) & (df['fatturato'] > 0)]
df_7    = df_open.tail(7)
n_7     = len(df_7)

fat7  = df_7['fatturato'].sum()
poke7 = df_7['poke_totali'].sum()
util7 = df_7['utile_lordo'].sum()
ping7 = df_7['pct_ingredienti'].mean() if n_7 else 0.0

delta_fat = delta_poke = delta_util = None
if anno_prec and n_7:
    d_min = df_7['data'].min().replace(year=anno_prec)
    d_max = df_7['data'].max().replace(year=anno_prec)
    df_7p = df[
        (df['anno'] == anno_prec) & (df['fatturato'] > 0) &
        (df['data'] >= d_min) & (df['data'] <= d_max)
    ]
    if not df_7p.empty:
        def _delta(a, b):
            return f"{(a - b) / b * 100:+.1f}% vs {anno_prec}" if b else None
        delta_fat  = _delta(fat7,  df_7p['fatturato'].sum())
        delta_poke = _delta(poke7, df_7p['poke_totali'].sum())
        delta_util = _delta(util7, df_7p['utile_lordo'].sum())

label_7 = f"ultimi {n_7} giorni aperti" if n_7 < 7 else "ultimi 7 giorni aperti"
kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric(f"Fatturato ({label_7})",    f"€ {fat7:,.0f}",  delta_fat)
kc2.metric(f"Poke venduti ({label_7})", f"{int(poke7):,}", delta_poke)
kc3.metric(f"Utile lordo ({label_7})",  f"€ {util7:,.0f}", delta_util)
kc4.metric("% Ingredienti media",       f"{ping7:.1f}%")

if n_7 < 5:
    st.caption(f"ℹ️ Solo {n_7} giorni con fatturato registrato — i KPI si normalizzano con l'avanzare della stagione.")

# KPI stagione in corso
st.markdown("**📊 Stagione in corso**")
fat_stagione = df_open['fatturato'].sum()
ul_stagione  = df_open['utile_lordo'].sum()
poke_stag    = df_open['poke_totali'].sum()
giorni_stag  = len(df_open)

delta_fat_stag = delta_ul_stag = None
if anno_prec and not df_open.empty:
    ult_mm_dd    = df_open['mm_dd'].max()
    df_prev_open = df[(df['anno'] == anno_prec) & (df['fatturato'] > 0)]
    df_prev_per  = df_prev_open[df_prev_open['mm_dd'] <= ult_mm_dd]
    if not df_prev_per.empty:
        def _delta_s(a, b):
            return f"{(a - b) / b * 100:+.1f}% vs {anno_prec}" if b else None
        delta_fat_stag = _delta_s(fat_stagione, df_prev_per['fatturato'].sum())
        delta_ul_stag  = _delta_s(ul_stagione,  df_prev_per['utile_lordo'].sum())

sc1, sc2, sc3, sc4 = st.columns(4)
sc1.metric(f"Fatturato {anno_corrente}",  f"€ {fat_stagione:,.0f}", delta_fat_stag)
sc2.metric("Utile lordo stagione",        f"€ {ul_stagione:,.0f}",  delta_ul_stag)
sc3.metric("Poke venduti stagione",       f"{int(poke_stag):,}")
sc4.metric("Giorni aperti",               str(giorni_stag))

if obiettivo > 0:
    st.markdown(f"**🎯 Obiettivo {anno_corrente}: € {fat_stagione:,.0f} / € {obiettivo:,.0f}**")
    st.progress(min(fat_stagione / obiettivo, 1.0))
    if fat_stagione >= obiettivo:
        st.success(f"🏆 Obiettivo raggiunto! Hai superato di € {fat_stagione - obiettivo:,.0f}")
    else:
        mancano = obiettivo - fat_stagione
        ultima_data = df_open['data'].max() if not df_open.empty else df[df['anno'] == anno_corrente]['data'].max()
        fine_stagione = pd.Timestamp(date(anno_corrente, 9, 30))
        giorni_rimasti = (fine_stagione - ultima_data).days
        if giorni_rimasti > 0:
            st.info(
                f"Mancano **€ {mancano:,.0f}** — "
                f"serve una media di **€ {mancano / giorni_rimasti:,.0f}/giorno** "
                f"nei ~{giorni_rimasti} giorni rimanenti"
            )
        else:
            st.warning(f"Stagione conclusa. Mancavano € {mancano:,.0f} all'obiettivo.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SEZIONE 2 — LA STAGIONE
# ══════════════════════════════════════════════════════════════════════════════

st.header("📈 La stagione")

col_y, col_cb = st.columns([1, 2])
with col_y:
    anno_sel = int(st.selectbox("Anno", options=[int(a) for a in anni[::-1]], index=0))
with col_cb:
    label_yoy = f"Confronta con {anno_prec}" if anno_prec else "Nessun anno precedente"
    mostra_yoy = st.checkbox(label_yoy, value=(anno_prec is not None), disabled=(anno_prec is None))

df_anno = df[df['anno'] == anno_sel].copy()

# Curva fatturato con eventuale overlay anno precedente
fig_stag = go.Figure()
fig_stag.add_trace(go.Scatter(
    x=df_anno['mm_dd'],
    y=df_anno['fatturato'].rolling(3, center=True, min_periods=1).mean(),
    mode='lines', name=str(anno_sel),
    line=dict(color='#e85d04', width=2.5),
    fill='tozeroy', fillcolor='rgba(232,93,4,0.08)',
    hovertemplate='%{x} — € %{y:,.0f}<extra></extra>',
))
if mostra_yoy and anno_prec:
    df_prev_stag = df[df['anno'] == anno_prec].copy()
    fig_stag.add_trace(go.Scatter(
        x=df_prev_stag['mm_dd'],
        y=df_prev_stag['fatturato'].rolling(3, center=True, min_periods=1).mean(),
        mode='lines', name=str(anno_prec),
        line=dict(color='#aaa', width=1.5, dash='dot'),
        hovertemplate='%{x} — € %{y:,.0f}<extra></extra>',
    ))
fig_stag.update_layout(
    title="Fatturato giornaliero (media mobile 3gg)",
    xaxis=dict(title=None, tickangle=-30),
    yaxis_title="€", hovermode='x unified',
    legend=dict(orientation='h', y=1.02),
    margin=dict(t=50, b=10),
)
st.plotly_chart(fig_stag, use_container_width=True)

# Metriche aggregate stagione
fat_tot  = df_anno['fatturato'].sum()
ul_tot   = df_anno['utile_lordo'].sum()
un_tot   = ul_tot - costi_fissi_gg * len(df_anno)
poke_tot = df_anno['poke_totali'].sum()
ric_poke = fat_tot / poke_tot if poke_tot > 0 else 0

s1, s2, s3, s4 = st.columns(4)
s1.metric("Fatturato stagione",    f"€ {fat_tot:,.0f}")
s2.metric("Utile lordo",           f"€ {ul_tot:,.0f}")
s3.metric("Utile netto stimato",   f"€ {un_tot:,.0f}",
          help=f"€ {costi_fissi_gg}/gg × {len(df_anno)} giorni = € {costi_fissi_gg * len(df_anno):,.0f} costi fissi")
s4.metric("Ricavo medio per poke", f"€ {ric_poke:.2f}")

# Tabella confronto multi-anno
if len(anni) > 1:
    st.markdown("**Confronto stagioni**")
    righe = []
    for a in anni:
        dfa = df[df['anno'] == a]
        n   = len(dfa)
        fat_a = dfa['fatturato'].sum()
        ul_a  = dfa['utile_lordo'].sum()
        righe.append({
            'Anno': int(a),
            'Fatturato': f"€ {fat_a:,.0f}",
            'Utile lordo': f"€ {ul_a:,.0f}",
            'Utile netto': f"€ {ul_a - costi_fissi_gg * n:,.0f}",
            'Poke venduti': f"{int(dfa['poke_totali'].sum()):,}",
            '% Ing. media': f"{dfa['pct_ingredienti'].mean():.1f}%",
            'Giorni aperti': n,
        })
    st.dataframe(pd.DataFrame(righe), hide_index=True, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SEZIONE 3 — DETTAGLIO OPERATIVO
# ══════════════════════════════════════════════════════════════════════════════

st.header("🔍 Dettaglio operativo")

min_d = df_anno['data'].min().date()
max_d = df_anno['data'].max().date()
date_range = st.date_input(
    "Periodo di analisi",
    value=(min_d, max_d),
    min_value=min_d, max_value=max_d,
    format="DD/MM/YYYY",
)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_sel = pd.Timestamp(date_range[0])
    end_sel   = pd.Timestamp(date_range[1])
else:
    start_sel, end_sel = pd.Timestamp(min_d), pd.Timestamp(max_d)

df_sel = df_anno[(df_anno['data'] >= start_sel) & (df_anno['data'] <= end_sel)].copy()

if df_sel.empty:
    st.warning("⚠️ Nessun dato nel periodo selezionato.")
    st.stop()

df_dist_sel = df[['data']].join(df_dist)
df_dist_sel = df_dist_sel[
    (df_dist_sel['data'] >= start_sel) & (df_dist_sel['data'] <= end_sel)
]

tab_v, tab_c, tab_f, tab_r, tab_cr = st.tabs([
    "📈 Vendite", "💸 Costi", "🏪 Fornitori", "📦 Rifornimenti", "⚠️ Giornate critiche"
])

# ── TAB VENDITE ───────────────────────────────────────────────────────────────
with tab_v:
    poke_avail = [c for c in POKE_COLS if c in df_sel.columns]
    melt_poke  = df_sel[['data'] + poke_avail].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(
        px.bar(melt_poke, x='data', y='Pezzi', color='Tipo', barmode='stack',
               labels={'data': ''}, title="Poke venduti per tipo"),
        use_container_width=True
    )

    fig_duo = go.Figure()
    fig_duo.add_trace(go.Bar(
        x=df_sel['data'], y=df_sel['fatturato'],
        name='Fatturato', marker_color='rgba(232,93,4,0.45)'
    ))
    fig_duo.add_trace(go.Scatter(
        x=df_sel['data'], y=df_sel['utile_lordo'],
        name='Utile lordo', mode='lines+markers',
        line=dict(color='#2d6a4f', width=2)
    ))
    fig_duo.add_hline(y=0, line_dash='dash', line_color='red', annotation_text='Pareggio')
    fig_duo.update_layout(
        title="Fatturato e utile lordo giornaliero",
        xaxis_title=None, yaxis_title="€",
        hovermode='x unified', legend=dict(orientation='h')
    )
    st.plotly_chart(fig_duo, use_container_width=True)

    df_sel['margine_per_poke'] = df_sel.apply(
        lambda r: r['utile_lordo'] / r['poke_totali'] if r['poke_totali'] > 0 else None, axis=1
    )
    top5 = df_sel.nlargest(5, 'margine_per_poke')[
        ['data', 'fatturato', 'poke_totali', 'margine_per_poke', 'utile_lordo']
    ].copy()
    top5.columns = ['Data', 'Fatturato (€)', 'Poke', 'Margine/poke (€)', 'Utile lordo (€)']
    st.subheader("💰 Top 5 giorni per margine per poke")
    st.dataframe(top5.round(2), hide_index=True, use_container_width=True)

# ── TAB COSTI ─────────────────────────────────────────────────────────────────
with tab_c:
    fat = df_sel['fatturato'].sum()
    ing = df_sel['ing_dist'].sum()
    dip = df_sel['Dipendente'].sum()
    bib = df_sel['bib_sorb_costo'].sum()
    cf  = costi_fissi_gg * len(df_sel)
    ul  = fat - ing - dip - bib
    un  = ul - cf

    cc1, cc2 = st.columns([1, 2])
    with cc1:
        st.metric("Fatturato",       f"€ {fat:,.0f}")
        st.metric("Ingredienti",     f"€ {ing:,.0f}", f"{safe_pct(ing, fat):.1f}% del fatturato")
        st.metric("Dipendente",      f"€ {dip:,.0f}", f"{safe_pct(dip, fat):.1f}%")
        st.metric("Bibite/Sorbetti", f"€ {bib:,.0f}", f"{safe_pct(bib, fat):.1f}%")
        st.metric("Costi fissi",     f"€ {cf:,.0f}",  f"{safe_pct(cf,  fat):.1f}%")
        st.divider()
        st.metric("Utile lordo",     f"€ {ul:,.0f}",  f"{safe_pct(ul, fat):.1f}%")
        if un >= 0:
            st.metric("✅ Utile netto", f"€ {un:,.0f}", f"{safe_pct(un, fat):.1f}%")
        else:
            st.metric("🔴 Perdita netta", f"€ {un:,.0f}")
    with cc2:
        if un < 0:
            st.warning(f"⚠️ Utile netto negativo nel periodo: € {un:,.0f}")
        pie_data = pd.DataFrame({
            'Voce': ['Ingredienti', 'Dipendente', 'Bibite/Sorbetti', 'Costi fissi', 'Utile netto'],
            '€':    [ing, dip, bib, cf, max(un, 0)],
        })
        fig_pie = px.pie(
            pie_data[pie_data['€'] > 0], values='€', names='Voce', hole=0.4,
            color_discrete_sequence=['#e07b39', '#4a90d9', '#9b59b6', '#95a5a6', '#2d6a4f']
        )
        fig_pie.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    melt_pct = df_sel[['data', 'pct_ingredienti', 'pct_dipendenti']].melt(
        'data', var_name='Voce', value_name='%'
    )
    fig_pct = px.line(melt_pct, x='data', y='%', color='Voce', markers=True,
                      title="% Ingredienti e Dipendenti nel tempo")
    fig_pct.add_hline(y=25, line_dash='dash', line_color='orange', annotation_text='Soglia 25%')
    fig_pct.update_layout(xaxis_title=None, yaxis_title='% sul fatturato',
                          legend=dict(orientation='h'))
    st.plotly_chart(fig_pct, use_container_width=True)

    ing_avail = [c for c in ingred_cols if c in df_dist_sel.columns]
    if ing_avail:
        top10 = df_dist_sel[ing_avail].mean().sort_values(ascending=False).head(10).reset_index()
        top10.columns = ['Ingrediente', '€/giorno medio']
        fig_top = px.bar(top10, x='Ingrediente', y='€/giorno medio', text='€/giorno medio',
                         title="Top 10 ingredienti per costo medio giornaliero distribuito")
        fig_top.update_traces(texttemplate='€%{text:.2f}', textposition='outside',
                              marker_color='#e85d04')
        fig_top.update_layout(xaxis_title=None)
        st.plotly_chart(fig_top, use_container_width=True)

# ── TAB FORNITORI ─────────────────────────────────────────────────────────────
with tab_f:
    if df_forn is None:
        st.info("👈 Carica il CSV Fornitori dalla sidebar per sbloccare questa sezione.")
    else:
        df_f_sel = df_forn[
            (df_forn['data'] >= start_sel) & (df_forn['data'] <= end_sel)
        ].copy()

        if df_f_sel.empty:
            st.info("Nessun ordine fornitore nel periodo selezionato.")
        else:
            ing_dispo = sorted(df_f_sel['ingrediente'].dropna().unique())
            scelta = st.selectbox("Ingrediente", ['— tutti —'] + ing_dispo)
            df_f = df_f_sel if scelta == '— tutti —' else df_f_sel[df_f_sel['ingrediente'] == scelta].copy()

            st.subheader("Prezzo unitario nel tempo")
            fig_sc = px.scatter(
                df_f, x='data', y='prezzo_unitario', color='ingrediente',
                size='spesa', hover_data=['fornitore', 'quantita', 'unita', 'spesa'],
                labels={'prezzo_unitario': '€/unità', 'data': ''},
            )
            if scelta != '— tutti —' and len(df_f) > 2:
                x_num = [(d - df_f['data'].min()).days for d in df_f['data']]
                y_num = df_f['prezzo_unitario'].tolist()
                if len(y_num) == len(x_num) and not any(v != v for v in y_num):
                    slope, intercept = ols_manuale(x_num, y_num)
                    fig_sc.add_trace(go.Scatter(
                        x=df_f['data'],
                        y=[intercept + slope * xi for xi in x_num],
                        mode='lines', name='Trend',
                        line=dict(color='red', dash='dot', width=1.5)
                    ))
            st.plotly_chart(fig_sc, use_container_width=True)

            if scelta != '— tutti —':
                media_p = df_f['prezzo_unitario'].mean()
                std_p   = df_f['prezzo_unitario'].std()
                if pd.notna(std_p) and std_p > 0:
                    for _, r in df_f[df_f['prezzo_unitario'] > media_p + std_p].iterrows():
                        pct = (r['prezzo_unitario'] - media_p) / media_p * 100
                        st.warning(
                            f"⚠️ **{r['data'].strftime('%d/%m/%Y')}** — {r['ingrediente']} "
                            f"da *{r['fornitore']}*: € {r['prezzo_unitario']:.2f}/u "
                            f"(+{pct:.0f}% rispetto alla media)"
                        )

            st.subheader("Spesa totale per fornitore")
            sp = df_f.groupby('fornitore')['spesa'].sum().reset_index().sort_values('spesa', ascending=False)
            sp.columns = ['Fornitore', 'Spesa totale (€)']
            st.dataframe(sp, hide_index=True, use_container_width=True)

            st.subheader("Tutti gli ordini")
            cols_show = [c for c in ['data','ingrediente','fornitore','quantita','unita','spesa','prezzo_unitario'] if c in df_f.columns]
            st.dataframe(df_f[cols_show].round(2), hide_index=True, use_container_width=True)

# ── TAB RIFORNIMENTI ──────────────────────────────────────────────────────────
with tab_r:
    cat_r  = st.selectbox("Categoria", ['Tutti'] + list(CATEGORIE_ING.keys()), key='cat_r')
    cols_r = ingred_cols if cat_r == 'Tutti' else [c for c in CATEGORIE_ING.get(cat_r, []) if c in df_sel.columns]

    df_rif = df_sel[['data'] + cols_r].copy()
    df_rif = df_rif[(df_rif[cols_r] > 0).any(axis=1)]
    melted_r = df_rif.melt(id_vars='data', var_name='Ingrediente', value_name='Spesa (€)')
    melted_r = melted_r[melted_r['Spesa (€)'] > 0]

    if melted_r.empty:
        st.info("Nessun rifornimento registrato per questa categoria nel periodo.")
    else:
        st.plotly_chart(
            px.bar(melted_r, x='data', y='Spesa (€)', color='Ingrediente', barmode='stack',
                   title="Spese di rifornimento per ingrediente", labels={'data': ''}),
            use_container_width=True
        )
        daily_r = melted_r.groupby('data')['Spesa (€)'].sum().reset_index()
        daily_r['Cumulata (€)'] = daily_r['Spesa (€)'].cumsum()
        st.plotly_chart(
            px.line(daily_r, x='data', y='Cumulata (€)', markers=True,
                    title="Spesa cumulata rifornimenti", labels={'data': ''}),
            use_container_width=True
        )
        st.dataframe(
            melted_r.sort_values(['data', 'Ingrediente']).round(2),
            hide_index=True, use_container_width=True
        )

# ── TAB GIORNATE CRITICHE ─────────────────────────────────────────────────────
with tab_cr:
    sc1, sc2 = st.columns(2)
    soglia_ing = sc1.slider("Soglia % ingredienti o dipendenti", 10, 50, 25, step=5)
    soglia_fat = sc2.number_input("Fatturato minimo (€)", min_value=0, value=360, step=20)

    critici = df_sel[
        (df_sel['pct_ingredienti'] > soglia_ing) |
        (df_sel['pct_dipendenti']  > soglia_ing) |
        (df_sel['fatturato']       < soglia_fat)
    ].copy()

    if critici.empty:
        st.success("✅ Nessuna giornata critica nel periodo selezionato.")
    else:
        def _motivo(r):
            m = []
            if r['pct_ingredienti'] > soglia_ing: m.append(f"🧂 Ing. {r['pct_ingredienti']:.0f}%")
            if r['pct_dipendenti']  > soglia_ing: m.append(f"👥 Dip. {r['pct_dipendenti']:.0f}%")
            if r['fatturato']       < soglia_fat: m.append(f"📉 Fat. €{r['fatturato']:.0f}")
            return '  '.join(m)
        critici['Motivo'] = critici.apply(_motivo, axis=1)
        st.info(f"{len(critici)} giorni da monitorare su {len(df_sel)} totali ({len(critici)/len(df_sel)*100:.0f}%)")
        st.dataframe(
            critici[['data','fatturato','poke_totali','pct_ingredienti','pct_dipendenti','utile_lordo','Motivo']].round(1).rename(columns={
                'data': 'Data', 'fatturato': 'Fatturato (€)', 'poke_totali': 'Poke',
                'pct_ingredienti': '% Ing', 'pct_dipendenti': '% Dip',
                'utile_lordo': 'Utile lordo (€)',
            }),
            hide_index=True, use_container_width=True
        )

# ── EXPORT ────────────────────────────────────────────────────────────────────
st.divider()
st.download_button(
    "📥 Scarica analisi periodo (CSV)",
    data=df_sel.to_csv(sep=';', index=False).encode('utf-8'),
    file_name=f"analisi_poketogo_{anno_sel}.csv",
    mime='text/csv',
)
