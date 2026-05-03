# Pokè To Go! – Dashboard Operativa Completa per Arianna
# Coerente con il sito poketogo.it, con grafici, tabs, metriche e alert

import io
import random
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import date, timedelta
import plotly.graph_objects as go

@st.cache_data
def genera_csv_esempio():
    rng = random.Random(42)

    _all_ingred = [
        'salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette',
        'Feta','Formaggio spalmabile','Tofu','Uova',
        'edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame',
        'Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria',
        'iceberg','riso_sushi','riso_nero','Riso integrale',
        'Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','Sale grosso',
        'Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha',
    ]
    _ing_ranges = {
        'salmone':(80,200),'tonno':(60,150),'Tonno Saku':(40,100),'Polpo':(50,120),
        'Gamberetti':(40,90),'Pollo Nuggets':(20,50),'Pollo fette':(20,50),
        'Feta':(15,40),'Formaggio spalmabile':(10,30),'Tofu':(10,25),'Uova':(5,15),
        'edamame':(15,35),'ceci':(5,15),'mais':(5,12),'carote':(3,8),
        'cetrioli':(4,10),'pomodori':(5,15),'Cavolo viola':(4,10),
        'zucchine':(4,10),'cipolle':(3,8),'Goma wakame':(15,35),
        'Avocado':(20,60),'Avo Hass':(20,60),'mango':(15,40),'Lime':(5,15),
        'uva':(5,15),'Mele':(5,12),'melone':(8,20),'Kiwi':(5,15),'Ananas':(8,20),'Anguria':(10,30),
        'iceberg':(8,20),'riso_sushi':(20,50),'riso_nero':(15,40),'Riso integrale':(10,25),
        'Sesamo nero':(5,15),'Sesamo bianco':(5,15),'Mandorle':(10,25),'nocciole':(10,25),
        'Cipolle croccanti':(8,20),'Pistacchio':(15,35),'Sale grosso':(2,6),
        'Salsa soya':(10,30),'Olio Evo':(15,40),'Teriyaki':(15,35),
        'Maionese':(8,20),'yogurt':(5,15),'Ponzu':(10,25),'Sriracha':(8,20),
    }
    _ing_freq = {}
    for ing in _all_ingred:
        if ing in ('salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette'):
            _ing_freq[ing] = (2, 4)
        elif ing in ('iceberg','riso_sushi','riso_nero','Riso integrale','Avocado','Avo Hass','mango','Anguria','melone'):
            _ing_freq[ing] = (3, 5)
        else:
            _ing_freq[ing] = (5, 9)

    start = date(2024, 6, 1)
    end   = date(2024, 9, 30)
    days  = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    next_restock = {ing: 0 for ing in _all_ingred}
    rows = []

    for i, day in enumerate(days):
        m, dom, dow = day.month, day.day, day.weekday()

        if m == 6:
            base = rng.uniform(350, 700)
        elif m == 7 and dom <= 14:
            base = rng.uniform(600, 1000)
        elif m == 7:
            base = rng.uniform(800, 1300)
        elif m == 8 and dom <= 20:
            base = rng.uniform(900, 1400)
        elif m == 8:
            base = rng.uniform(700, 1100)
        elif m == 9 and dom <= 15:
            base = rng.uniform(500, 800)
        else:
            base = rng.uniform(300, 600)

        if dow >= 5:
            base *= rng.uniform(1.15, 1.25)
        fatturato = round(base, 2)

        tot_poke  = max(1, int(fatturato / rng.uniform(11, 15)))
        poke_reg  = max(0, int(tot_poke * rng.uniform(0.50, 0.62)))
        poke_maxi = max(0, int(tot_poke * rng.uniform(0.15, 0.25)))
        poke_baby = max(0, int(tot_poke * rng.uniform(0.07, 0.13)))
        fruit_b   = max(0, int(tot_poke * rng.uniform(0.03, 0.07)))
        poke_veg  = max(0, tot_poke - poke_reg - poke_maxi - poke_baby - fruit_b)

        dipendente = float(rng.choice([70, 75, 80, 85, 90]))

        avo_v  = round(poke_reg * rng.uniform(0.25, 0.40) * 1.5, 2)
        feta_v = round(poke_reg * rng.uniform(0.10, 0.20) * 1.5, 2)
        phil_v = round(poke_reg * rng.uniform(0.15, 0.25) * 1.5, 2)
        goma_v = round(poke_reg * rng.uniform(0.20, 0.35) * 1.5, 2)
        sorb_v = max(0, int(tot_poke * rng.uniform(0.20, 0.50)))

        sc = tot_poke / 60.0
        bib = {
            'Acqua nat':      round(rng.uniform(0.8, 1.5) * sc * 10, 2),
            'Acqua gas':      round(rng.uniform(0.5, 1.2) * sc * 10, 2),
            'Coca cola':      round(rng.uniform(1.0, 2.0) * sc * 10, 2),
            'Coca zero':      round(rng.uniform(0.5, 1.5) * sc * 10, 2),
            'corona':         round(rng.uniform(0.8, 1.8) * sc * 10, 2),
            'ichnusa':        round(rng.uniform(0.8, 1.5) * sc * 10, 2),
            'fanta':          round(rng.uniform(0.4, 0.9) * sc * 10, 2),
            'Estathe limone': round(rng.uniform(0.4, 0.8) * sc * 10, 2),
            'Estathe pesca':  round(rng.uniform(0.3, 0.7) * sc * 10, 2),
        }
        sorb_costi = {
            'Sorbetto limone': round(rng.uniform(1.0, 2.5) * sc * 8, 2),
            'Sorbetto mela':   round(rng.uniform(0.8, 2.0) * sc * 8, 2),
            'Sorbetto mango':  round(rng.uniform(0.9, 2.2) * sc * 8, 2),
        }

        ing_vals = {}
        for ing in _all_ingred:
            if i >= next_restock[ing]:
                lo, hi = _ing_ranges[ing]
                ing_vals[ing] = round(rng.uniform(lo, hi), 2)
                fmin, fmax = _ing_freq[ing]
                next_restock[ing] = i + rng.randint(fmin, fmax)
            else:
                ing_vals[ing] = ''

        rows.append({
            'data': day.strftime('%d/%m/%Y'), 'fatturato': fatturato, 'Dipendente': dipendente,
            'poke_reglular': poke_reg, 'poke_maxi': poke_maxi, 'poke_baby': poke_baby,
            'fruit_bowl': fruit_b, 'poke_veggy': poke_veg,
            'Avocado_venduto': avo_v, 'Feta_venduto': feta_v,
            'Philad_venduto': phil_v, 'Gomawak_venduto': goma_v,
            'Sorbetti_venduti': sorb_v,
            **bib, **sorb_costi, **ing_vals,
        })

    col_order = (
        ['data','fatturato','Dipendente']
        + ['poke_reglular','poke_maxi','poke_baby','fruit_bowl','poke_veggy']
        + ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
        + ['Sorbetti_venduti']
        + list(bib.keys()) + list(sorb_costi.keys())
        + _all_ingred
    )
    df_fake = pd.DataFrame(rows)[col_order]
    buf = io.StringIO()
    df_fake.to_csv(buf, sep=';', index=False)
    return buf.getvalue().encode('utf-8')


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

