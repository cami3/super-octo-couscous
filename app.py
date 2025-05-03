import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Contabilità Pokeria", layout="wide")
st.title("Contabilità e Analisi - Pokeria")

uploaded_file = st.file_uploader("Carica il file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    df = df.dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'fatturato'])

    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    exclude = ['data', 'Dipendente', 'poke_reglular', 'poke_maxi', 'poke_baby',
               'fruit_bowl', 'Avocado_venduto', 'Feta_venduto', 'Philad_venduto',
               'Gomawak_venduto', 'fatturato']
    ingredienti = [col for col in df.columns if col not in exclude]

    df['totale_ingredienti'] = df[ingredienti].sum(axis=1)
    df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
    df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100
    df['mese'] = df['data'].dt.to_period('M')
    df['anno'] = df['data'].dt.year
    df['settimana'] = df['data'].dt.to_period('W')

    st.sidebar.subheader("Filtra per intervallo di date")
    inizio, fine = st.sidebar.date_input("Intervallo", [df['data'].min(), df['data'].max()])
    mask = (df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))
    subset = df[mask]

    st.subheader("Metriche Totali")
    ricavi = subset['fatturato'].sum()
    spesa_ingredienti = subset['totale_ingredienti'].sum()
    spesa_dipendenti = subset['Dipendente'].sum()
    utile = ricavi - spesa_ingredienti - spesa_dipendenti

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ricavi", f"€ {ricavi:,.2f}")
    col2.metric("Ingredienti", f"€ {spesa_ingredienti:,.2f}", f"{(spesa_ingredienti/ricavi)*100:.1f}%")
    col3.metric("Dipendenti", f"€ {spesa_dipendenti:,.2f}", f"{(spesa_dipendenti/ricavi)*100:.1f}%")
    col4.metric("Utile", f"€ {utile:,.2f}")

    st.subheader("Trend Settimanale")
    settimanale = subset.groupby('settimana').agg({
        'fatturato': 'sum',
        'totale_ingredienti': 'sum',
        'Dipendente': 'sum'
    }).reset_index()
    fig_week = px.line(settimanale, x='settimana', y=['fatturato', 'totale_ingredienti', 'Dipendente'], markers=True)
    st.plotly_chart(fig_week, use_container_width=True)

    st.subheader("Analisi Mensile")
    mensile = subset.groupby('mese').agg({
        'fatturato': 'sum',
        'totale_ingredienti': 'sum',
        'Dipendente': 'sum'
    }).reset_index()
    mensile['% ingredienti'] = (mensile['totale_ingredienti'] / mensile['fatturato']) * 100
    mensile['% dipendenti'] = (mensile['Dipendente'] / mensile['fatturato']) * 100
    fig_month = px.bar(mensile, x='mese', y=['% ingredienti', '% dipendenti'], barmode='group')
    st.plotly_chart(fig_month, use_container_width=True)

    st.subheader("Confronto Annuale")
    annuale = df.groupby('anno').agg({
        'fatturato': 'sum',
        'totale_ingredienti': 'sum',
        'Dipendente': 'sum'
    }).reset_index()
    annuale['% ingredienti'] = (annuale['totale_ingredienti'] / annuale['fatturato']) * 100
    annuale['% dipendenti'] = (annuale['Dipendente'] / annuale['fatturato']) * 100
    st.dataframe(annuale.style.format({'% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%', 'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}'}))

    st.subheader("Tabella giornaliera (per dettaglio, non per confronto)")
    tab = subset[['data', 'fatturato', 'totale_ingredienti', 'Dipendente']].copy()
    st.dataframe(tab.style.format({'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}'}))
