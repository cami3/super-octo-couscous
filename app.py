
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pokeria - Analisi Visiva", layout="wide")

st.title("Pokeria - Analisi Visiva e KPI Operativi")

uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file, sep=';')
df = df.dropna(how='all')

# Parse date
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data'])

# Conversione numerica
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.sort_values("data")

# Intervallo selezionabile
min_date, max_date = df['data'].min(), df['data'].max()
inizio, fine = st.date_input("Intervallo Analisi", [min_date, max_date], min_value=min_date, max_value=max_date)
mask = (df['data'] >= pd.to_datetime(inizio)) & (df['data'] <= pd.to_datetime(fine))
subset = df[mask]

# Colonne utili
vendite_poke = ['poke_reglular', 'poke_maxi', 'poke_baby', 'fruit_bowl']
extra = ['Avocado_venduto', 'Feta_venduto', 'Philad_venduto', 'Gomawak_venduto']
bibite = ['Acqua nat', 'Acqua gas', 'Coca cola', 'Coca zero', 'corona', 'ichnusa', 'fanta', 'Estathe limone', 'Estathe pesca']
sorbetti = ['Sorbetto limone', 'Sorbetto mela', 'Sorbetto mango']

ingredienti_esclusi = vendite_poke + extra + ['Dipendente', 'fatturato', 'data']
ingredienti = [col for col in df.columns if col not in ingredienti_esclusi]

# Calcoli
df['totale_ingredienti'] = df[ingredienti].sum(axis=1)
df['% ingredienti'] = (df['totale_ingredienti'] / df['fatturato']) * 100
df['% dipendenti'] = (df['Dipendente'] / df['fatturato']) * 100

ricavi = subset['fatturato'].sum()
spesa_ingredienti = subset['totale_ingredienti'].sum()
spesa_dipendenti = subset['Dipendente'].sum()
utile = ricavi - spesa_ingredienti - spesa_dipendenti
totale_poke = subset[vendite_poke].sum().sum()
extra_totali = subset[extra].sum().sum()
costo_per_poke = spesa_ingredienti / totale_poke if totale_poke else 0
ricavo_per_poke = ricavi / totale_poke if totale_poke else 0

# Documentazione
with st.expander("📘 Guida alla Lettura Dati"):
    st.markdown("""
    - I costi ingredienti sono stimati distribuendo gli acquisti nei giorni tra un acquisto e il successivo.
    - I KPI includono ricavo medio per poke e numero medio di extra ogni 10 poke.
    - Le giornate critiche sono quelle con percentuali oltre soglia o ricavi < €300.
    """)

# Metriche principali
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatturato", f"€ {ricavi:,.2f}")
col2.metric("Ingredienti stimati", f"€ {spesa_ingredienti:,.2f}")
col3.metric("Dipendenti", f"€ {spesa_dipendenti:,.2f}")
col4.metric("Utile stimato", f"€ {utile:,.2f}")

st.subheader("KPI Operativi")
col5, col6, col7 = st.columns(3)
col5.metric("Ricavo Medio per Poke", f"€ {ricavo_per_poke:.2f}")
col6.metric("Extra per 10 Poke", f"{extra_totali / (totale_poke / 10):.1f}" if totale_poke else "0")
col7.metric("Costo Ingredienti per Poke", f"€ {costo_per_poke:.2f}")

# Giornate critiche
st.subheader("📛 Giornate Critiche")
critiche = subset[
    (df['% ingredienti'] > 35) | (df['% dipendenti'] > 25) | (df['fatturato'] < 300)
][['data', 'fatturato', '% ingredienti', '% dipendenti']]
st.dataframe(critiche)

# Vendite poke
st.subheader("📈 Vendite Poke e Bowl")
df_melt_poke = subset.melt(id_vars='data', value_vars=vendite_poke, var_name='tipo', value_name='quantità')
fig1 = px.line(df_melt_poke, x='data', y='quantità', color='tipo')
st.plotly_chart(fig1, use_container_width=True)

# Extra venduti
st.subheader("🍥 Extra Venduti")
df_melt_extra = subset.melt(id_vars='data', value_vars=extra, var_name='extra', value_name='pezzi')
fig2 = px.area(df_melt_extra, x='data', y='pezzi', color='extra', groupnorm='')
st.plotly_chart(fig2, use_container_width=True)

# Bevande
st.subheader("🥤 Bevande")
df_bibite = subset.melt(id_vars='data', value_vars=bibite, var_name='bevanda', value_name='unità')
fig3 = px.line(df_bibite, x='data', y='unità', color='bevanda')
st.plotly_chart(fig3, use_container_width=True)

# Sorbetti
st.subheader("🍧 Sorbetti")
df_sorbetti = subset.melt(id_vars='data', value_vars=sorbetti, var_name='gusto', value_name='pezzi')
fig4 = px.bar(df_sorbetti, x='data', y='pezzi', color='gusto')
st.plotly_chart(fig4, use_container_width=True)
