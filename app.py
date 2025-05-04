[CODICE ESISTENTE FINO A st.dataframe(...)]

# Tabs
st.subheader("📋 Tabella giornaliera")
st.dataframe(df_sel[['data','fatturato','totale_ingredienti','% ingredienti','Dipendente','% dipendenti','poke_totali','extra_totali'] + poke_cols + extra_cols])

tabs = st.tabs(["📈 Vendite","🍱 Ingredienti","🥤 Bevande & Sorbetti","📊 Confronto Annuale","ℹ️ Aiuto"])

with tabs[0]:
    st.subheader("Vendite (pezzi)")
    melt_poke = df_sel[['data']+poke_cols].melt('data', var_name='Tipo', value_name='Pezzi')
    st.plotly_chart(px.line(melt_poke, x='data', y='Pezzi', color='Tipo', markers=True), use_container_width=True)
    st.subheader("Extra venduti (€)")
    melt_extra = df_sel[['data']+extra_cols].melt('data', var_name='Tipo', value_name='Euro')
    st.plotly_chart(px.bar(melt_extra, x='data', y='Euro', color='Tipo'), use_container_width=True)

with tabs[1]:
    st.subheader("Costi Ingredienti per Categoria (euro)")
    categorie = {
        'Proteine': ['salmone','tonno','Tonno Saku','Polpo','Gamberetti','Pollo Nuggets','Pollo fette','Feta','Formaggio spalmabile','Tofu','Uova'],
        'Verdure': ['edamame','ceci','mais','carote','cetrioli','pomodori','Cavolo viola','zucchine','cipolle','Goma wakame'],
        'Frutta': ['Avocado','Avo Hass','mango','Lime','uva','Mele','melone','Kiwi','Ananas','Anguria'],
        'Base': ['iceberg','riso_sushi','riso_nero','Riso integrale','Sale grosso'],
        'Granelle e Topping': ['Sesamo nero','Sesamo bianco','Mandorle','nocciole','Cipolle croccanti','Pistacchio'],
        'Salse e Condimenti': ['Salsa soya','Olio Evo','Teriyaki','Maionese','yogurt','Ponzu','Sriracha']
    }
    df_dist['data'] = df['data']
    df_dist_sel = df_dist[(df_dist['data'] >= start) & (df_dist['data'] <= end)]
    for nome, cols in categorie.items():
        st.markdown(f"**{nome}**")
        validi = [col for col in cols if col in df_dist_sel.columns]
        if validi:
            melted = df_dist_sel[['data'] + validi].melt(id_vars='data', var_name='Ingrediente', value_name='Euro')
            st.plotly_chart(px.area(melted, x='data', y='Euro', color='Ingrediente'), use_container_width=True)

with tabs[2]:
    st.subheader("Bibite & Sorbetti (approvvigionamento €)")
    melt_bs = df_sel[['data']+bibite_cols+sorbetti_cols].melt('data', var_name='Prodotto', value_name='Euro')
    st.plotly_chart(px.bar(melt_bs, x='data', y='Euro', color='Prodotto'), use_container_width=True)

with tabs[3]:
    st.subheader("Confronto Annuale – Costi e Ricavi")
    df['anno'] = df['data'].dt.year
    ann = df.groupby('anno').agg({'fatturato': 'sum', 'totale_ingredienti': 'sum', 'Dipendente': 'sum'}).reset_index()
    ann['% ingredienti'] = ann.apply(lambda r: safe_pct(r['totale_ingredienti'], r['fatturato']), axis=1)
    ann['% dipendenti'] = ann.apply(lambda r: safe_pct(r['Dipendente'], r['fatturato']), axis=1)
    st.dataframe(ann.style.format({
        'fatturato': '€{:.2f}', 'totale_ingredienti': '€{:.2f}', 'Dipendente': '€{:.2f}',
        '% ingredienti': '{:.1f}%', '% dipendenti': '{:.1f}%'
    }))

with tabs[4]:
    st.header("ℹ️ Note Metodi")
    st.markdown("""
- **Poke**: quantità in pezzi
- **Extra**: vendite in euro
- **Bibite/Sorbetti**: solo costo, non vendite
- **Ingredienti**: costo distribuito tra approvvigionamenti
- % calcolate solo se fatturato > 0
- Delta confrontano con intervallo precedente (default: stesso periodo anno precedente)
- Percentuali = media giornaliera nel periodo
- Categorie ingredienti includono granelle/topping
""")

csv = df_sel.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Analisi CSV", data=csv, file_name="analisi_poketogo.csv", mime='text/csv')