# --- TEMPLATE PREVIEW ---
with st.expander("📋 Come deve essere fatto il file CSV? (clicca per vedere)", expanded=not uploaded):
    st.markdown("""
### Formato del file CSV

- Separatore: **punto e virgola** `;`
- Date nel formato **gg/mm/aaaa** (es. `01/07/2024`)
- Decimali con la **virgola** o il **punto** (es. `12,50` o `12.50`)
- Celle **vuote** = giorno chiuso o ingrediente non rifornito quel giorno
- **Non usare 0** per i giorni di chiusura — lasciare la cella vuota

---

#### Gruppi di colonne

| Gruppo | Colonne | Compilazione | Cosa inserire |
|---|---|---|---|
| **Data** | `data` | Ogni giorno aperto | Data nel formato gg/mm/aaaa |
| **Ricavo** | `fatturato` | Ogni giorno aperto | Totale incassato in € |
| **Personale** | `Dipendente` | Ogni giorno aperto | Costo dipendente in € |
| **Poke venduti** | `poke_reglular`, `poke_maxi`, `poke_baby`, `fruit_bowl`, `poke_veggy` | Ogni giorno aperto | Numero di pezzi venduti |
| **Extra venduti** | `Avocado_venduto`, `Feta_venduto`, `Philad_venduto`, `Gomawak_venduto` | Ogni giorno aperto | € incassati per ogni extra |
| **Sorbetti venduti** | `Sorbetti_venduti` | Ogni giorno aperto | Numero di pezzi venduti |
| **Bibite (costo)** | `Acqua nat`, `Acqua gas`, `Coca cola`, `Coca zero`, `corona`, `ichnusa`, `fanta`, `Estathe limone`, `Estathe pesca` | Ogni giorno aperto | € spesi per ogni bibita |
| **Sorbetti (costo)** | `Sorbetto limone`, `Sorbetto mela`, `Sorbetto mango` | Ogni giorno aperto | € spesi per ogni gusto |
| **Ingredienti** | salmone, tonno, Avocado, riso_sushi, … (vedi lista completa) | Solo nei giorni di **rifornimento** | € spesi per quell'acquisto |

> 💡 Gli ingredienti vengono automaticamente **distribuiti** tra un rifornimento e il successivo.
> Lascia la cella vuota nei giorni in cui non hai comprato quell'ingrediente.

---
""")

    all_cols = (
        ['data', 'fatturato', 'Dipendente']
        + ['poke_reglular','poke_maxi','poke_baby','fruit_bowl','poke_veggy']
        + ['Avocado_venduto','Feta_venduto','Philad_venduto','Gomawak_venduto']
        + ['Sorbetti_venduti']
        + ['Acqua nat','Acqua gas','Coca cola','Coca zero','corona','ichnusa','fanta','Estathe limone','Estathe pesca']
        + ['Sorbetto limone','Sorbetto mela','Sorbetto mango']
        + ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova']
        + ['edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame']
        + ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria']
        + ['iceberg','riso_sushi','riso_nero','Riso integrale']
        + ['Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio','Sale grosso']
        + ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    )

    esempio = {
        'data':             ['01/07/2024',  '02/07/2024',  '03/07/2024'],
        'fatturato':        [850,            920,            ''],
        'Dipendente':       [80,             80,             ''],
        'poke_reglular':    [25,             28,             ''],
        'poke_maxi':        [12,             14,             ''],
        'poke_baby':        [8,              7,              ''],
        'fruit_bowl':       [3,              4,              ''],
        'poke_veggy':       [4,              5,              ''],
        'Avocado_venduto':  [5,              6,              ''],
        'Feta_venduto':     [2,              3,              ''],
        'Philad_venduto':   [3,              2,              ''],
        'Gomawak_venduto':  [1,              2,              ''],
        'Sorbetti_venduti': [15,             18,             ''],
        'Acqua nat':        [1.2,            1.6,            ''],
        'Coca cola':        [2.5,            3.0,            ''],
        'Sorbetto limone':  [4.5,            '',             ''],
        'salmone':          [120,            '',             ''],
        'tonno':            [80,             '',             ''],
        'riso_sushi':       [18,             '',             ''],
        'Avocado':          [15,             '',             ''],
    }
    df_template = pd.DataFrame(esempio)

    st.markdown("**Esempio (solo le colonne principali — le altre seguono lo stesso schema):**")
    st.dataframe(df_template, use_container_width=True, hide_index=True)
    st.caption("Le righe con celle vuote indicano giorni chiusi o ingredienti non riforniti quel giorno.")

    template_csv = ';'.join(all_cols) + '\n'
    template_csv += ';'.join(['gg/mm/aaaa'] + [''] * (len(all_cols) - 1)) + '\n'
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "⬇️ Scarica template CSV vuoto",
            data=template_csv.encode('utf-8'),
            file_name="template_poketogo.csv",
            mime="text/csv",
            help="Apri con Excel, compila e salva come CSV separato da punto e virgola",
            use_container_width=True,
        )
    with col_b:
        st.download_button(
            "🎲 Scarica dati di esempio (stagione estiva 2024 – dati finti)",
            data=genera_csv_esempio(),
            file_name="esempio_poketogo_2024.csv",
            mime="text/csv",
            help="Dati inventati realistici: giugno–settembre 2024 con picchi ad agosto",
            use_container_width=True,
        )

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
exclude = poke_cols + extra_cols + bibite_cols + sorbetti_cols + sorbetti_pezzi_col + cost_cols + ['data','fatturato']
ingred_cols = [c for c in df.columns if c not in exclude]

