import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import timedelta

st.set_page_config(page_title="Pokè To Go! – Dashboard Business", layout="wide")
st.image(Image.open("logo.png"), width=150)

st.markdown("""
    <style>
    .main { background-color: #fdfcfb; }
    h1, h2, h3 { color: #e85d04; }
    .stMetric { background-color: #fff7ed; border-radius: 10px; padding: 10px !important; }
    .block-container { padding-top: 2rem; }
    .stDataFrame { background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("Pokè To Go! – Dashboard Operativa 🍣")
st.markdown("""
**Le spese sono distribuite nel tempo tra due approvvigionamenti successivi.**  
**Le giornate critiche segnalano margini ridotti o ricavi bassi.**
""")

uploaded = st.file_uploader("⬆️ Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data', 'fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl']
extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
bibite_cols = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
sorbetti_cols = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data', 'fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

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

def safe_pct(cost, rev):
    return cost/rev*100 if rev > 0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti'] = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df['poke_totali'] = df[poke_cols].sum(axis=1)
df['extra_totali'] = df[extra_cols].sum(axis=1)

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

# METRICHE
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

st.header("📈 KPI Operativi – Efficienza e Ricavi")
tot_poke = df_sel['poke_totali'].sum()
tot_extra = df_sel['extra_totali'].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Ricavo Medio per Poke", f"€ {fatturato / tot_poke:.2f}" if tot_poke > 0 else "N/A")
col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
col3.metric("Costo Medio per Poke", f"€ {ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

# INTERPRETAZIONE
st.header("🧠 Interpretazione automatica")
giorni = len(df_sel)
critici = df_sel[(df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 300)]
perc = len(critici) / giorni * 100 if giorni > 0 else 0
st.info(f"Nel periodo selezionato ci sono {len(critici)} giornate critiche su {giorni} totali ({perc:.1f}%).")
if len(critici) > 3:
    st.warning("⚠️ Troppe giornate critiche: controlla costi ingredienti e fatturato.")
else:
    st.success("✅ Buona tenuta del periodo.")

if perc >= 30 or utile <= 0:
    st.error("🧯 Da migliorare: costi troppo alti o utile insufficiente.")
else:
    st.success("🌟 Stai mantenendo una buona efficienza operativa!")

tabs = st.tabs(["📈 Vendite", "🍱 Extra", "🍚 Ingredienti", "📊 Confronto Annuale", "ℹ️ Aiuto"])

with tabs[0]:
    st.header("📈 Vendite – Poke e Bowl")
    melt_poke = df_sel[['data'] + poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt_poke, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)

with tabs[1]:
    st.header("🍱 Extra più richiesti")
    melt_extra = df_sel[['data'] + extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt_extra, x='data', y='Euro', color='Tipo'), use_container_width=True)

with tabs[2]:
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

with tabs[3]:
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

with tabs[4]:
    st.header("ℹ️ Aiuto e Note Metodo")
    st.markdown("""
- Il costo ingredienti è **distribuito tra due approvvigionamenti**.
- Le quantità dei poke sono in **pezzi**, gli extra in **euro vendite**.
- Bibite e sorbetti sono costi, non vendite.
- Le giornate critiche hanno: fatturato < 300€, costi ingredienti > 35%, dipendenti > 25%.
- I delta sono confronti con lo stesso periodo dell’anno precedente.
""")

st.download_button("📥 Scarica Analisi CSV", data=df_sel.to_csv(index=False).encode('utf-8'), file_name="analisi_poketogo.csv", mime='text/csv')
