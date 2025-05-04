# Dashboard Pokè To Go! – Corretto con logica e calcoli coerenti

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Pokè To Go! – Dashboard Business", layout="wide")
st.image(Image.open("logo.png"), width=150)
st.markdown("""
    <style>
    .main { background-color: #fdfcfb; }
    h1, h2, h3 { color: #e85d04; }
    .stMetric { background-color: #fff7ed; border-radius: 10px; padding: 10px !important; }
    .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("Pokè To Go! – Dashboard Operativa 🍣")
st.markdown("""
**Le spese sono distribuite nel tempo tra due approvvigionamenti successivi.**  
**Le giornate critiche segnalano margini ridotti o ricavi bassi, ma non indicano necessariamente un problema.**  
**In una gestione stagionale, il focus va mantenuto sull’andamento complessivo.**
""")

# --- CARICAMENTO DATI ---
uploaded = st.file_uploader("⬆️ Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
try:
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')

except:
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
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

# --- DISTRIBUZIONE COSTI ---
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

# --- INTERVALLI TEMPORALI ---
min_date = df['data'].min()
max_date = df['data'].max()
if pd.isna(min_date) or pd.isna(max_date):
    st.error("Errore: colonne data non valide.")
    st.stop()

with st.form("date_form"):
    start, end = st.date_input("📅 Intervallo Analisi", [min_date.date(), max_date.date()], min_value=min_date.date(), max_value=max_date.date())
    submitted = st.form_submit_button("🔍 Analizza")

if not submitted:
    st.stop()

start = pd.to_datetime(start)
end = pd.to_datetime(end)
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

# --- METRICHE ---
st.header("📌 Metriche Totali – Performance del periodo")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatturato", f"€ {df_sel['fatturato'].sum():,.2f}")
col2.metric("Ingredienti stimati", f"€ {df_sel['totale_ingredienti'].sum():,.2f}")
col3.metric("Dipendenti", f"€ {df_sel['Dipendente'].sum():,.2f}")
col4.metric("Utile stimato", f"€ {df_sel['utile'].sum():,.2f}")

# Il resto della dashboard può seguire: KPI operativi, trend, tabs, confronto annuale, ecc.

# --- KPI OPERATIVI ---
st.header("📈 KPI Operativi – Efficienza e Ricavi")
tot_poke = df_sel['poke_totali'].sum()
tot_extra = df_sel['extra_totali'].sum()
ricavi = df_sel['fatturato'].sum()
costo_ingredienti = df_sel['totale_ingredienti'].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Ricavo Medio per Poke", f"€ {ricavi / tot_poke:.2f}" if tot_poke > 0 else "N/A")
col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
col3.metric("Costo Ingredienti per Poke", f"€ {costo_ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

# --- TREND UTILE GIORNALIERO ---
st.header("📈 Trend Utile Giornaliero")
fig_trend = px.line(df_sel, x='data', y='utile', title="Trend Utile Giornaliero", markers=True)
st.plotly_chart(fig_trend, use_container_width=True)

# Il resto del codice continua con tabs, giornate critiche, confronto annuale, esportazione ecc.

# --- TABS E VISUALIZZAZIONI ---
tabs = st.tabs(["📈 Vendite", "🍱 Extra", "🥤 Costi: Bibite e Sorbetti", "🍚 Ingredienti", "📊 Confronto Annuale", "⚠️ Giornate Critiche", "ℹ️ Aiuto"])

with tabs[0]:
    st.header("📈 Vendite – Poke e Bowl")
    melt_poke = df_sel[['data'] + poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt_poke, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)

with tabs[1]:
    st.header("🍱 Extra più richiesti (euro)")
    melt_extra = df_sel[['data'] + extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt_extra, x='data', y='Euro', color='Tipo'), use_container_width=True)

with tabs[2]:
    subtabs = st.tabs(["🥤 Bibite", "🍧 Sorbetti"])
    with subtabs[0]:
        st.header("🥤 Bibite – Costi di Approvvigionamento")
        melt_bib = df_sel[['data'] + bibite_cols].melt('data', var_name='Prodotto', value_name='Euro')
        st.plotly_chart(px.bar(melt_bib, x='data', y='Euro', color='Prodotto'), use_container_width=True)
    with subtabs[1]:
        st.header("🍧 Sorbetti – Costi di Approvvigionamento")
        melt_sorb = df_sel[['data'] + sorbetti_cols].melt('data', var_name='Gusto', value_name='Euro')
        st.plotly_chart(px.bar(melt_sorb, x='data', y='Euro', color='Gusto'), use_container_width=True)

with tabs[3]:
    st.header("🍚 Ingredienti per Categoria")
    categorie = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale'],
        'Topping': ['Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','Sale grosso'],
        'Salse': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    for nome, cols in categorie.items():
        st.subheader(nome)
        validi = [c for c in cols if c in df_dist_sel.columns]
        if validi:
            melted = df_dist_sel[['data'] + validi].melt(id_vars='data', var_name='Ingrediente', value_name='Euro')
            st.plotly_chart(px.area(melted, x='data', y='Euro', color='Ingrediente'), use_container_width=True)

with tabs[4]:
    st.header("📊 Confronto Annuale – Costi e Ricavi")
    df['anno'] = df['data'].dt.year
    ann = df.groupby('anno').agg({
        'fatturato': 'sum',
        'Dipendente': 'sum',
        'totale_ingredienti': 'sum'
    }).reset_index()
    ann['% ingredienti'] = ann.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
    ann['% dipendenti'] = ann.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
    st.dataframe(ann.style.format({
        'fatturato': '€{:.2f}',
        'totale_ingredienti': '€{:.2f}',
        'Dipendente': '€{:.2f}',
        '% ingredienti': '{:.1f}%',
        '% dipendenti': '{:.1f}%'
    }))

with tabs[5]:
    st.header("⚠️ Giornate da monitorare")
    critici = df_sel[(df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 300)]
    critici['Attenzione'] = ""
    critici.loc[critici['% ingredienti'] > 35, 'Attenzione'] += "🧂 Ingredienti alti  "
    critici.loc[critici['% dipendenti'] > 25, 'Attenzione'] += "👥 Dipendenti alti  "
    critici.loc[critici['fatturato'] < 300, 'Attenzione'] += "📉 Fatturato basso"
    st.dataframe(critici[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))

with tabs[6]:
    st.header("ℹ️ Aiuto e Note Metodo")
    st.markdown("""
- Il **costo ingredienti è distribuito** tra due approvvigionamenti successivi.
- Le **quantità poke** sono in **pezzi**.
- Gli **extra** sono vendite in **euro**.
- **Bibite e sorbetti** sono solo costi (approvvigionamento), non vendite.
- Le **percentuali** sono medie giornaliere sul periodo selezionato.
- Il **confronto** è fatto con lo stesso periodo dell’anno precedente (se disponibile).
""")

# --- ESPORTAZIONE ---
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
