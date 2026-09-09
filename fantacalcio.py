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
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata, irraggiungibile", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta, primo slot", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"Consiglio":"top","Note":"Voti alti e bonus, può diventare top", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini, solido", "Quotazione_2025_26":27, "Prezzo_Consigliato":None},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens", "Quotazione_2025_26":25, "Prezzo_Consigliato":None},
    {"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":33,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5 gol, media 6.24, centrale prolifico", "Quotazione_2025_26":33, "Prezzo_Consigliato":None},
    {"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"5 gol, centrale prolifico, solido", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":29,"FantaMedia":6.6,"Consiglio":"consigliato","Note":"3 gol, 4 assist, titolare a sinistra", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},
    {"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":27,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Sottovalutato, bonus garantiti, media buona", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualità offensiva, bonus sicuri", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Di Lorenzo","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":26,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"Sempre buona chiamata, 6-7 bonus potenziali", "Quotazione_2025_26":24, "Prezzo_Consigliato":None},
    {"Nome":"Kempf","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.2,"Consiglio":"consigliato","Note":"Certezza, voti e bonus, solido", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu, minutaggio garantito", "Quotazione_2025_26":21, "Prezzo_Consigliato":None},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite, può esplodere", "Quotazione_2025_26":11, "Prezzo_Consigliato":None},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila, centrale prolifico", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico, può giocare ovunque", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra, terzino di spinta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Çelik","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":19,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Duttile, Spalletti può schierarlo in varie occasioni", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, più appetibile, potenziale doppia-doppia", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti, doppia cifra potenziale", "Quotazione_2025_26":46, "Prezzo_Consigliato":None},
    {"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.4,"Consiglio":"top","Note":"Doppia cifra, sposta gli equilibri, top", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},
    {"Nome":"Nico Paz","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":48,"FantaMedia":7.3,"Consiglio":"top","Note":"Doppia cifra, top assoluto, crescita esponenziale", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"top","Note":"9 gol, media voto >6.5, migliore del reparto", "Quotazione_2025_26":40, "Prezzo_Consigliato":None},
    {"Nome":"Rabiot","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":42,"FantaMedia":7.0,"Consiglio":"top","Note":"6 gol, 4 assist, con Allegri era il migliore", "Quotazione_2025_26":38, "Prezzo_Consigliato":None},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista, garanzia", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Potenziale top, alla Milinkovic-Savic, può esplodere", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito, media >6.5, esperienza", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},
    {"Nome":"Koné","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza, solido", "Quotazione_2025_26":43, "Prezzo_Consigliato":None},
    {"Nome":"De Bruyne","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":46,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"Se sta bene fa la differenza, calcia rigori", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},
    {"Nome":"Barella","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":44,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Sempre Barella, secondo slot ideale, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe, coppia ideale", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, può crescere", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali, buon rapporto", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti, sottovalutato", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype, può fare bene", "Quotazione_2025_26":16, "Prezzo_Consigliato":None},
    {"Nome":"Douglas Luiz","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Intenzionato a restare, può tornare ai livelli di 2 anni fa", "Quotazione_2025_26":18, "Prezzo_Consigliato":None},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B, grande salto", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal più assist in Liga, possibile crack", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Liberali","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Giovane dal grande potenziale, spazio con Champions", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist, primo slot assoluto", "Quotazione_2025_26":90, "Prezzo_Consigliato":None},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"Consiglio":"top","Note":"Vice-cannoniere 14 gol, sposta gli equilibri", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"Consiglio":"top","Note":"13 gol, 6 assist, primo slot nonostante annata deludente", "Quotazione_2025_26":67, "Prezzo_Consigliato":None},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol, Allegri punta forte", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim, può superare doppia cifra", "Quotazione_2025_26":68, "Prezzo_Consigliato":None},
    {"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":76,"FantaMedia":7.9,"Consiglio":"top","Note":"Tornato alla Juve, Spalletti lo vuole, garanzia", "Quotazione_2025_26":69, "Prezzo_Consigliato":None},
    {"Nome":"Leao","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":72,"FantaMedia":7.8,"Consiglio":"top","Note":"Prima fascia, può migliorare, talento puro", "Quotazione_2025_26":65, "Prezzo_Consigliato":None},
    {"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":65,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Doppia cifra garantita, solido", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},
    {"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":70,"FantaMedia":7.7,"Consiglio":"consigliato","Note":"10 gol, 6 assist, centro progetto, può esplodere", "Quotazione_2025_26":58, "Prezzo_Consigliato":None},
    {"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":65,"FantaMedia":7.8,"Consiglio":"consigliato","Note":"14 gol, sorpresa 2024-25, doppia cifra sicura", "Quotazione_2025_26":64, "Prezzo_Consigliato":None},
    {"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":58,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"Sempre utile, momento della differenza, clutch", "Quotazione_2025_26":50, "Prezzo_Consigliato":None},
    {"Nome":"Davis","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":61,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"10 gol, rigorista, garanzia bonus", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":55,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Attenzione infortuni, ma potenziale top", "Quotazione_2025_26":44, "Prezzo_Consigliato":None},
    {"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"11 gol, conferma, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":48,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Doppia cifra a Bologna, solido", "Quotazione_2025_26":54, "Prezzo_Consigliato":None},
    {"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":35,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"7 gol, obiettivo doppia cifra, può crescere", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Yeboah","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":24,"FantaMedia":6.5,"Consiglio":"scommessa","Note":"Doppia cifra in Serie B, convocato al Mondiale", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Bowie","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":25,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Ex Verona, goal in Serie A li sa fare", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Alajbegovic K.","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.7,"Consiglio":"scommessa","Note":"Colpo di mercato, trequarti, attenzione hype", "Quotazione_2025_26":17, "Prezzo_Consigliato":None},
    {"Nome":"Rrahmani","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"15 gol in Rep. Ceca, nuovo attaccante titolare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Low cost, potenziale, parte dietro nelle gerarchie", "Quotazione_2025_26":7, "Prezzo_Consigliato":None},
    {"Nome":"Mendy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":15,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"2 gol in 8 partite, 2007, può esplodere", "Quotazione_2025_26":9, "Prezzo_Consigliato":None},
    {"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Vice Ramos, a 1 credito ci sta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Gattuso lo rilancia, puntatina senza esagerare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
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
    if st.session_state._ops_count % 5 == 0:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            user = st.session_state.get("current_user", "default")
            backup_name = f"fantamanager_auto_{user}_{ts}.pkl"
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
            }
            with open(backup_name, "wb") as f:
                pickle.dump(data, f)
            st.toast(f"💾 Auto-backup #{st.session_state._ops_count} salvato", icon="💾")
        except Exception:
            pass

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

def get_db_info(nome):
    db = st.session_state.giocatori_db
    match = db[db["Nome"].str.lower() == nome.lower()]
    if not match.empty:
        return match.iloc[0].to_dict()
    nome_match = fuzzy_match(nome, db["Nome"].tolist())
    if nome_match:
        match = db[db["Nome"] == nome_match]
        if not match.empty:
            return match.iloc[0].to_dict()
    return None

# ============================================================
# BUSINESS LOGIC
# ============================================================
def calcola_prezzo_consigliato(g_info, stats_df=None):
    nome = g_info.get("Nome", "")
    ruolo = g_info.get("Ruolo", "C")
    quot = float(g_info.get("Quotazione", 10))
    fm = float(g_info.get("FantaMedia", 6.0))
    fascia = g_info.get("Consiglio", "consigliato")

    base = quot
    medie_ruolo = {"P": 5.5, "D": 6.2, "C": 6.8, "A": 7.5}
    media_rif = medie_ruolo.get(ruolo, 6.5)
    delta_fm = fm - media_rif
    fattore_fm = 1 + (delta_fm * 0.15)
    fattore_fascia = {"top": 1.15, "consigliato": 1.0, "scommessa": 0.85}.get(fascia, 1.0)

    db = st.session_state.giocatori_db
    svinc = get_svincolati(db)
    total_fascia = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == fascia)])
    rimasti = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == fascia)])
    fattore_scarsita = 1 + max(0, (3 - rimasti)) * 0.05 if total_fascia > 0 else 1.0

    fattore_trend = 1.0
    trend_note = ""
    if stats_df is not None and not stats_df.empty and "Nome" in stats_df.columns:
        g_stats = stats_df[stats_df["Nome"].str.lower() == nome.lower()]
        if g_stats.empty:
            nome_fuzzy = fuzzy_match(nome, stats_df["Nome"].tolist())
            if nome_fuzzy:
                g_stats = stats_df[stats_df["Nome"] == nome_fuzzy]
        if not g_stats.empty:
            if "Stagione" in g_stats.columns:
                g_stats = g_stats.sort_values("Stagione", ascending=False)
            ultima = g_stats.iloc[0]
            if "FantaMedia" in ultima and pd.notna(ultima["FantaMedia"]):
                fm_storica = float(ultima["FantaMedia"])
                if fm > fm_storica + 0.3:
                    fattore_trend += 0.10
                    trend_note = " 📈 Trend in crescita"
                elif fm < fm_storica - 0.3:
                    fattore_trend -= 0.10
                    trend_note = " 📉 Trend in calo"
                else:
                    trend_note = " ➡️ Trend stabile"
            gol = float(ultima.get("Gol", 0)) if "Gol" in ultima and pd.notna(ultima.get("Gol")) else 0
            if ruolo in ["D", "C"] and gol >= 5:
                fattore_trend += 0.08
                trend_note += f" | ⚽ {int(gol)} gol"
            if ruolo == "A" and gol >= 15:
                fattore_trend += 0.12
                trend_note += f" | ⚽ {int(gol)} gol"
            if "Partite" in ultima and pd.notna(ultima["Partite"]):
                partite = int(ultima["Partite"])
                if partite >= 30:
                    fattore_trend += 0.05
                    trend_note += f" | 🏃 {partite} presenze"

    indice_affare = fm / max(quot, 1)
    if indice_affare > 0.20:
        fattore_affare = 1.0
    elif indice_affare > 0.15:
        fattore_affare = 0.95
    else:
        fattore_affare = 0.90

    prezzo = base * fattore_fm * fattore_fascia * fattore_scarsita * fattore_trend * fattore_affare
    prezzo = max(1, round(prezzo))

    spiegazione = (
        f"**Base listone:** {int(base)}cr\n"
        f"**FantaMedia:** {fm} (media ruolo {ruolo}: {media_rif}) → fattore {fattore_fm:.2f}\n"
        f"**Fascia:** {fascia} → fattore {fattore_fascia:.2f}\n"
        f"**Scarsità:** {rimasti}/{total_fascia} rimasti → fattore {fattore_scarsita:.2f}\n"
        f"**Indice affare:** {indice_affare:.3f} → fattore {fattore_affare:.2f}\n"
    )
    if trend_note:
        spiegazione += f"**Statistiche:**{trend_note} → fattore {fattore_trend:.2f}\n"
    spiegazione += f"\n**💡 Prezzo consigliato: {prezzo}cr**"
    return prezzo, spiegazione

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

