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
import plotly.express as px

# Prova a importare AgGrid per la griglia avanzata stile FantaLab
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# ============================================================
# CONFIGURAZIONE
# ============================================================
st.set_page_config(
    page_title="FantaManager 2026/27 (FantaLab Edition)",
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
# LISTONE DEFAULT (Arricchito con Metriche FantaLab: xG, xA, Rigorista)
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"xG":0.0,"xA":0.0,"Rigorista":"No","Consiglio":"top","Note":"18 clean sheet, fantamedia 6, media voto 6.35","Quotazione_2025_26":35,"Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"xG":0.0,"xA":0.0,"Rigorista":"No","Consiglio":"top","Note":"13 clean sheet, media voto 6.5, con Sarri può migliorare","Quotazione_2025_26":34,"Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"xG":0.0,"xA":0.0,"Rigorista":"No","Consiglio":"top","Note":"13 clean sheet, 2 rigori parati, affidabile","Quotazione_2025_26":29,"Prezzo_Consigliato":None},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"xG":2.1,"xA":6.5,"Rigorista":"No","Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata, irraggiungibile","Quotazione_2025_26":39,"Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"xG":3.2,"xA":0.5,"Rigorista":"No","Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta, primo slot","Quotazione_2025_26":34,"Prezzo_Consigliato":None},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"xG":2.8,"xA":1.0,"Rigorista":"No","Consiglio":"top","Note":"Voti alti e bonus, può diventare top","Quotazione_2025_26":34,"Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"xG":8.5,"xA":7.2,"Rigorista":"Si","Consiglio":"top","Note":"Cambio ruolo, più appetibile, potenziale doppia-doppia","Quotazione_2025_26":53,"Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"xG":9.1,"xA":4.5,"Rigorista":"Si","Consiglio":"top","Note":"Cambio ruolo, bonus garantiti, doppia cifra potenziale","Quotazione_2025_26":46,"Prezzo_Consigliato":None},
    {"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.4,"xG":7.8,"xA":3.2,"Rigorista":"No","Consiglio":"top","Note":"Doppia cifra, sposta gli equilibri, top","Quotazione_2025_26":42,"Prezzo_Consigliato":None},
    {"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"xG":6.5,"xA":5.0,"Rigorista":"Si","Consiglio":"top","Note":"9 gol, media voto >6.5, migliore del reparto","Quotazione_2025_26":40,"Prezzo_Consigliato":None},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"xG":16.2,"xA":4.1,"Rigorista":"Si","Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist, primo slot assoluto","Quotazione_2025_26":90,"Prezzo_Consigliato":None},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"xG":13.5,"xA":3.8,"Rigorista":"No","Consiglio":"top","Note":"Vice-cannoniere 14 gol, sposta gli equilibri","Quotazione_2025_26":72,"Prezzo_Consigliato":None},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"xG":12.1,"xA":6.0,"Rigorista":"No","Consiglio":"top","Note":"13 gol, 6 assist, primo slot nonostante annata deludente","Quotazione_2025_26":67,"Prezzo_Consigliato":None},
]
for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)
    g.setdefault("xG", 1.0)
    g.setdefault("xA", 1.0)
    g.setdefault("Rigorista", "No")

# ============================================================
# FUNZIONI ANALITICHE FANTALAB
# ============================================================
def calcola_prezzo_consigliato_fantalab(g_info):
    """Algoritmo avanzato stile FantaLab basato su xG, xA e piazzati."""
    base = float(g_info.get("Quotazione", 10))
    fm = float(g_info.get("FantaMedia", 6.0))
    xg = float(g_info.get("xG", 0.0))
    xa = float(g_info.get("xA", 0.0))
    rigorista = str(g_info.get("Rigorista", "No")).strip().lower() in ["si", "yes", "1", "rigorista"]
    
    bonus_rigori = 1.15 if rigorista else 1.0
    fattore_atteso = 1.0 + ((xg + xa) * 0.03)
    
    prezzo = base * (fm / 6.5) * bonus_rigori * fattore_atteso
    return max(1, round(prezzo))

