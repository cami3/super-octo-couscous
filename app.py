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

intro = """
**Le spese sono distribuite nel tempo tra due approvvigionamenti successivi.**  
**Le giornate critiche segnalano margini ridotti o ricavi bassi.**
"""
st.markdown(intro)

uploaded = st.file_uploader("Carica CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data','fatturato'])
for col in df.columns:
    if col not in ['data']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Categorie colonne
df_cols = df.columns.tolist()
poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl']
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
cost_cols = ['Dipendente']
# Ingredienti: tutte le altre colonne (numeriche) escluse
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df_cols if c not in exclude]

# Distribuzione costi ingredienti
df_dist = pd.DataFrame(index=df.index)
for ing in ingred_cols:
    s = df[['data',ing]].dropna()
    s = s[s[ing]>0].sort_values('data')
    arr = pd.Series(0,index=df.index)
    if len(s)>=2:
        for i in range(len(s)-1):
            a,b = s.iloc[i]['data'], s.iloc[i+1]['data']
            days = (b-a).days
            if days>0:
                val = s.iloc[i][ing]/days
                arr[(df['data']>=a)&(df['data']<b)] += val
    df_dist[ing] = arr

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df['totale_ingredienti']/df['fatturato']*100
df['% dipendenti'] = df['Dipendente']/df['fatturato']*100

# Selezione periodo
min_d, max_d = df['data'].min(), df['data'].max()
start,end = st.date_input("Intervallo Analisi", [min_d,max_d], min_value=min_d, max_value=max_d)
df_sel = df[(df['data']>=pd.to_datetime(start))&(df['data']<=pd.to_datetime(end))]

tot = len(df_sel)
crit = len(df_sel[(df_sel['fatturato']<300)|(df_sel['% ingredienti']>35)|(df_sel['% dipendenti']>25)])
st.info(f"Critiche: {crit}/{tot} ({crit/tot*100:.1f}%).")

# Periodo precedente
delta = pd.to_datetime(end)-pd.to_datetime(start)
prev = df[(df['data']>=pd.to_datetime(start)-delta)&(df['data']<pd.to_datetime(start))]

# Tabs
tabs = st.tabs(["Metriche","Vendite","Ingredienti","Bevande","Storico","Aiuto"])

with tabs[0]:
    pr1,pr2,pr3,pr4,pr5,pr6 = st.columns(6)
    pr1.metric("Fatturato", f"€{df_sel['fatturato'].sum():,.0f}")
    pr2.metric("Utile stimato", f"€{(df_sel['fatturato']-df_sel['totale_ingredienti']-df_sel['Dipendente']).sum():,.0f}")
    pr3.metric("% Ingredienti", f"{df_sel['% ingredienti'].mean():.1f}%")
    pr4.metric("% Dipendenti", f"{df_sel['% dipendenti'].mean():.1f}%")
    pr5.metric("Poke totali", f"{df_sel[poke_cols].sum().sum():,.0f}")
    pr6.metric("Extra totali", f"{df_sel[extra_cols].sum().sum():,.0f}")

with tabs[1]:
    st.subheader("Poke & Fruit Bowl (pezzi)")
    m1 = df_sel[['data']+poke_cols].melt('data',var_name='Tipo',value_name='Quantità')
    st.plotly_chart(px.line(m1,x='data',y='Quantità',color='Tipo',markers=True),use_container_width=True)
    st.subheader("Extra Venduti (pezzi)")
    m2 = df_sel[['data']+extra_cols].melt('data',var_name='Tipo',value_name='PezzI')
    st.plotly_chart(px.bar(m2,x='data',y='PezzI',color='Tipo'),use_container_width=True)

with tabs[2]:
    st.subheader("Costi Ingredienti per Categoria")
    cats = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale','Sale grosso'],
        'Condimenti': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    cat_tot = {cat: df_dist[cols].sum().sum() for cat,cols in cats.items() if any(c in df_dist.columns for c in cols)}
    df_cat = pd.DataFrame.from_dict(cat_tot,orient='index',columns=['Costo']).reset_index().rename(columns={'index':'Categoria'})
    st.bar_chart(df_cat.set_index('Categoria'))

with tabs[3]:
    bib = df_sel[['data']+bibite_cols].melt('data',var_name='Bevanda',value_name='PezzI')
    st.plotly_chart(px.bar(bib,x='data',y='PezzI',color='Bevanda'),use_container_width=True)
    sor = df_sel[['data']+sorbetti_cols].melt('data',var_name='Gusto',value_name='PezzI')
    st.plotly_chart(px.bar(sor,x='data',y='PezzI',color='Gusto'),use_container_width=True)

with tabs[4]:
    st.subheader("Aggregazioni")
    df_idx = df_sel.set_index('data')
    aggs = {
        'Giornaliero': df_idx.resample('D').sum(),
        'Settimanale': df_idx.resample('W').sum(),
        'Mensile': df_idx.resample('M').sum(),
        'Annuale': df_idx.resample('Y').sum()
    }
    for name, table in aggs.items():
        st.write(name)
        st.line_chart(table['fatturato'])

with tabs[5]:
    st.header("Note Metodi")
    st.markdown("""
- Costo giornaliero ingredienti: distribuito tra due approvvigionamenti consecutivi.
- Valori ingredienti, vendite, acquisti: in euro.
- Colonne vendite: quantità vendute; colonne spesa: euro spesi o incassati.
- % Ingredienti e % Dipendenti: medie sul periodo.
""")

# Esporta
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("Scarica CSV", data=csv, file_name="analisi.csv", mime='text/csv')
