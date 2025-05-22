# Pokè To Go! – Dashboard Operativa Completa per Arianna
# Coerente con il sito poketogo.it, con grafici, tabs, metriche e alert

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import timedelta

st.set_page_config(page_title="Pokè To Go! – Dashboard Business", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #fdfcfb;
    }
    h1, h2, h3 {
        color: #e85d04;
    }
    .stMetric {
        background-color: #fff5f0;
        border-radius: 10px;
        padding: 10px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.image(Image.open("logo.png"), width=140)
st.title("Pokè To Go! – Dashboard Operativa")

st.markdown("""
**🔍 Metodo di calcolo costi:**  
I costi degli ingredienti vengono **distribuiti tra due approvvigionamenti successivi**.  
**⚠️ Giornate critiche:** giornate con **ricavi bassi o costi alti**.  
**⛱️ Non sono allarmi**, ma **indicatori da osservare** con serenità.
""")

uploaded = st.file_uploader("📥 Carica file CSV giornaliero", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded, sep=';').dropna(how='all')
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data', 'fatturato'])
for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl', 'poke_veggy']
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto', 'Sorbetti_venduti']
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

# --- DISTRIBUZIONE COSTI ---
df_dist = pd.DataFrame(index=df.index)
for ing in ingred_cols:
    s = df[['data', ing]].dropna()
    s = s[s[ing] > 0].sort_values('data')
    arr = pd.Series(0.0, index=df.index)
    for i in range(len(s) - 1):
        a, b = s.iloc[i]['data'], s.iloc[i+1]['data']
        days = (b - a).days
        if days > 0:
            arr[(df['data'] >= a) & (df['data'] < b)] += s.iloc[i][ing] / days
    df_dist[ing] = arr

def safe_pct(cost, rev):
    return cost/rev*100 if rev > 0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti'] = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df['poke_totali'] = df[poke_cols].sum(axis=1)
df['extra_totali'] = df[extra_cols].sum(axis=1)
df['bibite_sorbetti'] = df[bibite_cols + sorbetti_cols].sum(axis=1)

min_date, max_date = df['data'].min().date(), df['data'].max().date()
with st.form("date_form"):
    start, end = st.date_input("📅 Seleziona periodo", [min_date, max_date], min_value=min_date, max_value=max_date)
    submitted = st.form_submit_button("📊 Analizza")
if not submitted:
    st.stop()

start, end = pd.to_datetime(start), pd.to_datetime(end)
prev_start = start.replace(year=start.year - 1)
prev_end = end.replace(year=end.year - 1)

df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
df_prev = df[(df['data'] >= prev_start) & (df['data'] <= prev_end)]
df_dist['data'] = df['data']
df_dist_sel = df_dist[(df_dist['data'] >= start) & (df_dist['data'] <= end)]

# --- KPI ---
st.header("📌 Riepilogo operativo")
col1, col2, col3, col4, col5 = st.columns(5)
fatturato = df_sel['fatturato'].sum()
ingredienti = df_sel['totale_ingredienti'].sum()
dipendenti = df_sel['Dipendente'].sum()
bibite_sorbetti = df_sel['bibite_sorbetti'].sum()
utile = fatturato - ingredienti - dipendenti - bibite_sorbetti
col1.metric("Fatturato", f"€ {fatturato:,.2f}")
col2.metric("Ingredienti", f"€ {ingredienti:,.2f}")
col3.metric("Dipendenti", f"€ {dipendenti:,.2f}")
col4.metric("Bibite/Sorbetti", f"€ {bibite_sorbetti:,.2f}")
col5.metric("Utile stimato", f"€ {utile:,.2f}")


tot_poke = df_sel['poke_totali'].sum()
tot_extra = df_sel['extra_totali'].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Ricavo Medio per Poke", f"€ {fatturato / tot_poke:.2f}" if tot_poke > 0 else "N/A")
col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
col3.metric("Costo Medio per Poke", f"€ {ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")

# --- INTERPRETAZIONE ---
st.header("🧠 Lettura sintetica del periodo")
giorni = len(df_sel)
critici = df_sel[(df_sel['% ingredienti'] > 35) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 300)]
perc = len(critici) / giorni * 100 if giorni > 0 else 0
solo1 = critici[((critici['% ingredienti'] > 35).astype(int) + 
                 (critici['% dipendenti'] > 25).astype(int) + 
                 (critici['fatturato'] < 300).astype(int)) == 1]
multi = len(critici) - len(solo1)

st.info(f"🔎 Su {giorni} giornate: {len(critici)} critiche ({perc:.1f}%) → {len(solo1)} con 1 criticità, {multi} con più.")
if utile <= 0:
    st.error("🔴 Utile negativo: costi superiori ai ricavi.")
elif perc > 50:
    st.warning("🟠 Molte giornate sotto soglia: valuta interventi.")
else:
    st.success("🟢 Equilibrio OK nel periodo.")

# --- TABS ---
tabs = st.tabs(["📈 Vendite", "🍱 Extra", "🥤 Bibite", "🍧 Sorbetti", "🍚 Ingredienti", "📊 Annuale", "⚠️ Giornate Critiche", "ℹ️ Aiuto"])

with tabs[0]:
    st.header("📈 Vendite - Poke e Bowl")
    melt = df_sel[['data'] + poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)

with tabs[1]:
    st.header("🍱 Extra venduti")
    melt = df_sel[['data'] + extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt, x='data', y='Euro', color='Tipo'), use_container_width=True)