def mostra_statistiche_giocatore(nome, stats_df):
    if stats_df is None or stats_df.empty or "Nome" not in stats_df.columns:
        return None
    g_stats = stats_df[stats_df["Nome"].str.lower() == nome.lower()]
    if g_stats.empty:
        nome_fuzzy = fuzzy_match(nome, stats_df["Nome"].tolist())
        if nome_fuzzy:
            g_stats = stats_df[stats_df["Nome"] == nome_fuzzy]
    if g_stats.empty:
        return None
    return g_stats.sort_values("Stagione") if "Stagione" in g_stats.columns else g_stats

def _get_fm_2627(nome):
    if "stats_per_stagione" not in st.session_state:
        return None
    if "2026-27" not in st.session_state.stats_per_stagione:
        return None
    s2627 = st.session_state.stats_per_stagione["2026-27"]
    if s2627.empty or "Nome" not in s2627.columns:
        return None
    match = s2627[s2627["Nome"].str.lower() == nome.lower()]
    if match.empty:
        nm = fuzzy_match(nome, s2627["Nome"].tolist())
        if nm:
            match = s2627[s2627["Nome"] == nm]
    if not match.empty and "FantaMedia" in match.columns and pd.notna(match.iloc[0]["FantaMedia"]):
        return float(match.iloc[0]["FantaMedia"])
    return None

def simula_formazione(squadra_nome, modulo):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    if not rosa:
        return 0, [], []
    enriched = []
    for g in rosa:
        g_copy = dict(g)
        fm_2627 = _get_fm_2627(g["Nome"])
        if fm_2627 is not None:
            g_copy["FantaMedia_Usata"] = fm_2627
            g_copy["FM_Origine"] = "📊 2026/27"
        else:
            g_copy["FantaMedia_Usata"] = g.get("FantaMedia", 0)
            g_copy["FM_Origine"] = "📋 Listone"
        enriched.append(g_copy)
    df = pd.DataFrame(enriched)
    try:
        d, c, a = map(int, modulo.split("-"))
    except:
        return 0, [], []
    p = 1
    titolari = []
    panchina = []
    for ruolo, n in [("P", p), ("D", d), ("C", c), ("A", a)]:
        subset = df[df["Ruolo"] == ruolo].sort_values("FantaMedia_Usata", ascending=False)
        presi = subset.head(n)
        rimasti = subset.iloc[n:]
        for _, row in presi.iterrows():
            titolari.append(row.to_dict())
        for _, row in rimasti.iterrows():
            panchina.append(row.to_dict())
    fm_tit = sum(g.get("FantaMedia_Usata", 0) for g in titolari)
    return round(fm_tit, 2), panchina, titolari

def arricchisci_con_stats_2627(df_listone):
    df = df_listone.copy()
    if "stats_per_stagione" not in st.session_state:
        return df
    if "2026-27" not in st.session_state.stats_per_stagione:
        return df
    stats_2627 = st.session_state.stats_per_stagione["2026-27"].copy()
    if stats_2627.empty or "Nome" not in stats_2627.columns:
        return df
    stats_2627["Nome_lower"] = stats_2627["Nome"].str.lower().str.strip()
    df["Nome_lower"] = df["Nome"].str.lower().str.strip()
    cols_stats = [c for c in stats_2627.columns if c not in ["Nome", "Stagione", "Nome_lower"]]
    if "FantaMedia" in cols_stats and "FantaMedia" in df.columns:
        df = df.drop(columns=["FantaMedia"])
    if "Gol" in cols_stats and "Gol" in df.columns:
        df = df.drop(columns=["Gol"])
    if "Assist" in cols_stats and "Assist" in df.columns:
        df = df.drop(columns=["Assist"])
    merge_df = stats_2627[["Nome_lower"] + [c for c in cols_stats if c not in df.columns]].copy()
    df = df.merge(merge_df, on="Nome_lower", how="left")
    df = df.drop(columns=["Nome_lower"])
    if "FantaMedia" in df.columns:
        df["FantaMedia"] = pd.to_numeric(df["FantaMedia"], errors="coerce")
    return df

def calcola_indice_titolarita(row, stats_2627=None):
    fm = float(row.get("FantaMedia", 6.0))
    fascia = row.get("Consiglio", "consigliato")
    quot = float(row.get("Quotazione", 10))
    nome = str(row.get("Nome", ""))

    base = min(50, (fm / 10) * 50)
    bonus_fascia = {"top": 25, "consigliato": 15, "scommessa": 5}.get(fascia, 10)
    bonus_presenze = 12.5
    if stats_2627 is not None and not stats_2627.empty and "Nome" in stats_2627.columns:
        match = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
        if match.empty:
            nm = fuzzy_match(nome, stats_2627["Nome"].tolist())
            if nm:
                match = stats_2627[stats_2627["Nome"] == nm]
        if not match.empty and "Partite" in match.columns and pd.notna(match.iloc[0]["Partite"]):
            partite = int(match.iloc[0]["Partite"])
            bonus_presenze = min(25, (partite / 38) * 25)

    bonus_quot = min(10, max(0, (quot / 100) * 10))
    totale = base + bonus_fascia + bonus_presenze + bonus_quot
    return min(100, round(totale, 1))

# ============================================================
# ANALISI BUDGET ASTA
# ============================================================
def budget_libero_effettivo(squadra_nome):
    riep = riepilogo_rosa(squadra_nome)
    crediti = riep["crediti"]
    posti_mancanti = riep["tot_mancanti"]
    budget_minimo = posti_mancanti * 1
    return max(0, crediti - budget_minimo)

def offerta_massima_realistica(squadra_nome, ruolo):
    riep = riepilogo_rosa(squadra_nome)
    crediti = riep["crediti"]
    posti_mancanti = riep["tot_mancanti"]
    budget_sicurezza = posti_mancanti * 2
    return max(0, crediti - budget_sicurezza)

def spese_per_ruolo(squadra_nome):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    spese = {"P": {"tot": 0, "n": 0, "avg": 0}, "D": {"tot": 0, "n": 0, "avg": 0},
             "C": {"tot": 0, "n": 0, "avg": 0}, "A": {"tot": 0, "n": 0, "avg": 0}}
    for g in rosa:
        r = g.get("Ruolo", "C")
        costo = g.get("Costo_Acquisto", 0)
        if r in spese:
            spese[r]["tot"] += costo
            spese[r]["n"] += 1
    for r in spese:
        if spese[r]["n"] > 0:
            spese[r]["avg"] = round(spese[r]["tot"] / spese[r]["n"], 1)
    return spese

