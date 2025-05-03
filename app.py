import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import timedelta

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
st.title("Pokè To Go – Dashboard Operativa 🍣")

st.markdown("""
**Le spese distribuite tra approvvigionamenti successivi.**  
**Giornate critiche: margini ridotti o ricavi sotto soglia.**
""")

uploaded = st.file_uploader("⬆️ Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data','fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
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
    return cost/rev*100 if rev>0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti']   = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df['poke_totali'] = df[poke_cols].sum(axis=1)
df['extra_totali'] = df[extra_cols].sum(axis=1)

min_date, max_date = df['data'].min().date(), df['data'].max().date()
with st.form("date_form"):
    start, end = st.date_input("📅 Intervallo Analisi", [min_date, max_date], min_value=min_date, max_value=max_date)
    submitted = st.form_submit_button("🔍 Analizza")

# Dopo il blocco form
prev_start = start - timedelta(days=365)
prev_end = end - timedelta(days=365)


if not submitted:
    st.stop()

start, end = pd.to_datetime(start), pd.to_datetime(end)
prev_start, prev_end = pd.to_datetime(prev_start), pd.to_datetime(prev_end)
df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
df_prev = df[(df['data'] >= prev_start) & (df['data'] <= prev_end)]

def total(col, df, average=False):
    if average:
        return df[col].mean() if len(df) > 0 else 0
    return df[col].sum() if col in df.columns else df[col].sum(axis=1).sum()

metriche = [
    ("🍣 Fatturato", 'fatturato', '€', False),
    ("💰 Utile stimato", None, '€', False),
    ("🧂 % Ingredienti", '% ingredienti', '%', True),
    ("👥 % Dipendenti", '% dipendenti', '%', True),
    ("🍱 Poke totali", 'poke_totali', '', False),
    ("🍓 Extra totali (€)", 'extra_totali', '€', False)
]

colonne = st.columns(len(metriche))
for i, (label, key, unit, avg) in enumerate(metriche):
    if key:
        cur = total(key, df_sel, average=avg)
        prev = total(key, df_prev, average=avg)
    else:
        cur = df_sel['fatturato'].sum() - df_sel['totale_ingredienti'].sum() - df_sel['Dipendente'].sum()
        prev = df_prev['fatturato'].sum() - df_prev['totale_ingredienti'].sum() - df_prev['Dipendente'].sum()
    delta_val = cur - prev
    colonne[i].metric(label, f"{unit}{cur:,.1f}", delta=f"{unit}{delta_val:,.1f}" if delta_val != 0 else None)

crit = df_sel[(df_sel['fatturato']<300) | (df_sel['% ingredienti']>35) | (df_sel['% dipendenti']>25)]
if len(crit) > 3:
    st.warning(f"⚠️ {len(crit)} giornate critiche nel periodo selezionato.")

if not crit.empty:
    st.header("❗ Giornate da monitorare")
    crit['Attenzione'] = ""
    crit.loc[crit['% ingredienti'] > 35, 'Attenzione'] += "🧂 Alto costo ingredienti  "
    crit.loc[crit['% dipendenti'] > 25, 'Attenzione'] += "👥 Alto costo dipendenti  "
    crit.loc[crit['fatturato'] < 300, 'Attenzione'] += "📉 Fatturato basso"
    st.dataframe(crit[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))