with tabs[2]:
    st.header("🥤 Bibite (costi)")
    melt = df_sel[['data'] + bibite_cols].melt('data', var_name='Prodotto', value_name='Euro')
    st.plotly_chart(px.bar(melt, x='data', y='Euro', color='Prodotto'), use_container_width=True)

with tabs[3]:
    st.header("🍧 Sorbetti (costi)")
    melt = df_sel[['data'] + sorbetti_cols].melt('data', var_name='Gusto', value_name='Euro')
    st.plotly_chart(px.bar(melt, x='data', y='Euro', color='Gusto'), use_container_width=True)

with tabs[4]:
    st.header("🍚 Ingredienti per Categoria")
    categorie = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale'],
        'Topping': ['Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','Sale grosso'],
        'Salse': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    for nome, cols in categorie.items():
        st.subheader(nome)
        validi = [c for c in cols if c in df_dist_sel.columns]
        if validi:
            melt = df_dist_sel[['data'] + validi].melt('data', var_name='Ingrediente', value_name='Euro')
            st.plotly_chart(px.area(melt, x='data', y='Euro', color='Ingrediente'), use_container_width=True)

with tabs[5]:
    st.header("📊 Confronto Annuale")
    df['anno'] = df['data'].dt.year
    ann = df.groupby('anno').agg({
        'fatturato': 'sum',
        'totale_ingredienti': 'sum',
        'Dipendente': 'sum'
    }).reset_index()
    ann['% ingredienti'] = ann.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
    ann['% dipendenti'] = ann.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
    st.dataframe(ann.style.format({
        'fatturato': '€{:.2f}',
        'totale_ingredienti': '€{:.2f}',
        'Dipendente': '€{:.2f}',
        '% ingredienti': '{:.1f}%',
        '% dipendenti': '{:.1f}%'
    }))

with tabs[6]:
    st.header("⚠️ Giornate da monitorare")
    # critici['Attenzione'] = ""
    # critici.loc[critici['% ingredienti'] >= 25, 'Attenzione'] += "🧂 Ingredienti alti  "
   #  critici.loc[critici['% ingredienti'] < 25, 'Attenzione'] += "🧂 Ingredienti OK  "
    # critici.loc[critici['% dipendenti'] >= 20, 'Attenzione'] += "👥 Dipendenti alti  "
   #  critici.loc[critici['% dipendenti'] < 20, 'Attenzione'] += "👥 Dipendenti OK  "
   #  critici.loc[critici['fatturato'] <= 450, 'Attenzione'] += "📉 Fatturato basso"
   #  critici.loc[critici['fatturato'] > 450, 'Attenzione'] += "📉 Fatturato OK"

    # Definisci una funzione di stile
   #  def highlight_perfetto(row):
   #      if row['Attenzione'] == "":
   #          return ['background-color: #d4edda'] * len(row)  # verde chiaro
   #      else:
   #          return [''] * len(row)
    
   #  styled_df = critici[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1).style.apply(highlight_perfetto, axis=1)
   #  st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)
# Colonna Attenzione
    with tabs[6]:
    st.header("⚠️ Giornate da monitorare")

    # Costruzione colonna Attenzione
    critici['Attenzione'] = ""
    critici.loc[critici['% ingredienti'] >= 25, 'Attenzione'] += "🧂 Ingredienti alti  "
    critici.loc[critici['% ingredienti'] < 25, 'Attenzione'] += "🧂 Ingredienti OK  "
    critici.loc[critici['% dipendenti'] >= 20, 'Attenzione'] += "👥 Dipendenti alti  "
    critici.loc[critici['% dipendenti'] < 20, 'Attenzione'] += "👥 Dipendenti OK  "
    critici.loc[critici['fatturato'] <= 450, 'Attenzione'] += "📉 Fatturato basso"
    critici.loc[critici['fatturato'] > 450, 'Attenzione'] += "📉 Fatturato OK"

    # CSS SEPARATO
    st.markdown(
        """
        <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        .styled-table th, .styled-table td {
            padding: 6px 10px;
            border: 1px solid #ccc;
            text-align: left;
        }
        .styled-table .perfetto {
            background-color: #d4edda;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # HTML puro con classe
    table_html = """
    <table class="styled-table">
        <tr>
            <th>Data</th>
            <th>Fatturato</th>
            <th>% Ingredienti</th>
            <th>% Dipendenti</th>
            <th>Attenzione</th>
        </tr>
    """

    for _, row in critici.iterrows():
        is_perfect = "alti" not in row['Attenzione'] and "basso" not in row['Attenzione']
        row_class = "perfetto" if is_perfect else ""
        table_html += f"""
        <tr class="{row_class}">
            <td>{row['data']}</td>
            <td>{row['fatturato']}</td>
            <td>{row['% ingredienti']}</td>
            <td>{row['% dipendenti']}</td>
            <td>{row['Attenzione']}</td>
        </tr>
        """

    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)

    #st.dataframe(critici[['data', 'fatturato', '% ingredienti', '% dipendenti', 'Attenzione']].round(1))

with tabs[7]:
    st.header("ℹ️ Aiuto e Note")
    st.markdown("""
- **Ingredienti**: costi distribuiti tra due acquisti.
- **Extra**: vendite in euro.
- **Bibite e Sorbetti**: solo costi.
- **%**: medie giornaliere.
- **Confronto annuale**: su anno solare.
- **Soglie di attenzione**: % Ingredienti 25; % Dipendenti 20; Fatturato 450€.
""")

# --- ESPORTAZIONE ---
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
