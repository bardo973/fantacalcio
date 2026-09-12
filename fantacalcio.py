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
    .card-3d-titolare:active {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 0 30px rgba(0,210,106,0.6), 0 8px 16px rgba(0,0,0,0.4);
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
    .card-3d-panchina:active {
        transform: translateY(-1px);
        box-shadow: 0 0 15px rgba(0,210,106,0.3);
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
    .stScatterChart {
        background: transparent !important;
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
    .card-premium .flip-card-front::after {
        content: "✨";
        position: absolute;
        top: 6px;
        right: 10px;
        font-size: 1.1em;
        animation: sparkle 2s infinite;
        pointer-events: none;
    }
    @keyframes sparkle {
        0%, 100% { opacity: 0.3; transform: scale(1) rotate(0deg); }
        50% { opacity: 1; transform: scale(1.4) rotate(15deg); }
    }
    .card-premium .flip-card-back {
        border: 2px solid rgba(255, 215, 0, 0.5) !important;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.25) !important;
    }
    .badge-premium {
        background: linear-gradient(90deg, #ffd700, #ff8c00);
        color: #1a1a00;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(255,215,0,0.5);
        text-shadow: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"Consiglio":"top","Note":"13 clean sheet, media voto 6.5, con Sarri può migliorare", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati, affidabile", "Quotazione_2025_26":29, "Prezzo_Consigliato":None},
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":32,"FantaMedia":5.8,"Consiglio":"top","Note":"19 clean sheet, miglior difesa del campionato", "Quotazione_2025_26":32, "Prezzo_Consigliato":None},
    {"Nome":"Martinez","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Genoa, fiducia Chivu", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":30,"FantaMedia":5.8,"Consiglio":"consigliato","Note":"Titolare con Allegri, sottovalutato, ottimo rapporto qualità-prezzo", "Quotazione_2025_26":31, "Prezzo_Consigliato":None},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":24,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Vicario","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":28,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26":15, "Prezzo_Consigliato":None},
    {"Nome":"Mandas","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":5.5,"Consiglio":"consigliato","Note":"Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":17,"FantaMedia":5.5,"Consiglio":"scommessa","Note":"Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26":5, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":13,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Torna in Serie A, potenziale sorpresa", "Quotazione_2025_26":6, "Prezzo_Consigliato":None},
    {"Nome":"Corvi","Ruolo":"P","Squadra_SerieA":"Parma","Quotazione":12,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Nuovo titolare, aveva fatto vedere buone cose", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Caprile","Ruolo":"P","Squadra_SerieA":"Cagliari","Quotazione":10,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Buon portiere da modificatore, low cost", "Quotazione_2025_26":3, "Prezzo_Consigliato":None},
{"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata, irraggiungibile", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},{"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta, primo slot", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},{"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"Consiglio":"top","Note":"Voti alti e bonus, può diventare top", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},{"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini, solido", "Quotazione_2025_26":27, "Prezzo_Consigliato":None},{"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens", "Quotazione_2025_26":25, "Prezzo_Consigliato":None},{"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":33,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5 gol, media 6.24, centrale prolifico", "Quotazione_2025_26":33, "Prezzo_Consigliato":None},{"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"5 gol, centrale prolifico, solido", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},{"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":29,"FantaMedia":6.6,"Consiglio":"consigliato","Note":"3 gol, 4 assist, titolare a sinistra", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},{"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":27,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Sottovalutato, bonus garantiti, media buona", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},{"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualità offensiva, bonus sicuri", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},{"Nome":"Di Lorenzo","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":26,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"Sempre buona chiamata, 6-7 bonus potenziali", "Quotazione_2025_26":24, "Prezzo_Consigliato":None},{"Nome":"Kempf","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.2,"Consiglio":"consigliato","Note":"Certezza, voti e bonus, solido", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},{"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu, minutaggio garantito", "Quotazione_2025_26":21, "Prezzo_Consigliato":None},{"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite, può esplodere", "Quotazione_2025_26":11, "Prezzo_Consigliato":None},{"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila, centrale prolifico", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},{"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico, può giocare ovunque", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},{"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra, terzino di spinta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},{"Nome":"Çelik","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":19,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Duttile, Spalletti può schierarlo in varie occasioni", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},{"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, più appetibile, potenziale doppia-doppia", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},{"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti, doppia cifra potenziale", "Quotazione_2025_26":46, "Prezzo_Consigliato":None},{"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.4,"Consiglio":"top","Note":"Doppia cifra, sposta gli equilibri, top", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},{"Nome":"Nico Paz","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":48,"FantaMedia":7.3,"Consiglio":"top","Note":"Doppia cifra, top assoluto, crescita esponenziale", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},{"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"top","Note":"9 gol, media voto >6.5, migliore del reparto", "Quotazione_2025_26":40, "Prezzo_Consigliato":None},{"Nome":"Rabiot","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":42,"FantaMedia":7.0,"Consiglio":"top","Note":"6 gol, 4 assist, con Allegri era il migliore", "Quotazione_2025_26":38, "Prezzo_Consigliato":None},{"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista, garanzia", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},{"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Potenziale top, alla Milinkovic-Savic, può esplodere", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},{"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},{"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito, media >6.5, experience", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},{"Nome":"Koné","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza, solido", "Quotazione_2025_26":43, "Prezzo_Consigliato":None},{"Nome":"De Bruyne","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":46,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"Se sta bene fa la differenza, calcia rigori", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},{"Nome":"Barella","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":44,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Sempre Barella, secondo slot ideale, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},{"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe, coppia ideale", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},{"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, può crescere", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},{"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali, buon rapporto", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},{"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti, sottovalutato", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},{"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype, può fare bene", "Quotazione_2025_26":16, "Prezzo_Consigliato":None},{"Nome":"Douglas Luiz","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Intenzionato a restare, può tornare ai livelli di 2 anni fa", "Quotazione_2025_26":18, "Prezzo_Consigliato":None},{"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},{"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},{"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B, grande salto", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},{"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal più assist in Liga, possibile crack", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},{"Nome":"Liberali","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Giovane dal grande potenziale, spazio con Champions", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},{"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist, primo slot assoluto", "Quotazione_2025_26":90, "Prezzo_Consigliato":None},{"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"Consiglio":"top","Note":"Vice-cannoniere 14 gol, sposta gli equilibri", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},{"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"Consiglio":"top","Note":"13 gol, 6 assist, primo slot nonostante annata deludente", "Quotazione_2025_26":67, "Prezzo_Consigliato":None},{"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol, Allegri punta forte", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},{"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim, può superare doppia cifra", "Quotazione_2025_26":68, "Prezzo_Consigliato":None},{"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":76,"FantaMedia":7.9,"Consiglio":"top","Note":"Tornato alla Juve, Spalletti lo vuole, garanzia", "Quotazione_2025_26":69, "Prezzo_Consigliato":None},{"Nome":"Leao","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":72,"FantaMedia":7.8,"Consiglio":"top","Note":"Prima fascia, può migliorare, talento puro", "Quotazione_2025_26":65, "Prezzo_Consigliato":None},{"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":65,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Doppia cifra garantita, solido", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},{"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":70,"FantaMedia":7.7,"Consiglio":"consigliato","Note":"10 gol, 6 assist, centro progetto, può esplodere", "Quotazione_2025_26":58, "Prezzo_Consigliato":None},{"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":65,"FantaMedia":7.8,"Consiglio":"consigliato","Note":"14 gol, sorpresa 2024-25, doppia cifra sicura", "Quotazione_2025_26":64, "Prezzo_Consigliato":None},{"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":58,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"Sempre utile, momento della differenza, clutch", "Quotazione_2025_26":50, "Prezzo_Consigliato":None},{"Nome":"Davis","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":61,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"10 gol, rigorista, garanzia bonus", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},{"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":55,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Attenzione infortuni, ma potenziale top", "Quotazione_2025_26":44, "Prezzo_Consigliato":None},{"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Torino","Quotazione":50,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"11 gol, conferma, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},{"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":48,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Doppia cifra a Bologna, solido", "Quotazione_2025_26":54, "Prezzo_Consigliato":None},{"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":35,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"7 gol, obiettivo doppia cifra, può crescere", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},{"Nome":"Yeboah","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":24,"FantaMedia":6.5,"Consiglio":"scommessa","Note":"Doppia cifra in Serie B, convocato al Mondiale", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},{"Nome":"Bowie","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":25,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Ex Verona, goal in Serie A li sa fare", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},{"Nome":"Alajbegovic K.","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.7,"Consiglio":"scommessa","Note":"Colpo di mercato, trequarti, attenzione hype", "Quotazione_2025_26":17, "Prezzo_Consigliato":None},{"Nome":"Rrahmani","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"15 gol in Rep. Ceca, nuovo attaccante titolare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},{"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Low cost, potenziale, parte dietro nelle gerarchie", "Quotazione_2025_26":7, "Prezzo_Consigliato":None},{"Nome":"Mendy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":15,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"2 gol in 8 partite, 2007, può esplodere", "Quotazione_2025_26":9, "Prezzo_Consigliato":None},{"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Vice Ramos, a 1 credito ci sta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},{"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Gattuso lo rilancia, puntatina senza esagerare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},]

# -----------------------------------------------------------------------------
# Applicazione ricostruita
# -----------------------------------------------------------------------------

for _player in LISTONE_DEFAULT:
    _player.setdefault("Prezzo_Consigliato", None)


def _default_squadre():
    return {
        squadra: {"crediti": CREDITI_INIZIALI, "rosa": []}
        for squadra in NOMI_SQUADRE
    }


def _default_session_state():
    defaults = {
        "nomi_squadre": list(NOMI_SQUADRE),
        "crediti_iniziali": CREDITI_INIZIALI,
        "giocatori_db": pd.DataFrame(LISTONE_DEFAULT),
        "squadre": _default_squadre(),
        "watchlist": [],
        "storico_mercato": [],
        "stats_storiche": pd.DataFrame(),
        "stats_per_stagione": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _json_safe_state():
    return {
        "nomi_squadre": st.session_state.nomi_squadre,
        "crediti_iniziali": st.session_state.crediti_iniziali,
        "squadre": st.session_state.squadre,
        "watchlist": st.session_state.watchlist,
        "storico_mercato": st.session_state.storico_mercato,
    }


def save_state():
    with open(SAVE_FILE_JSON, "w", encoding="utf-8") as file:
        json.dump(_json_safe_state(), file, ensure_ascii=False, indent=2)


def load_state():
    if not os.path.exists(SAVE_FILE_JSON):
        return False
    try:
        with open(SAVE_FILE_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
        nomi = data.get("nomi_squadre") or list(NOMI_SQUADRE)
        st.session_state.nomi_squadre = nomi
        st.session_state.crediti_iniziali = int(
            data.get("crediti_iniziali", CREDITI_INIZIALI)
        )
        squadre = data.get("squadre") or {}
        for squadra in nomi:
            entry = squadre.get(squadra, {})
            squadre[squadra] = {
                "crediti": int(entry.get("crediti", st.session_state.crediti_iniziali)),
                "rosa": entry.get("rosa", []),
            }
        st.session_state.squadre = squadre
        st.session_state.watchlist = data.get("watchlist", [])
        st.session_state.storico_mercato = data.get("storico_mercato", [])
        return True
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        st.warning(f"Salvataggio non leggibile: {error}")
        return False


def get_nomi_squadre():
    return st.session_state.get("nomi_squadre", list(NOMI_SQUADRE))


def get_player_index():
    return {
        player.get("Nome", "").casefold(): squadra
        for squadra, dati in st.session_state.squadre.items()
        for player in dati.get("rosa", [])
    }


def get_svincolati(db):
    owned = set(get_player_index())
    return db[~db["Nome"].str.casefold().isin(owned)].copy()


def fuzzy_match(name, choices, cutoff=0.75):
    normalized = str(name).strip().casefold()
    matches = difflib.get_close_matches(
        normalized, [str(choice).casefold() for choice in choices], n=1, cutoff=cutoff
    )
    if not matches:
        return None
    index = [str(choice).casefold() for choice in choices].index(matches[0])
    return choices[index]


def get_db_info(nome):
    db = st.session_state.giocatori_db
    exact = db[db["Nome"].str.casefold() == str(nome).casefold()]
    if not exact.empty:
        return exact.iloc[0].to_dict()
    matched = fuzzy_match(nome, db["Nome"].tolist())
    if matched is None:
        return None
    return db[db["Nome"] == matched].iloc[0].to_dict()


def calcola_prezzo_consigliato(player):
    role = player.get("Ruolo", "C")
    quote = float(player.get("Quotazione", 10))
    average = float(player.get("FantaMedia", 6.0))
    role_average = {"P": 5.5, "D": 6.2, "C": 6.8, "A": 7.5}.get(role, 6.5)
    tier_factor = {"top": 1.15, "consigliato": 1.0, "scommessa": 0.85}.get(
        player.get("Consiglio", "consigliato"), 1.0
    )
    price = quote * (1 + (average - role_average) * 0.15) * tier_factor
    return max(1, round(price))


def riepilogo_rosa(squadra_nome):
    rosa = st.session_state.squadre[squadra_nome].get("rosa", [])
    counts = {role: sum(p.get("Ruolo") == role for p in rosa) for role in ROSA_REQ}
    return {
        role: {
            "posseduti": counts[role],
            "richiesti": required,
            "mancanti": max(0, required - counts[role]),
        }
        for role, required in ROSA_REQ.items()
    }


def simula_formazione(squadra_nome, modulo):
    rosa = st.session_state.squadre[squadra_nome].get("rosa", [])
    try:
        defenders, midfielders, forwards = (int(value) for value in modulo.split("-"))
    except ValueError:
        return [], [], "Modulo non valido"
    limits = {"P": 1, "D": defenders, "C": midfielders, "A": forwards}
    starters, bench = [], []
    for role, limit in limits.items():
        players = sorted(
            [player for player in rosa if player.get("Ruolo") == role],
            key=lambda player: float(player.get("FantaMedia", 0)),
            reverse=True,
        )
        starters.extend(players[:limit])
        bench.extend(players[limit:])
        if len(players) < limit:
            return starters, bench, f"Servono almeno {limit} giocatori nel ruolo {role}"
    return starters, bench, ""


def _acquista(squadra, nome, prezzo):
    info = get_db_info(nome)
    if info is None:
        return False, "Giocatore non trovato"
    if nome.casefold() in get_player_index():
        return False, "Questo giocatore è già stato acquistato"
    team = st.session_state.squadre[squadra]
    role = info.get("Ruolo")
    summary = riepilogo_rosa(squadra)
    if summary[role]["posseduti"] >= ROSA_REQ[role]:
        return False, f"La rosa ha già raggiunto il limite per il ruolo {role}"
    if prezzo < 1 or prezzo > team["crediti"]:
        return False, "Prezzo non valido o superiore ai crediti disponibili"
    player = dict(info)
    player["Prezzo_Acquisto"] = int(prezzo)
    player["Acquistato_A"] = datetime.now().isoformat(timespec="seconds")
    team["rosa"].append(player)
    team["crediti"] -= int(prezzo)
    st.session_state.storico_mercato.append(
        {"Squadra": squadra, "Giocatore": info["Nome"], "Prezzo": int(prezzo), "Tipo": "Acquisto"}
    )
    save_state()
    return True, f"{info['Nome']} acquistato da {squadra}"


def _svincola(squadra, nome):
    team = st.session_state.squadre[squadra]
    player = next((item for item in team["rosa"] if item.get("Nome") == nome), None)
    if player is None:
        return False, "Giocatore non presente in rosa"
    team["rosa"].remove(player)
    team["crediti"] += int(player.get("Prezzo_Acquisto", player.get("Quotazione", 0)))
    st.session_state.storico_mercato.append(
        {"Squadra": squadra, "Giocatore": nome, "Prezzo": 0, "Tipo": "Svincolo"}
    )
    save_state()
    return True, f"{nome} svincolato"


def _render_dashboard(squadra):
    team = st.session_state.squadre[squadra]
    summary = riepilogo_rosa(squadra)
    missing = sum(item["mancanti"] for item in summary.values())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Crediti", team["crediti"])
    c2.metric("Giocatori", len(team["rosa"]))
    c3.metric("Posti mancanti", missing)
    c4.metric("Valore rosa", sum(int(p.get("Prezzo_Acquisto", 0)) for p in team["rosa"]))


def _render_listone(squadra):
    st.subheader("Listone e mercato")
    db = get_svincolati(st.session_state.giocatori_db)
    c1, c2, c3 = st.columns(3)
    search = c1.text_input("Cerca giocatore", key="market_search")
    role = c2.selectbox("Ruolo", ["Tutti", "P", "D", "C", "A"], key="market_role")
    tier = c3.selectbox(
        "Fascia", ["Tutte", "top", "consigliato", "scommessa"], key="market_tier"
    )
    if search:
        db = db[db["Nome"].str.contains(search, case=False, na=False)]
    if role != "Tutti":
        db = db[db["Ruolo"] == role]
    if tier != "Tutte":
        db = db[db["Consiglio"] == tier]
    st.dataframe(
        db[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Consiglio"]],
        use_container_width=True,
        hide_index=True,
    )
    if db.empty:
        st.info("Nessun giocatore corrisponde ai filtri")
        return
    choices = db["Nome"].tolist()
    selected = st.selectbox("Giocatore da acquistare", choices, key="selected_player")
    info = get_db_info(selected)
    suggested = calcola_prezzo_consigliato(info)
    st.caption(f"{info['Note']} — prezzo indicativo: {suggested} crediti")
    left, right = st.columns([2, 1])
    price = left.number_input(
        "Prezzo d'acquisto",
        min_value=1,
        max_value=max(1, int(st.session_state.squadre[squadra]["crediti"])),
        value=min(suggested, max(1, int(st.session_state.squadre[squadra]["crediti"]))),
        key="purchase_price",
    )
    if right.button("Acquista", type="primary", use_container_width=True):
        ok, message = _acquista(squadra, selected, price)
        (st.success if ok else st.error)(message)
        if ok:
            st.rerun()


def _render_rosa(squadra):
    st.subheader(f"Rosa di {squadra}")
    team = st.session_state.squadre[squadra]
    if not team["rosa"]:
        st.info("La rosa è vuota. Vai al Listone per acquistare i primi giocatori.")
        return
    for player in team["rosa"]:
        left, middle, right = st.columns([3, 2, 1])
        left.write(f"**{player['Nome']}** · {player['Ruolo']} · {player['Squadra_SerieA']}")
        middle.write(f"{player.get('Prezzo_Acquisto', 0)} cr · FM {player.get('FantaMedia', 0)}")
        if right.button("Svincola", key=f"release_{squadra}_{player['Nome']}"):
            ok, message = _svincola(squadra, player["Nome"])
            (st.success if ok else st.error)(message)
            if ok:
                st.rerun()


def _render_formazione(squadra):
    st.subheader("Simulatore formazione")
    module = st.selectbox("Modulo", ["3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-3-2", "5-4-1"])
    if st.button("Calcola formazione", type="primary"):
        starters, bench, error = simula_formazione(squadra, module)
        if error:
            st.warning(error)
        else:
            st.success(f"Formazione calcolata: {len(starters)} titolari")
            st.dataframe(
                pd.DataFrame(starters)[["Nome", "Ruolo", "Squadra_SerieA", "FantaMedia"]],
                use_container_width=True,
                hide_index=True,
            )
            if bench:
                st.caption("Panchina")
                st.dataframe(
                    pd.DataFrame(bench)[["Nome", "Ruolo", "Squadra_SerieA", "FantaMedia"]],
                    use_container_width=True,
                    hide_index=True,
                )


def main():
    _default_session_state()
    if not st.session_state.get("_loaded_once"):
        load_state()
        st.session_state._loaded_once = True
    st.title("FantaManager 2026/27")
    st.caption("Gestisci le rose, controlla il mercato e simula la formazione migliore.")
    with st.sidebar:
        st.header("Gestione lega")
        squadra = st.selectbox("Squadra attiva", get_nomi_squadre(), key="active_team")
        pagina = st.radio("Sezione", ["Riepilogo", "Listone", "Rosa", "Formazione"])
        st.divider()
        if st.button("Salva dati", use_container_width=True):
            save_state()
            st.success("Dati salvati")
        if st.button("Ricarica dati", use_container_width=True):
            load_state()
            st.rerun()
    _render_dashboard(squadra)
    st.divider()
    if pagina == "Riepilogo":
        summary = riepilogo_rosa(squadra)
        st.subheader("Composizione rosa")
        st.dataframe(pd.DataFrame(summary).T, use_container_width=True)
        st.subheader("Ultimi movimenti")
        history = [item for item in st.session_state.storico_mercato if item.get("Squadra") == squadra]
        if history:
            st.dataframe(pd.DataFrame(history[-10:]), use_container_width=True, hide_index=True)
        else:
            st.info("Nessun movimento registrato")
    elif pagina == "Listone":
        _render_listone(squadra)
    elif pagina == "Rosa":
        _render_rosa(squadra)
    else:
        _render_formazione(squadra)


if __name__ == "__main__":
    main()
