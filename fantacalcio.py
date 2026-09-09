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
        background: rgba(30,30,63,0.7) !important;
        backdrop-filter: blur(10px);
        border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #00d26a;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; text-shadow: 0 0 10px rgba(0,210,106,0.3); }

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
# LISTONE DEFAULT & WEB SCRAPING
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"MediaVoto":6.35,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"MediaVoto":6.5,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"13 clean sheet, media voto 6.5", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"MediaVoto":6.2,"Gol_Fatti":0,"Assist":0,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati", "Quotazione_2025_26":29, "Prezzo_Consigliato":None},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"MediaVoto":6.4,"Gol_Fatti":5,"Assist":8,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"MediaVoto":6.3,"Gol_Fatti":4,"Assist":3,"Consiglio":"top","Note":"4 gol, 3 assist, primo slot", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"MediaVoto":6.7,"Gol_Fatti":11,"Assist":7,"Consiglio":"top","Note":"Cambio ruolo, doppia-doppia", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"MediaVoto":6.5,"Gol_Fatti":10,"Assist":5,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti", "Quotazione_2025_26":46, "Prezzo_Consigliato":None},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"MediaVoto":7.1,"Gol_Fatti":17,"Assist":6,"Consiglio":"top","Note":"Capocannoniere 17 gol, primo slot assoluto", "Quotazione_2025_26":90, "Prezzo_Consigliato":None},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"MediaVoto":6.8,"Gol_Fatti":15,"Assist":3,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
]

for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)
    g.setdefault("MediaVoto", 6.0)
    g.setdefault("Gol_Fatti", 0)
    g.setdefault("Assist", 0)

def fetch_fantalab_data_from_web():
    try:
        url = "https://www.fantacalcio.it/quotazioni-fantacalcio"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            if tables:
                df_raw = tables[0]
                updated_rows = []
                for _, row in df_raw.iterrows():
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
                    st.success(f"🌐 Sincronizzazione FantaLab completata! Scaricati {len(df_res)} giocatori.")
                    save_state()
                    return True
    except Exception as e:
        st.warning(f"⚠️ Impossibile raggiungere il server web ({e}). Utilizzo dati in cache.")
    return False

# ============================================================
# AUTH & STATE MANAGEMENT
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

class StateManager:
    @staticmethod
    def snapshot():
        if "_undo_stack" not in st.session_state:
            st.session_state._undo_stack = []
        snap = {
            "squadre": pickle.loads(pickle.dumps(st.session_state.squadre)),
            "storico_mercato": list(st.session_state.storico_mercato),
            "watchlist": list(st.session_state.watchlist),
            "giocatori_db": st.session_state.giocatori_db.copy(),
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
        st.session_state.giocatori_db = snap["giocatori_db"]
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
            "giocatori_db": st.session_state.giocatori_db,
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
        st.session_state.squadre = data.get("squadre", {})
        st.session_state.storico_mercato = data.get("storico_mercato", [])
        st.session_state.watchlist = data.get("watchlist", [])
        st.session_state.giocatori_db = data.get("giocatori_db", pd.DataFrame(LISTONE_DEFAULT))
        invalidate_cache()

def save_state():
    StateManager.save()

def load_state():
    return StateManager.load()

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

    riepilogo["crediti"] = crediti
    riepilogo["tot_mancanti"] = tot_mancanti
    riepilogo["tot_posseduti"] = len(rosa)
    return riepilogo

# ============================================================
# 🎴 FLIP CARD 3D RENDERING
# ============================================================
def render_flip_card(row):
    nome = row["Nome"] if hasattr(row, "__getitem__") else row.get("Nome", "N/D")
    ruolo = row["Ruolo"] if hasattr(row, "__getitem__") else row.get("Ruolo", "C")
    sa = row.get("Squadra_SerieA", "N/D") if hasattr(row, "get") else "N/D"
    fm = row.get("FantaMedia", 0) if hasattr(row, "get") else 0
    mv = row.get("MediaVoto", 0) if hasattr(row, "get") else 0
    gol = row.get("Gol_Fatti", 0) if hasattr(row, "get") else 0
    ast = row.get("Assist", 0) if hasattr(row, "get") else 0
    quot = int(row.get("Quotazione", 0)) if hasattr(row, "get") else 0
    fascia = row.get("Consiglio", "consigliato") if hasattr(row, "get") else "consigliato"

    colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
    colore = colori_ruolo.get(ruolo, "#888")
    badge_fascia = {"top": "⭐ TOP", "consigliato": "👍 CONSIGLIATO", "scommessa": "🎲 SCOMMESSA"}.get(fascia, "")

    is_premium = quot > 40
    premium_badge = '<span class="badge-premium">💎 PREMIUM</span>' if is_premium else ""
    premium_class = " card-premium" if is_premium else ""

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
# LOGIN
# ============================================================
def render_login():
    st.title("🔐 FantaManager 2026/27 — Accesso")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("🔑 Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Accedi", type="primary", use_container_width=True):
                accounts = load_accounts()
                if username in accounts and accounts[username]["password"] == hash_password(password):
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("❌ Credenziali errate")
    with col2:
        with st.container(border=True):
            st.subheader("📝 Registrazione")
            new_user = st.text_input("Nuovo Username", key="reg_user")
            new_pass = st.text_input("Nuova Password", type="password", key="reg_pass")
            if st.button("Crea Account", type="primary", use_container_width=True):
                if new_user and new_pass:
                    accounts = load_accounts()
                    if new_user in accounts:
                        st.error("Esistente")
                    else:
                        accounts[new_user] = {"password": hash_password(new_pass)}
                        save_accounts(accounts)
                        st.success("✅ Account creato! Fai login.")

if "current_user" not in st.session_state:
    render_login()
    st.stop()

if "initialized" not in st.session_state:
    st.session_state.squadre = {}
    st.session_state.storico_mercato = []
    st.session_state.watchlist = []
    st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
    if not load_state():
        for sq in get_nomi_squadre():
            st.session_state.squadre[sq] = {"crediti": CREDITI_INIZIALI, "rosa": []}
    st.session_state.initialized = True

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ FantaManager")
    st.caption(f"Utente: {st.session_state.current_user}")
    if st.button("🌐 Sincronizza FantaLab (Web)", use_container_width=True, type="primary"):
        fetch_fantalab_data_from_web()
        st.rerun()
    if st.button("🚪 Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("---")
    if st.session_state.get("_undo_stack"):
        if st.button("↩️ Annulla Ultima Azione", use_container_width=True):
            if StateManager.undo():
                save_state()
                st.toast("✅ Azione annullata!", icon="↩️")
                st.rerun()

# ============================================================
# INTERFACCIA PRINCIPALE — TUTTE LE SCHEDE RIPRISTINATE
# ============================================================
st.title("⚽ FantaManager 2026/27 — Dashboard FantaLab")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Listone", 
    "🔨 Asta & Mercato", 
    "👥 Rose & Squadre", 
    "🔍 Scouting & Consigli", 
    "📊 Statistiche", 
    "⚡ Asta Live"
])