def render_fantalab_grid(df):
    """Renderizza una tabella interattiva con filtri avanzati stile FantaLab Grid."""
    if AGGRID_AVAILABLE:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
        gb.configure_side_bar()
        gb.configure_default_column(editable=False, groupable=True, value=True, enableRowGroup=True, aggFunc='sum', sortable=True, filter=True)
        gb.configure_selection('single', use_checkbox=True)
        gridOptions = gb.build()
        
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=False,
            theme='balham',
            height=450,
            allow_unsafe_jscode=True,
        )
        return grid_response.get('selected_rows', [])
    else:
        st.info("💡 Installa `streamlit-aggrid` (`pip install streamlit-aggrid`) per sbloccare la griglia avanzata FantaLab.")
        st.dataframe(df, use_container_width=True)
        return []

def render_value_matrix(df):
    """Crea la Matrice di Convenienza (Scatter Plot) Rendimento/Prezzo."""
    if "Quotazione" in df.columns and "FantaMedia" in df.columns:
        st.subheader("📊 Matrice Rendimento / Prezzo (I 'Crack' nascosti)")
        fig = px.scatter(
            df, 
            x="Quotazione", 
            y="FantaMedia",
            color="Ruolo",
            hover_name="Nome",
            text="Nome",
            size_max=15,
            template="plotly_dark",
            color_discrete_map={"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
        )
        fig.update_traces(textposition='top center')
        fig.update_layout(
            xaxis_title="Quotazione / Prezzo Iniziale",
            yaxis_title="FantaMedia Prevista",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

def check_blocchi_squadra(rosa_utente):
    """Segnala se ci sono troppi giocatori della stessa squadra di Serie A in rosa."""
    squadre_counter = {}
    for ruolo in ["P", "D", "C", "A"]:
        for g in rosa_utente.get(ruolo, []):
            sq = g.get("Squadra_SerieA", "N/D")
            squadre_counter[sq] = squadre_counter.get(sq, 0) + 1
    
    allarme = [sq for sq, count in squadre_counter.items() if count >= 3]
    if allarme:
        st.warning(f"⚠️ **Attenzione effetto blocco squadra:** Hai {squadre_counter[allarme[0]]} giocatori della squadra **{allarme[0]}**. Rischio calo rendimento nei big match o turni difficili!")

def calcola_inflazione_asta(squadra_nome, riepilogo_rosa_func):
    """Calcola l'indice di inflazione e potere d'acquisto rispetto agli avversari."""
    squadre = st.session_state.squadre
    if squadra_nome not in squadre:
        return 1.0
    
    crediti_miei = squadre[squadra_nome]["crediti_residui"]
    riepilogo_mio = riepilogo_rosa_func(squadra_nome)
    posti_miei = riepilogo_mio["tot_mancanti"]
    
    altre_squadre = [sq for sq in get_nomi_squadre() if sq != squadra_nome]
    if not altre_squadre:
        return 1.0
    
    crediti_tot_avversari = sum(squadre[sq]["crediti_residui"] for sq in altre_squadre)
    posti_tot_avversari = sum(riepilogo_rosa_func(sq)["tot_mancanti"] for sq in altre_squadre)
    
    media_crediti_slot_avv = crediti_tot_avversari / max(posti_tot_avversari, 1)
    miei_crediti_slot = crediti_miei / max(posti_miei, 1)
    
    indice_inflazione = miei_crediti_slot / max(media_crediti_slot_avv, 0.1)
    return round(indice_inflazione, 2)

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
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
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
        st.session_state.crediti_iniziali = snap["crediti_iniziali"]
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
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
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
        st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)

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

# ============================================================
# AUTHENTICATION UI
# ============================================================
accounts = load_accounts()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.authenticated:
    st.markdown("## ⚽ FantaManager 2026/27 — Login")
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
                st.success("Accesso effettuato!")
                st.rerun()
            else:
                st.error("Credenziali non valide.")
                
    with tab_reg:
        reg_user = st.text_input("Nuovo Username", key="reg_user")
        reg_pass = st.text_input("Nuova Password", type="password", key="reg_pass")
        if st.button("Registrati", use_container_width=True):
            if reg_user and reg_pass:
                if reg_user in accounts:
                    st.error("Username già esistente.")
                else:
                    accounts[reg_user] = hash_password(reg_pass)
                    save_accounts(accounts)
                    st.success("Registrazione completata! Ora puoi effettuare il login.")
            else:
                st.warning("Compella tutti i campi.")
    st.stop()

# ============================================================
# APP PRINCIPALE
# ============================================================
init_session()

st.sidebar.title(f"⚽ FantaManager (Utente: {st.session_state.current_user})")
menu = st.sidebar.radio("Navigazione", ["📊 Dashboard & Analisi FantaLab", "🛒 Gestione Asta / Mercato", "👥 Rose & Blocchi Squadra", "⚙️ Impostazioni"])

def riepilogo_rosa(sq_nome):
    squadra = st.session_state.squadre[sq_nome]
    tot_giocatori = sum(len(squadra[r]) for r in ["P", "D", "C", "A"])
    tot_mancanti = sum(ROSA_REQ[r] - len(squadra[r]) for r in ["P", "D", "C", "A"])
    return {"tot_giocatori": tot_giocatori, "tot_mancanti": tot_mancanti, "crediti": squadra["crediti_residui"]}

if menu == "📊 Dashboard & Analisi FantaLab":
    st.title("📊 Dashboard Statistica & Analisi FantaLab")
    
    df_db = st.session_state.giocatori_db
    if not df_db.empty:
        # Calcola prezzo consigliato avanzato se non presente
        if "Prezzo_Consigliato" not in df_db.columns or df_db["Prezzo_Consigliato"].isnull().any():
            df_db["Prezzo_Consigliato"] = df_db.apply(calcola_prezzo_consigliato_fantalab, axis=1)
            
        col1, col2, col3 = st.columns(3)
        col1.metric("Giocatori nel Database", len(df_db))
        col2.metric("FantaMedia Massima", f"{df_db['FantaMedia'].max():.2f}")
        col3.metric("Quotazione Media", f"{df_db['Quotazione'].mean():.1f}")
        
        st.markdown("---")
        
        # Visualizzazione Matrice di Convenienza
        render_value_matrix(df_db)
        
        st.markdown("---")
        st.subheader("🔍 Ricerca Avanzata Listone (FantaLab Grid)")
        selected = render_fantalab_grid(df_db)
        if selected:
            st.write("Giocatore Selezionato:", selected)
    else:
        st.info("Nessun giocatore disponibile nel database.")

elif menu == "🛒 Gestione Asta / Mercato":
    st.title("🛒 Assistente Asta Live & Inflazione")
    
    squadre = get_nomi_squadre()
    sq_scelta = st.selectbox("Seleziona la tua squadra", squadre)
    
    if sq_scelta:
        inflazione = calcola_inflazione_asta(sq_scelta, riepilogo_rosa)
        c1, c2 = st.columns(2)
        c1.metric("Crediti Residui", st.session_state.squadre[sq_scelta]["crediti_residui"])
        c2.metric("Indice Inflazione Asta", f"{inflazione}x", help=">1.0 significa che hai più potere d'acquisto rispetto alla media degli avversari per slot liberi.")
        
        st.markdown("---")
        st.subheader("💡 Consigli d'acquisto rapidi (Algoritmo FantaLab)")
        df_db = st.session_state.giocatori_db
        if not df_db.empty:
            df_db["Prezzo_Consigliato"] = df_db.apply(calcola_prezzo_consigliato_fantalab, axis=1)
            st.dataframe(df_db[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "xG", "xA", "Rigorista", "Prezzo_Consigliato"]], use_container_width=True)

elif menu == "👥 Rose & Blocchi Squadra":
    st.title("👥 Controllo Rose & Blocchi di Squadra")
    squadre = get_nomi_squadre()
    sq_scelta = st.selectbox("Seleziona squadra da analizzare", squadre, key="sel_rosa_squadra")
    
    if sq_scelta:
        rosa = st.session_state.squadre[sq_scelta]
        st.subheader(f"Rosa di {sq_scelta}")
        
        # Controllo blocchi di squadra
        check_blocchi_squadra(rosa)
        
        for r in ["P", "D", "C", "A"]:
            st.markdown(f"**Reparto {r}** (Totale: {len(rosa[r])}/{ROSA_REQ[r]})")
            if rosa[r]:
                df_rep = pd.DataFrame(rosa[r])
                st.dataframe(df_rep, use_container_width=True)
            else:
                st.info(f"Nessun giocatore in {r}")

elif menu == "⚙️ Impostazioni":
    st.title("⚙️ Impostazioni & Account")
    if st.button("Salva Stato"):
        StateManager.save()
        st.success("Stato salvato con successo!")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()