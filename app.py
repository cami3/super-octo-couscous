# Pokè To Go! – Dashboard corretta per decisioni operative
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# --- CONFIG ---
st.set_page_config(page_title="Pokè To Go! Dashboard", layout="wide")
st.image(Image.open("logo.png"), width=150)

# --- STILE ---
st.markdown("""
    <style>
    .main {
        background-color: #fdfcfb;
    }
    h1, h2, h3 {
        color: #e85d04;
    }
    .stMetric {
        background-color: #fff7ed;
        border-radius: 10px;
        padding: 10px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stDataFrame {
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- TITOLO ---
st.title("🍣 Pokè To Go – Dashboard Operativa")

# --- UPLOAD ---
uploaded = st.file_uploader("⬆️ Carica file CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data', 'fatturato'])

for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

# --- COLONNE ---
poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

# --- COSTI DISTRIBUITI ---
df_dist = pd.DataFrame(index=df.index)
for ing in ingred_cols:
    s = df[['data', ing]].dropna()
    s = s[s[ing] > 0].sort_values('data')
    arr = pd.Series(0.0, index=df.index)
    for i in range(len(s) - 1):
        a, b = s.iloc[i]['data'], s.iloc[i+1]['data']
        days = (b - a).days
        if days > 0:
            arr[(df['data'] >= a) & (df['data'] < b)] += s.iloc[i][ing] / days
    df_dist[ing] = arr

df_dist['data'] = df['data']

# --- INTERVALLO ---
min_date, max_date = df['data'].min(), df['data'].max()
with st.form("date_form"):
    start, end = st.date_input("🗓️ Intervallo Analisi", [min_date.date(), max_date.date()], min_value=min_date.date(), max_value=max_date.date())
    submitted = st.form_submit_button("🔍 Analizza")
if not submitted:
    st.stop()

start, end = pd.to_datetime(start), pd.to_datetime(end)
df_sel = df[(df['data'] >= start) & (df['data'] <= end)].copy()
df_dist_sel = df_dist[(df_dist['data'] >= start) & (df_dist['data'] <= end)].copy()

# --- CALCOLI ---
def safe_pct(cost, rev):
    return cost / rev * 100 if rev > 0 else 0

df_sel['totale_ingredienti'] = df_dist_sel[ingred_cols].sum(axis=1)
df_sel['% ingredienti'] = df_sel.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df_sel['% dipendenti'] = df_sel.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df_sel['poke_totali'] = df_sel[poke_cols].sum(axis=1)
df_sel['extra_totali'] = df_sel[extra_cols].sum(axis=1)
df_sel['utile'] = df_sel['fatturato'] - df_sel['totale_ingredienti'] - df_sel['Dipendente']
df_sel['giorno_settimana'] = df_sel['data'].dt.day_name()

# --- METRICHE ---
st.header("📌 Metriche Totali – Performance del periodo")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatturato", f"€ {df_sel['fatturato'].sum():,.2f}")
col2.metric("Ingredienti stimati", f"€ {df_sel['totale_ingredienti'].sum():,.2f}")
col3.metric("Dipendenti", f"€ {df_sel['Dipendente'].sum():,.2f}")
col4.metric("Utile stimato", f"€ {df_sel['utile'].sum():,.2f}")

# --- KPI ---
st.header("📈 KPI Operativi – Efficienza e Ricavi")
tot_poke = df_sel['poke_totali'].sum()
tot_extra = df_sel['extra_totali'].sum()
ricavi = df_sel['fatturato'].sum()
costo_ingredienti = df_sel['totale_ingredienti'].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Ricavo Medio per Poke", f"€ {ricavi / tot_poke:.2f}" if tot_poke > 0 else "N/A")
col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
col3.metric("Costo Ingredienti per Poke", f"€ {costo_ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

# --- ANALISI SETTIMANALE ---
st.header("📊 Andamento settimanale")
df_giorni = df_sel.groupby('giorno_settimana').agg({'fatturato': 'mean', 'poke_totali': 'sum', 'utile': 'mean'}).reindex([
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
])
st.bar_chart(df_giorni['fatturato'], height=250)

# --- GIORNATE CRITICHE ---
st.header("❗ Giornate da monitorare")
critici = df_sel[(df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 300)]
critici['Attenzione'] = ""
critici.loc[critici['% ingredienti'] > 35, 'Attenzione'] += "🧂 Alto costo ingredienti  "
critici.loc[critici['% dipendenti'] > 25, 'Attenzione'] += "👥 Alto costo dipendenti  "
critici.loc[critici['fatturato'] < 300, 'Attenzione'] += "📉 Fatturato basso"
st.dataframe(critici[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))

# --- AZIONI ---
st.header("📌 Azioni Consigliate per Arianna")
st.markdown("""
- Riduci scorte di ingredienti se % supera il 35% per più di 3 giorni.
- Verifica turni se % dipendenti alta in giornate con basso volume.
- Valuta promozioni mirate il martedì e mercoledì (mediamente più deboli).
- Punta sugli extra più richiesti nei giorni di picco.
""")
