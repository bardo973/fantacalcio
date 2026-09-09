import streamlit as st
import pandas as pd
import json
import os
import difflib
import pickle
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import io
import random
import hashlib

# ============================================================
# CONFIGURAZIONE
# ============================================================
st.set_page_config(
    page_title="FantaManager 2026/27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

SAVE_FILE_PKL = "fantamanager_state_v2.pkl"
SAVE_FILE_JSON = "fantamanager_save.json"
ACCOUNTS_FILE = "fantamanager_accounts.json"

NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

def get_nomi_squadre():
    """Ritorna la lista dinamica delle squadre dallo stato, o il default."""
    return st.session_state.get("nomi_squadre", list(NOMI_SQUADRE))

ANNO_CORRENTE = 2026
CONTRATTO_ANNI = 3
CREDITI_INIZIALI = 50
ROSA_REQ = {"P": 3, "D": 9, "C": 9, "A": 7}
MAX_UNDO = 10

# ============================================================
# CSS CUSTOM
# ============================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #1a1c24;
        border: 1px solid #2d3238;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT
# ============================================================
LISTONE_DEFAULT = [
    {"Nome": "Svilar", "Ruolo": "P", "Squadra_SerieA": "Roma", "Quotazione": 38, "FantaMedia": 6.0, "Consiglio": "top", "Note": "18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26": 35, "Prezzo_Consigliato": None},
    {"Nome": "Carnesecchi", "Ruolo": "P", "Squadra_SerieA": "Atalanta", "Quotazione": 34, "FantaMedia": 6.1, "Consiglio": "top", "Note": "13 clean sheet, media voto 6.5, con Sarri può migliorare", "Quotazione_2025_26": 34, "Prezzo_Consigliato": None},
    {"Nome": "Maignan", "Ruolo": "P", "Squadra_SerieA": "Milan", "Quotazione": 34, "FantaMedia": 5.9, "Consiglio": "top", "Note": "13 clean sheet, 2 rigori parati, affidabile", "Quotazione_2025_26": 29, "Prezzo_Consigliato": None},
    {"Nome": "Butez", "Ruolo": "P", "Squadra_SerieA": "Como", "Quotazione": 32, "FantaMedia": 5.8, "Consiglio": "top", "Note": "19 clean sheet, miglior difesa del campionato", "Quotazione_2025_26": 32, "Prezzo_Consigliato": None},
    {"Nome": "Martinez", "Ruolo": "P", "Squadra_SerieA": "Inter", "Quotazione": 29, "FantaMedia": 5.7, "Consiglio": "consigliato", "Note": "Nuovo titolare, ex Genoa, fiducia Chivu", "Quotazione_2025_26": 23, "Prezzo_Consigliato": None},
    {"Nome": "Meret", "Ruolo": "P", "Squadra_SerieA": "Napoli", "Quotazione": 30, "FantaMedia": 5.8, "Consiglio": "consigliato", "Note": "Titolare con Allegri, sottovalutato, ottimo rapporto qualità-prezzo", "Quotazione_2025_26": 31, "Prezzo_Consigliato": None},
    {"Nome": "De Gea", "Ruolo": "P", "Squadra_SerieA": "Fiorentina", "Quotazione": 24, "FantaMedia": 5.6, "Consiglio": "consigliato", "Note": "Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26": 26, "Prezzo_Consigliato": None},
    {"Nome": "Vicario", "Ruolo": "P", "Squadra_SerieA": "Juventus", "Quotazione": 28, "FantaMedia": 5.7, "Consiglio": "consigliato", "Note": "Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26": 15, "Prezzo_Consigliato": None},
    {"Nome": "Mandas", "Ruolo": "P", "Squadra_SerieA": "Lazio", "Quotazione": 22, "FantaMedia": 5.5, "Consiglio": "consigliato", "Note": "Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26": 12, "Prezzo_Consigliato": None},
    {"Nome": "Falcone", "Ruolo": "P", "Squadra_SerieA": "Lecce", "Quotazione": 17, "FantaMedia": 5.5, "Consiglio": "scommessa", "Note": "Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26": 5, "Prezzo_Consigliato": None},
    {"Nome": "Dimarco", "Ruolo": "D", "Squadra_SerieA": "Inter", "Quotazione": 45, "FantaMedia": 7.2, "Consiglio": "top", "Note": "Top assoluto, vale un +3 a giornata, irraggiungibile", "Quotazione_2025_26": 39, "Prezzo_Consigliato": None},
    {"Nome": "Bremer", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 38, "FantaMedia": 6.9, "Consiglio": "top", "Note": "4 gol, 3 assist, fantamedia alta, primo slot", "Quotazione_2025_26": 34, "Prezzo_Consigliato": None},
    {"Nome": "Bisseck", "Ruolo": "D", "Squadra_SerieA": "Inter", "Quotazione": 35, "FantaMedia": 6.8, "Consiglio": "top", "Note": "Voti alti e bonus, può diventare top", "Quotazione_2025_26": 34, "Prezzo_Consigliato": None},
    {"Nome": "Pulisic", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 57, "FantaMedia": 7.8, "Consiglio": "top", "Note": "Cambio ruolo, più appetibile, potenziale doppia-doppia", "Quotazione_2025_26": 53, "Prezzo_Consigliato": None},
    {"Nome": "Orsolini", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 53, "FantaMedia": 7.6, "Consiglio": "top", "Note": "Cambio ruolo, bonus garantiti, doppia cifra potenziale", "Quotazione_2025_26": 46, "Prezzo_Consigliato": None},
    {"Nome": "McTominay", "Ruolo": "C", "Squadra_SerieA": "Napoli", "Quotazione": 50, "FantaMedia": 7.4, "Consiglio": "top", "Note": "Doppia cifra, sposta gli equilibri, top", "Quotazione_2025_26": 42, "Prezzo_Consigliato": None},
    {"Nome": "Lautaro", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 88, "FantaMedia": 8.5, "Consiglio": "top", "Note": "Capocannoniere 17 gol, 6 assist, primo slot assoluto", "Quotazione_2025_26": 90, "Prezzo_Consigliato": None},
    {"Nome": "Malen", "Ruolo": "A", "Squadra_SerieA": "Roma", "Quotazione": 84, "FantaMedia": 8.2, "Consiglio": "top", "Note": "Vice-cannoniere 14 gol, sposta gli equilibri", "Quotazione_2025_26": 72, "Prezzo_Consigliato": None},
    {"Nome": "Thuram", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 74, "FantaMedia": 7.9, "Consiglio": "top", "Note": "13 gol, 6 assist, primo slot nonostante annata deludente", "Quotazione_2025_26": 67, "Prezzo_Consigliato": None}
]
for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)

