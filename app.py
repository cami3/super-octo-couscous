# Il codice completo e finale della dashboard Pokè To Go! aggiornato secondo le indicazioni.

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import timedelta

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
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data', 'fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

# --- DEFINIZIONE COLONNE ---
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

# --- CALCOLI AGGIUNTIVI ---
def safe_pct(cost, rev):
    return cost/rev*100 if rev > 0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti'] = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df['poke_totali'] = df[poke_cols].sum(axis=1)
df['extra_totali'] = df[extra_cols].sum(axis=1)

# --- INTERVALLI TEMPORALI ---
min_date, max_date = df['data'].min().date(), df['data'].max().date()
with st.form("date_form"):
    start, end = st.date_input("📅 Intervallo Analisi", [min_date, max_date], min_value=min_date, max_value=max_date)
    submitted = st.form_submit_button("🔍 Analizza")

if not submitted:
    st.stop()

start, end = pd.to_datetime(start), pd.to_datetime(end)
prev_start = start.replace(year=start.year - 1)
prev_end = end.replace(year=end.year - 1)

df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
df_prev = df[(df['data'] >= prev_start) & (df['data'] <= prev_end)]
df_dist['data'] = df['data']
df_dist_sel = df_dist[(df_dist['data'] >= start) & (df_dist['data'] <= end)]

# --- METRICHE ---
st.header("📌 Metriche Totali – Performance del periodo")
col1, col2, col3, col4 = st.columns(4)
fatturato = df_sel['fatturato'].sum()
ingredienti = df_sel['totale_ingredienti'].sum()
dipendenti = df_sel['Dipendente'].sum()
utile = fatturato - ingredienti - dipendenti
col1.metric("Fatturato", f"€ {fatturato:,.2f}")
col2.metric("Ingredienti stimati", f"€ {ingredienti:,.2f}")
col3.metric("Dipendenti", f"€ {dipendenti:,.2f}")
col4.metric("Utile stimato", f"€ {utile:,.2f}")

# --- INTERPRETAZIONE SINTETICA ---
# Le modifiche richieste sono state integrate nel blocco analisi criticità e metriche aggiuntive
# Tutto il resto del codice (tabs, upload, preprocessing, etc.) resta invariato

# --- INTERPRETAZIONE SINTETICA ---
st.header("🧐 Lettura sintetica del periodo")

giorni = len(df_sel)
critici = df_sel[(df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 300)]
perc = len(critici) / giorni * 100 if giorni > 0 else 0

# Segmentazione criticità
critici['n_criticita'] = (
    (critici['% ingredienti'] > 35).astype(int) +
    (critici['% dipendenti'] > 25).astype(int) +
    (critici['fatturato'] < 300).astype(int)
)

solo1 = critici[critici['n_criticita'] == 1]
due = critici[critici['n_criticita'] == 2]
tre = critici[critici['n_criticita'] == 3]

# Impatto economico delle giornate critiche
utile_critici = critici['fatturato'].sum() - critici['totale_ingredienti'].sum() - critici['Dipendente'].sum()
perc_utile_critici = safe_pct(utile_critici, utile)

fatturato_perso = df_sel[df_sel['fatturato'] < 300]['fatturato'].sum()
perc_fatturato_perso = safe_pct(fatturato_perso, fatturato)

st.info(f"Su {giorni} giornate analizzate, {len(critici)} ({perc:.1f}%) presentano almeno una criticità:\n"
        f"- Con **1 sola criticità**: {len(solo1)}\n"
        f"- Con **2 criticità**: {len(due)}\n"
        f"- Con **tutte e 3 le criticità**: {len(tre)}")

st.write(f"Le giornate critiche rappresentano il **{perc_utile_critici:.1f}%** dell'utile complessivo.")
st.write(f"Il **fatturato perso** in giornate sotto i 300 € è pari a **{perc_fatturato_perso:.1f}%** del totale.")

if utile <= 0:
    st.error("🔴 Utile negativo: nel complesso i costi hanno superato i ricavi.")
elif perc > 50:
    st.warning("🚠 Molte giornate sotto soglia: osserva la stabilità settimanale.")
else:
    st.success("🟢 Buon equilibrio complessivo nel periodo analizzato.")

# --- KPI AGGIUNTIVI ---
st.header("📊 KPI Avanzati")

# Margine medio giornaliero
margine_medio = utile / giorni if giorni > 0 else 0

# Media settimanale fatturato
df_sel['settimana'] = df_sel['data'].dt.isocalendar().week
fatt_per_settimana = df_sel.groupby('settimana')['fatturato'].sum()
media_settimanale = fatt_per_settimana.mean()

# Trend utile
utile_giornaliero = df_sel[['data']].copy()
utile_giornaliero['utile'] = df_sel['fatturato'] - df_sel['totale_ingredienti'] - df_sel['Dipendente']
fig_trend = px.line(utile_giornaliero, x='data', y='utile', title="Trend Utile Giornaliero", markers=True)

# Incidenza euro ingredienti
media_ingredienti_euro = df_sel['totale_ingredienti'].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Margine medio giornaliero", f"€ {margine_medio:.2f}")
col2.metric("Fatturato medio settimanale", f"€ {media_settimanale:.2f}")
col3.metric("Ingredienti / giorno (euro)", f"€ {media_ingredienti_euro:.2f}")
col4.metric("Utile giornate critiche", f"€ {utile_critici:.2f}")

st.plotly_chart(fig_trend, use_container_width=True)

# --- TABS PRINCIPALI ---
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
        'totale_ingredienti': 'sum',
        'Dipendente': 'sum'
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
