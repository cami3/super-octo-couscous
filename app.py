# Pokè To Go! – Dashboard Operativa Completa per Arianna
# Coerente con il sito poketogo.it, con grafici, tabs, metriche e alert

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import date, timedelta

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
# df = df.dropna(subset=['data', 'fatturato'], how='any')  # elimina righe incomplete

for col in df.columns:
    if col != 'data':
        df[col] = pd.to_numeric(df[col], errors='coerce')

poke_cols = ['poke_reglular','poke_maxi','poke_baby','fruit_bowl', 'poke_veggy']
extra_cols = ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
sorbetti_pezzi_col = ['Sorbetti_venduti']
bibite_cols = ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
sorbetti_cols = ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
cost_cols = ['Dipendente']
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]



# Min e max da dati
min_date = df['data'].min().date()
max_date = df['data'].max().date()
today = max_date

# Preset disponibili
presets = {
    "Ultimi 7 giorni": (today - timedelta(days=6), today),
    "Ultimi 30 giorni": (today - timedelta(days=29), today),
    "Tutto il periodo": (min_date, max_date)
}

# Fasce annuali dinamiche
for year in sorted(df['data'].dt.year.unique()):
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    presets[f"{year} intero"] = (max(min_date, year_start), min(max_date, year_end))

# Inizializzazione solo alla prima esecuzione
if "date_range" not in st.session_state:
    st.session_state["date_range"] = [min_date, max_date]

# Selezione rapida (modifica lo stato solo se è cambiato)
preset_selection = st.radio("⏱️ Selezione rapida", options=list(presets.keys()), index=list(presets).index("Tutto il periodo"))
preset_start, preset_end = presets[preset_selection]

# Aggiorna lo stato solo se diverso dal precedente
if st.session_state["date_range"] != [preset_start, preset_end]:
    st.session_state["date_range"] = [preset_start, preset_end]

# Form con il valore sempre aggiornato da session_state
with st.form("date_form"):
    _ = st.date_input(
        "📅 Oppure scegli manualmente:",
        min_value=min_date,
        max_value=max_date,
        key="date_range"
    )
    submitted = st.form_submit_button("✅ Analizza periodo")

# Se non hai mai cliccato il bottone ma lo state è già pieno, prosegui comunque
if not submitted and st.session_state.get("analisi_avviata") is not True:
    st.stop()
else:
    st.session_state["analisi_avviata"] = True

# Estrai date dal session_state
start, end = pd.to_datetime(st.session_state["date_range"][0]), pd.to_datetime(st.session_state["date_range"][1])

# Info
durata = (end - start).days + 1
st.info(f"📆 Periodo selezionato: **{start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}** ({durata} giorni)")
if durata < 3:
    st.warning("⚠️ Periodo breve: potrebbero esserci pochi dati.")

# Periodi di confronto
prev_start = start.replace(year=start.year - 1)
prev_end = end.replace(year=end.year - 1)

# --- DISTRIBUZIONE COSTI CORRETTA (spezzata tra stagioni annuali) ---
df_dist = pd.DataFrame(index=df.index)
for ing in ingred_cols:
    s = df[['data', ing]].dropna()
    s = s[s[ing] > 0].sort_values('data')
    arr = pd.Series(0.0, index=df.index)

    # ▸ Tra acquisti nello stesso anno
    for i in range(len(s) - 1):
        a = s.iloc[i]['data']
        b = s.iloc[i+1]['data']
        if a.year == b.year:
            intervallo = (df['data'] >= a) & (df['data'] < b)
            giorni_utili = intervallo.sum()
            if giorni_utili > 0:
                arr[intervallo] += s.iloc[i][ing] / giorni_utili

    # ▸ Dopo ultimo acquisto (fino alla fine dell'anno in corso)
    if not s.empty:
        last_date = s.iloc[-1]['data']
        last_value = s.iloc[-1][ing]
        final_day = df['data'].max()

        # spalmatura solo nello stesso anno dell'acquisto
        if last_date.year == final_day.year:
            intervallo_finale = (df['data'] >= last_date) & (df['data'] <= final_day)
            giorni_utili_finali = intervallo_finale.sum()
            if giorni_utili_finali > 0:
                arr[intervallo_finale] += last_value / giorni_utili_finali

    df_dist[ing] = arr




def safe_pct(cost, rev):
    return cost/rev*100 if rev > 0 else 0

df['totale_ingredienti'] = df_dist.sum(axis=1)
df['% ingredienti'] = df.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
df['% dipendenti'] = df.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
df['poke_totali'] = df[poke_cols].sum(axis=1).fillna(0)

df['extra_totali'] = df[extra_cols].sum(axis=1)
df['bibite_sorbetti'] = df[bibite_cols + sorbetti_cols].sum(axis=1)