# ============================================================
# AUTH & MULTI-USER
# ============================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def get_user_save_paths():
    user = st.session_state.get("current_user")
    if user:
        return f"fantamanager_state_{user}.pkl", f"fantamanager_save_{user}.json"
    return SAVE_FILE_PKL, SAVE_FILE_JSON

# ============================================================
# STATE MANAGER (Pickle Atomico + Undo)
# ============================================================
class StateManager:
    @staticmethod
    def snapshot():
        if "_undo_stack" not in st.session_state:
            st.session_state._undo_stack = []
        snap = {
            "squadre": pickle.loads(pickle.dumps(st.session_state.squadre)),
            "storico_mercato": list(st.session_state.storico_mercato),
            "watchlist": list(st.session_state.watchlist),
            "prestiti": pickle.loads(pickle.dumps(st.session_state.prestiti)),
            "contratti": pickle.loads(pickle.dumps(st.session_state.contratti)),
            "giocatori_db": st.session_state.giocatori_db.copy(),
            "stats_storiche": st.session_state.stats_storiche.copy() if not st.session_state.stats_storiche.empty else pd.DataFrame(),
            "stats_per_stagione": {k: v.copy() for k, v in st.session_state.get("stats_per_stagione", {}).items()},
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
            "quotazioni_2025_26": st.session_state.quotazioni_2025_26.copy() if not st.session_state.quotazioni_2025_26.empty else pd.DataFrame(),
            "wizard_completato": st.session_state.get("wizard_completato", False),
            "simulatore_rosa": st.session_state.get("simulatore_rosa", {sq: {"P": [], "D": [], "C": [], "A": []} for sq in get_nomi_squadre()}),
        }
        st.session_state._undo_stack.append(snap)
        if len(st.session_state._undo_stack) > MAX_UNDO:
            st.session_state._undo_stack.pop(0)

    @staticmethod
    def undo():
        if not st.session_state.get("_undo_stack"):
            return False
        snap = st.session_state._undo_stack.pop()
        st.session_state.squadre = snap["squadre"]
        st.session_state.storico_mercato = snap["storico_mercato"]
        st.session_state.watchlist = snap["watchlist"]
        st.session_state.prestiti = snap["prestiti"]
        st.session_state.contratti = snap["contratti"]
        st.session_state.giocatori_db = snap["giocatori_db"]
        st.session_state.stats_storiche = snap["stats_storiche"]
        st.session_state.stats_per_stagione = snap["stats_per_stagione"]
        st.session_state.crediti_iniziali = snap["crediti_iniziali"]
        st.session_state.quotazioni_2025_26 = snap["quotazioni_2025_26"]
        st.session_state.wizard_completato = snap["wizard_completato"]
        invalidate_cache()
        return True

    @staticmethod
    def save():
        pkl_path, _ = get_user_save_paths()
        data = {
            "nomi_squadre": st.session_state.get("nomi_squadre", list(NOMI_SQUADRE)),
            "squadre": st.session_state.squadre,
            "storico_mercato": st.session_state.storico_mercato,
            "watchlist": st.session_state.watchlist,
            "prestiti": st.session_state.prestiti,
            "contratti": st.session_state.contratti,
            "giocatori_db": st.session_state.giocatori_db,
            "stats_storiche": st.session_state.stats_storiche,
            "stats_per_stagione": st.session_state.get("stats_per_stagione", {}),
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
            "quotazioni_2025_26": st.session_state.quotazioni_2025_26,
            "wizard_completato": st.session_state.get("wizard_completato", False),
            "simulatore_rosa": st.session_state.get("simulatore_rosa", {sq: {"P": [], "D": [], "C": [], "A": []} for sq in st.session_state.get("nomi_squadre", list(NOMI_SQUADRE))}),
        }
        tmp = tempfile.NamedTemporaryFile(delete=False, dir=".")
        try:
            with open(tmp.name, "wb") as f:
                pickle.dump(data, f)
            shutil.move(tmp.name, pkl_path)
        except Exception:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
            raise

    @staticmethod
    def load():
        pkl_path, json_path = get_user_save_paths()
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                StateManager._hydrate(data)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def _hydrate(data):
        if "nomi_squadre" in data:
            st.session_state.nomi_squadre = data["nomi_squadre"]
        nomi = get_nomi_squadre()
        squadre_caricate = data.get("squadre", {})
        st.session_state.squadre = {}
        for sq in nomi:
            if sq in squadre_caricate:
                st.session_state.squadre[sq] = squadre_caricate[sq]
            else:
                st.session_state.squadre[sq] = {"P": [], "D": [], "C": [], "A": [], "crediti_residui": data.get("crediti_iniziali", CREDITI_INIZIALI)}
        st.session_state.storico_mercato = data.get("storico_mercato", [])
        st.session_state.watchlist = data.get("watchlist", [])
        st.session_state.prestiti = data.get("prestiti", [])
        st.session_state.contratti = data.get("contratti", {})
        st.session_state.giocatori_db = data.get("giocatori_db", pd.DataFrame(LISTONE_DEFAULT))
        st.session_state.stats_storiche = data.get("stats_storiche", pd.DataFrame())
        st.session_state.stats_per_stagione = data.get("stats_per_stagione", {})
        st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
        st.session_state.quotazioni_2025_26 = data.get("quotazioni_2025_26", pd.DataFrame())
        st.session_state.wizard_completato = data.get("wizard_completato", False)
        sim = data.get("simulatore_rosa", {})
        st.session_state.simulatore_rosa = {sq: sim.get(sq, {"P": [], "D": [], "C": [], "A": []}) for sq in nomi}

