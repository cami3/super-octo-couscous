import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pokeria - Dashboard Completa", layout="wide")
st.title("Pokeria - Analisi Vendite, Costi e KPI")

uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])

st.markdown("""
## Guida alla Lettura Dati

Questa dashboard analizza vendite e costi stimati della Pokeria su base giornaliera.

**Fonte dei dati**: file CSV con fatturato, acquisti, personale, quantità vendute.

### Logica di calcolo

- **Costi ingredienti**: distribuiti tra due acquisti successivi, proporzionalmente nel tempo (simulano consumo + scadenza)
- **% Ingredienti / % Dipendenti**: indicano l’incidenza dei costi giornalieri sul fatturato
- **Utile stimato**: differenza tra fatturato e costi stimati
- **KPI per poke**: ricavo medio, extra per 10 poke, costo medio stimato

### Soglie di attenzione

- **% Ingredienti > 35%**: rischio inefficienza o spreco
- **% Dipendenti > 25%**: rischio squilibrio organico
- **Fatturato < €300**: giornata critica

### Esportazione

È possibile scaricare l’intero periodo filtrato in CSV per condivisione o archiviazione.

---
""")

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

    poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby']
    extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    df['poke_totali'] = df[poke_cols].sum(axis=1)
    df['extra_totali'] = df[extra_cols].sum(axis=1)

    st.subheader("Metriche Totali")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fatturato", f"€ {df['fatturato'].sum():,.2f}")
    col2.metric("Ingredienti stimati", f"€ {df['totale_ingredienti'].sum():,.2f}")
    col3.metric("Dipendenti", f"€ {df['Dipendente'].sum():,.2f}")
    col4.metric("Utile stimato", f"€ {(df['fatturato'] - df['totale_ingredienti'] - df['Dipendente']).sum():,.2f}")

    st.subheader("KPI Operativi")
    tot_poke = df['poke_totali'].sum()
    tot_extra = df['extra_totali'].sum()
    ricavi = df['fatturato'].sum()
    costo_ingredienti = df['totale_ingredienti'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Ricavo Medio per Poke", f"€ {ricavi / tot_poke:.2f}" if tot_poke > 0 else "N/A")
    col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
    col3.metric("Costo Ingredienti per Poke", f"€ {costo_ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

    st.subheader("Giornate Critiche")
    crit = df[(df['fatturato'] < 300) | (df['% ingredienti'] > 35) | (df['% dipendenti'] > 25)]
    st.dataframe(crit[['data', 'fatturato', '% ingredienti', '% dipendenti']].round(1))

    st.subheader("Vendite Poke e Bowl")
    poke_melt = df[['data'] + poke_cols + ['fruit_bowl']].melt(id_vars='data', var_name='tipo', value_name='quantità')
    fig = px.line(poke_melt, x='data', y='quantità', color='tipo')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Extra venduti")
    extra_melt = df[['data'] + extra_cols].melt(id_vars='data', var_name='extra', value_name='pezzi')
    fig2 = px.area(extra_melt, x='data', y='pezzi', color='extra')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Confronto Annuale")
    df['anno'] = df['data'].dt.year
    ann = df.groupby('anno').agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
    ann['% ingredienti'] = ann['totale_ingredienti'] / ann['fatturato'] * 100
    ann['% dipendenti'] = ann['Dipendente'] / ann['fatturato'] * 100
    st.dataframe(ann.style.format({'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}', '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'}))

    st.subheader("Esporta i dati")
    csv_export = df.to_csv(index=False).encode('utf-8')
    st.download_button("Scarica il CSV filtrato", data=csv_export, file_name="analisi_pokeria.csv", mime='text/csv')
