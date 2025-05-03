import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import io

# Configurazione pagina
st.set_page_config(page_title="Pokè To Go – Dashboard Business", layout="wide")

# Caricamento logo
logo = Image.open("/mnt/data/logo.png")
st.image(logo, width=150)

# Stili personalizzati
st.markdown("""
    <style>
    .main { background-color: #fdfcfb; }
    h1, h2, h3 { color: #e85d04; }
    .stMetric { background-color: #fff7ed; border-radius: 10px; padding: 10px !important; }
    .block-container { padding-top: 2rem; }
    .stDataFrame { background-color: white; }
    </style>
""", unsafe_allow_html=True)

# Titolo
st.title("🍣 Pokè To Go – Dashboard Operativa")

# Introduzione
st.markdown("""
#### Benvenuta Arianna 👋  
Questa dashboard mostra vendite, spese e margini stimati in base al file caricato.  
I costi ingredienti vengono **distribuiti sui giorni** tra due approvvigionamenti consecutivi.  
Le *giornate critiche* sono segnalate se:
- il fatturato è sotto i 300€  
- i costi ingredienti superano il 35%  
- i costi dipendenti superano il 25%
""")

# Upload file
uploaded_file = st.file_uploader("⬆️ Carica il file CSV estratto", type=["csv"])

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

    # Distribuzione costi ingredienti
    df_distribuiti = pd.DataFrame(index=df.index)
    for ingrediente in ingredienti:
        serie = df[['data', ingrediente]].dropna()
        serie = serie[serie[ingrediente] > 0].sort_values('data')
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
    inizio, fine = st.date_input("📅 Intervallo Analisi", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))]

    # Dati aggregati
    poke_cols = ['poke_reglular', 'poke_maxi', 'poke_baby']
    extra_cols = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    df['poke_totali'] = df[poke_cols].sum(axis=1)
    df['extra_totali'] = df[extra_cols].sum(axis=1)

    # Alert se molte giornate critiche
    giornate_critiche = df[(df['fatturato'] < 300) | (df['% ingredienti'] > 35) | (df['% dipendenti'] > 25)]
    if len(giornate_critiche) >= 5:
        st.warning(f"🚨 Attenzione: ci sono {len(giornate_critiche)} giornate da monitorare nel periodo selezionato.")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📌 Metriche", "🍱 Vendite", "🥤 Bevande & Sorbetti", "📆 Storico"])

    with tab1:
        st.header("📌 Performance Totale")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fatturato", f"€ {df['fatturato'].sum():,.2f}")
        col2.metric("Ingredienti stimati", f"€ {df['totale_ingredienti'].sum():,.2f}")
        col3.metric("Dipendenti", f"€ {df['Dipendente'].sum():,.2f}")
        col4.metric("Utile stimato", f"€ {(df['fatturato'] - df['totale_ingredienti'] - df['Dipendente']).sum():,.2f}")

        st.header("📈 KPI Operativi")
        tot_poke = df['poke_totali'].sum()
        tot_extra = df['extra_totali'].sum()
        ricavi = df['fatturato'].sum()
        costo_ingredienti = df['totale_ingredienti'].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Ricavo Medio per Poke", f"€ {ricavi / tot_poke:.2f}" if tot_poke > 0 else "N/A")
        col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
        col3.metric("Costo Medio per Poke", f"€ {costo_ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

        st.header("❗ Giornate Critiche")
        giornate_critiche['Attenzione'] = ""
        giornate_critiche.loc[giornate_critiche['% ingredienti'] > 35, 'Attenzione'] += "🧂 Costi ingredienti alti  "
        giornate_critiche.loc[giornate_critiche['% dipendenti'] > 25, 'Attenzione'] += "👥 Costi dipendenti alti  "
        giornate_critiche.loc[giornate_critiche['fatturato'] < 300, 'Attenzione'] += "📉 Fatturato basso"
        st.dataframe(giornate_critiche[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))

    with tab2:
        st.header("🍱 Vendite Poke e Bowl")
        poke_melt = df[['data'] + poke_cols + ['fruit_bowl']].melt(id_vars='data', var_name='tipo', value_name='quantità')
        fig1 = px.line(poke_melt, x='data', y='quantità', color='tipo', markers=True)
        st.plotly_chart(fig1, use_container_width=True)

        st.header("🥑 Extra Venduti")
        extra_melt = df[['data'] + extra_cols].melt(id_vars='data', var_name='extra', value_name='pezzi')
        fig2 = px.area(extra_melt, x='data', y='pezzi', color='extra')
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.header("🥤 Bevande")
        bibite_melt = df[['data'] + bibite].melt(id_vars='data', var_name='bevanda', value_name='pezzi')
        fig3 = px.bar(bibite_melt, x='data', y='pezzi', color='bevanda')
        st.plotly_chart(fig3, use_container_width=True)

        st.header("🍧 Sorbetti")
        sorbetti_melt = df[['data'] + sorbetti].melt(id_vars='data', var_name='gusto', value_name='pezzi')
        fig4 = px.bar(sorbetti_melt, x='data', y='pezzi', color='gusto')
        st.plotly_chart(fig4, use_container_width=True)

    with tab4:
        st.header("📆 Confronto Annuale")
        df['anno'] = df['data'].dt.year
        ann = df.groupby('anno').agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
        ann['% ingredienti'] = ann['totale_ingredienti'] / ann['fatturato'] * 100
        ann['% dipendenti'] = ann['Dipendente'] / ann['fatturato'] * 100
        st.dataframe(ann.style.format({'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}', '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'}))

    # Download CSV
    csv_export = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Analisi in CSV", data=csv_export, file_name="analisi_poketogo.csv", mime='text/csv')
