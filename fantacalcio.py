"quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if not st.session_state.quotazioni_2025_26.empty else [],
        "crediti_iniziali": st.session_state.crediti_iniziali,
        "wizard_completato": st.session_state.wizard_completato
    }
    json_bytes = json.dumps(save_data, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("⬇️ Esporta JSON", json_bytes, f"fanta_manager_{datetime.now().strftime('%Y%m%d')}.json", "application/json", use_container_width=True)

    uploaded_file = st.file_uploader("📂 Importa JSON", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.squadre = data.get("squadre", {})
            st.session_state.storico_mercato = data.get("storico_mercato", [])
            st.session_state.watchlist = data.get("watchlist", [])
            st.session_state.prestiti = data.get("prestiti", [])
            st.session_state.contratti = data.get("contratti", {})
            if "nomi_squadre" in data:
                st.session_state.nomi_squadre = data["nomi_squadre"]
            db = data.get("giocatori_db", [])
            st.session_state.giocatori_db = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
            if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
                st.session_state.giocatori_db["Prezzo_Consigliato"] = None
            stats = data.get("stats_storiche", [])
            st.session_state.stats_storiche = pd.DataFrame(stats) if stats else pd.DataFrame()
            st.session_state.stats_per_stagione = {k: pd.DataFrame(v) for k, v in data.get("stats_per_stagione", {}).items()}
            q25 = data.get("quotazioni_2025_26", [])
            st.session_state.quotazioni_2025_26 = pd.DataFrame(q25) if q25 else pd.DataFrame()
            st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
            st.session_state.wizard_completato = data.get("wizard_completato", True)
            invalidate_cache()
            save_state()
            st.success("✅ Importazione riuscita!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Errore nell'importazione: {e}")

# ============================================================
# MAIN INTERFACE & NAVIGATION
# ============================================================
if check_wizard_needed():
    render_wizard()
    st.stop()

tabs = st.tabs([
    "📋 Listone & Prezzi",
    "🛒 Mercato & Asta",
    "👥 Rose",
    "📈 Statistiche Storiche",
    "⚔️ Testa a Testa",
    "🔮 Simulatore Formazione",
    "🏆 Analisi & Report",
    "⚡ Dashboard Avanzata"
])

# ============================================================
# TAB 1: LISTONE & PREZZI
# ============================================================
with tabs[0]:
    st.header("📋 Listone Giocatori & Calcolo Prezzi AI")
    st.markdown("Gestisci il listone ufficiale, filtra per ruolo o fascia, e calcola i prezzi consigliati basati su intelligenza algoritmica e storico.")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Cerca giocatore", placeholder="Nome o squadra Serie A...", key="search_listone")
    with col2:
        filtro_ruolo = st.selectbox("Ruolo", ["Tutti", "P", "D", "C", "A"], key="filtro_ruolo_listone")
    with col3:
        filtro_fascia = st.selectbox("Fascia", ["Tutte", "top", "consigliato", "scommessa"], key="filtro_fascia_listone")
    with col4:
        filtro_prop = st.selectbox("Stato", ["Tutti", "Svincolati", "In Rosa"], key="filtro_prop_listone")

    df_db = st.session_state.giocatori_db.copy()

    # Arricchisci con stats 2026-27 se presenti
    df_db = arricchisci_con_stats_2627(df_db)

    if search_query:
        df_db = df_db[df_db["Nome"].str.lower().str.contains(search_query.lower()) | df_db["Squadra_SerieA"].str.lower().str.contains(search_query.lower())]
    if filtro_ruolo != "Tutti":
        df_db = df_db[df_db["Ruolo"] == filtro_ruolo]
    if filtro_fascia != "Tutte":
        df_db = df_db[df_db["Consiglio"] == filtro_fascia]

    idx_map = get_player_index()
    df_db["Proprietario"] = df_db["Nome"].apply(lambda x: idx_map.get(x.lower(), "Svincolato"))

    if filtro_prop == "Svincolati":
        df_db = df_db[df_db["Proprietario"] == "Svincolato"]
    elif filtro_prop == "In Rosa":
        df_db = df_db[df_db["Proprietario"] != "Svincolato"]

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🤖 Calcola Prezzi Consigliati (Tutti)", use_container_width=True):
            StateManager.snapshot()
            stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
            for i, row in df_db.iterrows():
                p, _ = calcola_prezzo_consigliato(row.to_dict(), stats_df)
                df_db.at[i, "Prezzo_Consigliato"] = p
            st.session_state.giocatori_db = df_db.copy()
            save_state()
            st.success("✅ Prezzi consigliati calcolati per tutti i giocatori filtrati!")
            st.rerun()
    with col_btn2:
        if st.button("⚡ Classifica Fasce Automatica", use_container_width=True, help="Classifica in Top/Consigliato/Scommessa basandosi sullo storico stagionale"):
            StateManager.snapshot()
            applica_fasce_automatiche()
            st.rerun()

    st.markdown(f"**Giocatori visualizzati:** {len(df_db)}")

    # Visualizzazione a griglia flip card (3 colonne)
    cols = st.resize_columns(3) if hasattr(st, "resize_columns") else st.columns(3)
    for idx, row in df_db.reset_index(drop=True).iterrows():
        col_idx = idx % 3
        with [col1, col2, col3][col_idx] if 'col1' in locals() and False else st.columns(3)[col_idx]:
            # Aggiungi indici per la flip card
            row_dict = row.to_dict()
            row_dict["Indice_Affare"] = round(float(row_dict.get("FantaMedia", 6)) / max(float(row_dict.get("Quotazione", 10)), 1), 2)
            row_dict["Indice_Titolarita"] = calcola_indice_titolarita(row_dict, st.session_state.stats_per_stagione.get("2026-27", None))
            html_card = render_flip_card(row_dict, st.session_state.stats_per_stagione, st.session_state.stats_per_stagione.get("2026-27", None))
            st.markdown(html_card, unsafe_allow_html=True)
            prop = row_dict["Proprietario"]
            prop_color = "#00d26a" if prop == "Svincolati" else "#ff6b6b"
            st.caption(f"Proprietà: <span style='color:{prop_color};font-weight:bold;'>{prop}</span>", unsafe_allow_html=True)

# ============================================================
# TAB 2: MERCATO & ASTA
# ============================================================
with tabs[1]:
    st.header("🛒 Gestione Mercato & Asta Live")
    st.markdown("Acquista, svincola, scambia o gestisci prestiti e contratti durante l'asta in tempo reale.")

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["⚡ Asta Live", "🔄 Scambi", "🤝 Prestiti", "📜 Contratti"])

    with sub_tab1:
        st.subheader("⚡ Asta Live / Acquisto Giocatore")
        c1, c2 = st.columns(2)
        with c1:
            squadra_asta = st.selectbox("Squadra acquirente", get_nomi_squadre(), key="asta_squadra")
            db = st.session_state.giocatori_db
            svinc = get_svincolati(db)
            giocatori_disponibili = svinc["Nome"].tolist()
            giocatore_scelto = st.selectbox("Seleziona Svincolato", giocatori_disponibili, key="asta_giocatore")

            g_info = get_db_info(giocatore_scelto) if giocatore_scelto else None
            if g_info:
                st.info(f"📋 **{g_info['Nome']}** | Ruolo: **{g_info['Ruolo']}** | Squadra: {g_info['Squadra_SerieA']} | Listone: {g_info['Quotazione']}cr | Fascia: {g_info['Consiglio']}")
                stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                prezzo_cons, spiego = calcola_prezzo_consigliato(g_info, stats_df)
                st.markdown(spiego)

        with c2:
            crediti_sq = st.session_state.squadre[squadra_asta]["crediti"]
            st.metric("Crediti disponibili squadra", f"{crediti_sq}cr")
            prezzo_default = int(g_info.get("Quotazione", 10)) if g_info else 10
            costo_acquisto = st.number_input("Costo effettivo (crediti)", min_value=1, max_value=max(1, crediti_sq), value=min(prezzo_default, crediti_sq), key="asta_costo")

            riep_sq = riepilogo_rosa(squadra_asta)
            st.markdown(f"**Rosa attuale:** {riep_sq['tot_posseduti']} giocatori | **Mancanti:** {riep_sq['tot_mancanti']}")
            for r, dati in riep_sq.items():
                if r in ROSA_REQ:
                    st.caption(f"Ruolo {r}: {dati['posseduti']}/{dati['req']} (Offerta max consigliata: {dati['offerta_max']}cr)")

            if st.button("🔨 Conferma Acquisto", type="primary", use_container_width=True):
                if not giocatore_scelto:
                    st.error("Seleziona un giocatore")
                elif crediti_sq < costo_acquisto:
                    st.error("Crediti insufficienti!")
                else:
                    StateManager.snapshot()
                    st.session_state.squadre[squadra_asta]["crediti"] -= costo_acquisto
                    g_data = g_info.copy()
                    g_data["Costo_Acquisto"] = costo_acquisto
                    g_data["Data_Acquisto"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.squadre[squadra_asta]["rosa"].append(g_data)
                    st.session_state.storico_mercato.append({
                        "Tipo": "ACQUISTO",
                        "Squadra": squadra_asta,
                        "Giocatore": giocatore_scelto,
                        "Costo": costo_acquisto,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ {giocatore_scelto} acquistato da {squadra_asta} per {costo_acquisto}cr!")
                    st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Svincola Giocatore")
        c1, c2 = st.columns(2)
        with c1:
            sq_svincola = st.selectbox("Squadra", get_nomi_squadre(), key="svin_sq")
            rosa_sq = rosa_proprieta(sq_svincola)
            nomi_rosa = [g["Nome"] for g in rosa_sq]
            giocatore_svincola = st.selectbox("Giocatore da svincolare", nomi_rosa, key="svin_gioc") if nomi_rosa else st.selectbox("Nessun giocatore in rosa", ["Nessuno"], key="svin_gioc_empty")
        with c2:
            rimborso = st.number_input("Crediti rimborso", min_value=0, max_value=100, value=0, key="svin_rimborso")
            if st.button("🗑️ Conferma Svincolo", type="primary", use_container_width=True):
                if giocatore_svincola and giocatore_svincola != "Nessuno":
                    StateManager.snapshot()
                    rosa_attuale = st.session_state.squadre[sq_svincola]["rosa"]
                    gioc_rimosso = None
                    nuova_rosa = []
                    for g in rosa_attuale:
                        if g["Nome"] == giocatore_svincola:
                            gioc_rimosso = g
                        else:
                            nuova_rosa.append(g)
                    st.session_state.squadre[sq_svincola]["rosa"] = nuova_rosa
                    st.session_state.squadre[sq_svincola]["crediti"] += rimborso
                    st.session_state.storico_mercato.append({
                        "Tipo": "SVINCOLO",
                        "Squadra": sq_svincola,
                        "Giocatore": giocatore_svincola,
                        "Rimborso": rimborso,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ {giocatore_svincola} svincolato da {sq_svincola} (Rimborso: {rimborso}cr)")
                    st.rerun()

    with sub_tab2:
        st.subheader("🔄 Scambio Giocatori tra Squadre")
        c1, c2 = st.columns(2)
        with c1:
            sq1 = st.selectbox("Squadra 1", get_nomi_squadre(), key="scambio_sq1")
            rosa1 = rosa_proprieta(sq1)
            gioc1 = st.multiselect("Giocatori da dare a Squadra 2", [g["Nome"] for g in rosa1], key="scambio_gioc1")
            conguaglio1 = st.number_input("Conguaglio crediti da Squadra 1 a Squadra 2", min_value=0, max_value=200, value=0, key="cong1")
        with c2:
            altre_sq = [s for s in get_nomi_squadre() if s != sq1]
            sq2 = st.selectbox("Squadra 2", altre_sq if altre_sq else get_nomi_squadre(), key="scambio_sq2")
            rosa2 = rosa_proprieta(sq2)
            gioc2 = st.multiselect("Giocatori da dare a Squadra 1", [g["Nome"] for g in rosa2], key="scambio_gioc2")
            conguaglio2 = st.number_input("Conguaglio crediti da Squadra 2 a Squadra 1", min_value=0, max_value=200, value=0, key="cong2")

        if st.button("🔄 Conferma Scambio", type="primary", use_container_width=True):
            if sq1 == sq2:
                st.error("Seleziona due squadre differenti")
            elif not gioc1 and not gioc2 and conguaglio1 == 0 and conguaglio2 == 0:
                st.error("Seleziona almeno un giocatore o un conguaglio")
            else:
                StateManager.snapshot()
                # Esegui scambio
                s1_rosa = st.session_state.squadre[sq1]["rosa"]
                s2_rosa = st.session_state.squadre[sq2]["rosa"]

                spostati_s1_to_s2 = []
                nuova_s1 = []
                for g in s1_rosa:
                    if g["Nome"] in gioc1:
                        spostati_s1_to_s2.append(g)
                    else:
                        nuova_s1.append(g)

                spostati_s2_to_s1 = []
                nuova_s2 = []
                for g in s2_rosa:
                    if g["Nome"] in gioc2:
                        spostati_s2_to_s1.append(g)
                    else:
                        nuova_s2.append(g)

                nuova_s1.extend(spostati_s2_to_s1)
                nuova_s2.extend(spostati_s1_to_s2)

                st.session_state.squadre[sq1]["rosa"] = nuova_s1
                st.session_state.squadre[sq2]["rosa"] = nuovan_s2 if 'nuovan_s2' in locals() else nuova_s2

                st.session_state.squadre[sq1]["crediti"] = st.session_state.squadre[sq1]["crediti"] - conguaglio1 + conguaglio2
                st.session_state.squadre[sq2]["crediti"] = st.session_state.squadre[sq2]["crediti"] - conguaglio2 + conguaglio1

                st.session_state.storico_mercato.append({
                    "Tipo": "SCAMBIO",
                    "Squadra_1": sq1, "Giocatori_1": gioc1,
                    "Squadra_2": sq2, "Giocatori_2": gioc2,
                    "Conguaglio_1": conguaglio1, "Conguaglio_2": conguaglio2,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                invalidate_cache()
                save_state()
                st.success(f"✅ Scambio completato tra {sq1} e {sq2}!")
                st.rerun()

    with sub_tab3:
        st.subheader("🤝 Gestione Prestiti")
        c1, c2 = st.columns(2)
        with c1:
            sq_da = st.selectbox("Squadra proprietaria (Da)", get_nomi_squadre(), key="prest_da")
            rosa_p = rosa_proprieta(sq_da)
            gioc_p = st.selectbox("Giocatore in prestito", [g["Nome"] for g in rosa_p], key="prest_gioc") if rosa_p else None
        with c2:
            altre_s = [s for s in get_nomi_squadre() if s != sq_da]
            sq_a = st.selectbox("Squadra ricevente (A)", altre_s if altre_s else get_nomi_squadre(), key="prest_a")
            if st.button("🤝 Registra Prestito", type="primary", use_container_width=True):
                if gioc_p and sq_da != sq_a:
                    StateManager.snapshot()
                    # Trova giocatore in rosa_p
                    g_obj = None
                    for g in st.session_state.squadre[sq_da]["rosa"]:
                        if g["Nome"] == gioc_p:
                            g_obj = g
                            break
                    if g_obj:
                        g_obj["Prestito_Da"] = sq_da
                        g_obj["Prestito_A"] = sq_a
                        # Rimuovi da sq_da e aggiungi a sq_a
                        st.session_state.squadre[sq_da]["rosa"] = [g for g in st.session_state.squadre[sq_da]["rosa"] if g["Nome"] != gioc_p]
                        st.session_state.squadre[sq_a]["rosa"].append(g_obj)
                        st.session_state.prestiti.append({"Giocatore": gioc_p, "Da": sq_da, "A": sq_a, "Data": datetime.now().strftime("%Y-%m-%d")})
                        invalidate_cache()
                        save_state()
                        st.success(f"✅ Prestito di {gioc_p} da {sq_da} a {sq_a} registrato!")
                        st.rerun()

        if st.session_state.prestiti:
            st.markdown("### Prestiti Attivi")
            for idx, p in enumerate(st.session_state.prestiti):
                st.markdown(f"- **{p['Giocatore']}**: da `{p['Da']}` ➡️ a `{p['A']}` (dal {p.get('Data', 'N/D')})")
                if st.button(f"↩️ Termina prestito {p['Giocatore']}", key=f"term_prest_{idx}"):
                    StateManager.snapshot()
                    # Restituisci alla squadra proprietaria
                    gioc_nome = p["Giocatore"]
                    sq_prop = p["Da"]
                    sq_corr = p["A"]
                    g_obj = None
                    for g in st.session_state.squadre[sq_corr]["rosa"]:
                        if g["Nome"] == gioc_nome:
                            g_obj = g
                            break
                    if g_obj:
                        g_obj.pop("Prestito_Da", None)
                        g_obj.pop("Prestito_A", None)
                        st.session_state.squadre[sq_corr]["rosa"] = [g for g in st.session_state.squadre[sq_corr]["rosa"] if g["Nome"] != gioc_nome]
                        st.session_state.squadre[sq_prop]["rosa"].append(g_obj)
                    st.session_state.prestiti.pop(idx)
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ Prestito terminato. {gioc_nome} torna a {sq_prop}.")
                    st.rerun()

    with sub_tab4:
        st.subheader("📜 Contratti Pluriennali (Max 3 anni)")
        c1, c2 = st.columns(2)
        with c1:
            sq_contratto = st.selectbox("Squadra", get_nomi_squadre(), key="cont_sq")
            rosa_c = st.session_state.squadre[sq_contratto]["rosa"]
            gioc_c = st.selectbox("Giocatore", [g["Nome"] for g in rosa_c], key="cont_gioc") if rosa_c else None
        with c2:
            durata = st.slider("Anni di contratto", 1, 3, 2, key="cont_durata")
            stangata = st.checkbox("Ingaggio crescente (+20% all'anno)", value=False, key="cont_stangata")
            if st.button("📜 Assegna Contratto", type="primary", use_container_width=True):
                if gioc_c:
                    StateManager.snapshot()
                    st.session_state.contratti[gioc_c] = {
                        "squadra": sq_contratto,
                        "anni": durata,
                        "crescente": stangata,
                        "data": datetime.now().strftime("%Y-%m-%d")
                    }
                    save_state()
                    st.success(f"✅ Contratto di {durata} anni assegnato a {gioc_c} ({sq_contratto})!")
                    st.rerun()

        if st.session_state.contratti:
            st.markdown("### Contratti Registrati")
            for g_nome, c_info in st.session_state.contratti.items():
                st.markdown(f"- **{g_nome}** (`{c_info['squadra']}`): **{c_info['anni']} anni** | Crescente: `{'Sì' if c_info['crescente'] else 'No'}` (Stipulato il {c_info.get('data', 'N/D')})")

# ============================================================
# TAB 3: ROSE
# ============================================================
with tabs[2]:
    st.header("👥 Rose delle 10 Squadre")
    st.markdown("Esamina le rose, i crediti residui e la completezza dei reparti per ciascun fantallenatore.")

    riepiloghi = get_all_riepiloghi()
    squadre_lista = get_nomi_squadre()

    # Visualizzazione metrica rapida crediti
    cols_met = st.columns(min(len(squadre_lista), 5))
    for idx, sq in enumerate(squadre_lista[:5]):
        with cols_met[idx]:
            cred = riepiloghi[sq]["crediti"]
            poss = riepiloghi[sq]["tot_posseduti"]
            st.metric(sq, f"{cred}cr", f"Rosa: {poss}/28")

    st.markdown("---")
    sq_selezionata = st.selectbox("Seleziona Squadra da visualizzare", squadre_lista, key="sel_rosa_det")

    if sq_selezionata:
        dati_sq = st.session_state.squadre[sq_selezionata]
        riep_sq = riepiloghi[sq_selezionata]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"### 🛡️ {sq_selezionata}")
            st.markdown(f"**Crediti residui:** `{dati_sq['crediti']}cr`")
            st.markdown(f"**Giocatori in rosa:** `{riep_sq['tot_posseduti']}` / 28")
        with c2:
            st.markdown("### 📊 Reparti")
            for r, req in ROSA_REQ.items():
                poss = riep_sq[r]["posseduti"]
                manc = riep_sq[r]["mancanti"]
                col_r = "#00d26a" if manc == 0 else "#ff6b6b"
                st.markdown(f"- **{r}**: {poss}/{req} <span style='color:{col_r};'>(Mancanti: {manc})</span>", unsafe_allow_html=True)
        with c3:
            st.markdown("### 📈 Statistiche Rosa")
            rosa_rosa = dati_sq["rosa"]
            if rosa_rosa:
                fm_media_rosa = sum(g.get("FantaMedia", 6.0) for g in rosa_rosa) / len(rosa_rosa)
                spesa_tot = sum(g.get("Costo_Acquisto", 0) for g in rosa_rosa)
                st.markdown(f"**FantaMedia Rosa:** `{fm_media_rosa:.2f}`")
                st.markdown(f"**Spesa Totale:** `{spesa_tot}cr`")
            else:
                st.markdown("*Rosa vuota*")

        st.markdown("---")
        st.subheader("📋 Elenco Giocatori in Rosa")
        if dati_sq["rosa"]:
            df_rosa = pd.DataFrame(dati_sq["rosa"])
            cols_show = ["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Costo_Acquisto", "Consiglio"]
            cols_avail = [c for c in cols_show if c in df_rosa.columns]
            st.dataframe(df_rosa[cols_avail], use_container_width=True, hide_index=True)
        else:
            st.info(f"Nessun giocatore in rosa per {sq_selezionata}.")

# ============================================================
# TAB 4: STATISTICHE STORICHE
# ============================================================
with tabs[3]:
    st.header("📈 Statistiche Storiche & Importazione Dati")
    st.markdown("Carica i file CSV/Excel delle stagioni passate (es. 2024-25, 2025-26, 2026-27) per alimentare i calcoli algoritmici e l'AI.")

    c1, c2 = st.columns(2)
    with c1:
        stagione_nome = st.selectbox("Seleziona Stagione", ["2026-27", "2025-26", "2024-25", "2023-24"], key="stagione_sel")
    with c2:
        file_stats = st.file_uploader(f"Carica CSV o Excel per {stagione_nome}", type=["csv", "xlsx", "xls"], key="upload_stats")

    if file_stats is not None:
        try:
            if file_stats.name.endswith(".csv"):
                df_load = pd.read_csv(file_stats)
            else:
                df_load = pd.read_excel(file_stats)
            st.success(f"✅ File caricato con successo! Colonne trovate: {list(df_load.columns)}")
            st.dataframe(df_load.head(5), use_container_width=True)

            if st.button(f"💾 Salva Statistiche per {stagione_nome}", type="primary", use_container_width=True):
                StateManager.snapshot()
                if "stats_per_stagione" not in st.session_state:
                    st.session_state.stats_per_stagione = {}
                st.session_state.stats_per_stagione[stagione_nome] = df_load
                if stagione_nome == "2025-26" and "Quotazione" in df_load.columns:
                    st.session_state.quotazioni_2025_26 = df_load
                st.session_state.stats_storiche = df_load # fallback
                save_state()
                st.success(f"✅ Statistiche per la stagione {stagione_nome} salvate correttamente!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Errore nella lettura del file: {e}")

    st.markdown("---")
    st.subheader("📚 Stagioni già caricate")
    stats_map = st.session_state.get("stats_per_stagione", {})
    if stats_map:
        for stag, df_s in stats_map.items():
            with st.expander(f"Stagione {stag} ({len(df_s)} giocatori)"):
                st.dataframe(df_s.head(10), use_container_width=True)
    else:
        st.info("Nessuna statistica storica caricata finora.")

# ============================================================
# TAB 5: TESTA A TESTA
# ============================================================
with tabs[4]:
    st.header("⚔️ Confronto Testa a Testa tra Giocatori")
    st.markdown("Confronta le statistiche, le fanta medie storiche e i parametri di due calciatori.")

    db = st.session_state.giocatori_db
    nomi_giocatori = db["Nome"].tolist() if not db.empty else []

    c1, c2 = st.columns(2)
    with c1:
        gioc1_nome = st.selectbox("Giocatore 1", nomi_giocatori, key="h2h_g1")
    with c2:
        gioc2_nome = st.selectbox("Giocatore 2", nomi_giocatori, index=min(1, len(nomi_giocatori)-1), key="h2h_g2")

    if gioc1_nome and gioc2_nome:
        g1_info = get_db_info(gioc1_nome)
        g2_info = get_db_info(gioc2_nome)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"### 🟢 {gioc1_nome}")
            if g1_info:
                st.markdown(f"**Ruolo:** {g1_info['Ruolo']} | **Squadra:** {g1_info['Squadra_SerieA']}")
                st.markdown(f"**FantaMedia:** {g1_info['FantaMedia']}")
                st.markdown(f"**Quotazione:** {g1_info['Quotazione']}cr")
                st.markdown(f"**Fascia:** {g1_info['Consiglio']}")
                st.markdown(f"**Note:** {g1_info.get('Note', 'N/D')}")
            stats_1 = mostra_statistiche_giocatore(gioc1_nome, st.session_state.get("stats_per_stagione", {}).get("2026-27", pd.DataFrame()))
            if stats_1 is not None and not stats_1.empty:
                st.dataframe(stats_1, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown(f"### 🔵 {gioc2_nome}")
            if g2_info:
                st.markdown(f"**Ruolo:** {g2_info['Ruolo']} | **Squadra:** {g2_info['Squadra_SerieA']}")
                st.markdown(f"**FantaMedia:** {g2_info['FantaMedia']}")
                st.markdown(f"**Quotazione:** {g2_info['Quotazione']}cr")
                st.markdown(f"**Fascia:** {g2_info['Consiglio']}")
                st.markdown(f"**Note:** {g2_info.get('Note', 'N/D')}")
            stats_2 = mostra_statistiche_giocatore(gioc2_nome, st.session_state.get("stats_per_stagione", {}).get("2026-27", pd.DataFrame()))
            if stats_2 is not None and not stats_2.empty:
                st.dataframe(stats_2, use_container_width=True, hide_index=True)

# ============================================================
# TAB 6: SIMULATORE FORMAZIONE
# ============================================================
with tabs[5]:
    st.header("🔮 Simulatore Formazione Ideale")
    st.markdown("Simula la migliore formazione titolare e la panchina per ciascuna squadra in base ai moduli tattici.")

    sq_sim = st.selectbox("Seleziona Squadra", get_nomi_squadre(), key="sim_sq")
    modulo_scelto = st.selectbox("Modulo", ["3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-2-3-1"], key="sim_mod")

    if sq_sim and modulo_scelto:
        fm_tot, panchina, titolari = simula_formazione(sq_sim, modulo_scelto)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### 🟢 Titolari ({modulo_scelto})")
            st.markdown(f"**FantaMedia Stimata Titolari:** `{fm_tot}`")
            for t in titolari:
                origine = t.get("FM_Origine", "📋 Listone")
                st.markdown(f"- **{t['Nome']}** ({t['Ruolo']} - {t['Squadra_SerieA']}) | FM: `{t.get('FantaMedia_Usata', 0)}` [{origine}]")

        with c2:
            st.markdown("### 🔵 Panchina")
            for p in panchina:
                origine = p.get("FM_Origine", "📋 Listone")
                st.markdown(f"- {p['Nome']} ({p['Ruolo']} - {p['Squadra_SerieA']}) | FM: `{p.get('FantaMedia_Usata', 0)}` [{origine}]")

# ============================================================
# TAB 7: ANALISI & REPORT
# ============================================================
with tabs[6]:
    st.header("🏆 Analisi & Report Completi")
    st.markdown("Panoramica avanzata di tutte le squadre, spesa media, top player posseduti e storico transazioni.")

    squadre_lista = get_nomi_squadre()
    riepiloghi = get_all_riepiloghi()

    data_tabella = []
    for sq in squadre_lista:
        r = riepiloghi[sq]
        rosa = st.session_state.squadre[sq]["rosa"]
        spesa_tot = sum(g.get("Costo_Acquisto", 0) for g in rosa)
        fm_m = round(sum(g.get("FantaMedia", 6.0) for g in rosa) / len(rosa), 2) if rosa else 0.0
        data_tabella.append({
            "Squadra": sq,
            "Crediti Residui": r["crediti"],
            "Giocatori": r["tot_posseduti"],
            "Spesa Totale": spesa_tot,
            "FantaMedia Rosa": fm_m,
            "Portieri": r["P"]["posseduti"],
            "Difensori": r["D"]["posseduti"],
            "Centrocampisti": r["C"]["posseduti"],
            "Attaccanti": r["A"]["posseduti"]
        })

    df_report = pd.DataFrame(data_tabella)
    st.dataframe(df_report, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📜 Storico Transazioni Mercato")
    if st.session_state.storico_mercato:
        df_storico = pd.DataFrame(st.session_state.storico_mercato)
        st.dataframe(df_storico, use_container_width=True, hide_index=True)
    else:
        st.info("Nessuna transazione registrata finora.")

# ============================================================
# TAB 8: DASHBOARD AVANZATA (Statistiche Avanzate Richiesta)
# ============================================================
with tabs[7]:
    st.header("⚡ Dashboard Avanzata & Indicatori AI")
    st.markdown("Analisi predittiva di mercato, budget effettivo per top player (>40cr), fuga top tracker e indici di titolarità.")

    sub_d1, sub_d2, sub_d3 = st.tabs(["💎 Top Player (>40cr) & Budget", "🏃 Fuga Top Tracker", "📊 Indice Titolarità & Heatmap"])

    with sub_d1:
        st.subheader("💎 Gestione Budget per Top Player (>40cr)")
        st.markdown("Calcola quanto puoi spendere realmente per un top player lasciando la riserva minima per completare la rosa.")

        sq_top = st.selectbox("Seleziona Squadra", get_nomi_squadre(), key="top_sq_sel")
        if sq_top:
            riep_t = riepilogo_rosa(sq_top)
            cred_res = riep_t["crediti"]
            posti_man = riep_t["tot_mancanti"]
            budget_lib = budget_libero_effettivo(sq_top)
            offerta_max_p = offerta_massima_realistica(sq_top, "A")

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Crediti Residui", f"{cred_res}cr")
            with col_m2:
                st.metric("Posti Mancanti in Rosa", f"{posti_man}")
            with col_m3:
                st.metric("Budget Sicuro per Top", f"{budget_lib}cr", help="Crediti spendibili senza rischiare di non completare la rosa (1 credito per posto rimanente)")

            st.markdown("---")
            st.subheader("📈 Spese per Ruolo")
            spese_r = spese_per_ruolo(sq_top)
            df_spese = pd.DataFrame.from_dict(spese_r, orient="index")
            st.dataframe(df_spese, use_container_width=True)

    with sub_d2:
        st.subheader("🏃 Fuga Top & Consigliati (Svincolati)")
        st.markdown("Monitora quanti top player e consigliati sono ancora liberi nel listone per ciascun ruolo.")

        tracker = fuga_top_tracker()
        for ruolo, dati in tracker.items():
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown(f"### Ruolo: {ruolo}")
            with col_r2:
                st.metric(f"Top Rimasti ({ruolo})", f"{dati['top_rimasti']} / {dati['top_totali']}", f"{dati['pct_top_rimasti']}%")
            with col_r3:
                st.metric(f"Consigliati Rimasti ({ruolo})", f"{dati['cons_rimasti']} / {dati['cons_totali']}", f"{dati['pct_cons_rimasti']}%")
            if alert_scarsita_top(ruolo):
                st.error(f"🚨 **ALLARME SCARSITÀ:** I top nel ruolo `{ruolo}` stanno finendo! (Rimasti: {dati['top_rimasti']})")
            st.markdown("---")

    with sub_d3:
        st.subheader("📊 Indice di Titolarità & Statistiche Avanzate")
        st.markdown("Indice calcolato (0-100) basato su FantaMedia, presenze e fiducia del mercato.")

        db_adv = st.session_state.giocatori_db.copy()
        stats_27 = st.session_state.stats_per_stagione.get("2026-27", pd.DataFrame())
        db_adv["Indice_Titolarita"] = db_adv.apply(lambda row: calcola_indice_titolarita(row, stats_27), axis=1)
        db_adv = db_adv.sort_values("Indice_Titolarita", ascending=False)

        cols_adv_show = ["Nome", "Ruolo", "Squadra_SerieA", "FantaMedia", "Quotazione", "Consiglio", "Indice_Titolarita"]
        st.dataframe(db_adv[[c for c in cols_adv_show if c in db_adv.columns]].head(25), use_container_width=True, hide_index=True)