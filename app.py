import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analisi Pokeria", layout="wide")

st.title("Contabilità Pokeria")

uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.dropna(how='all')  # Rimuove righe completamente vuote

    # Assunzioni minime su struttura CSV
    # Colonne: data, vendite, ingredienti, dipendenti, spese_varie
    df.columns = [c.strip().lower() for c in df.columns]
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])  # Rimuove righe senza data valida

    # Filtri temporali
    min_date = df['data'].min()
    max_date = df['data'].max()
    start, end = st.date_input("Seleziona intervallo", [min_date, max_date])
    mask = (df['data'] >= pd.to_datetime(start)) & (df['data'] <= pd.to_datetime(end))
    filtered = df[mask]

    # Calcoli
    ricavi = filtered['vendite'].sum()
    costo_ingredienti = filtered['ingredienti'].sum()
    costo_dipendenti = filtered['dipendenti'].sum()
    spese_varie = filtered['spese_varie'].sum()
    totale_spese = costo_ingredienti + costo_dipendenti + spese_varie
    utile = ricavi - totale_spese

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ricavi", f"€ {ricavi:,.2f}")
    col2.metric("Costo Ingredienti", f"€ {costo_ingredienti:,.2f}", f"{(costo_ingredienti/ricavi)*100:.1f} %")
    col3.metric("Costo Dipendenti", f"€ {costo_dipendenti:,.2f}", f"{(costo_dipendenti/ricavi)*100:.1f} %")
    col4.metric("Utile Netto", f"€ {utile:,.2f}")

    # Grafici
    trend = filtered.groupby('data')[['vendite', 'ingredienti', 'dipendenti']].sum().reset_index()
    fig = px.line(trend, x='data', y=['vendite', 'ingredienti', 'dipendenti'], markers=True,
                  labels={"value": "€", "data": "Data", "variable": "Voce"})
    st.plotly_chart(fig, use_container_width=True)

    # Confronto tra due periodi
    st.subheader("Confronto tra due periodi")
    col5, col6 = st.columns(2)
    with col5:
        p1 = st.date_input("Periodo 1", [min_date, max_date], key='p1')
    with col6:
        p2 = st.date_input("Periodo 2", [min_date, max_date], key='p2')

    def analyze_period(start_date, end_date):
        mask = (df['data'] >= pd.to_datetime(start_date)) & (df['data'] <= pd.to_datetime(end_date))
        d = df[mask]
        return {
            "ricavi": d['vendite'].sum(),
            "ingredienti": d['ingredienti'].sum(),
            "dipendenti": d['dipendenti'].sum(),
            "spese": d['spese_varie'].sum()
        }

    a = analyze_period(*p1)
    b = analyze_period(*p2)

    confronto = pd.DataFrame({
        "Periodo 1": [a['ricavi'], a['ingredienti'], a['dipendenti'], a['spese']],
        "Periodo 2": [b['ricavi'], b['ingredienti'], b['dipendenti'], b['spese']]
    }, index=["Ricavi", "Ingredienti", "Dipendenti", "Spese Varie"])

    st.dataframe(confronto.style.format("€ {:,.2f}"))