df['ingredienti_grezzi'] = df[ingred_cols].sum(axis=1)
df['% ingredienti grezzi'] = df.apply(lambda r: safe_pct(r['ingredienti_grezzi'], r['fatturato']), axis=1)


df_sel = df[(df['data'] >= start) & (df['data'] <= end)]
df_prev = df[(df['data'] >= prev_start) & (df['data'] <= prev_end)]
df_dist_with_date = df[['data']].join(df_dist)
df_dist_sel = df_dist_with_date[(df_dist_with_date['data'] >= start) & (df_dist_with_date['data'] <= end)]

df_sel['fatturato'] = df_sel['fatturato'].fillna(0)
df_sel['poke_totali'] = df_sel[poke_cols].sum(axis=1)

st.header("🥇 Top 10 ingredienti per spesa media giornaliera")
top_10 = df_dist_sel[ingred_cols].mean().sort_values(ascending=False).head(10)

top_10_df = top_10.reset_index()
top_10_df.columns = ['Ingrediente', 'Spesa Media Giornaliera (€)']
fig = px.bar(top_10_df, x='Ingrediente', y='Spesa Media Giornaliera (€)', text='Spesa Media Giornaliera (€)')
fig.update_traces(texttemplate='€ %{text:.2f}', textposition='outside')
fig.update_layout(title="🥇 Top 10 Ingredienti – Spesa Media Giornaliera", yaxis_title="€ al giorno")
st.plotly_chart(fig, use_container_width=True)

st.write("Somma ingredienti grezzi:", df[ingred_cols].sum().sum())
st.write("Somma ingredienti spalmati:", df_dist.sum().sum())
st.write("Somma spalmati in df_sel:", df_sel['totale_ingredienti'].sum())
st.write("Somma grezzi in df_sel:", df_sel['ingredienti_grezzi'].sum())


# --- KPI ---
st.header("📌 Riepilogo operativo")
col1, col2, col3, col4, col5, col6 = st.columns(6)
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

col6 = st.columns(6)[5]
ingredienti_grezzi = df_sel['ingredienti_grezzi'].sum()
col6.metric("Ingredienti Grezzi", f"€ {ingredienti_grezzi:,.2f}")


tot_poke = df_sel['poke_totali'].sum()
tot_extra = df_sel['extra_totali'].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Ricavo Medio per Poke", f"€ {fatturato / tot_poke:.2f}" if tot_poke > 0 else "N/A")
col2.metric("Extra per 10 Poke", f"{(tot_extra / tot_poke) * 10:.1f}" if tot_poke > 0 else "N/A")
col3.metric("Costo Medio Ingredienti per Poke", f"€ {ingredienti / tot_poke:.2f}" if tot_poke > 0 else "N/A")



costi_fissi = 300  # puoi aggiornarlo da una variabile laterale
ricavo_medio_poke = fatturato / tot_poke if tot_poke > 0 else 0

if ricavo_medio_poke > 0:
    poke_break_even = costi_fissi / ricavo_medio_poke
    st.metric("📈 Break-even Poke (stima)", f"{poke_break_even:.1f} poke")
else:
    st.metric("📈 Break-even Poke (stima)", "N/A")
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

df_sel['utile_giornaliero'] = df_sel['fatturato'] - df_sel['totale_ingredienti'] - df_sel['Dipendente'] - df_sel['bibite_sorbetti']
df_sel['margine_per_poke'] = df_sel.apply(
    lambda r: r['utile_giornaliero'] / r['poke_totali'] if r['poke_totali'] > 0 else None, axis=1
)

top_days = df_sel.sort_values('margine_per_poke', ascending=False).head(5)

st.subheader("💰 Giorni migliori per margine per poke")
st.dataframe(top_days[['data', 'margine_per_poke', 'fatturato', 'poke_totali']].round(2))

