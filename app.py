
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pokeria Arianna – Dashboard Visiva", layout="wide")

st.title("🌸 Pokeria – Analisi Visiva e KPI Giornalieri")

uploaded_file = st.file_uploader("Carica file CSV giornaliero", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    df = df.dropna(how='all')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data'])

    for col in df.columns:
        if col != 'data':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    vendite_poke = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl']
    extra = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
    bibite = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
    sorbetti = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']

    exclude = ['data', 'Dipendente', 'fatturato'] + vendite_poke + extra
    ingredienti = [col for col in df.columns if col not in exclude]

    df['totale_ingredienti'] = df[ingredienti].sum(axis=1)
    df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
    df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100
    df = df.sort_values('data')

    min_date = df['data'].min()
    max_date = df['data'].max()
    inizio, fine = st.date_input("Seleziona intervallo", [min_date, max_date])
    mask = (df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))
    subset = df[mask]

    totale_poke = subset[vendite_poke].sum().sum()
    ricavi = subset['fatturato'].sum()
    spesa_ingredienti = subset['totale_ingredienti'].sum()
    spesa_dipendenti = subset['Dipendente'].sum()
    utile = ricavi - spesa_ingredienti - spesa_dipendenti
    extra_totali = subset[extra].sum().sum()
    costo_per_poke = spesa_ingredienti / totale_poke if totale_poke else 0
    ricavo_per_poke = ricavi / totale_poke if totale_poke else 0

    st.markdown("""
    <div style='padding: 1rem; background-color: #fef6fa; border-radius: 10px;'>
    <h4 style='color: #4b2e83;'>Guida visiva</h4>
    <ul>
        <li>🌈 <b>Pattern all-over</b> = coerenza nel tempo</li>
        <li>🍱 <b>Poke venduti</b>: ritmo e varietà</li>
        <li>🥑 <b>Extra</b>: personalizzazione efficace</li>
        <li>💸 <b>Costi</b>: sotto soglia = gestione buona</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("✨ Metriche Chiave")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fatturato", f"€ {ricavi:,.2f}")
    col2.metric("Ingredienti", f"€ {spesa_ingredienti:,.2f}")
    col3.metric("Dipendenti", f"€ {spesa_dipendenti:,.2f}")
    col4.metric("Utile stimato", f"€ {utile:,.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Ricavo Medio per Poke", f"€ {ricavo_per_poke:.2f}")
    col6.metric("Extra ogni 10 poke", f"{extra_totali / (totale_poke / 10):.1f}" if totale_poke else "0")
    col7.metric("Costo Ingredienti per Poke", f"€ {costo_per_poke:.2f}")

    st.subheader("🚨 Giornate Critiche")
    critiche = subset[
        (subset['% ingredienti'] > 35) |
        (subset['% dipendenti'] > 25) |
        (subset['fatturato'] < 300)
    ][['data', 'fatturato', '% ingredienti', '% dipendenti']]
    st.dataframe(critiche)

    st.subheader("📊 Vendite Poke e Bowl")
    poke_df = subset[['data'] + vendite_poke].melt(id_vars='data', var_name='tipo', value_name='quantità')
    fig1 = px.line(poke_df, x='data', y='quantità', color='tipo')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🧁 Extra Ingredienti Venduti")
    extra_df = subset[['data'] + extra].melt(id_vars='data', var_name='extra', value_name='pezzi')
    fig2 = px.area(extra_df, x='data', y='pezzi', color='extra')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🥤 Bevande")
    df_bibite = subset.melt(id_vars='data', value_vars=bibite, var_name='bevanda', value_name='unità')
    fig3 = px.line(df_bibite, x='data', y='unità', color='bevanda')
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🍧 Sorbetti")
    df_sorbetti = subset.melt(id_vars='data', value_vars=sorbetti, var_name='gusto', value_name='pezzi')
    fig4 = px.bar(df_sorbetti, x='data', y='pezzi', color='gusto')
    st.plotly_chart(fig4, use_container_width=True)

    st.download_button("📥 Scarica il CSV filtrato", subset.to_csv(index=False).encode('utf-8'), "dati_filtrati.csv", "text/csv")