def init_session():
    nomi = get_nomi_squadre()
    if "squadre" not in st.session_state:
        st.session_state.squadre = {sq: {"P": [], "D": [], "C": [], "A": [], "crediti_residui": CREDITI_INIZIALI} for sq in nomi}
    if "storico_mercato" not in st.session_state:
        st.session_state.storico_mercato = []
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "prestiti" not in st.session_state:
        st.session_state.prestiti = []
    if "contratti" not in st.session_state:
        st.session_state.contratti = {}
    if "crediti_iniziali" not in st.session_state:
        st.session_state.crediti_iniziali = CREDITI_INIZIALI
    if "giocatori_db" not in st.session_state:
        st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
    if "stats_storiche" not in st.session_state:
        st.session_state.stats_storiche = pd.DataFrame()
    if "stats_per_stagione" not in st.session_state:
        st.session_state.stats_per_stagione = {}
    if "quotazioni_2025_26" not in st.session_state:
        st.session_state.quotazioni_2025_26 = pd.DataFrame()
    if "wizard_completato" not in st.session_state:
        st.session_state.wizard_completato = False
    if "simulatore_rosa" not in st.session_state:
        st.session_state.simulatore_rosa = {sq: {"P": [], "D": [], "C": [], "A": []} for sq in nomi}
    if "_undo_stack" not in st.session_state:
        st.session_state._undo_stack = []

