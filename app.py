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
st.title("Pokè To Go – Dashboard Operativa 🤰🏻🍣")

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

poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']  # quantità
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']  # vendite €
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']  # costi
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']  # costi
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

start, end = st.date_input("📅 Intervallo Analisi", [df['data'].min().date(), df['data'].max().date()])
start, end = pd.to_datetime(start), pd.to_datetime(end)
df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
delta = end - start
df_prev = df[(df['data'] >= start - delta) & (df['data'] < start)]


def total(col, df):
    return df[col].sum() if col in df.columns else df[col].sum(axis=1).sum()

metriche = [
    ("🍣 Fatturato", 'fatturato', '€'),
    ("💰 Utile stimato", None, '€'),
    ("🧂 % Ingredienti", '% ingredienti', '%'),
    ("👥 % Dipendenti", '% dipendenti', '%'),
    ("🍱 Poke totali", 'poke_totali', ''),
    ("🍓 Extra totali (€)", 'extra_totali', '€')
]

colonne = st.columns(len(metriche))
for i, (label, key, unit) in enumerate(metriche):
    if key:
        cur = total(key, df_sel)
        prev = total(key, df_prev)
    else:
        cur = df_sel['fatturato'].sum() - df_sel['totale_ingredienti'].sum() - df_sel['Dipendente'].sum()
        prev = df_prev['fatturato'].sum() - df_prev['totale_ingredienti'].sum() - df_prev['Dipendente'].sum()
    delta_val = cur - prev
    colonne[i].metric(label, f"{unit}{cur:,.1f}", delta=f"{unit}{delta_val:,.1f}")

crit = df_sel[(df_sel['fatturato']<300) | (df_sel['% ingredienti']>35) | (df_sel['% dipendenti']>25)]
if len(crit) > 3:
    st.warning(f"⚠️ {len(crit)} giornate critiche nel periodo selezionato.")

tabs = st.tabs(["📈 Vendite","🍱 Ingredienti","🥤 Bevande&Sorbetti","📆 Storico","ℹ️ Aiuto"])

with tabs[0]:
    st.subheader("Vendite (pezzi)")
    melt_poke = df_sel[['data']+poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt_poke, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)
    st.subheader("Extra venduti (€)")
    melt_extra = df_sel[['data']+extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt_extra, x='data', y='Euro', color='Tipo'), use_container_width=True)

with tabs[1]:
    st.subheader("Costi Ingredienti per Categoria (euro)")
    categorie = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale','Sale grosso'],
        'Condimenti': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    cat_data = {cat: df_dist[cols].sum().sum() for cat, cols in categorie.items() if any(c in df_dist.columns for c in cols)}
    df_cat = pd.DataFrame.from_dict(cat_data, orient='index', columns=['Euro']).reset_index().rename(columns={'index':'Categoria'})
    st.plotly_chart(px.bar(df_cat, x='Categoria', y='Euro'), use_container_width=True)

with tabs[2]:
    st.subheader("Bibite & Sorbetti (approvvigionamento €)")
    melt_bs = df_sel[['data']+bibite_cols+sorbetti_cols].melt('data', var_name='Prodotto', value_name='Euro')
    st.plotly_chart(px.bar(melt_bs, x='data', y='Euro', color='Prodotto'), use_container_width=True)

with tabs[3]:
    st.subheader("Trend Storico Fatturato")
    idx = df_sel.set_index('data')
    for freq, label in [('D','Giornaliero'),('W','Settimanale'),('M','Mensile'),('Y','Annuale')]:
        st.line_chart(idx['fatturato'].resample(freq).sum(), use_container_width=True, key=label)

with tabs[4]:
    st.header("ℹ️ Note Metodi")
    st.markdown("""
- **Poke**: quantità in pezzi
- **Extra**: vendite in euro
- **Bibite/Sorbetti**: solo costo, non vendite
- **Ingredienti**: costo distribuito tra approvvigionamenti
- % calcolate solo se fatturato > 0
""")

csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
