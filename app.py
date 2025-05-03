import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

st.set_page_config(page_title="Pokè To Go – Dashboard Business", layout="wide")

logo = Image.open("logo.png")
st.image(logo, width=150)

st.markdown("""
<style>
.main { background-color: #fdfcfb; }
h1, h2, h3 { color: #e85d04; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.title("Pokè To Go – Dashboard Operativa")

fixed_intro = """
**Le spese sono distribuite nel tempo tra due approvvigionamenti successivi.**  
**Le giornate critiche segnalano margini ridotti o ricavi bassi.**
"""
st.markdown(fixed_intro)

uploaded_file = st.file_uploader("Carica CSV", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data', 'fatturato'])
for col in df.columns:
    if col != 'data': df[col] = pd.to_numeric(df[col], errors='coerce')

# Definizione categorie
sales_cols = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl',
              'Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
bibite = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
sorbetti = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']
cost_cols = ['Dipendente']

# Ingredienti: tutte le colonne non vendite, non bibite, non sorbetti, non costi, non data, non fatturato
exclude = sales_cols + bibite + sorbetti + cost_cols + ['data', 'fatturato']
ingredienti = [c for c in df.columns if c not in exclude]

# Distribuzione costi ingredienti
df_dist = pd.DataFrame(index=df.index)
for ing in ingredienti:
    serie = df[['data', ing]].dropna()
    serie = serie[serie[ing] > 0].sort_values('data')
    disp = pd.Series(0, index=df.index)
    if len(serie) >= 2:
        for i in range(len(serie) - 1):
            start = serie.iloc[i]['data']
            end = serie.iloc[i + 1]['data']
            days = (end - start).days
            if days > 0:
                val = serie.iloc[i][ing] / days
                disp[(df['data'] >= start) & (df['data'] < end)] += val
    df_dist[ing] = disp

# Calcoli metriche
df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df['totale_ingredienti'] / df['fatturato'] * 100
df['% dipendenti'] = df['Dipendente'] / df['fatturato'] * 100

# Intervallo analisi
date_min, date_max = df['data'].min(), df['data'].max()
start, end = st.date_input("Intervallo Analisi", [date_min, date_max], min_value=date_min, max_value=date_max)
df_sel = df[(df['data'] >= pd.to_datetime(start)) & (df['data'] <= pd.to_datetime(end))]

tot_days = len(df_sel)
crit_days = len(df_sel[(df_sel['fatturato'] < 300) | (df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25)])
perc_crit = crit_days / tot_days * 100 if tot_days > 0 else 0
st.info(f"Nel periodo selezionato: {crit_days}/{tot_days} giornate critiche ({perc_crit:.1f}%).")

# Confronto con periodo precedente
delta = pd.to_datetime(end) - pd.to_datetime(start)
prev_start = pd.to_datetime(start) - delta
prev_end = pd.to_datetime(start)
df_prev = df[(df['data'] >= prev_start) & (df['data'] < prev_end)]

def total(col): return df_sel[col].sum(), df_prev[col].sum()
curr_rev, prev_rev = total('fatturato')
curr_ing, prev_ing = total('totale_ingredienti')
col1, col2 = st.columns(2)
col1.metric("Fatturato periodo", f"€{curr_rev:,.0f}", delta=f"€{curr_rev - prev_rev:,.0f}")
col2.metric("Costo ingredienti", f"€{curr_ing:,.0f}", delta=f"€{curr_ing - prev_ing:,.0f}")

if crit_days > 3:
    st.warning(f"Attenzione: {crit_days} giornate critiche nel periodo selezionato.")

tabs = st.tabs(["Metriche", "Vendite", "Bevande & Sorbetti", "Storico", "Aiuto"])
with tabs[0]:
    df_sel['poke_totali'] = df_sel[sales_cols[:3]].sum(axis=1)
    df_sel['extra_totali'] = df_sel[sales_cols[3:]].sum(axis=1)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fatturato", f"€{df_sel['fatturato'].sum():,.0f}")
    c2.metric("Ingredienti", f"€{df_sel['totale_ingredienti'].sum():,.0f}")
    c3.metric("Dipendenti", f"€{df_sel['Dipendente'].sum():,.0f}")
    c4.metric("Utile stimato", f"€{(df_sel['fatturato'] - df_sel['totale_ingredienti'] - df_sel['Dipendente']).sum():,.0f}")
    st.success(f"Cosa va bene: {tot_days - crit_days} giornate senza criticità")
    st.error(f"Dove migliorare: {crit_days} giornate critiche da analizzare")
with tabs[1]:
    sales_melt = df_sel[['data'] + sales_cols].melt('data', var_name='Tipo', value_name='Quantità')
    st.plotly_chart(px.line(sales_melt, x='data', y='Quantità', color='Tipo', markers=True), use_container_width=True)
with tabs[2]:
    bib_m = df_sel[['data'] + bibite].melt('data', var_name='Bevanda', value_name='Quantità')
    sor_m = df_sel[['data'] + sorbetti].melt('data', var_name='Gusto', value_name='Quantità')
    st.plotly_chart(px.bar(bib_m, x='data', y='Quantità', color='Bevanda'), use_container_width=True)
    st.plotly_chart(px.bar(sor_m, x='data', y='Quantità', color='Gusto'), use_container_width=True)
with tabs[3]:
    ann = df.groupby(df['data'].dt.year).agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
    ann['% ingredienti'] = ann['totale_ingredienti'] / ann['fatturato'] * 100
    ann['% dipendenti'] = ann['Dipendente'] / ann['fatturato'] * 100
    st.dataframe(ann.style.format({'fatturato': '€{:.0f}', 'totale_ingredienti': '€{:.0f}', 'Dipendente': '€{:.0f}', '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'}))
with tabs[4]:
    st.header("Note Metodi")
    st.markdown("""
- Costo giornaliero ingredienti: distribuito tra due approvvigionamenti consecutivi.
- Valori ingredienti, vendite, acquisti: in euro.
- Colonne vendite: quantità vendute; colonne spesa: euro spesi o incassati.
""")

csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("Scarica CSV", data=csv, file_name="analisi.csv", mime='text/csv')