# --- TABS ---
tabs = st.tabs(["📈 Vendite", "🍱 Extra", "🥤 Bibite", "🍧 Sorbetti", "🍚 Ingredienti", "📊 Annuale", "⚠️ Giornate Critiche", "ℹ️ Aiuto", "📦 Rifornimenti"])

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
    
    st.subheader("🍧 Sorbetti venduti (in pezzi)")
    fig = px.line(df_sel, x='data', y='Sorbetti_venduti', markers=True)
    fig.update_layout(yaxis_title="Pezzi", title="📊 Quantità di Sorbetti venduti")
    st.plotly_chart(fig, use_container_width=True)

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


    st.header("🔥 % Ingredienti e Dipendenti")
    st.info('Quanto incidono, in media quotidiana, i costi distribuiti degli ingredienti sul fatturato di quel giorno.')
    import plotly.graph_objects as go
    melt = df_sel[['data', '% ingredienti', '% dipendenti']].melt('data', var_name='Tipo', value_name='Percentuale')
    fig = px.line(melt, x='data', y='Percentuale', color='Tipo', markers=True)
    fig.update_layout(title="📊 Andamento % Ingredienti e Dipendenti")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 Confronto % ingredienti grezzi")
    
    show_raw = st.checkbox("Mostra anche % Ingredienti Grezzi")
    
    if show_raw:
        melt = df_sel[['data', '% ingredienti', '% ingredienti grezzi']].melt('data', var_name='Tipo', value_name='Percentuale')
        fig = px.line(melt, x='data', y='Percentuale', color='Tipo', markers=True)
        fig.update_layout(title="📊 % Ingredienti Distribuiti vs Grezzi", yaxis_title="% sul fatturato")
        st.plotly_chart(fig, use_container_width=True)

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
    if df_sel.empty:
        st.warning("⚠️ Nessun dato nel periodo selezionato.")
        st.stop()

    st.header("⚠️ Giornate da monitorare")
    critici['Attenzione'] = ""
    critici.loc[critici['% ingredienti'] >= 25, 'Attenzione'] += "🧂 Ingredienti alti  "
    critici.loc[critici['% dipendenti'] >= 20, 'Attenzione'] += "👥 Dipendenti alti  "
    critici.loc[critici['fatturato'] <= 450, 'Attenzione'] += "📉 Fatturato basso"
    
    st.markdown("""
    <style>
    .green-row td {
        background-color: #d4edda !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    critici['Perfetto'] = (critici['Attenzione'] == "")
    table_html = """
    <table>
    <tr><th>Data</th><th>Fatturato</th><th>% Ingredienti</th><th>% Dipendenti</th><th>Attenzione</th></tr>
    """
    
    for _, r in critici.iterrows():
        cls = 'green-row' if r['Perfetto'] else ''
        table_html += f"<tr class='{cls}'><td>{r['data'].date()}</td><td>{r['fatturato']:.2f}</td><td>{r['% ingredienti']:.1f}</td><td>{r['% dipendenti']:.1f}</td><td>{r['Attenzione']}</td></tr>"
    
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
- **costi_fissi = 300**
""")

with tabs[8]:
    st.header("📦 Rifornimenti Effettivi")

    # --- Categorie ingredienti ---
    categorie = {
        'Tutti': ingred_cols,
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale'],
        'Topping': ['Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','Sale grosso'],
        'Salse': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }

    # --- Selezione categoria ---
    cat_keys = list(categorie.keys())
    default_index = cat_keys.index(st.session_state.get("cat_sel", "Tutti"))
    cat_sel = st.selectbox("🧂 Filtra per categoria", cat_keys, index=default_index, key="cat_sel")

    col_sel = categorie[cat_sel]
    df_rif = df[['data'] + col_sel].copy()
    df_rif = df_rif[(df_rif[col_sel] > 0).any(axis=1)]

    # --- Formato long
    melted = df_rif.melt(id_vars='data', var_name='Ingrediente', value_name='Spesa (€)')
    melted = melted[melted['Spesa (€)'] > 0]

    if melted.empty:
        st.warning("Nessun rifornimento registrato per questa categoria.")
        st.stop()

    # --- 📊 Grafico barre impilate
    st.subheader("📊 Spese per Ingrediente nel tempo")
    fig_bar = px.bar(melted, x='data', y='Spesa (€)', color='Ingrediente', barmode='stack')
    fig_bar.update_layout(xaxis_title="Data", yaxis_title="€ spesi", title="📦 Rifornimenti")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 📈 Spesa cumulata
    st.subheader("📈 Andamento spesa cumulata")
    daily = melted.groupby('data')['Spesa (€)'].sum().reset_index()
    daily['Spesa Cumulata (€)'] = daily['Spesa (€)'].cumsum()
    fig_line = px.line(daily, x='data', y='Spesa Cumulata (€)', markers=True)
    fig_line.update_layout(title="📈 Spesa Cumulata", yaxis_title="€ cumulati")
    st.plotly_chart(fig_line, use_container_width=True)

    # --- ⚠ Avvisi su spese alte
    melted['Avviso'] = melted['Spesa (€)'].apply(lambda x: "⚠ Alto" if x > 100 else "")

    # --- 📋 Tabella giornaliera
    st.subheader("📋 Dettaglio Giornaliero")
    st.dataframe(melted.sort_values(['data', 'Ingrediente']), use_container_width=True)

    # --- 🔢 Confronto categorie (extra)
    st.subheader("🔢 Spesa Totale per Categoria")
    cat_sums = {cat: df[cols].sum().sum() for cat, cols in categorie.items() if cat != 'Tutti'}
    df_cat_sums = pd.DataFrame(list(cat_sums.items()), columns=['Categoria', 'Spesa Totale (€)'])
    fig_pie = px.pie(df_cat_sums, values='Spesa Totale (€)', names='Categoria', title="📉 Distribuzione Spesa per Categoria")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.caption("Visualizzazione 100% data-driven basata su acquisti reali registrati nel file CSV.")


# --- ESPORTAZIONE ---
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