# --- 🧾 CONTROLLO QUALITÀ DEL FILE CARICATO ---
with st.expander("🦾 Controllo qualità del file caricato", expanded=True):
    campi_critici = ['fatturato', 'Dipendente'] + poke_cols + extra_cols
    st.markdown("""
    👀 Questo controllo ti aiuta a capire se ci sono **dimenticanze, errori o ambiguità** nella raccolta dati giornaliera. Usa **Excel** per filtrare e correggere. Se un giorno il negozio era **chiuso**, lascia pure le celle **vuote**.
    """)

    # --- 1. CELLE VUOTE ---
    nan_mask = df[campi_critici].isna()
    for col in campi_critici:
        nan_dates = df['data'][nan_mask[col]].dt.strftime("%d/%m/%Y").tolist()
        if nan_dates:
            st.warning(f"⚠️ **{col}** ha {len(nan_dates)} giorni vuoti → {', '.join(nan_dates[:5])}...")

    # --- 2. ZERI ESPLICITI (es. chiusure compilate manualmente) ---
    zero_mask = (df[campi_critici] == 0)
    for col in campi_critici:
        zero_dates = df['data'][zero_mask[col]].dt.strftime("%d/%m/%Y").tolist()
        if zero_dates:
            st.info(f"ℹ️ **{col} = 0** in {len(zero_dates)} giorni → {', '.join(zero_dates[:5])}...")

    # --- 3. FATTURATO > 0 MA NESSUNA VENDITA ---
    df['vendite_totali'] = df[poke_cols + extra_cols].sum(axis=1)
    anom_fatt = df[(df['fatturato'] > 0) & (df['vendite_totali'] == 0)]
    if not anom_fatt.empty:
        st.error(f"💸 **Fatturato > 0 ma nessuna vendita registrata** in {len(anom_fatt)} giorni → {', '.join(anom_fatt['data'].dt.strftime('%d/%m/%Y').tolist()[:5])}...")

    # --- 4. VENDITE > 0 MA FATTURATO = 0 ---
    anom_vend = df[(df['fatturato'] == 0) & (df['vendite_totali'] > 0)]
    if not anom_vend.empty:
        st.warning(f"📜 **Vendite > 0 ma fatturato = 0** in {len(anom_vend)} giorni → {', '.join(anom_vend['data'].dt.strftime('%d/%m/%Y').tolist()[:5])}...")

    # --- 5. NESSUN POKE VENDUTO ---
    no_poke = df[df[poke_cols].sum(axis=1) == 0]
    if not no_poke.empty:
        st.info(f"🍱 Nessun poke venduto in {len(no_poke)} giorni → {', '.join(no_poke['data'].dt.strftime('%d/%m/%Y').tolist()[:5])}...")

    # --- 6. DIPENDENTE = 0 ---
    if 'Dipendente' in df.columns:
        dip_0 = df[df['Dipendente'].fillna(0) == 0]
        if not dip_0.empty:
            st.info(f"👥 Costo **Dipendente = 0** in {len(dip_0)} giorni → {', '.join(dip_0['data'].dt.strftime('%d/%m/%Y').tolist()[:5])}...")

    # --- 7. INGREDIENTI A 0 (da evitare) ---
    ingr_zero = df[ingred_cols].fillna(0).apply(lambda col: (col == 0).sum())
    ingr_zero = ingr_zero[ingr_zero > 0]
    if not ingr_zero.empty:
        st.warning("🧂 Ingredienti con valore 0 rilevato (meglio lasciarli vuoti se non riforniti):")
        for col, n in ingr_zero.items():
            st.markdown(f"- {col}: {n} righe")
    else:
        st.success("✅ Nessun ingrediente impostato a 0: ottimo!")

    st.markdown("""
    ✏️ **Suggerimenti Excel:**
    - Usa `Filtro` → `Celle Vuote` per completare solo i giorni di apertura.
    - Filtra `=0` per controllare giornate compilate a mano.
    - Se vendite = 0 e anche fatturato = 0, è possibile che fosse una chiusura.
    """)

