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

# Introduzione fissa
intro = """
**Le spese distribuite tra approvvigionamenti successivi.**  
**Giornate critiche: margini ridotti o ricavi sotto soglia.**
"""
st.markdown(intro)

# Caricamento file
uploaded = st.file_uploader("⬆️ Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data','fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Definizione colonne
poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']  # quantità pezzi
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']  # euro
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']  # euro
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']  # euro
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

# Distribuzione costi ingredienti
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

# Calcolo metriche

def safe_pct(cost, rev):
    return cost/rev*100 if rev>0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti']   = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)

df['anno'] = df['data'].dt.year
df['mese'] = df['data'].dt.to_period('M').astype(str)

# Selezione periodo corrente
start, end = st.date_input("📅 Intervallo Analisi", [df['data'].min(), df['data'].max()])
df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
# Selezione periodo precedente
delta = end - start
df_prev = df[(df['data'] >= start - delta) & (df['data'] < start)]

# Calcolo valori attuali e delta
def tot(col_list, df1, df2):
    return df1[col_list].sum().sum(), df2[col_list].sum().sum()

cur_rev, prev_rev = tot(['fatturato'], df_sel, df_prev)
cur_u, prev_u = (cur_rev - df_sel['totale_ingredienti'].sum() - df_sel['Dipendente'].sum()), (prev_rev - df_prev['totale_ingredienti'].sum() - df_prev['Dipendente'].sum())
cur_ing, prev_ing = tot(['totale_ingredienti'], df_sel, df_prev)
cur_dep, prev_dep = tot(['Dipendente'], df_sel, df_prev)
cur_pct_ing, prev_pct_ing = df_sel['% ingredienti'].mean(), df_prev['% ingredienti'].mean()
cur_pct_dep, prev_pct_dep = df_sel['% dipendenti'].mean(), df_prev['% dipendenti'].mean()
cur_poke, prev_poke = tot(poke_cols, df_sel, df_prev)
cur_extra, prev_extra = tot(extra_cols, df_sel, df_prev)

# Metriche iniziali con delta
metric_list = [
    ("🍣 Fatturato", cur_rev, cur_rev-prev_rev, "€"),
    ("💰 Utile stimato", cur_u, cur_u-prev_u, "€"),
    ("🧂 % Ingredienti", cur_pct_ing, cur_pct_ing-prev_pct_ing, "%"),
    ("👥 % Dipendenti", cur_pct_dep, cur_pct_dep-prev_pct_dep, "%"),
    ("🍱 Poke totali", cur_poke, cur_poke-prev_poke, ""),
    ("🍓 Extra totali", cur_extra, cur_extra-prev_extra, "€")
]

cols = st.columns(len(metric_list))
for i, (label, value, delta, unit) in enumerate(metric_list):
    cols[i].metric(label, f"{unit}{value:,.1f}" if unit else f"{value:,.0f}", delta=f"{unit}{delta:,.1f}" if unit else f"{delta:,.0f}")

# Avviso giornate critiche
crit = df_sel[(df_sel['fatturato']<300) | (df_sel['% ingredienti']>35) | (df_sel['% dipendenti']>25)]
if len(crit) > 3:
    st.warning(f"⚠️ {len(crit)} giornate critiche nel periodo selezionato.")

# Tabs per visualizzazioni
tabs = st.tabs(["📈 Vendite","🍱 Ingredienti","🥤 Bevande&Sorbetti","📆 Storico","ℹ️ Aiuto"])
with tabs[0]:
    st.subheader("Vendite (pezzi)")
    melt_poke = df_sel[['data']+poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt_poke, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)
    st.subheader("Extra (euro)")
    melt_extra = df_sel[['data']+extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt_extra, x='data', y='Euro', color='Tipo'), use_container_width=True)
with tabs[1]:
    st.subheader("Costi Ingredienti per Categoria (euro)")
    categories = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale','Sale grosso'],
        'Condimenti': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    data_cat = {cat: df_dist[cols].sum().sum() for cat, cols in categories.items()}
    df_cat = pd.DataFrame.from_dict(data_cat, orient='index', columns=['Euro']).reset_index().rename(columns={'index':'Categoria'})
    st.plotly_chart(px.bar(df_cat, x='Categoria', y='Euro'), use_container_width=True)
with tabs[2]:
    st.subheader("Bibite & Sorbetti (euro)")
    melt_bs = df_sel[['data']+bibite_cols+sorbetti_cols].melt('data', var_name='Prodotto', value_name='Euro')
    st.plotly_chart(px.bar(melt_bs, x='data', y='Euro', color='Prodotto'), use_container_width=True)
with tabs[3]:
    st.subheader("Trend Storico Fatturato")
    idx = df_sel.set_index('data')
    for freq, name in [('D','Giornaliero'),('W','Settimanale'),('M','Mensile'),('Y','Annuale')]:
        series = idx.resample(freq)['fatturato'].sum()
        st.line_chart(series, use_container_width=True, key=name)
with tabs[4]:
    st.header("ℹ️ Note Metodi")
    st.markdown("""
- Poke: quantità in pezzi.
- Extra, bibite, sorbetti: importi in euro.
- Costi ingredienti distribuiti tra approvvigionamenti.
- % Ingredienti e % Dipendenti protezioni divisione zero.
- Delta mostrano variazioni vs periodo precedente.
""")

# Esportazione CSV
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