def fuga_top_tracker():
    db = st.session_state.giocatori_db.copy()
    idx = get_player_index()
    db["Proprietario"] = db["Nome"].apply(lambda x: idx.get(x.lower(), "Svincolato"))
    svinc = db[db["Proprietario"] == "Svincolato"]
    result = {}
    for ruolo in ["P", "D", "C", "A"]:
        total_top = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == "top")])
        rimasti_top = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == "top")])
        total_cons = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == "consigliato")])
        rimasti_cons = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == "consigliato")])
        result[ruolo] = {
            "top_totali": total_top, "top_rimasti": rimasti_top,
            "cons_totali": total_cons, "cons_rimasti": rimasti_cons,
            "pct_top_rimasti": round((rimasti_top / max(total_top, 1)) * 100, 1),
            "pct_cons_rimasti": round((rimasti_cons / max(total_cons, 1)) * 100, 1),
        }
    return result

def alert_scarsita_top(ruolo):
    tracker = fuga_top_tracker()
    if ruolo in tracker:
        return tracker[ruolo]["pct_top_rimasti"] < 30 and tracker[ruolo]["top_rimasti"] <= 2
    return False

def calcola_fascia_da_storico(nome: str, stats_per_stagione: dict, ruolo: str = "C") -> str:
    storico = []
    for stagione, df in stats_per_stagione.items():
        if df.empty or "Nome" not in df.columns:
            continue
        match = df[df["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(
                nome.lower(),
                [n.lower() for n in df["Nome"].dropna().unique().tolist()],
                n=1, cutoff=0.8
            )
            if close:
                match = df[df["Nome"].str.lower() == close[0]]
        if not match.empty:
            row = match.iloc[0].to_dict()
            row["Stagione"] = stagione
            storico.append(row)

    if not storico:
        return "consigliato"

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def safe_int(val, default=0):
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return default

    fm_list = [safe_float(r.get("FantaMedia")) for r in storico if safe_float(r.get("FantaMedia")) > 0]
    pres_list = [safe_int(r.get("Partite")) for r in storico if safe_int(r.get("Partite")) > 0]
    gol_list = [safe_int(r.get("Gol")) for r in storico]
    ast_list = [safe_int(r.get("Assist")) for r in storico]

    if not fm_list:
        return "consigliato"

    fm_media = sum(fm_list) / len(fm_list)
    pres_media = sum(pres_list) / len(pres_list) if pres_list else 0
    gol_totali = sum(gol_list)
    ast_totali = sum(ast_list)
    stagioni_giocate = len(fm_list)

    try:
        df_storico = pd.DataFrame(storico)
        df_storico_sorted = df_storico.sort_values("Stagione")
        fm_ultima = safe_float(df_storico_sorted.iloc[-1].get("FantaMedia"), fm_media)
    except Exception:
        fm_ultima = fm_list[-1]

    soglie = {
        "P": {"top_fm": 5.8, "cons_fm": 5.4, "top_pres": 25, "cons_pres": 15},
        "D": {"top_fm": 6.5, "cons_fm": 6.0, "top_pres": 28, "cons_pres": 18},
        "C": {"top_fm": 6.8, "cons_fm": 6.3, "top_pres": 28, "cons_pres": 18},
        "A": {"top_fm": 7.2, "cons_fm": 6.8, "top_pres": 28, "cons_pres": 18},
    }
    s = soglie.get(ruolo, soglie["C"])
    punteggio = 0.0

    if fm_media >= s["top_fm"]:
        punteggio += 40
    elif fm_media >= s["cons_fm"]:
        punteggio += 25
    else:
        punteggio += max(0, (fm_media / s["cons_fm"]) * 15)

    if pres_media >= s["top_pres"]:
        punteggio += 30
    elif pres_media >= s["cons_pres"]:
        punteggio += 18
    else:
        punteggio += max(0, (pres_media / s["cons_pres"]) * 10)

    if fm_ultima >= fm_media + 0.3:
        punteggio += 20
    elif fm_ultima >= fm_media - 0.3:
        punteggio += 12
    else:
        punteggio += max(0, 5 + (fm_ultima - fm_media) * 10)

    if ruolo in ["D", "C"]:
        bonus_per_stag = (gol_totali + ast_totali) / max(stagioni_giocate, 1)
        if bonus_per_stag >= 8:
            punteggio += 10
        elif bonus_per_stag >= 4:
            punteggio += 5
    elif ruolo == "A":
        bonus_per_stag = gol_totali / max(stagioni_giocate, 1)
        if bonus_per_stag >= 15:
            punteggio += 10
        elif bonus_per_stag >= 10:
            punteggio += 5

    if punteggio >= 70:
        return "top"
    elif punteggio >= 42:
        return "consigliato"
    else:
        return "scommessa"

def applica_fasce_automatiche():
    db = st.session_state.giocatori_db.copy()
    stats = st.session_state.get("stats_per_stagione", {})
    if not stats:
        st.warning("⚠️ Nessuna statistica storica caricata. Vai su 📈 Statistiche Storiche e carica almeno una stagione.")
        return
    conteggi = {"top": 0, "consigliato": 0, "scommessa": 0}
    for idx, row in db.iterrows():
        nome = row.get("Nome", "")
        ruolo = row.get("Ruolo", "C")
        nuova_fascia = calcola_fascia_da_storico(nome, stats, ruolo)
        db.at[idx, "Consiglio"] = nuova_fascia
        conteggi[nuova_fascia] = conteggi.get(nuova_fascia, 0) + 1
    st.session_state.giocatori_db = db
    save_state()
    st.success(
        f"✅ Fasce ricalcolate da storico!  "
        f"⭐ Top: {conteggi['top']} | 👍 Consigliati: {conteggi['consigliato']} | 🎲 Scommesse: {conteggi['scommessa']}"
    )

def flame_indicator(nome: str, stats_per_stagione: dict) -> str:
    if not stats_per_stagione:
        return ""
    fm_vals = []
    for stagione, df in sorted(stats_per_stagione.items()):
        if df.empty or "Nome" not in df.columns:
            continue
        match = df[df["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(nome.lower(), [n.lower() for n in df["Nome"].dropna().unique().tolist()], n=1, cutoff=0.8)
            if close:
                match = df[df["Nome"].str.lower() == close[0]]
        if not match.empty and "FantaMedia" in match.columns and pd.notna(match.iloc[0]["FantaMedia"]):
            try:
                fm_vals.append(float(match.iloc[0]["FantaMedia"]))
            except:
                pass
    if len(fm_vals) < 2:
        return ""
    delta = fm_vals[-1] - fm_vals[-2]
    if delta > 0.4:
        flames = "🔥🔥🔥"
        color = "#ff4500"
        label = "HOT"
    elif delta > 0.2:
        flames = "🔥🔥"
        color = "#ff8c00"
        label = "WARM"
    elif delta > 0.05:
        flames = "🔥"
        color = "#eab308"
        label = "RISING"
    else:
        return ""
    return f'<div style="display:inline-flex;align-items:center;gap:4px;background:{color}18;border:1px solid {color}40;padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:bold;color:{color};margin-left:4px;">{flames} {label} +{delta:.2f}</div>'

def render_flip_card(row, stats_per_stagione=None, stats_2627=None):
    nome = row["Nome"] if hasattr(row, "__getitem__") else row.get("Nome", "N/D")
    ruolo = row["Ruolo"] if hasattr(row, "__getitem__") else row.get("Ruolo", "C")
    sa = row.get("Squadra_SerieA", "N/D") if hasattr(row, "get") else row.get("Squadra_SerieA", "N/D")
    fm = row.get("FantaMedia", 0) if hasattr(row, "get") else row.get("FantaMedia", 0)
    quot = int(row.get("Quotazione", 0)) if hasattr(row, "get") else int(row.get("Quotazione", 0))
    fascia = row.get("Consiglio", "consigliato") if hasattr(row, "get") else row.get("Consiglio", "consigliato")
    pc = row.get("Prezzo_Consigliato") if hasattr(row, "get") else row.get("Prezzo_Consigliato")
    pc_txt = f"💡 {int(pc)}cr" if pd.notna(pc) else ""

    colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
    colore = colori_ruolo.get(ruolo, "#888")
    badge_fascia = {"top": "⭐ TOP", "consigliato": "👍 CONSIGLIATO", "scommessa": "🎲 SCOMMESSA"}.get(fascia, "")
    flame_badge = flame_indicator(nome, stats_per_stagione) if stats_per_stagione else ""

    pc_premium = pc
    if pd.isna(pc_premium) or pc_premium is None:
        try:
            stats_df_prem = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
            pc_premium, _ = calcola_prezzo_consigliato(row.to_dict() if hasattr(row, "to_dict") else dict(row), stats_df_prem)
        except Exception:
            pc_premium = quot
    is_premium = (pc_premium if pd.notna(pc_premium) else quot) > 40
    premium_badge = '<span class="badge-premium">💎 PREMIUM</span>' if is_premium else ""
    premium_class = " card-premium" if is_premium else ""

    front_html = f'''<div style="background:linear-gradient(135deg, rgba(30,30,63,0.95) 0%, rgba(42,42,74,0.8) 100%);backdrop-filter:blur(10px);border-radius:12px;padding:14px;height:100%;box-sizing:border-box;border-left:4px solid {colore};box-shadow:0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);display:flex;flex-direction:column;justify-content:space-between;"><div><div style="font-size:1.1em;font-weight:bold;color:#fff;text-shadow:0 2px 4px rgba(0,0,0,0.5);">{nome}</div><div style="font-size:0.85em;color:#aaa;">{sa} | <span style="color:{colore};font-weight:600;">{ruolo}</span></div></div><div style="text-align:center;margin:8px 0;"><div style="font-size:2em;font-weight:bold;color:#ffd700;">{fm}</div><div style="font-size:0.75em;color:#888;">FantaMedia</div></div><div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:center;"><span style="background:{colore}30;color:{colore};padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:600;border:1px solid {colore}40;">{badge_fascia}</span><span style="background:rgba(26,26,46,0.6);color:#ddd;padding:2px 8px;border-radius:12px;font-size:0.7em;">{quot}cr</span>{pc_txt}</div>{flame_badge}{premium_badge}</div>'''

    stats_html = _build_stats_html(nome, stats_per_stagione if stats_per_stagione else {})
    back_html = f'''<div style="background:linear-gradient(135deg, #0f0f24 0%, #1a1a2e 100%);border-radius:12px;padding:14px;height:100%;box-sizing:border-box;border:1px solid {colore}40;box-shadow:0 8px 32px rgba(0,0,0,0.4);display:flex;flex-direction:column;justify-content:center;overflow:hidden;"><div style="font-size:0.85em;color:#00d26a;font-weight:bold;margin-bottom:6px;">📊 {nome}</div><div style="overflow-y:auto;max-height:140px;">{stats_html}</div></div>'''

    return f'''<div class="flip-card{premium_class}" style="height:200px;margin-bottom:10px;"><div class="flip-card-inner"><div class="flip-card-front">{front_html}</div><div class="flip-card-back">{back_html}</div></div></div>'''

def _build_stats_html(nome, stats_per_stagione):
    rows = []
    fm_points = []
    stagioni_label = []
    for stagione, df in sorted(stats_per_stagione.items()):
        if df.empty or "Nome" not in df.columns:
            continue
        match = df[df["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(
                nome.lower(),
                [n.lower() for n in df["Nome"].dropna().unique().tolist()],
                n=1, cutoff=0.8
            )
            if close:
                match = df[df["Nome"].str.lower() == close[0]]
        if not match.empty:
            r = match.iloc[0]
            fm = r.get("FantaMedia", "—")
            gol = r.get("Gol", "—")
            ast = r.get("Assist", "—")
            part = r.get("Partite", "—")
            rig = r.get("Rigori", "—")
            rows.append(f'<tr><td style="padding:4px 8px;color:#aaa;font-size:0.8em;">{stagione}</td><td style="padding:4px 8px;color:#ffd700;font-size:0.85em;font-weight:bold;">{fm}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{gol}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{ast}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{part}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{rig}</td></tr>')
            try:
                fm_val = float(fm)
                if fm_val > 0:
                    fm_points.append(fm_val)
                    stagioni_label.append(stagione)
            except (TypeError, ValueError):
                pass

    chart_svg = ""
    if len(fm_points) >= 2:
        w, h = 280, 80
        pad = 10
        max_fm = max(fm_points + [8.0])
        min_fm = min(fm_points + [4.0])
        rng = max_fm - min_fm if max_fm != min_fm else 1
        n = len(fm_points)
        pts = []
        for i, val in enumerate(fm_points):
            x = pad + (i / (n - 1)) * (w - 2 * pad)
            y = h - pad - ((val - min_fm) / rng) * (h - 2 * pad)
            pts.append(f"{x:.1f},{y:.1f}")
        polyline = " ".join(pts)
        circles = ""
        for i, val in enumerate(fm_points):
            x = pad + (i / (n - 1)) * (w - 2 * pad)
            y = h - pad - ((val - min_fm) / rng) * (h - 2 * pad)
            circles += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#00d26a"/><text x="{x:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="#ffd700" font-size="8">{val:.1f}</text>'
        labels = ""
        for i, lbl in enumerate(stagioni_label):
            x = pad + (i / (n - 1)) * (w - 2 * pad)
            labels += f'<text x="{x:.1f}" y="{h-2:.1f}" text-anchor="middle" fill="#888" font-size="7">{lbl}</text>'
        chart_svg = f'<div style="margin:10px 0;"><svg width="{w}" height="{h}" style="background:#0f0f24;border-radius:6px;"><polyline points="{polyline}" fill="none" stroke="#00d26a" stroke-width="2"/>{circles}{labels}</svg></div>'

    if not rows:
        return '<div style="padding:8px;color:#888;font-size:0.8em;text-align:center;">📭 Nessuno storico disponibile</div>'
    return chart_svg + f'<table style="width:100%;border-collapse:collapse;margin-top:8px;"><thead><tr style="border-bottom:1px solid #2a2a4a;"><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">Stagione</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">FM</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">⚽</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🅰️</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🏃</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🎯</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'

def aggiungi_squadra(nome: str, crediti: int = None):
    if "nomi_squadre" not in st.session_state:
        st.session_state.nomi_squadre = list(NOMI_SQUADRE)
    if "squadre" not in st.session_state:
        st.session_state.squadre = {}
    if "simulatore_rosa" not in st.session_state:
        st.session_state.simulatore_rosa = {sq: {"P": [], "D": [], "C": [], "A": []} for sq in st.session_state.nomi_squadre}
    nome = nome.strip().upper()
    if not nome:
        return False, "Nome vuoto"
    if nome in st.session_state.nomi_squadre:
        return False, "Squadra già esistente"
    st.session_state.nomi_squadre.append(nome)
    st.session_state.squadre[nome] = {"crediti": crediti or st.session_state.get("crediti_iniziali", CREDITI_INIZIALI), "rosa": []}
    st.session_state.simulatore_rosa[nome] = {"P": [], "D": [], "C": [], "A": []}
    invalidate_cache()
    save_state()
    return True, f"Squadra {nome} aggiunta"

def rimuovi_squadra(nome: str):
    if "nomi_squadre" not in st.session_state:
        st.session_state.nomi_squadre = list(NOMI_SQUADRE)
    if "squadre" not in st.session_state:
        st.session_state.squadre = {}
    if "prestiti" not in st.session_state:
        st.session_state.prestiti = []
    if "contratti" not in st.session_state:
        st.session_state.contratti = {}
    if "simulatore_rosa" not in st.session_state:
        st.session_state.simulatore_rosa = {sq: {"P": [], "D": [], "C": [], "A": []} for sq in st.session_state.nomi_squadre}
    nome = nome.strip().upper()
    if nome not in st.session_state.nomi_squadre:
        return False, "Squadra non trovata"
    if nome in st.session_state.squadre:
        del st.session_state.squadre[nome]
    st.session_state.prestiti = [p for p in st.session_state.prestiti if p["Da"] != nome and p["A"] != nome]
    st.session_state.contratti = {k: v for k, v in st.session_state.contratti.items() if v.get("squadra") != nome}
    if nome in st.session_state.simulatore_rosa:
        del st.session_state.simulatore_rosa[nome]
    st.session_state.nomi_squadre.remove(nome)
    invalidate_cache()
    save_state()
    return True, f"Squadra {nome} rimossa"

# ============================================================
# AUTH — LOGIN / REGISTRAZIONE
# ============================================================
def render_login():
    st.title("🔐 FantaManager 2026/27 — Accesso")
    st.markdown("Accedi o crea un account per gestire il tuo fantacalcio in modo indipendente. Ogni utente ha il proprio salvataggio separato.")

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
                elif len(new_pass) < 4:
                    st.error("Password troppo corta (min 4 caratteri)")
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

# ============================================================
# INIZIALIZZAZIONE
# ============================================================
require_auth()

if "initialized" not in st.session_state:
    st.session_state.squadre = {}
    st.session_state.storico_mercato = []
    st.session_state.watchlist = []
    st.session_state.prestiti = []
    st.session_state.contratti = {}
    st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
    if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
        st.session_state.giocatori_db["Prezzo_Consigliato"] = None
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
# WIZARD
# ============================================================
def check_wizard_needed():
    if st.session_state.get("wizard_completato", False):
        return False
    return all(len(st.session_state.squadre[sq]["rosa"]) == 0 for sq in get_nomi_squadre())

def render_wizard():
    st.header("⚽ Benvenuto in FantaManager 2026/27")
    step = st.session_state.get("wizard_step", 1)
    progress = (step / 4) * 100
    st.progress(int(progress), text=f"Passaggio {step} di 4")

    if step == 1:
        st.subheader("1. Listone Giocatori")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Usa Listone Default", use_container_width=True):
                st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
                st.session_state.wizard_step = 2
                save_state()
                st.rerun()
        with c2:
            if st.button("⏭️ Salta per ora", use_container_width=True):
                st.session_state.wizard_step = 2
                st.rerun()

    elif step == 2:
        st.subheader("2. Crediti Iniziali")
        cred = st.number_input("Crediti iniziali per squadra", min_value=10, max_value=500, value=CREDITI_INIZIALI, step=5)
        if st.button("💾 Imposta Crediti", type="primary", use_container_width=True):
            st.session_state.crediti_iniziali = cred
            for sq in get_nomi_squadre():
                st.session_state.squadre[sq]["crediti"] = cred
            st.session_state.wizard_step = 3
            save_state()
            st.rerun()

    elif step == 3:
        st.subheader("3. Importa Rose Pregresse (Opzionale)")
        if st.button("⏭️ Salta", use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()

    elif step == 4:
        st.subheader("4. Pronto!")
        st.success("Setup completato. Buon divertimento!")
        if st.button("🚀 Inizia", type="primary", use_container_width=True):
            st.session_state.wizard_completato = True
            save_state()
            st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ FantaManager")
    st.caption("2026/27 — 10 Squadre")
    st.markdown(f"👤 **Account:** `{st.session_state.get('current_user', 'N/D')}`")
    if st.button("🚪 Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.subheader("👥 Gestione Fantallenatori")
    st.caption(f"Attuali: {len(get_nomi_squadre())} squadre")
    with st.expander("➕ Aggiungi / ➖ Rimuovi"):
        nuova_sq = st.text_input("Nuova squadra", key="new_sq_name", placeholder="es. MARCO")
        cred_sq = st.number_input("Crediti iniziali", min_value=10, max_value=500, value=int(st.session_state.get("crediti_iniziali", CREDITI_INIZIALI)), step=5, key="new_sq_cred")
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
            if st.button("➖ Rimuovi Squadra", use_container_width=True):
                rosa_sq = st.session_state.squadre.get(sq_da_rimuovere, {}).get("rosa", [])
                if rosa_sq:
                    st.warning(f"⚠️ {sq_da_rimuovere} ha {len(rosa_sq)} giocatori. Verranno svincolati e i prestiti annullati.")
                ok, msg = rimuovi_squadra(sq_da_rimuovere)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    st.markdown("---")

    if st.session_state.get("_undo_stack"):
        if st.button("↩️ Annulla Ultima Operazione", use_container_width=True):
            if StateManager.undo():
                save_state()
                st.toast("✅ Operazione annullata!", icon="↩️")
                st.rerun()
            else:
                st.toast("⚠️ Impossibile annullare", icon="⚠️")

    st.subheader("💾 Backup Rapido")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salva", use_container_width=True):
            save_state()
            st.toast("💾 Salvataggio completato", icon="✅")
    with c2:
        if st.button("📂 Carica", use_container_width=True):
            if load_state():
                st.toast("📂 Stato caricato!", icon="✅")
                st.rerun()
            else:
                st.toast("⚠️ Nessun salvataggio trovato", icon="⚠️")

    save_data = {
        "nomi_squadre": st.session_state.get("nomi_squadre", list(NOMI_SQUADRE)),
        "squadre": st.session_state.squadre,
        "storico_mercato": st.session_state.storico_mercato,
        "watchlist": st.session_state.watchlist,
        "prestiti": st.session_state.prestiti,
        "contratti": st.session_state.contratti,
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if not st.session_state.stats_storiche.empty else [],
        "stats_per_stagione": {k: v.to_dict(orient="records") for k, v in st.session_state.get("stats_per_stagione", {}).items()},
        "quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if not st.session_state.quotazioni_2025_26.empty else [],
        "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
        "wizard_completato": st.session_state.get("wizard_completato", False),
        "simulatore_rosa": st.session_state.get("simulatore_rosa", {sq: {"P": [], "D": [], "C": [], "A": []} for sq in st.session_state.get("nomi_squadre", list(NOMI_SQUADRE))}),
    }
    json_bytes = json.dumps(save_data, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        label="⬇️ Scarica Stato (JSON)",
        data=json_bytes,
        file_name=f"fantamanager_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("📂 Ripristina da PC")
    up_json = st.file_uploader("File JSON stato", type=["json"], key="up_json")
    if "last_json_key" not in st.session_state:
        st.session_state.last_json_key = ""
    if up_json is not None:
        file_key = f"{up_json.name}_{up_json.size}"
        if file_key != st.session_state.last_json_key:
            try:
                data = json.load(up_json)
                st.session_state.nomi_squadre = data.get("nomi_squadre", list(NOMI_SQUADRE))
                st.session_state.squadre = data.get("squadre", {})
                st.session_state.storico_mercato = data.get("storico_mercato", [])
                st.session_state.watchlist = data.get("watchlist", [])
                st.session_state.prestiti = data.get("prestiti", [])
                st.session_state.contratti = data.get("contratti", {})
                db_data = data.get("giocatori_db", [])
                st.session_state.giocatori_db = pd.DataFrame(db_data) if db_data else pd.DataFrame(LISTONE_DEFAULT)
                if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
                    st.session_state.giocatori_db["Prezzo_Consigliato"] = None
                stats_data = data.get("stats_storiche", [])
                st.session_state.stats_storiche = pd.DataFrame(stats_data) if stats_data else pd.DataFrame()
                st.session_state.stats_per_stagione = {k: pd.DataFrame(v) if v else pd.DataFrame() for k, v in data.get("stats_per_stagione", {}).items()}
                q25_data = data.get("quotazioni_2025_26", [])
                st.session_state.quotazioni_2025_26 = pd.DataFrame(q25_data) if q25_data else pd.DataFrame()
                st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
                st.session_state.wizard_completato = data.get("wizard_completato", False)
                st.session_state.simulatore_rosa = data.get("simulatore_rosa", {sq: {"P": [], "D": [], "C": [], "A": []} for sq in get_nomi_squadre()})
                st.session_state.last_json_key = file_key
                invalidate_cache()
                save_state()
                st.success("✅ Stato ripristinato con successo!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nel caricamento del file: {e}")

# ============================================================
# INTERFACCIA PRINCIPALE & MENU
# ============================================================
if check_wizard_needed():
    render_wizard()
    st.stop()

st.title("⚽ FantaManager 2026/27 — Dashboard")

menu = st.sidebar.selectbox(
    "🧭 Navigazione",
    [
        "📋 Listone & Quotazioni",
        "👥 Rose & Squadre",
        "🔨 Mercato & Asta Live",
        "🔄 Prestiti & Contratti",
        "📈 Statistiche Storiche",
        "📊 Statistiche Avanzate",
        "⭐ Watchlist",
        "🏟️ Simulatore Formazione",
        "⚙️ Impostazioni & Reset"
    ]
)

# ============================================================
# SEZIONE: 📋 LISTONE & QUOTAZIONI
# ============================================================
if menu == "📋 Listone & Quotazioni":
    st.header("📋 Listone Giocatori & Quotazioni")
    st.markdown("Consulta il listone ufficiale, filtra per ruolo, squadra o fascia, e analizza i prezzi consigliati dall'AI.")

    db = st.session_state.giocatori_db.copy()
    db = arricchisci_con_stats_2627(db)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_ruolo = st.selectbox("Filtra Ruolo", ["Tutti", "P", "D", "C", "A"])
    with col2:
        squadre_sa = ["Tutte"] + sorted(db["Squadra_SerieA"].dropna().unique().tolist())
        filtro_sa = st.selectbox("Filtra Squadra Serie A", squadre_sa)
    with col3:
        filtro_fascia = st.selectbox("Filtra Fascia", ["Tutte", "top", "consigliato", "scommessa"])
    with col4:
        filtro_prop = st.selectbox("Proprietario", ["Tutti", "Svincolati"] + get_nomi_squadre())

    search_query = st.text_input("🔍 Cerca giocatore", placeholder="Es. Lautaro, Svilar, Pulisic...")

    filtered_db = db.copy()
    if filtro_ruolo != "Tutti":
        filtered_db = filtered_db[filtered_db["Ruolo"] == filtro_ruolo]
    if filtro_sa != "Tutte":
        filtered_db = filtered_db[filtered_db["Squadra_SerieA"] == filtro_sa]
    if filtro_fascia != "Tutte":
        filtered_db = filtered_db[filtered_db["Consiglio"] == filtro_fascia]
    if search_query.strip():
        filtered_db = filtered_db[filtered_db["Nome"].str.contains(search_query.strip(), case=False, na=False)]

    idx_map = get_player_index()
    if filtro_prop == "Svincolati":
        filtered_db = filtered_db[~filtered_db["Nome"].str.lower().isin(idx_map.keys())]
    elif filtro_prop != "Tutti":
        nomi_prop = [n.lower() for n, sq in idx_map.items() if sq == filtro_prop]
        filtered_db = filtered_db[filtered_db["Nome"].str.lower().isin(nomi_prop)]

    st.caption(f"Mostrando {len(filtered_db)} giocatori su {len(db)}")

    cols = st.columns(3)
    for i, (_, row) in enumerate(filtered_db.iterrows()):
        col = cols[i % 3]
        with col:
            stats_storiche_dict = st.session_state.get("stats_per_stagione", {})
            st.markdown(render_flip_card(row, stats_storiche_dict, stats_per_stagione.get("2026-27") if "stats_per_stagione" in st.session_state else None), unsafe_allow_html=True)

# ============================================================
# SEZIONE: 👥 ROSE & SQUADRE
# ============================================================
elif menu == "👥 Rose & Squadre":
    st.header("👥 Rose & Gestione Squadre")
    st.markdown("Visualizza i roster completi delle 10 squadre, i crediti residui e la copertura dei ruoli.")

    riepiloghi = get_all_riepiloghi()
    nomi_squadre = get_nomi_squadre()

    cols = st.columns(min(len(nomi_squadre), 5))
    for i, sq in enumerate(nomi_squadre):
        col = cols[i % len(cols)]
        riep = riepiloghi[sq]
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <h4>{sq}</h4>
                <p>💰 <b>{riep['crediti']}</b> cr<br>
                👥 <b>{riep['tot_posseduti']}/28</b><br>
                Mancanti: <b>{riep['tot_mancanti']}</b></p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    sq_sel = st.selectbox("Seleziona Squadra per Dettaglio", nomi_squadre, key="sel_sq_rosa")
    dati_sq = st.session_state.squadre[sq_sel]
    riep_sq = riepiloghi[sq_sel]

    col_A, col_B = st.columns([2, 1])
    with col_A:
        st.subheader(f"Rosa di {sq_sel} ({len(dati_sq['rosa'])} giocatori)")
        rosa = dati_sq["rosa"]
        if not rosa:
            st.info("📭 Rosa vuota. Vai su 'Mercato & Asta Live' per acquistare giocatori.")
        else:
            df_rosa = pd.DataFrame(rosa)
            display_cols = ["Nome", "Ruolo", "Squadra_SerieA", "Costo_Acquisto", "FantaMedia"]
            if "Prestito_Da" in df_rosa.columns:
                display_cols.append("Prestito_Da")
            st.dataframe(df_rosa[[c for c in display_cols if c in df_rosa.columns]], use_container_width=True, hide_index=True)

    with col_B:
        st.subheader("📊 Copertura Ruoli")
        for ruolo, req in ROSA_REQ.items():
            poss = riep_sq[ruolo]["posseduti"]
            manc = riep_sq[ruolo]["mancanti"]
            off = riep_sq[ruolo]["offerta_max"]
            colore = "#00d26a" if manc == 0 else "#ff6b6b"
            st.markdown(f"**{ruolo}**: {poss}/{req} (Mancanti: {manc}) | Offerta max consigliata: <span style='color:{colore};'><b>{off}cr</b></span>", unsafe_allow_html=True)

        st.markdown("---")
        spese = spese_per_ruolo(sq_sel)
        st.subheader("💵 Spese per Ruolo")
        for r, info in spese.items():
            st.caption(f"**{r}**: Totale {info['tot']}cr ({info['n']} giocatori, media {info['avg']}cr)")

# ============================================================
# SEZIONE: 🔨 MERCATO & ASTA LIVE
# ============================================================
elif menu == "🔨 Mercato & Asta Live":
    st.header("🔨 Mercato & Asta Live")
    st.markdown("Gestisci gli acquisti durante l'asta in tempo reale, calcola i prezzi consigliati e monitora i top player.")

    tab_asta, tab_svincolati, tab_scambio, tab_storico = st.tabs(["⚡ Asta Live", "🏷️ Svincolati", "🔄 Scambi", "📜 Storico"])

    with tab_asta:
        st.subheader("⚡ Console Asta Rapida")
        col1, col2 = st.columns([1, 1])
        with col1:
            db = st.session_state.giocatori_db
            svinc = get_svincolati(db)
            giocatori_disp = sorted(svinc["Nome"].tolist())
            giocatore_scelto = st.selectbox("Seleziona Giocatore da Acquistare", giocatori_disp, key="asta_giocatore")

            if giocatore_scelto:
                g_info = get_db_info(giocatore_scelto)
                if g_info:
                    stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                    prezzo_cons, spiegazione = calcola_prezzo_consigliato(g_info, stats_df)
                    st.info(f"💡 **Prezzo consigliato:** {prezzo_cons} crediti\n\n{spiegazione}")

        with col2:
            squadre_disp = get_nomi_squadre()
            squadra_acquirente = st.selectbox("Squadra Acquirente", squadre_disp, key="asta_squadra")
            crediti_sq = st.session_state.squadre[squadra_acquirente]["crediti"]
            riep_sq = riepilogo_rosa(squadra_acquirente)
            st.caption(f"💰 Crediti disponibili: **{crediti_sq}** | Posti mancanti: **{riep_sq['tot_mancanti']}**")

            max_possibile = budget_libero_effettivo(squadra_acquirente)
            st.caption(f"🛡️ Budget libero effettivo (lasciando 1cr per ogni posto vuoto): **{max_possibile}cr**")

            prezzo_asta = st.number_input("Prezzo di Acquisto (Crediti)", min_value=1, max_value=max(1, crediti_sq), value=5, key="asta_prezzo")

            if st.button("✅ Conferma Acquisto Asta", type="primary", use_container_width=True):
                if giocatore_scelto and squadra_acquirente:
                    g_info = get_db_info(giocatore_scelto)
                    if g_info:
                        if crediti_sq < prezzo_asta:
                            st.error(f"❌ {squadra_acquirente} ha solo {crediti_sq} crediti!")
                        else:
                            StateManager.snapshot()
                            st.session_state.squadre[squadra_acquirente]["crediti"] -= prezzo_asta
                            g_aggiunto = dict(g_info)
                            g_aggiunto["Costo_Acquisto"] = prezzo_asta
                            st.session_state.squadre[squadra_acquirente]["rosa"].append(g_aggiunto)
                            st.session_state.storico_mercato.insert(0, {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "tipo": "ACQUISTO",
                                "giocatore": giocatore_scelto,
                                "ruolo": g_info.get("Ruolo"),
                                "squadra": squadra_acquirente,
                                "prezzo": prezzo_asta
                            })
                            invalidate_cache()
                            save_state()
                            st.success(f"🎉 {giocatore_scelto} acquistato da {squadra_acquirente} per {prezzo_asta}cr!")
                            st.rerun()

        st.markdown("---")
        st.subheader("🔥 Fuga dei Top Player")
        tracker = fuga_top_tracker()
        cols_tk = st.columns(4)
        for i, (ruolo, info) in enumerate(tracker.items()):
            col = cols_tk[i]
            with col:
                colore_alert = "#ff6b6b" if alert_scarsita_top(ruolo) else "#00d26a"
                st.markdown(f"""
                <div class="metric-box" style="border-left: 4px solid {colore_alert};">
                    <h4>Ruolo {ruolo}</h4>
                    <p>⭐ Top rimasti: <b>{info['top_rimasti']}/{info['top_totali']}</b> ({info['pct_top_rimasti']}%)<br>
                    👍 Consigliati: <b>{info['cons_rimasti']}/{info['cons_totali']}</b></p>
                </div>
                """, unsafe_allow_html=True)

    with tab_svincolati:
        st.subheader("🏷️ Giocatori Svincolati")
        db = st.session_state.giocatori_db
        svinc = get_svincolati(db)
        ruolo_svinc = st.selectbox("Filtra per ruolo", ["Tutti", "P", "D", "C", "A"], key="svinc_ruolo")
        if ruolo_svinc != "Tutti":
            svinc = svinc[svinc["Ruolo"] == ruolo_svinc]
        st.caption(f"Totale svincolati: {len(svinc)}")
        st.dataframe(svinc[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Consiglio", "Note"]], use_container_width=True, hide_index=True)

    with tab_scambio:
        st.subheader("🔄 Gestione Scambi Diretti")
        c1, c2 = st.columns(2)
        with c1:
            sq1 = st.selectbox("Squadra 1", get_nomi_squadre(), key="scambio_sq1")
            rosa1 = st.session_state.squadre[sq1]["rosa"]
            gioc1 = st.selectbox("Cede da Squadra 1", [g["Nome"] for g in rosa1] if rosa1 else [], key="scambio_g1")
        with c2:
            sq2 = st.selectbox("Squadra 2", [s for s in get_nomi_squadre() if s != sq1], key="scambio_sq2")
            rosa2 = st.session_state.squadre[sq2]["rosa"] if sq2 else []
            gioc2 = st.selectbox("Cede da Squadra 2", [g["Nome"] for g in rosa2] if rosa2 else [], key="scambio_g2")

        conguaglio = st.number_input("Conguaglio crediti (positivo = da Sq2 a Sq1)", min_value=-100, max_value=100, value=0, key="scambio_cong")

        if st.button("🔄 Esegui Scambio", type="primary", use_container_width=True):
            if gioc1 and gioc2 and sq1 and sq2:
                StateManager.snapshot()
                # Trova e rimuovi gioc1 da sq1
                g1_obj = None
                for idx, g in enumerate(st.session_state.squadre[sq1]["rosa"]):
                    if g["Nome"] == gioc1:
                        g1_obj = st.session_state.squadre[sq1]["rosa"].pop(idx)
                        break
                # Trova e rimuovi gioc2 da sq2
                g2_obj = None
                for idx, g in enumerate(st.session_state.squadre[sq2]["rosa"]):
                    if g["Nome"] == gioc2:
                        g2_obj = st.session_state.squadre[sq2]["rosa"].pop(idx)
                        break

                if g1_obj and g2_obj:
                    st.session_state.squadre[sq2]["rosa"].append(g1_obj)
                    st.session_state.squadre[sq1]["rosa"].append(g2_obj)
                    st.session_state.squadre[sq1]["crediti"] += conguaglio
                    st.session_state.squadre[sq2]["crediti"] -= conguaglio

                    st.session_state.storico_mercato.insert(0, {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "tipo": "SCAMBIO",
                        "dettaglio": f"{sq1} dà {gioc1} a {sq2} per {gioc2} (Conguaglio: {conguaglio}cr)"
                    })
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ Scambio completato con successo tra {sq1} e {sq2}!")
                    st.rerun()

    with tab_storico:
        st.subheader("📜 Storico Operazioni di Mercato")
        storico = st.session_state.storico_mercato
        if not storico:
            st.info("📭 Nessuna operazione registrata.")
        else:
            for op in storico:
                st.markdown(f"`{op.get('timestamp')}` — **{op.get('tipo')}**: {op.get('giocatore', '')} ({op.get('ruolo', '')}) alla squadra **{op.get('squadra', '')}** per **{op.get('prezzo', '')}cr**" if op.get('tipo') == 'ACQUISTO' else f"`{op.get('timestamp')}` — **{op.get('tipo')}**: {op.get('dettaglio', '')}")

# ============================================================
# SEZIONE: 🔄 PRESTITI & CONTRATTI
# ============================================================
elif menu == "🔄 Prestiti & Contratti":
    st.header("🔄 Prestiti & Gestione Contratti")
    st.markdown("Gestisci i prestiti temporanei tra squadre e la durata dei contratti pluriennali.")

    tab_prest, tab_contr = st.tabs(["🤝 Prestiti", "📝 Contratti"])

    with tab_prest:
        st.subheader("🤝 Gestione Prestiti Temporanei")
        c1, c2 = st.columns(2)
        with c1:
            sq_da = st.selectbox("Squadra Proprietaria", get_nomi_squadre(), key="prest_da")
            rosa_prop = rosa_proprieta(sq_da)
            g_prest = st.selectbox("Giocatore in prestito", [g["Nome"] for g in rosa_prop] if rosa_prop else [], key="prest_gioc")
        with c2:
            sq_a = st.selectbox("Squadra Prendetrice", [s for s in get_nomi_squadre() if s != sq_da], key="prest_a")
            durata_prestito = st.selectbox("Durata", ["Stagione 2026/27", "1 Anno + Dir. Riscatto", "2 Anni"], key="prest_durata")
            prezzo_riscatto = st.number_input("Prezzo di Riscatto (Crediti, 0=Senza)", min_value=0, max_value=200, value=0, key="prest_riscatto")

        if st.button("🤝 Cedi in Prestito", type="primary", use_container_width=True):
            if sq_da and sq_a and g_prest:
                StateManager.snapshot()
                # Trova il giocatore nella rosa della squadra proprietaria
                g_obj = None
                for g in st.session_state.squadre[sq_da]["rosa"]:
                    if g["Nome"] == g_prest:
                        g_obj = dict(g)
                        break
                if g_obj:
                    g_obj["Prestito_Da"] = sq_da
                    st.session_state.squadre[sq_a]["rosa"].append(g_obj)
                    st.session_state.prestiti.append({
                        "Giocatore": g_prest,
                        "Da": sq_da,
                        "A": sq_a,
                        "Durata": durata_prestito,
                        "Riscatto": prezzo_riscatto
                    })
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ {g_prest} ceduto in prestito da {sq_da} a {sq_a}!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Prestiti Attivi")
        prestiti = st.session_state.prestiti
        if not prestiti:
            st.info("📭 Nessun prestito attivo.")
        else:
            for idx, p in enumerate(prestiti):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{p['Giocatore']}** | Proprietario: `{p['Da']}` ➡️ In prestito a: `{p['A']}` | Durata: {p['Durata']} | Riscatto: {p['Riscatto']}cr")
                with col2:
                    if st.button("❌ Termina", key=f"term_prest_{idx}"):
                        StateManager.snapshot()
                        # Rimuovi da squadra ricevente
                        st.session_state.squadre[p['A']]["rosa"] = [g for g in st.session_state.squadre[p['A']]["rosa"] if g["Nome"] != p['Giocatore']]
                        st.session_state.prestiti.pop(idx)
                        invalidate_cache()
                        save_state()
                        st.rerun()

    with tab_contr:
        st.subheader("📝 Contratti Pluriennali")
        st.markdown(f"I contratti standard durano **{CONTRATTO_ANNI} anni**. Assegna o rinnova i contratti ai giocatori in rosa.")
        sq_contr = st.selectbox("Seleziona Squadra", get_nomi_squadre(), key="contr_sq")
        rosa_contr = st.session_state.squadre[sq_contr]["rosa"]
        if not rosa_contr:
            st.info("📭 Rosa vuota.")
        else:
            for g in rosa_contr:
                nome_g = g["Nome"]
                key_c = f"contr_{sq_contr}_{nome_g}"
                durata_attuale = st.session_state.contratti.get(key_c, {"anni": CONTRATTO_ANNI, "ingaggio": 5})
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.markdown(f"**{nome_g}** ({g['Ruolo']} - {g['Squadra_SerieA']})")
                with c2:
                    nuovi_anni = st.number_input("Anni", min_value=1, max_value=5, value=durata_attuale["anni"], key=f"anni_{key_c}")
                with c3:
                    nuovo_ingaggio = st.number_input("Ingaggio", min_value=1, max_value=100, value=durata_attuale["ingaggio"], key=f"ing_{key_c}")
                st.session_state.contratti[key_c] = {"squadra": sq_contr, "giocatore": nome_g, "anni": nuovi_anni, "ingaggio": nuovo_ingaggio}
            save_state()
            st.success("✅ Contratti aggiornati in tempo reale.")

# ============================================================
# SEZIONE: 📈 STATISTICHE STORICHE
# ============================================================
elif menu == "📈 Statistiche Storiche":
    st.header("📈 Statistiche Storiche & Caricamento Dati")
    st.markdown("Carica i file CSV/Excel delle stagioni passate per alimentare il motore predittivo e il calcolo dei prezzi consigliati.")

    uploaded_files = st.file_uploader(
        "Carica file statistiche (CSV o Excel)",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="upload_stats_storiche"
    )

    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith(".csv"):
                    df_up = pd.read_csv(file)
                else:
                    df_up = pd.read_excel(file)

                stagione_nome = st.text_input(f"Etichetta Stagione per {file.name}", value="2025-26", key=f"stag_{file.name}")
                if st.button(f"💾 Salva {file.name} come {stagione_nome}", key=f"btn_save_{file.name}"):
                    if "stats_per_stagione" not in st.session_state:
                        st.session_state.stats_per_stagione = {}
                    st.session_state.stats_per_stagione[stagione_nome] = df_up
                    st.session_state.stats_storiche = df_up
                    save_state()
                    st.success(f"✅ Statistiche per la stagione {stagione_nome} caricate con successo ({len(df_up)} giocatori)!")
            except Exception as e:
                st.error(f"❌ Errore nella lettura di {file.name}: {e}")

    st.markdown("---")
    st.subheader("📊 Stagioni Storiche Caricate")
    stats_reg = st.session_state.get("stats_per_stagione", {})
    if not stats_reg:
        st.info("📭 Nessuna stagione caricata al momento.")
    else:
        for stag, df_s in stats_reg.items():
            with st.expander(f"Stagione: {stag} ({len(df_s)} giocatori)"):
                st.dataframe(df_s.head(10), use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ Ricalcolo Fasce Automatico da Storico")
    st.markdown("Fai analizzare all'AI le performance storiche di tutti i giocatori per riassegnare automaticamente le fasce (⭐ Top, 👍 Consigliato, 🎲 Scommessa).")
    if st.button("🚀 Ricalcola Fasce Automaticamente", type="primary"):
        applica_fasce_automatiche()

# ============================================================
# SEZIONE: 📊 STATISTICHE AVANZATE (RICHIESTA UTENTE)
# ============================================================
elif menu == "📊 Statistiche Avanzate":
    st.header("📊 Statistiche Avanzate & Analisi Dettagliate")
    st.markdown("Esplora metriche avanzate, distribuzioni dei punteggi, ranking per efficienza e rendimento storico dei calciatori.")

    db = st.session_state.giocatori_db.copy()
    db = arricchisci_con_stats_2627(db)

    # Assicuriamoci che le colonne numeriche siano corrette
    for col in ["Quotazione", "FantaMedia"]:
        if col in db.columns:
            db[col] = pd.to_numeric(db[col], errors="coerce").fillna(0)

    # Calcolo metriche derivate se non presenti
    db["Indice_Affare"] = db["FantaMedia"] / db["Quotazione"].replace(0, 1)

    tab_dist, tab_rank, tab_comp = st.tabs(["📉 Distribuzioni & Scatter", "🏆 Ranking & Efficienza", "⚖️ Confronto Diretto"])

    with tab_dist:
        st.subheader("📉 Distribuzione FantaMedia vs Quotazione")
        st.markdown("Individua rapidamente i giocatori con il miglior rapporto qualità-prezzo (alto rendimento a basso costo).")

        ruolo_filtro = st.selectbox("Filtra per Ruolo", ["Tutti", "P", "D", "C", "A"], key="adv_ruolo_dist")
        df_plot = db.copy()
        if ruolo_filtro != "Tutti":
            df_plot = df_plot[df_plot["Ruolo"] == ruolo_filtro]

        if not df_plot.empty:
            # Scatter chart con Streamlit nativo
            st.scatter_chart(df_plot, x="Quotazione", y="FantaMedia", color="Ruolo", size="FantaMedia")
        else:
            st.info("Nessun dato disponibile per il filtro selezionato.")

        st.markdown("---")
        st.subheader("📈 Statistiche Descrittive per Ruolo")
        if not db.empty:
            agg_df = db.groupby("Ruolo").agg(
                Giocatori=("Nome", "count"),
                Media_FM=("FantaMedia", "mean"),
                Max_FM=("FantaMedia", "max"),
                Media_Quotazione=("Quotazione", "mean")
            ).reset_index()
            agg_df["Media_FM"] = agg_df["Media_FM"].round(2)
            agg_df["Media_Quotazione"] = agg_df["Media_Quotazione"].round(1)
            st.dataframe(agg_df, use_container_width=True, hide_index=True)

    with tab_rank:
        st.subheader("🏆 Classifiche e Specialisti")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💎 I Migliori Affari (Indice FantaMedia/Quotazione)")
            top_affari = db.sort_values("Indice_Affare", ascending=False).head(10)
            st.dataframe(top_affari[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Indice_Affare"]], use_container_width=True, hide_index=True)

        with col2:
            st.markdown("### ⭐ Top Player Assoluti per FantaMedia")
            top_fm = db.sort_values("FantaMedia", ascending=False).head(10)
            st.dataframe(top_fm[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia"]], use_container_width=True, hide_index=True)

    with tab_comp:
        st.subheader("⚖️ Confronto Diretto tra Giocatori")
        col1, col2 = st.columns(2)
        nodi_list = sorted(db["Nome"].dropna().unique().tolist())
        with col1:
            g1_name = st.selectbox("Seleziona Giocatore 1", nodi_list, key="comp_g1")
        with col2:
            g2_name = st.selectbox("Seleziona Giocatore 2", [n for n in nodi_list if n != g1_name], key="comp_g2")

        if g1_name and g2_name:
            info1 = get_db_info(g1_name)
            info2 = get_db_info(g2_name)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"### {g1_name}")
                if info1:
                    st.markdown(f"**Ruolo:** {info1.get('Ruolo')}")
                    st.markdown(f"**Squadra:** {info1.get('Squadra_SerieA')}")
                    st.markdown(f"**Quotazione:** {info1.get('Quotazione')} cr")
                    st.markdown(f"**FantaMedia:** {info1.get('FantaMedia')}")
                    st.markdown(f"**Fascia:** {info1.get('Consiglio')}")
                    st.markdown(f"**Note:** {info1.get('Note')}")
            with col_b:
                st.markdown(f"### {g2_name}")
                if info2:
                    st.markdown(f"**Ruolo:** {info2.get('Ruolo')}")
                    st.markdown(f"**Squadra:** {info2.get('Squadra_SerieA')}")
                    st.markdown(f"**Quotazione:** {info2.get('Quotazione')} cr")
                    st.markdown(f"**FantaMedia:** {info2.get('FantaMedia')}")
                    st.markdown(f"**Fascia:** {info2.get('Consiglio')}")
                    st.markdown(f"**Note:** {info2.get('Note')}")

# ============================================================
# SEZIONE: ⭐ WATCHLIST
# ============================================================
elif menu == "⭐ Watchlist":
    st.header("⭐ Watchlist Personale")
    st.markdown("Segna i tuoi obiettivi di mercato preferiti e monitora la loro disponibilità e prezzo.")

    db = st.session_state.giocatori_db
    watchlist = st.session_state.watchlist

    col1, col2 = st.columns([2, 1])
    with col1:
        gioc_aggiungi = st.selectbox("Aggiungi giocatore alla Watchlist", sorted(db["Nome"].tolist()), key="watch_add_sel")
        if st.button("⭐ Aggiungi a Watchlist", use_container_width=True):
            if gioc_aggiungi not in watchlist:
                watchlist.append(gioc_aggiungi)
                save_state()
                st.success(f"✅ {gioc_aggiungi} aggiunto alla watchlist!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 I tuoi obiettivi monitorati")
    if not watchlist:
        st.info("📭 Watchlist vuota.")
    else:
        idx_map = get_player_index()
        for idx, g_nome in enumerate(watchlist):
            g_info = get_db_info(g_nome)
            proprietario = idx_map.get(g_nome.lower(), "Svincolato")
            colore_prop = "#ff6b6b" if proprietario != "Svincolato" else "#00d26a"
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{g_nome}** ({g_info.get('Ruolo')} - {g_info.get('Squadra_SerieA')}) | Quotazione: {g_info.get('Quotazione')}cr | FM: {g_info.get('FantaMedia')}")
            with c2:
                st.markdown(f"Stato: <span style='color:{colore_prop};'><b>{proprietario}</b></span>", unsafe_allow_html=True)
            with c3:
                if st.button("🗑️ Rimuovi", key=f"del_watch_{idx}"):
                    watchlist.pop(idx)
                    save_state()
                    st.rerun()

# ============================================================
# SEZIONE: 🏟️ SIMULATORE FORMAZIONE
# ============================================================
elif menu == "🏟️ Simulatore Formazione":
    st.header("🏟️ Simulatore Formazione")
    st.markdown("Simula la migliore formazione schierabile per ogni squadra in base ai moduli tattici.")

    sq_sim = st.selectbox("Seleziona Squadra", get_nomi_squadre(), key="sim_sq")
    modulo = st.selectbox("Modulo Tattico", ["3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-2-3-1"], key="sim_mod")

    if st.button("⚡ Calcola Miglior Formazione", type="primary", use_container_width=True):
        fm_tot, panchina, titolari = simula_formazione(sq_sim, modulo)
        st.success(f"🎯 FantaMedia stimata titolari ({modulo}): **{fm_tot}**")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🟢 Titolari")
            for t in titolari:
                st.markdown(f"- **{t['Nome']}** ({t['Ruolo']} - {t['Squadra_SerieA']}) | FM: `{t.get('FantaMedia_Usata', t.get('FantaMedia'))}` [{t.get('FM_Origine', 'Listone')}]")
        with c2:
            st.subheader("🟡 Panchina")
            for p in panchina:
                st.markdown(f"- {p['Nome']} ({p['Ruolo']} - {p['Squadra_SerieA']}) | FM: `{p.get('FantaMedia_Usata', p.get('FantaMedia'))}`")

# ============================================================
# SEZIONE: ⚙️ IMPOSTAZIONI & RESET
# ============================================================
elif menu == "⚙️ Impostazioni & Reset":
    st.header("⚙️ Impostazioni & Reset Dati")
    st.markdown("Gestisci la configurazione dell'applicazione, resetta le rose o ripristina i dati di default.")

    st.warning("⚠️ Area di pericolo: le azioni qui sotto modificano o cancellano permanentemente i dati salvati.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Svuota Tutte le Rose", use_container_width=True):
            StateManager.snapshot()
            for sq in get_nomi_squadre():
                st.session_state.squadre[sq]["rosa"] = []
                st.session_state.squadre[sq]["crediti"] = st.session_state.get("crediti_iniziali", CREDITI_INIZIALI)
            st.session_state.storico_mercato = []
            st.session_state.prestiti = []
            invalidate_cache()
            save_state()
            st.success("✅ Tutte le rose sono state svuotate!")
            st.rerun()

    with c2:
        if st.button("🔄 Ripristina Listone Default", use_container_width=True):
            StateManager.snapshot()
            st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
            save_state()
            st.success("✅ Listone ripristinato ai valori di default!")
            st.rerun()

    st.markdown("---")
    st.subheader("ℹ️ Informazioni su FantaManager")
    st.markdown("""
    - **Versione:** 2026/27 Professional Edition
    - **Autore:** Configurato per Bardo
    - **Stack:** Python, Streamlit, Pandas, Pickle
    """)