# Giornate originali presenti nel CSV (cioè negozio realmente aperto)
date_originali = set(df['data'])



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
# --- DISTRIBUZIONE COSTI CORRETTA (includendo il giorno di acquisto e senza attraversare stagioni annuali) ---
df_dist = pd.DataFrame(index=df.index)

for ing in ingred_cols:
    s = df[['data', ing]].dropna()
    s = s[s[ing] > 0].sort_values('data')
    arr = pd.Series(0.0, index=df.index)

    for i in range(len(s)):
        a = s.iloc[i]['data']
        valore = s.iloc[i][ing]

        if i < len(s) - 1:
            b = s.iloc[i+1]['data']

            # ❗ Spalma solo se nello stesso anno
            if a.year == b.year:
                intervallo = (df['data'] >= a) & (df['data'] < b)
            else:
                fine_anno = pd.Timestamp(year=a.year, month=12, day=31)
                intervallo = (df['data'] >= a) & (df['data'] <= fine_anno)
        else:
            # Ultimo acquisto: spalma fino a fine anno
            fine_anno = pd.Timestamp(year=a.year, month=12, day=31)
            intervallo = (df['data'] >= a) & (df['data'] <= fine_anno)

        giorni_utili = intervallo.sum()
        if giorni_utili > 0:
            arr[intervallo] += valore / giorni_utili

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


