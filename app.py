import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

st.set_page_config(page_title="Pokè To Go – Dashboard Business", layout="wide")
logo = Image.open("/mnt/data/logo.png")
st.image(logo, width=150)
st.markdown("""
<style>
.main { background-color: #fdfcfb; }
h1, h2, h3 { color: #e85d04; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)
st.title("Pokè To Go – Dashboard Operativa 🤰🏻🍣")

intro = """
**Le spese distribuite tra approvvigionamenti successivi.**  
**Giornate critiche: margini ridotti o ricavi sotto soglia.**
"""
st.markdown(intro)

uploaded = st.file_uploader("⬆️ Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data','fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Colonne
poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']  # quantità
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']  # euro
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']  # euro
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']  # euro
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

# Distribuisci costi ingredienti
df_dist = pd.DataFrame(index=df.index)
for ing in ingred_cols:
    s = df[['data', ing]].dropna()
    s = s[s[ing] > 0].sort_values('data')
    arr = pd.Series(0, index=df.index)
    for i in range(len(s) - 1):
        a, b = s.iloc[i]['data'], s.iloc[i+1]['data']
        days = (b - a).days
        if days > 0:
            arr[(df['data'] >= a) & (df['data'] < b)] += s.iloc[i][ing] / days
    df_dist[ing] = arr

# Calcoli

def safe_pct(cost, rev): return cost/rev*100 if rev>0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti']   = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)

df['anno'] = df['data'].dt.year
df['mese'] = df['data'].dt.to_period('M').astype(str)

# Selezione periodo
start, end = st.date_input("📅 Intervallo Analisi", [df['data'].min(), df['data'].max()])
df_sel = df[(df['data']>=start)&(df['data']<=end)]
# Periodo precedente
delta = end - start
df_prev = df[(df['data']>=start-delta)&(df['data']<start)]

# Totali e delta
metrics = {
    'Fatturato':     ('fatturato', '€', ''),
    'Utile stimato': (None, '€', lambda sel, prev: (sel['fatturato'].sum()-sel['totale_ingredienti'].sum()-sel['Dipendente'].sum()) - (prev['fatturato'].sum()-prev['totale_ingredienti'].sum()-prev['Dipendente'].sum())),
    '% Ingredienti': ('% ingredienti', '%', ''),
    '% Dipendenti':  ('% dipendenti', '%', ''),
    'Poke totali':  (poke_cols, '', lambda sel, prev: sel[poke_cols].sum().sum() - prev[poke_cols].sum().sum()),
    'Extra totali (€)': ('extra_sum', '€', '')
}

df_sel['extra_sum'] = df_sel[extra_cols].sum(axis=1)
df_prev['extra_sum'] = df_prev[extra_cols].sum(axis=1)
\cols = st.columns(len(metrics))
for idx, (label, spec) in enumerate(metrics.items()):
    col = cols[idx]
    key, unit, delta_fn = spec
    if callable(delta_fn):
        delta = delta_fn(df_sel, df_prev)
    else:
        delta = df_sel[key].sum() - df_prev[key].sum()
    value = df_sel[key].sum() if isinstance(key, str) else df_sel[key].sum().sum()
    col.metric(f"{label}", f"{unit}{value:,.1f}" if unit else f"{value:,.0f}", delta=f"{unit}{delta:,.1f}" if unit else f"{delta:,.0f}")

# Alert
crit = df_sel[(df_sel['fatturato']<300)|(df_sel['% ingredienti']>35)|(df_sel['% dipendenti']>25)]
if len(crit)>3: st.warning(f"⚠️ {len(crit)} giornate critiche")

# Tabs
tabs = st.tabs(["📈 Vendite","🍱 Ingredienti","🥤 Bevande&Sorbetti","📆 Storico","ℹ️ Aiuto"])
with tabs[0]:
    st.subheader("Vendite (pezzi)")
    m = df_sel[['data']+poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(m, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)
    st.subheader("Extra (euro)")
    e = df_sel[['data']+extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(e, x='data', y='Euro', color='Tipo'), use_container_width=True)
with tabs[1]:
    st.subheader("Costi Ingredienti per Categoria (euro)")
    cats = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale','Sale grosso'],
        'Condimenti': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    df_cat = pd.DataFrame({cat: df_dist[cols].sum().sum() for cat, cols in cats.items()}, index=[0]).T.reset_index()
    df_cat.columns = ['Categoria','Euro']
    st.plotly_chart(px.bar(df_cat, x='Categoria', y='Euro'), use_container_width=True)
with tabs[2]:
    st.subheader("Bibite e Sorbetti (euro)")
    bs = df_sel[['data']+bibite_cols+sorbetti_cols].melt('data', var_name='Prodotto', value_name='Euro')
    st.plotly_chart(px.bar(bs, x='data', y='Euro', color='Prodotto'), use_container_width=True)
with tabs[3]:
    st.subheader("Trend Storico Fatturato")
    idx = df_sel.set_index('data')
    for freq, label in [('D','Giornaliero'),('W','Settimanale'),('M','Mensile'),('Y','Annuale')]:
        tmp = idx.resample(freq)['fatturato'].sum()
        st.line_chart(tmp, width=0, height=0, use_container_width=True, key=label)
with tabs[4]:
    st.header("ℹ️ Note Metodi")
    st.markdown("""
- Poke: quantità (pezzi).
- Extra, bibite, sorbetti: importi in euro (approvvigionamento).
- Costi ingredienti: distribuiti tra acquisti successivi.
- % Ingredienti/Dipendenti: protezione divisione per zero.
- Delta mostrano variazioni vs periodo precedente.
""")

# Esporta
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi.csv", mime='text/csv')