def invalidate_cache():
    pass

# ============================================================
# AUTHENTICATION UI
# ============================================================
accounts = load_accounts()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.authenticated:
    st.title("⚽ FantaManager 2026/27 — Login")
    tab_login, tab_reg = st.tabs(["Accedi", "Registrati"])
    
    with tab_login:
        user_input = st.text_input("Username", key="login_user")
        pass_input = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", use_container_width=True):
            if user_input in accounts and accounts[user_input] == hash_password(pass_input):
                st.session_state.authenticated = True
                st.session_state.current_user = user_input
                init_session()
                StateManager.load()
                st.success("Accesso eseguito con successo!")
                st.rerun()
            else:
                st.error("Credenziali non valide.")
                
    with tab_reg:
        reg_user = st.text_input("Scegli Username", key="reg_user")
        reg_pass = st.text_input("Scegli Password", type="password", key="reg_pass")
        if st.button("Registrati", use_container_width=True):
            if reg_user and reg_pass:
                if reg_user in accounts:
                    st.error("Username già esistente.")
                else:
                    accounts[reg_user] = hash_password(reg_pass)
                    save_accounts(accounts)
                    st.success("Registrazione completata! Adesso puoi effettuare il login.")
            else:
                st.warning("Inserisci username e password.")
    st.stop()

# Inizializzazione sessione utente loggato
init_session()
if not st.session_state.get("_loaded_once", False):
    StateManager.load()
    st.session_state._loaded_once = True

# ============================================================
# INTERFACCIA PRINCIPALE E NAVIGAZIONE
# ============================================================
st.sidebar.title(f"Benvenuto, {st.session_state.current_user}!")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Navigazione", 
    ["📊 Dashboard & Rose", "📋 Listone & Asta", "📈 Statistiche Avanzate", "⚙️ Gestione & Configurazione"]
)

