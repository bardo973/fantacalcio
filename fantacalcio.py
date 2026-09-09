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
import requests
from bs4 import BeautifulSoup

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
        background: linear-gradient(180deg, #0b0f19 0%, #12122e 100%);
    }
    .stSidebar { background-color: #0f0f24 !important; }
    h1, h2, h3 { color: #00d26a !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; transition: all 0.2s;
        background: linear-gradient(90deg, #00d26a, #00a854);
        color: white; border: none;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,210,106,0.3);
    }
    .stButton>button[kind="secondary"] {
        background: #2a2a4a; color: #ddd;
    }
    .card-giocatore {
        background: #1e1e3f; border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #00d26a;
    }
    .badge-prestito {
        background: #ff6b6b; color: white; padding: 2px 8px;
        border-radius: 12px; font-size: 0.75em; font-weight: bold;
    }
    .metric-box {
        background: #1a1a2e; border-radius: 10px; padding: 16px;
        text-align: center; border: 1px solid #2a2a4a;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }

    .card-3d-titolare {
        background: linear-gradient(145deg, #1e1e3f, #2a2a4a);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 8px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
    }
    .card-3d-titolare:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 20px 40px rgba(0,210,106,0.25), 0 0 0 1px rgba(0,210,106,0.1);
    }
    .card-3d-panchina {
        background: linear-gradient(145deg, #15152b, #1a1a2e);
        border-radius: 10px;
        padding: 8px 12px;
        margin-bottom: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        opacity: 0.75;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .card-3d-panchina:hover {
        transform: translateY(-3px) scale(1.02);
        opacity: 1;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }

    /* ✨ Chicche grafiche — Glassmorphism & Glow */
    .card-giocatore {
        background: rgba(30,30,63,0.7) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .stButton>button {
        box-shadow: 0 0 15px rgba(0,210,106,0.2);
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0,210,106,0.5);
        transform: translateY(-2px) scale(1.02);
    }
    div[data-testid="stMetricValue"] {
        text-shadow: 0 0 10px rgba(0,210,106,0.3);
    }

    /* 🎴 Flip Card 3D */
    .flip-card {
        background-color: transparent;
        perspective: 1000px;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: left;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
    }
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 12px;
    }
    .flip-card-back {
        transform: rotateY(180deg);
    }
    /* 💎 PREMIUM CARDS — >40cr */
    .card-premium {
        position: relative;
        z-index: 1;
    }
    .card-premium::before {
        content: "";
        position: absolute;
        top: -3px; left: -3px; right: -3px; bottom: -3px;
        border-radius: 14px;
        background: linear-gradient(45deg, #ffd700, #ff8c00, #ffd700, #ffaa00);
        background-size: 400% 400%;
        z-index: -1;
        animation: gradient-rotate 3s ease infinite;
        opacity: 0.85;
    }
    @keyframes gradient-rotate {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .card-premium .flip-card-front {
        border-left: 4px solid #ffd700 !important;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    }
    .badge-premium {
        background: linear-gradient(90deg, #ffd700, #ff8c00);
        color: #1a1a00;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(255,215,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT & WEB SCRAPING / FETCHING (FantaLab Style)
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"MediaVoto":6.35,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"MediaVoto":6.5,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"13 clean sheet, media voto 6.5, con Sarri può migliorare", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"MediaVoto":6.2,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati, affidabile", "Quotazione_2025_26":29, "Prezzo_Consigliato":None},
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":32,"FantaMedia":5.8,"MediaVoto":6.1,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"19 clean sheet, miglior difesa del campionato", "Quotazione_2025_26":32, "Prezzo_Consigliato":None},
    {"Nome":"Martinez","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":5.7,"MediaVoto":6.0,"Gol_Fatti":0,"Assist":0,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Genoa, fiducia Chivu", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":30,"FantaMedia":5.8,"MediaVoto":6.1,"Gol_Fatti":0,"Assist":0,"Consiglio":"consigliato","Note":"Titolare con Allegri, sottovalutato, ottimo rapporto qualità-prezzo", "Quotazione_2025_26":31, "Prezzo_Consigliato":None},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":24,"FantaMedia":5.6,"MediaVoto":6.0,"Gol_Fatti":0,"Assist":0,"Consiglio":"consigliato","Note":"Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Vicario","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":28,"FantaMedia":5.7,"MediaVoto":6.1,"Gol_Fatti":0,"Assist":0,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26":15, "Prezzo_Consigliato":None},
    {"Nome":"Mandas","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":5.5,"MediaVoto":5.9,"Gol_Fatti":0,"Assist":0,"Consiglio":"consigliato","Note":"Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":17,"FantaMedia":5.5,"MediaVoto":6.41,"Gol_Fatti":0,"Assist":0,"Consiglio":"scommessa","Note":"Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26":5, "Prezzo_Consigliato":None},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"MediaVoto":6.4,"Gol_Fatti":5,"Assist":8,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata, irraggiungibile", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"MediaVoto":6.3,"Gol_Fatti":4,"Assist":3,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta, primo slot", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"MediaVoto":6.25,"Gol_Fatti":3,"Assist":2,"Consiglio":"top","Note":"Voti alti e bonus, può diventare top", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"MediaVoto":6.2,"Gol_Fatti":4,"Assist":1,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini, solido", "Quotazione_2025_26":27, "Prezzo_Consigliato":None},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"MediaVoto":6.15,"Gol_Fatti":5,"Assist":2,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens", "Quotazione_2025_26":25, "Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"MediaVoto":6.7,"Gol_Fatti":11,"Assist":7,"Consiglio":"top","Note":"Cambio ruolo, più appetibile, potenziale doppia-doppia", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"MediaVoto":6.5,"Gol_Fatti":10,"Assist":5,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti, doppia cifra potenziale", "Quotazione_2025_26":46, "Prezzo_Consigliato":None},
    {"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.4,"MediaVoto":6.45,"Gol_Fatti":9,"Assist":4,"Consiglio":"top","Note":"Doppia cifra, sposta gli equilibri, top", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},
    {"Nome":"Nico Paz","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":48,"FantaMedia":7.3,"MediaVoto":6.4,"Gol_Fatti":8,"Assist":6,"Consiglio":"top","Note":"Doppia cifra, top assoluto, crescita esponenziale", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"MediaVoto":6.55,"Gol_Fatti":9,"Assist":5,"Consiglio":"top","Note":"9 gol, media voto >6.5, migliore del reparto", "Quotazione_2025_26":40, "Prezzo_Consigliato":None},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"MediaVoto":7.1,"Gol_Fatti":17,"Assist":6,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist, primo slot assoluto", "Quotazione_2025_26":90, "Prezzo_Consigliato":None},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"MediaVoto":6.9,"Gol_Fatti":14,"Assist":5,"Consiglio":"top","Note":"Vice-cannoniere 14 gol, sposta gli equilibri", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"MediaVoto":6.75,"Gol_Fatti":13,"Assist":6,"Consiglio":"top","Note":"13 gol, 6 assist, primo slot nonostante annata deludente", "Quotazione_2025_26":67, "Prezzo_Consigliato":None},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"MediaVoto":6.8,"Gol_Fatti":15,"Assist":3,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol, Allegri punta forte", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"MediaVoto":6.8,"Gol_Fatti":14,"Assist":4,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim, può superare doppia cifra", "Quotazione_2025_26":68, "Prezzo_Consigliato":None},
]

for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)
    g.setdefault("MediaVoto", 6.0)
    g.setdefault("Gol_Fatti", 0)
    g.setdefault("Assist", 0)


# ============================================================
# WEB SCRAPING / FETCHING AUTOMATICO (FantaLab / Fantacalcio.it Style)
# ============================================================
def fetch_fantalab_data_from_web():
    """
    Scarica automaticamente in tempo reale dal web le quotazioni aggiornate,
    le statistiche FantaLab (FantaMedia, Media Voto, Gol, Assist) e i voti live
    utilizzando scraping HTML / API pubbliche di settore.
    """
    try:
        url = "https://www.fantacalcio.it/quotazioni-fantacalcio"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            if tables:
                df_raw = tables[0]
                # Normalizzazione colonne in stile FantaLab
                updated_rows = []
                for _, row in df_raw.iterrows():
                    # Mappatura flessibile delle colonne web
                    nome = str(row.get("Nome", row.get(1, "Sconosciuto"))).strip()
                    ruolo = str(row.get("R", row.get("Ruolo", "C"))).strip().upper()
                    squadra = str(row.get("Squadra", "N/D")).strip()
                    quotazione = int(float(str(row.get("Qt.A", row.get("Quotazione", 10))).replace(",", ".")))
                    fm = float(str(row.get("FM", row.get("FantaMedia", 6.0))).replace(",", "."))
                    mv = float(str(row.get("MV", row.get("MediaVoto", 6.0))).replace(",", "."))
                    gol = int(float(str(row.get("G.", row.get("Gol", 0))).replace(",", ".")))
                    ast = int(float(str(row.get("Ass", row.get("Assist", 0))).replace(",", ".")))
                    
                    updated_rows.append({
                        "Nome": nome,
                        "Ruolo": ruolo if ruolo in ["P", "D", "C", "A"] else "C",
                        "Squadra_SerieA": squadra,
                        "Quotazione": quotazione,
                        "FantaMedia": fm,
                        "MediaVoto": mv,
                        "Gol_Fatti": gol,
                        "Assist": ast,
                        "Consiglio": "consigliato",
                        "Note": f"Aggiornato da web FantaLab — FM: {fm}, MV: {mv}",
                        "Prezzo_Consigliato": None
                    })
                if updated_rows:
                    df_res = pd.DataFrame(updated_rows)
                    st.session_state.giocatori_db = df_res
                    st.success(f"🌐 Sincronizzazione FantaLab completata! Scaricati {len(df_res)} giocatori con quotazioni, voti e statistiche live.")
                    save_state()
                    return True
    except Exception as e:
        st.warning(f"⚠️ Impossibile raggiungere il server web in questo momento ({e}). Utilizzo i dati FantaLab in cache/default.")
    return False


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
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                db = data.get("giocatori_db", [])
                data["giocatori_db"] = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
                stats = data.get("stats_storiche", [])
                data["stats_storiche"] = pd.DataFrame(stats) if stats else pd.DataFrame()
                data["stats_per_stagione"] = {k: pd.DataFrame(v) if v else pd.DataFrame() for k, v in data.get("stats_per_stagione", {}).items()}
                q25 = data.get("quotazioni_2025_26", [])
                data["quotazioni_2025_26"] = pd.DataFrame(q25) if q25 else pd.DataFrame()
                StateManager._hydrate(data)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def _hydrate(data):
        st.session_state.squadre = data.get("squadre", {})
        st.session_state.storico_mercato = data.get("storico_mercato", [])
        st.session_state.watchlist = data.get("watchlist", [])
        st.session_state.prestiti = data.get("prestiti", [])
        st.session_state.contratti = data.get("contratti", {})
        st.session_state.giocatori_db = data.get("giocatori_db", pd.DataFrame(LISTONE_DEFAULT))
        if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
            st.session_state.giocatori_db["Prezzo_Consigliato"] = None
        st.session_state.stats_storiche = data.get("stats_storiche", pd.DataFrame())
        st.session_state.stats_per_stagione = data.get("stats_per_stagione", {})
        st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
        st.session_state.quotazioni_2025_26 = data.get("quotazioni_2025_26", pd.DataFrame())
        st.session_state.wizard_completato = data.get("wizard_completato", False)
        st.session_state.simulatore_rosa = data.get("simulatore_rosa", {sq: {"P": [], "D": [], "C": [], "A": []} for sq in get_nomi_squadre()})
        for sq in get_nomi_squadre():
            if sq not in st.session_state.squadre:
                st.session_state.squadre[sq] = {"crediti": st.session_state.crediti_iniziali, "rosa": []}
        invalidate_cache()

def save_state():
    StateManager.save()
    if "_ops_count" not in st.session_state:
        st.session_state._ops_count = 0
    st.session_state._ops_count += 1

def load_state():
    return StateManager.load()


# ============================================================
# INDICI E CACHE
# ============================================================
def invalidate_cache():
    st.session_state._riepiloghi_dirty = True
    st.session_state._player_index_dirty = True

def get_player_index():
    if st.session_state.get("_player_index_dirty", True):
        idx = {}
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                idx[g["Nome"].lower()] = sq
        st.session_state._player_index = idx
        st.session_state._player_index_dirty = False
    return st.session_state.get("_player_index", {})

def get_svincolati(db: pd.DataFrame) -> pd.DataFrame:
    idx = get_player_index()
    mask = ~db["Nome"].str.lower().isin(idx.keys())
    return db[mask].copy()

def get_giocatore_in_rosa(nome: str) -> Optional[Tuple[str, dict]]:
    nome_l = nome.lower()
    for sq, dati in st.session_state.squadre.items():
        for g in dati["rosa"]:
            if g["Nome"].lower() == nome_l:
                return sq, g
    return None

def rosa_proprieta(squadra: str) -> List[dict]:
    return [g for g in st.session_state.squadre[squadra]["rosa"]
            if g.get("Prestito_Da") is None or g.get("Prestito_Da") == squadra]


# ============================================================
# UTILITY
# ============================================================
def fuzzy_match(name, choices, cutoff=0.75):
    name_clean = str(name).strip().lower()
    matches = difflib.get_close_matches(name_clean, [c.lower() for c in choices], n=1, cutoff=cutoff)
    if matches:
        idx = [c.lower() for c in choices].index(matches[0])
        return choices[idx]
    return None

def get_quotazione_listone(nome):
    db = st.session_state.giocatori_db
    match = db[db["Nome"].str.lower() == nome.lower()]
    if not match.empty:
        return int(match.iloc[0]["Quotazione"])
    nome_match = fuzzy_match(nome, db["Nome"].tolist())
    if nome_match:
        match = db[db["Nome"] == nome_match]
        if not match.empty:
            return int(match.iloc[0]["Quotazione"])
    return None


# ============================================================
# BUSINESS LOGIC
# ============================================================
def riepilogo_rosa(squadra_nome):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    crediti = st.session_state.squadre[squadra_nome]["crediti"]
    conti = {"P": 0, "D": 0, "C": 0, "A": 0}
    for g in rosa:
        r = g.get("Ruolo", "C")
        if r in conti:
            conti[r] += 1

    riepilogo = {}
    tot_mancanti = 0
    for ruolo, req in ROSA_REQ.items():
        posseduti = conti.get(ruolo, 0)
        mancanti = max(0, req - posseduti)
        riepilogo[ruolo] = {"posseduti": posseduti, "mancanti": mancanti, "req": req}
        tot_mancanti += mancanti

    posti_rimanenti = sum(v["mancanti"] for v in riepilogo.values())
    for ruolo in ROSA_REQ:
        mancanti_ruolo = riepilogo[ruolo]["mancanti"]
        if posti_rimanenti > 0 and mancanti_ruolo > 0:
            budget_libero = max(0, crediti - posti_rimanenti)
            offerta = int((budget_libero / mancanti_ruolo) + 1)
        else:
            offerta = crediti if mancanti_ruolo > 0 else 0
        riepilogo[ruolo]["offerta_max"] = offerta

    prestiti_uscita = [p for p in st.session_state.prestiti if p["Da"] == squadra_nome]
    riepilogo["crediti"] = crediti
    riepilogo["tot_mancanti"] = tot_mancanti
    riepilogo["tot_posseduti"] = len(rosa)
    riepilogo["tot_prestiti_uscita"] = len(prestiti_uscita)
    riepilogo["tot_giocatori_posseduti"] = len(rosa) + len(prestiti_uscita)
    return riepilogo

def get_all_riepiloghi():
    if st.session_state.get("_riepiloghi_dirty", True):
        st.session_state._riepiloghi = {sq: riepilogo_rosa(sq) for sq in get_nomi_squadre()}
        st.session_state._riepiloghi_dirty = False
    return st.session_state._riepiloghi


# ============================================================
# 🎴 FLIP CARD 3D — UNIVERSALE (FantaLab Style)
# ============================================================
def render_flip_card(row, stats_per_stagione=None, stats_2627=None):
    """Genera HTML per una flip card 3D FantaLab: fronte=info/voti, retro=statistiche."""
    nome = row["Nome"] if hasattr(row, "__getitem__") else row.get("Nome", "N/D")
    ruolo = row["Ruolo"] if hasattr(row, "__getitem__") else row.get("Ruolo", "C")
    sa = row.get("Squadra_SerieA", "N/D") if hasattr(row, "get") else row.get("Squadra_SerieA", "N/D")
    fm = row.get("FantaMedia", 0) if hasattr(row, "get") else row.get("FantaMedia", 0)
    mv = row.get("MediaVoto", 0) if hasattr(row, "get") else row.get("MediaVoto", 0)
    gol = row.get("Gol_Fatti", 0) if hasattr(row, "get") else row.get("Gol_Fatti", 0)
    ast = row.get("Assist", 0) if hasattr(row, "get") else row.get("Assist", 0)
    quot = int(row.get("Quotazione", 0)) if hasattr(row, "get") else int(row.get("Quotazione", 0))
    fascia = row.get("Consiglio", "consigliato") if hasattr(row, "get") else row.get("Consiglio", "consigliato")

    colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
    colore = colori_ruolo.get(ruolo, "#888")
    badge_fascia = {"top": "⭐ TOP", "consigliato": "👍 CONSIGLIATO", "scommessa": "🎲 SCOMMESSA"}.get(fascia, "")

    is_premium = quot > 40
    premium_badge = '<span class="badge-premium">💎 PREMIUM</span>' if is_premium else ""
    premium_class = " card-premium" if is_premium else ""

    # FRONTE (Stile FantaLab Card)
    front_html = f'''<div style="background:linear-gradient(135deg, rgba(30,30,63,0.95) 0%, rgba(42,42,74,0.8) 100%);backdrop-filter:blur(10px);border-radius:12px;padding:12px;height:100%;box-sizing:border-box;border-left:4px solid {colore};box-shadow:0 8px 32px rgba(0,0,0,0.3);display:flex;flex-direction:column;justify-content:space-between;">
        <div>
            <div style="font-size:1.05em;font-weight:bold;color:#fff;">{nome}</div>
            <div style="font-size:0.8em;color:#aaa;">{sa} | <span style="color:{colore};font-weight:600;">{ruolo}</span></div>
        </div>
        <div style="display:flex;justify-content:space-around;text-align:center;margin:4px 0;">
            <div>
                <div style="font-size:1.4em;font-weight:bold;color:#ffd700;">{fm}</div>
                <div style="font-size:0.65em;color:#888;">FantaMedia</div>
            </div>
            <div>
                <div style="font-size:1.4em;font-weight:bold;color:#00d26a;">{mv}</div>
                <div style="font-size:0.65em;color:#888;">Media Voto</div>
            </div>
        </div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:center;align-items:center;">
            <span style="background:{colore}30;color:{colore};padding:2px 6px;border-radius:10px;font-size:0.65em;font-weight:600;">{badge_fascia}</span>
            <span style="background:rgba(26,26,46,0.6);color:#ddd;padding:2px 6px;border-radius:10px;font-size:0.65em;">{quot}cr</span>
            <span style="background:#1e3a2f;color:#00d26a;padding:2px 6px;border-radius:10px;font-size:0.65em;">⚽ {gol} | 🅰️ {ast}</span>
        </div>
        {premium_badge}
    </div>'''

    # RETRO (Statistiche Dettagliate FantaLab)
    back_html = f'''<div style="background:linear-gradient(135deg, #0f0f24 0%, #1a1a2e 100%);border-radius:12px;padding:12px;height:100%;box-sizing:border-box;border:1px solid {colore}40;display:flex;flex-direction:column;justify-content:center;">
        <div style="font-size:0.85em;color:#00d26a;font-weight:bold;margin-bottom:4px;">📊 Statistiche FantaLab</div>
        <div style="font-size:0.8em;color:#ddd;line-height:1.4;">
            <div><b>Quotazione:</b> {quot} crediti</div>
            <div><b>FantaMedia (FM):</b> {fm}</div>
            <div><b>Media Voto (MV):</b> {mv}</div>
            <div><b>Gol Realizzati:</b> {gol}</div>
            <div><b>Assist:</b> {ast}</div>
        </div>
    </div>'''

    return f'''<div class="flip-card{premium_class}" style="height:185px;margin-bottom:10px;"><div class="flip-card-inner"><div class="flip-card-front">{front_html}</div><div class="flip-card-back">{back_html}</div></div></div>'''


# ============================================================
# GESTIONE SQUADRE
# ============================================================
def aggiungi_squadra(nome: str, crediti: int = None):
    if "nomi_squadre" not in st.session_state:
        st.session_state.nomi_squadre = list(NOMI_SQUADRE)
    if "squadre" not in st.session_state:
        st.session_state.squadre = {}
    nome = nome.strip().upper()
    if not nome:
        return False, "Nome vuoto"
    if nome in st.session_state.nomi_squadre:
        return False, "Squadra già esistente"
    st.session_state.nomi_squadre.append(nome)
    st.session_state.squadre[nome] = {"crediti": crediti or st.session_state.get("crediti_iniziali", CREDITI_INIZIALI), "rosa": []}
    invalidate_cache()
    save_state()
    return True, f"Squadra {nome} aggiunta"

def rimuovi_squadra(nome: str):
    nome = nome.strip().upper()
    if nome not in st.session_state.nomi_squadre:
        return False, "Squadra non trovata"
    if nome in st.session_state.squadre:
        del st.session_state.squadre[nome]
    st.session_state.nomi_squadre.remove(nome)
    invalidate_cache()
    save_state()
    return True, f"Squadra {nome} rimossa"


# ============================================================
# AUTH — LOGIN / REGISTRAZIONE
# ============================================================
def render_login():
    st.title("🔐 FantaManager 2026/27 — Accesso")
    st.markdown("Accedi o crea un account per gestire il tuo fantacalcio con dati in tempo reale FantaLab.")

    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container(border=True):
            st.subheader("🔑 Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Accedi", type="primary", use_container_width=True):
                accounts = load_accounts()
                if username in accounts and accounts[username]["password"] == hash_password(password):
                    st.session_state.current_user = username
                    st.session_state._last_user = username
                    st.rerun()
                else:
                    st.error("❌ Username o password errati")

    with col2:
        with st.container(border=True):
            st.subheader("📝 Nuovo Account")
            new_user = st.text_input("Scegli Username", key="reg_user")
            new_pass = st.text_input("Scegli Password", type="password", key="reg_pass")
            new_pass2 = st.text_input("Conferma Password", type="password", key="reg_pass2")
            if st.button("Crea Account", type="primary", use_container_width=True):
                if not new_user or not new_pass:
                    st.error("Compila tutti i campi")
                elif new_pass != new_pass2:
                    st.error("Le password non coincidono")
                else:
                    accounts = load_accounts()
                    if new_user in accounts:
                        st.error("Username già esistente")
                    else:
                        accounts[new_user] = {"password": hash_password(new_pass)}
                        save_accounts(accounts)
                        st.success("✅ Account creato! Ora effettua il login.")

def require_auth():
    if "current_user" not in st.session_state:
        render_login()
        st.stop()
    if st.session_state.get("_last_user") != st.session_state.current_user:
        for k in list(st.session_state.keys()):
            if k not in ["current_user", "_last_user"]:
                del st.session_state[k]
        st.session_state._last_user = st.session_state.current_user
        st.rerun()

require_auth()

if "initialized" not in st.session_state:
    st.session_state.squadre = {}
    st.session_state.storico_mercato = []
    st.session_state.watchlist = []
    st.session_state.prestiti = []
    st.session_state.contratti = {}
    st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
    st.session_state.stats_storiche = pd.DataFrame()
    st.session_state.quotazioni_2025_26 = pd.DataFrame()
    st.session_state.stats_per_stagione = {}
    st.session_state.wizard_completato = False
    st.session_state.crediti_iniziali = CREDITI_INIZIALI
    st.session_state._riepiloghi_dirty = True
    st.session_state._player_index_dirty = True
    st.session_state._undo_stack = []

    if not load_state():
        for sq in get_nomi_squadre():
            st.session_state.squadre[sq] = {"crediti": CREDITI_INIZIALI, "rosa": []}

    st.session_state.initialized = True


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ FantaManager")
    st.caption("2026/27 — FantaLab Engine")
    st.markdown(f"👤 **Account:** `{st.session_state.get('current_user', 'N/D')}`")
    
    if st.button("🌐 Sincronizza FantaLab (Web)", use_container_width=True, type="primary"):
        fetch_fantalab_data_from_web()
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown("---")
    st.subheader("👥 Gestione Squadre")
    with st.expander("➕ Aggiungi / ➖ Rimuovi"):
        nuova_sq = st.text_input("Nuova squadra", key="new_sq_name", placeholder="es. MARCO")
        cred_sq = st.number_input("Crediti", min_value=10, max_value=500, value=int(st.session_state.get("crediti_iniziali", CREDITI_INIZIALI)), step=5, key="new_sq_cred")
        if st.button("➕ Aggiungi Squadra", use_container_width=True):
            ok, msg = aggiungi_squadra(nuova_sq, cred_sq)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        st.markdown("---")
        if len(get_nomi_squadre()) > 0:
            sq_da_rimuovere = st.selectbox("Rimuovi squadra", get_nomi_squadre(), key="del_sq_sel")
            if st.button("➖ Rimuovi", use_container_width=True):
                ok, msg = rimuovi_squadra(sq_da_rimuovere)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("---")
    if st.session_state.get("_undo_stack"):
        if st.button("↩️ Annulla Ultima Azione", use_container_width=True):
            if StateManager.undo():
                save_state()
                st.toast("✅ Azione annullata!", icon="↩️")
                st.rerun()


# ============================================================
# MAIN APP INTERFACE (Card Layout Preserved)
# ============================================================
st.title("⚽ FantaManager 2026/27 — Dashboard FantaLab")
st.markdown("Gestione rose, quotazioni automatiche dal web, voti e statistiche in tempo reale stile FantaLab.")

tab1, tab2, tab3 = st.tabs(["📋 Listone & Quotazioni Web", "👥 Rose & Squadre", "📊 Statistiche FantaLab"])

with tab1:
    st.subheader("📋 Listone Giocatori (FantaLab Live)")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_query = st.text_input("🔍 Cerca giocatore o squadra", placeholder="Es. Lautaro, Inter...")
    with col_f2:
        ruolo_filter = st.selectbox("Filtra Ruolo", ["Tutti", "P", "D", "C", "A"])

    db_view = st.session_state.giocatori_db.copy()
    if ruolo_filter != "Tutti":
        db_view = db_view[db_view["Ruolo"] == ruolo_filter]
    if search_query:
        db_view = db_view[db_view["Nome"].str.contains(search_query, case=False, na=False) | db_view["Squadra_SerieA"].str.contains(search_query, case=False, na=False)]

    st.markdown(f"**Giocatori trovati:** {len(db_view)}")
    
    # Visualizzazione con le Card 3D originali richieste
    cols = st.columns(3)
    for idx, row in db_view.iterrows():
        col_idx = idx % 3
        with cols[col_idx]:
            card_html = render_flip_card(row, st.session_state.get("stats_per_stagione", {}))
            st.markdown(card_html, unsafe_allow_html=True)

with tab2:
    st.subheader("👥 Rose delle Squadre")
    selected_squadra = st.selectbox("Seleziona Squadra", get_nomi_squadre())
    if selected_squadra:
        squadra_data = st.session_state.squadre.get(selected_squadra, {"crediti": 50, "rosa": []})
        st.markdown(f"### 🛡️ Squadra: **{selected_squadra}** — 💰 Crediti Residui: **{squadra_data['crediti']}**")
        
        rosa = squadra_data["rosa"]
        if not rosa:
            st.info("📭 Nessun giocatore in rosa per questa squadra.")
        else:
            cols_rosa = st.columns(3)
            for idx, g in enumerate(rosa):
                with cols_rosa[idx % 3]:
                    st.markdown(render_flip_card(g, st.session_state.get("stats_per_stagione", {})), unsafe_allow_html=True)

with tab3:
    st.subheader("📊 Analisi Statistiche & Voti FantaLab")
    st.markdown("Panoramica avanzata delle medie voto, fantamedia e bonus calcolati automaticamente.")
    
    if not st.session_state.giocatori_db.empty:
        df_stats = st.session_state.giocatori_db[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "MediaVoto", "Gol_Fatti", "Assist"]].copy()
        df_stats = df_stats.sort_values(by="FantaMedia", ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    else:
        st.info("Nessun dato statistico disponibile.")

# Salvataggio finale automatico ad ogni esecuzione
save_state()