import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pokeria", layout="wide")
st.title("Dashboard Pokeria - Costi stimati e vendite")

uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])

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
    inizio, fine = st.date_input("Intervallo", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))]

    st.subheader("Metriche Totali")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fatturato", f"€ {df['fatturato'].sum():,.2f}")
    col2.metric("Ingredienti", f"€ {df['totale_ingredienti'].sum():,.2f}")
    col3.metric("Dipendenti", f"€ {df['Dipendente'].sum():,.2f}")
    col4.metric("Utile stimato", f"€ {(df['fatturato'] - df['totale_ingredienti'] - df['Dipendente']).sum():,.2f}")

    st.subheader("Giorni con percentuali critiche")
    alert = df[(df['% ingredienti'] > 30) | (df['% dipendenti'] > 20)]
    st.dataframe(alert[['data', 'fatturato', '% ingredienti', '% dipendenti']].round(1))

    st.subheader("Vendite Poke e Bowl")
    poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl']
    poke_melt = df[['data'] + poke_cols].melt(id_vars='data', var_name='tipo', value_name='quantità')
    fig = px.line(poke_melt, x='data', y='quantità', color='tipo')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Extra venduti")
    extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    extra_melt = df[['data'] + extra_cols].melt(id_vars='data', var_name='extra', value_name='pezzi')
    fig2 = px.area(extra_melt, x='data', y='pezzi', color='extra')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Confronto Annuale")
    df['anno'] = df['data'].dt.year
    ann = df.groupby('anno').agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
    ann['% ingredienti'] = ann['totale_ingredienti'] / ann['fatturato'] * 100
    ann['% dipendenti'] = ann['Dipendente'] / ann['fatturato'] * 100
    st.dataframe(ann.style.format({'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}', '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'}))

    st.subheader("Tabella Giornaliera")
    st.dataframe(df[['data', 'fatturato', 'totale_ingredienti', '% ingredienti', 'Dipendente', '% dipendenti'] + poke_cols + extra_cols])