with tab1:
    st.subheader("📋 Listone Giocatori")
    search_q = st.text_input("🔍 Cerca giocatore", key="search_listone")
    db_view = st.session_state.giocatori_db.copy()
    if search_q:
        db_view = db_view[db_view["Nome"].str.contains(search_q, case=False, na=False)]
    
    cols = st.columns(3)
    for idx, row in db_view.iterrows():
        with cols[idx % 3]:
            st.markdown(render_flip_card(row), unsafe_allow_html=True)

with tab2:
    st.subheader("🔨 Gestione Asta & Mercato")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        sq_sel = st.selectbox("Squadra acquirente", get_nomi_squadre(), key="asta_sq")
        svincolati_df = get_svincolati(st.session_state.giocatori_db)
        if not svincolati_df.empty:
            g_sel = st.selectbox("Seleziona Svincolato", svincolati_df["Nome"].tolist(), key="asta_g")
            prezzo_acq = st.number_input("Prezzo pagato", min_value=1, value=1, key="asta_p")
            if st.button("Acquista Giocatore", type="primary"):
                StateManager.snapshot()
                g_info = svincolati_df[svincolati_df["Nome"] == g_sel].iloc[0].to_dict()
                st.session_state.squadre[sq_sel]["rosa"].append(g_info)
                st.session_state.squadre[sq_sel]["crediti"] -= prezzo_acq
                st.session_state.storico_mercato.append({"Squadra": sq_sel, "Giocatore": g_sel, "Prezzo": prezzo_acq})
                save_state()
                st.success(f"Acquistato {g_sel} per {prezzo_acq} crediti!")
                st.rerun()

with tab3:
    st.subheader("👥 Rose delle Squadre")
    sq_rosa_sel = st.selectbox("Seleziona Squadra", get_nomi_squadre(), key="view_rosa_sq")
    if sq_rosa_sel:
        sdata = st.session_state.squadre[sq_rosa_sel]
        rip = riepilogo_rosa(sq_rosa_sel)
        st.markdown(f"**Crediti residui:** {sdata['crediti']} | **Giocatori in rosa:** {rip['tot_posseduti']}")
        cols_r = st.columns(3)
        for idx, g in enumerate(sdata["rosa"]):
            with cols_r[idx % 3]:
                st.markdown(render_flip_card(g), unsafe_allow_html=True)

with tab4:
    st.subheader("🔍 Scouting & Consigli")
    st.markdown("Filtra i migliori profili e scopre le occasioni in base alle statistiche FantaLab.")
    top_giocatori = st.session_state.giocatori_db.sort_values(by="FantaMedia", ascending=False).head(10)
    for _, row in top_giocatori.iterrows():
        st.markdown(f"⭐ **{row['Nome']}** ({row['Squadra_SerieA']} - {row['Ruolo']}) | FantaMedia: **{row['FantaMedia']}** | Quotazione: `{row['Quotazione']}cr`")

with tab5:
    st.subheader("📊 Statistiche Globali")
    if not st.session_state.giocatori_db.empty:
        st.dataframe(st.session_state.giocatori_db, use_container_width=True, hide_index=True)

with tab6:
    st.subheader("⚡ Asta Live")
    st.info("Funzionalità Asta Live attiva per chiamate rapide e gestione rilanci in tempo reale.")
    if st.session_state.storico_mercato:
        st.write("### Ultimi acquisti effettuati:")
        for trans in reversed(st.session_state.storico_mercato[-5:]):
            st.markdown(f"- **{trans['Squadra']}** ha acquistato **{trans['Giocatore']}** per `{trans['Prezzo']} crediti`")

save_state()