
import streamlit as st
import pandas as pd
import plotly.express as px

# 🌈 STYLE & THEME
st.set_page_config(page_title="Pokè to Go – Dashboard Arianna", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #fdfcfb;
    }
    h1, h2, h3 {
        color: #e85d04;
    }
    .stMetric {
        background-color: #fff7ed;
        border-radius: 10px;
        padding: 10px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stDataFrame {
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# 🎯 TITOLO E UPLOAD FILE
st.title("🍣 Pokè to Go – La tua Dashboard Giornaliera")
uploaded_file = st.file_uploader("⬆️ Carica il file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    df = df.dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'fatturato'])

    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    venduti = [
        'Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto',
        'poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl',
        'fatturato', 'Dipendente'
    ]
    bibite = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
    sorbetti = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']

    ingredienti = [col for col in df.columns if col not in venduti + ['data']]

    df_distribuiti = pd.DataFrame(index=df.index)
    for ingrediente in ingredienti:
        serie = df[['data', ingrediente]].dropna()
        serie = serie[serie[ingrediente] > 0].sort_values('data')
        serie['data'] = pd.to_datetime(serie['data'])

        distribuzione = pd.Series(0, index=df.index)
        if len(serie) >= 2:
            for i in range(len(serie) - 1):
                start = serie.iloc[i]['data']
                end = serie.iloc[i + 1]['data']
                days = (end - start).days
                if days > 0:
                    valore = serie.iloc[i][ingrediente] / days
                    mask = (df['data'] >= start) & (df['data'] < end)
                    distribuzione[mask] += valore

        df_distribuiti[ingrediente] = distribuzione

    df['totale_ingredienti'] = df_distribuiti.sum(axis=1)
    df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
    df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100

    min_date, max_date = df['data'].min(), df['data'].max()
    inizio, fine = st.date_input("📅 Seleziona un intervallo", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))]

    poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby']
    extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    df['poke_totali'] = df[poke_cols].sum(axis=1)
    df['extra_totali'] = df[extra_cols].sum(axis=1)

    tab1, tab2, tab3, tab4 = st.tabs(["📌 Metriche", "🍱 Vendite", "🥤 Bevande & Sorbetti", "📆 Storico"])

    with tab1:
        st.header("📌 Le tue Metriche Totali")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fatturato", f"€ {df['fatturato'].sum():,.2f}")
        col2.metric("Ingredienti stimati", f"€ {df['totale_ingredienti'].sum():,.2f}")
        col3.metric("Dipendenti", f"€ {df['Dipendente'].sum():,.2f}")
        col4.metric("Utile stimato", f"€ {(df['fatturato'] - df['totale_ingredienti'] - df['Dipendente']).sum():,.2f}")

        st.header("📈 KPI Operativi – Quanto rende ogni poke?")
        tot_poke = df['poke_totali'].sum()
        tot_extra = df['extra_totali'].sum()
        ricavi = df['fatturato'].sum()
        costo_ingredienti = df['totale_ingredienti'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Ricavo Medio per Poke", f"€ {ricavi / tot_poke:.2f}" if tot_poke > 0 else "N/A")
        col2.metric("Extra ogni 10 poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
        col3.metric("Costo ingredienti per Poke", f"€ {costo_ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

        st.header("❗ Giornate Critiche da tenere d'occhio")
        crit = df[(df['fatturato'] < 300) | (df['% ingredienti'] > 35) | (df['% dipendenti'] > 25)]
        crit['Attenzione'] = ""
        crit.loc[crit['% ingredienti'] > 35, 'Attenzione'] += "🧂 Ingredienti >35%  "
        crit.loc[crit['% dipendenti'] > 25, 'Attenzione'] += "👥 Dipendenti >25%  "
        crit.loc[crit['fatturato'] < 300, 'Attenzione'] += "📉 Fatturato <300€"
        st.dataframe(crit[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))

    st.download_button("📥 Scarica il CSV filtrato", data=df.to_csv(index=False).encode('utf-8'), file_name="analisi_poketogo.csv", mime='text/csv')