df_sel = df[(df['data'] >= start) & (df['data'] <= end)].copy()
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


# --- KPI ---
st.header("📌 Riepilogo operativo")
col1, col2, col3, col4 = st.columns(4)
col5, col6, col7, col8 = st.columns(4)
fatturato = df_sel['fatturato'].sum()
ingredienti = df_sel['totale_ingredienti'].sum()
dipendenti = df_sel['Dipendente'].sum()
bibite_sorbetti = df_sel['bibite_sorbetti'].sum()
# Inizializza costi fissi a 0 per tutti i giorni visibili nel filtro utente
df_sel['costi_fissi'] = 0

# Applica 300€ solo ai giorni presenti nel CSV originale
df_sel.loc[df_sel['data'].isin(date_originali), 'costi_fissi'] = 166
costi_fissi_sel = df_sel['costi_fissi'].sum()

utile = fatturato - ingredienti - dipendenti - bibite_sorbetti
col1.metric("Fatturato", f"€ {fatturato:,.2f}")
col2.metric("Ingredienti", f"€ {ingredienti:,.2f}")
col3.metric("Dipendenti", f"€ {dipendenti:,.2f}")
col4.metric("Bibite/Sorbetti", f"€ {bibite_sorbetti:,.2f}")
col5.metric("Utile stimato", f"€ {utile:,.2f}")
utile_netto = fatturato - ingredienti - dipendenti - bibite_sorbetti - costi_fissi_sel

ingredienti_grezzi = df_sel['ingredienti_grezzi'].sum()
col7.metric("Ingredienti Grezzi", f"€ {ingredienti_grezzi:,.2f}")
col6.metric("Utile Netto Stimato", f"€ {utile_netto:,.2f}")
col8.metric("Costi Fissi Totali", f"€ {costi_fissi_sel:,.2f}")

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
critici = df_sel[(df_sel['% ingredienti'] > 25) | (df_sel['% dipendenti'] > 25) | (df_sel['fatturato'] < 360)]
perc = len(critici) / giorni * 100 if giorni > 0 else 0
solo1 = critici[((critici['% ingredienti'] > 25).astype(int) + 
                 (critici['% dipendenti'] > 25).astype(int) + 
                 (critici['fatturato'] < 360).astype(int)) == 1]
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

    # Grafico utile giornaliero
    fig = go.Figure(go.Scatter(
        x=df_sel['data'], y=df_sel['utile_giornaliero'],
        mode='lines+markers', name='Utile Giornaliero'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Soglia zero", annotation_position="bottom right")
    fig.update_layout(title='Utile Giornaliero', xaxis_title='Data', yaxis_title='Utile (€)', hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
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
    critici.loc[critici['% dipendenti'] >= 25, 'Attenzione'] += "👥 Dipendenti alti  "
    critici.loc[critici['fatturato'] <= 360, 'Attenzione'] += "📉 Fatturato basso"
    
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
- **Soglie di attenzione**: % Ingredienti 25; % Dipendenti 25; Fatturato 360€.
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

    col_sel = [c for c in categorie[cat_sel] if c in df_sel.columns]
    df_rif = df_sel[['data'] + col_sel].copy()
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
    cat_sums = {cat: df_sel[[c for c in cols if c in df_sel.columns]].sum().sum() for cat, cols in categorie.items() if cat != 'Tutti'}
    df_cat_sums = pd.DataFrame(list(cat_sums.items()), columns=['Categoria', 'Spesa Totale (€)'])
    fig_pie = px.pie(df_cat_sums, values='Spesa Totale (€)', names='Categoria', title="📉 Distribuzione Spesa per Categoria")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.caption("Visualizzazione 100% data-driven basata su acquisti reali registrati nel file CSV.")


# --- ESPORTAZIONE ---
csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
