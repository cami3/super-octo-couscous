import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Contabilità Pokeria", layout="wide")
st.title("Analisi Vendite e Spese - Pokeria")

uploaded_file = st.file_uploader("Carica il file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    df = df.dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data'])
    df = df[df['fatturato'].notna()]
    
    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Ingredienti = tutto tranne queste colonne
    exclude = ['data', 'Dipendente', 'poke_reglular', 'poke_maxi', 'poke_baby',
               'fruit_bowl', 'Avocado_venduto', 'Feta_venduto', 'Philad_venduto',
               'Gomawak_venduto', 'fatturato']
    ingredienti = [col for col in df.columns if col not in exclude]

    df['totale_ingredienti'] = df[ingredienti].sum(axis=1)
    df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
    df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100

    df = df.sort_values('data')

    # Intervallo
    min_date = df['data'].min()
    max_date = df['data'].max()
    inizio, fine = st.date_input("Intervallo analisi", [min_date, max_date])
    mask = (df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))
    subset = df[mask]

    # METRICHE
    ricavi = subset['fatturato'].sum()
    spesa_ingredienti = subset['totale_ingredienti'].sum()
    spesa_dipendenti = subset['Dipendente'].sum()
    utile = ricavi - spesa_ingredienti - spesa_dipendenti

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ricavi", f"€ {ricavi:,.2f}")
    col2.metric("Ingredienti", f"€ {spesa_ingredienti:,.2f}", f"{(spesa_ingredienti/ricavi)*100:.1f} %")
    col3.metric("Dipendenti", f"€ {spesa_dipendenti:,.2f}", f"{(spesa_dipendenti/ricavi)*100:.1f} %")
    col4.metric("Utile", f"€ {utile:,.2f}")

    # GRAFICO TREND
    trend = subset[['data', 'fatturato', 'totale_ingredienti', 'Dipendente']].copy()
    trend = trend.groupby('data').sum().reset_index()
    fig = px.line(trend, x='data', y=['fatturato', 'totale_ingredienti', 'Dipendente'], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # TABELLA DETTAGLIO
    # TABELLA DETTAGLIO con evidenziazione soglie
def highlight_thresholds(val, soglia):
    try:
        return 'color: red' if float(val) > soglia else ''
    except:
        return ''

df_show = subset[['data', 'fatturato', 'totale_ingredienti', 'Dipendente', '% ingredienti', '% dipendenti']].copy()
df_show['% ingredienti'] = df_show['% ingredienti'].round(1)
df_show['% dipendenti'] = df_show['% dipendenti'].round(1)

st.dataframe(
    df_show.style
    .format({'% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'})
    .applymap(lambda v: highlight_thresholds(v, 30), subset=['% ingredienti'])
    .applymap(lambda v: highlight_thresholds(v, 20), subset=['% dipendenti'])
)