# ------------------------------------------------            
# SEZIONE 1: DASHBOARD & ROSE
# ------------------------------------------------
if menu == "📊 Dashboard & Rose":
    st.header("📊 Dashboard & Rose delle Squadre")
    nomi = get_nomi_squadre()
    
    cols = st.columns(2)
    for idx, sq in enumerate(nomi):
        with cols[idx % 2]:
            with st.container():
                st.subheader(f"🛡️ {sq}")
                squadra_data = st.session_state.squadre[sq]
                crediti_res = squadra_data.get("crediti_residui", st.session_state.crediti_iniziali)
                st.metric("Crediti Residui", crediti_res)
                
                tot_giocatori = sum(len(squadra_data[r]) for r in ["P", "D", "C", "A"])
                st.text(f"Rosa: {tot_giocatori} giocatori totali")
                
                with st.expander(f"Dettaglio Rosa ({sq})"):
                    for r in ["P", "D", "C", "A"]:
                        giocatori_ruolo = squadra_data[r]
                        st.markdown(f"**{r}** ({len(giocatori_ruolo)}):")
                        for g in giocatori_ruolo:
                            st.text(f" - {g.get('Nome', 'Sconosciuto')} ({g.get('Squadra_SerieA', '')}) [Q: {g.get('Quotazione', 0)}]")

# ------------------------------------------------
# SEZIONE 2: LISTONE & ASTA
# ------------------------------------------------
elif menu == "📋 Listone & Asta":
    st.header("📋 Listone Giocatori e Gestione Asta")
    df_db = st.session_state.giocatori_db
    
    if not df_db.empty:
        filtro_ruolo = st.multiselect("Filtra per Ruolo", ["P", "D", "C", "A"], default=["P", "D", "C", "A"])
        df_filtrato = df_db[df_db["Ruolo"].isin(filtro_ruolo)]
        st.dataframe(df_filtrato, use_container_width=True)
    else:
        st.info("Il listone è attualmente vuoto.")

# ------------------------------------------------
# SEZIONE 3: STATISTICHE AVANZATE (Nuova Integrazione)
# ------------------------------------------------
elif menu == "📈 Statistiche Avanzate":
    st.header("📈 Statistiche Avanzate e Analisi Dettagliate")
    st.markdown("Sezione potenziata per l'analisi approfondita di rendimenti, fantamedie e distribuzioni di valore per reparto.")

    df_db = st.session_state.giocatori_db
    if not df_db.empty and "FantaMedia" in df_db.columns:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Giocatori nel Database", len(df_db))
        with col2:
            fanta_media_generale = df_db["FantaMedia"].mean()
            st.metric("Fantamedia Media Generale", f"{fanta_media_generale:.2f}")
        with col3:
            quotazione_media = df_db["Quotazione"].mean() if "Quotazione" in df_db.columns else 0
            st.metric("Quotazione Media", f"{quotazione_media:.1f}")

        st.markdown("---")
        st.subheader("🎯 Top Giocatori per Fantamedia e Ruolo")
        
        ruolo_selezionato = st.selectbox("Seleziona Ruolo per Analisi", ["P", "D", "C", "A"])
        df_ruolo = df_db[df_db["Ruolo"] == ruolo_selezionato].sort_values(by="FantaMedia", ascending=False)
        
        if not df_ruolo.empty:
            st.dataframe(df_ruolo[["Nome", "Squadra_SerieA", "FantaMedia", "Quotazione", "Consiglio", "Note"]], use_container_width=True)
        else:
            st.warning("Nessun giocatore trovato per questo ruolo.")
            
        st.markdown("---")
        st.subheader("📊 Distribuzione Quotazioni per Ruolo")
        if "Quotazione" in df_db.columns:
            st.bar_chart(df_db.groupby("Ruolo")["Quotazione"].mean())
    else:
        st.info("Carica o popola il listone giocatori per visualizzare le statistiche avanzate.")

# ------------------------------------------------
# SEZIONE 4: GESTIONE & CONFIGURAZIONE
# ------------------------------------------------
elif menu == "⚙️ Gestione & Configurazione":
    st.header("⚙️ Gestione e Salvataggio Dati")
    
    if st.button("Salva Stato Manualmente", use_container_width=True):
        StateManager.save()
        st.success("Stato salvato correttamente su disco!")
        
    if st.button("Annulla ultima modifica (Undo)", use_container_width=True):
        if StateManager.undo():
            st.success("Modifica annullata con successo!")
            st.rerun()
        else:
            st.warning("Nessuna azione precedente da annullare.")
```[cite: 2]