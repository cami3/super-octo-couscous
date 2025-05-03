import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pokeria Dashboard", layout="wide")
st.title("Pokeria - Analisi Vendite e Costi")

uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    df = df.dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'fatturato'])

    # Conversione numerica
    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Intervallo analisi
    min_date, max_date = df['data'].min(), df['data'].max()
    inizio, fine = st.date_input("Intervallo", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))]

    # Calcoli
    df['totale_ingredienti'] = df.iloc[:, 1:60].sum(axis=1)
    df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
    df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100
    df['anno'] = df['data'].dt.year
    df['mese'] = df['data'].dt.to_period('M').astype(str)

    st.header("Metriche Totali")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fatturato", f"€ {df['fatturato'].sum():,.2f}")
    col2.metric("Ingredienti", f"€ {df['totale_ingredienti'].sum():,.2f}")
    col3.metric("Dipendenti", f"€ {df['Dipendente'].sum():,.2f}")
    col4.metric("Utile stimato", f"€ {(df['fatturato'] - df['totale_ingredienti'] - df['Dipendente']).sum():,.2f}")

    st.header("Percentuali Critiche")
    alert = df[(df['% ingredienti'] > 30) | (df['% dipendenti'] > 20)]
    st.dataframe(alert[['data', 'fatturato', '% ingredienti', '% dipendenti']].round(1))

    st.header("Vendite Poke e Bowl")
    poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl']
    poke_melt = df[['data'] + poke_cols].melt(id_vars='data', var_name='tipo', value_name='quantità')
    fig = px.line(poke_melt, x='data', y='quantità', color='tipo', title="Andamento Vendite")
    st.plotly_chart(fig, use_container_width=True)

    st.header("Extra Venduti")
    extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    extra_melt = df[['data'] + extra_cols].melt(id_vars='data', var_name='extra', value_name='pezzi')
    fig2 = px.area(extra_melt, x='data', y='pezzi', color='extra', title="Trend Extra")
    st.plotly_chart(fig2, use_container_width=True)

    st.header("Confronto Annuale")
    ann = df.groupby('anno').agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
    ann['% ingredienti'] = ann['totale_ingredienti'] / ann['fatturato'] * 100
    ann['% dipendenti'] = ann['Dipendente'] / ann['fatturato'] * 100
    st.dataframe(ann.style.format({'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}', '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'}))

    st.header("Costo Ingredienti Totale per Mese")
    mensile = df.groupby('mese')[['totale_ingredienti']].sum().reset_index()
    fig3 = px.bar(mensile, x='mese', y='totale_ingredienti', title="Totale Ingredienti per Mese")
    st.plotly_chart(fig3, use_container_width=True)

    st.header("Tabella Giornaliera")
    st.dataframe(df[['data', 'fatturato', 'poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl'] + extra_cols])
