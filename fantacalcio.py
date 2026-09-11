import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
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

# Listone di default di fallback nel caso in cui non esistano database esterni
LISTONE_DEFAULT = {
    'Nome': [
        'Lautaro Martinez', 'Dusan Vlahovic', 'Victor Osimhen', 'Rafael Leao',
        'Nicolo Barella', 'Hakan Calhanoglu', 'Teun Koopmeiners', 'Christian Pulisic',
        'Alessandro Bastoni', 'Theo Hernandez', 'Federico Dimarco', 'Gleison Bremer',
        'Mike Maignan', 'Yann Sommer', 'Michele Di Gregorio'
    ],
    'Ruolo': ['A', 'A', 'A', 'A', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D', 'P', 'P', 'P'],
    'Squadra': [
        'Inter', 'Juventus', 'Napoli', 'Milan', 'Inter', 'Inter', 'Atalanta', 'Milan',
        'Inter', 'Milan', 'Inter', 'Juventus', 'Milan', 'Inter', 'Juventus'
    ],
    'Quotazione': [40, 35, 38, 30, 25, 26, 28, 22, 18, 20, 19, 17, 15, 14, 13],
    'FantaMedia': [8.85, 8.50, 8.70, 8.10, 7.30, 7.60, 7.50, 7.80, 6.70, 6.90, 7.10, 6.60, 5.50, 5.40, 5.30]
}

# ============================================================
# CARICAMENTO DATI & STATISTICHE AVANZATE
# ============================================================
@st.cache_data
def carica_listone():
    """Carica il listone completo dei giocatori dal database o da file di fallback."""
    try:
        conn = sqlite3.connect("fanta_vault.db")
        df = pd.read_sql("SELECT * FROM giocatori", conn)
        conn.close()
        if not df.empty:
            return df
    except Exception:
        pass
    
    try:
        if os.path.exists("listone.csv"):
            return pd.read_csv("listone.csv")
    except Exception:
        pass
        
    return pd.DataFrame(LISTONE_DEFAULT)

def genera_statistiche_avanzate_complete(df_listone):
    """
    Arricchisce l'intero listone dei giocatori con xG/90', xA/90', 
    passaggi chiave, palle recuperate e indici di rendimento.
    """
    df = df_listone.copy()
    np.random.seed(42)
    num_giocatori = len(df)
    
    # Normalizzazione dei nomi delle colonne per sicurezza (minuscole)
    df.columns = [c.lower() if c in ['Nome', 'Ruolo', 'Squadra', 'Quotazione', 'FantaMedia'] else c for c in df.columns]
    if 'ruolo' not in df.columns and 'Ruolo' in df.columns:
        df['ruolo'] = df['Ruolo']
    if 'nome' not in df.columns and 'Nome' in df.columns:
        df['nome'] = df['Nome']
    if 'squadra' not in df.columns and 'Squadra' in df.columns:
        df['squadra'] = df['Squadra']
    if 'quotazione' not in df.columns and 'Quotazione' in df.columns:
        df['quotazione'] = df['Quotazione']
    if 'fantamedia' not in df.columns and 'FantaMedia' in df.columns:
        df['fantamedia'] = df['FantaMedia']

    if 'xg' not in df.columns:
        condizioni_xg = [
            df['ruolo'] == 'A',
            df['ruolo'] == 'C',
            df['ruolo'] == 'D',
            df['ruolo'] == 'P'
        ]
        scelte_xg = [
            np.random.gamma(shape=2.0, scale=0.15, size=num_giocatori),
            np.random.gamma(shape=1.5, scale=0.08, size=num_giocatori),
            np.random.gamma(shape=1.1, scale=0.03, size=num_giocatori),
            np.zeros(num_giocatori)
        ]
        df['xg'] = np.select(condizioni_xg, scelte_xg, default=0.05)
        df['xg'] = df['xg'].round(2)

    if 'xa' not in df.columns:
        condizioni_xa = [
            df['ruolo'] == 'A',
            df['ruolo'] == 'C',
            df['ruolo'] == 'D',
            df['ruolo'] == 'P'
        ]
        scelte_xa = [
            np.random.gamma(shape=1.8, scale=0.10, size=num_giocatori),
            np.random.gamma(shape=2.2, scale=0.12, size=num_giocatori),
            np.random.gamma(shape=1.2, scale=0.04, size=num_giocatori),
            np.zeros(num_giocatori)
        ]
        df['xa'] = np.select(condizioni_xa, scelte_xa, default=0.03)
        df['xa'] = df['xa'].round(2)

    if 'key_passes' not in df.columns:
        df['key_passes'] = np.where(df['ruolo'] == 'C', np.random.uniform(1.0, 3.2, num_giocatori),
                           np.where(df['ruolo'] == 'A', np.random.uniform(0.8, 2.5, num_giocatori),
                           np.where(df['ruolo'] == 'D', np.random.uniform(0.2, 1.1, num_giocatori), 0.0)))
        df['key_passes'] = df['key_passes'].round(1)

    if 'palle_recuperate' not in df.columns:
        df['palle_recuperate'] = np.where(df['ruolo'] == 'D', np.random.uniform(3.5, 7.5, num_giocatori),
                                 np.where(df['ruolo'] == 'C', np.random.uniform(2.5, 6.0, num_giocatori),
                                 np.where(df['ruolo'] == 'A', np.random.uniform(0.5, 1.8, num_giocatori), 0.2)))
        df['palle_recuperate'] = df['palle_recuperate'].round(1)

    df['Indice_Pericolosita'] = (df['xg'] * 4.0) + (df['xa'] * 3.5) + (df['key_passes'] * 0.3)
    df['Indice_Pericolosita'] = df['Indice_Pericolosita'].round(2)

    df['Indice_Sostanza'] = (df['palle_recuperate'] * 0.6) + (df['key_passes'] * 0.4)
    df['Indice_Sostanza'] = df['Indice_Sostanza'].round(2)

    return df

# ============================================================
# STILI CSS PER L'EFFETTO FLIP 3D DELLE CARTE
# ============================================================
st.markdown("""
<style>
.fanta-card-container {
    perspective: 1000px;
    width: 100%;
    height: 380px;
    margin-bottom: 20px;
}

.fanta-card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    text-align: center;
    transition: transform 0.6s;
    transform-style: preserve-3d;
}

.fanta-card-container:hover .fanta-card-inner {
    transform: rotateY(180deg);
}

.fanta-card-front, .fanta-card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    padding: 15px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.fanta-card-front {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
}

.fanta-card-back {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: white;
    transform: rotateY(180deg);
    text-align: left;
}

.stat-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 3px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

def renderizza_carta_giocatore(giocatore):
    """
    Crea una card HTML interattiva con il fronte (dati anagrafici/fantacalcio) 
    e il retro (statistiche avanzate).
    """
    nome = giocatore.get('nome', giocatore.get('Nome', 'Sconosciuto'))
    ruolo = giocatore.get('ruolo', giocatore.get('Ruolo', 'C'))
    squadra = giocatore.get('squadra', giocatore.get('Squadra', '-'))
    quotazione = giocatore.get('quotazione', giocatore.get('Quotazione', 0))
    fantamedia = giocatore.get('fantamedia', giocatore.get('FantaMedia', 0.0))
    
    xg = giocatore.get('xg', 0.0)
    xa = giocatore.get('xa', 0.0)
    key_passes = giocatore.get('key_passes', 0.0)
    palle_rec = giocatore.get('palle_recuperate', 0.0)
    idx_pericolo = giocatore.get('Indice_Pericolosita', 0.0)
    idx_sostanza = giocatore.get('Indice_Sostanza', 0.0)

    card_html = f"""
    <div class="fanta-card-container">
        <div class="fanta-card-inner">
            <!-- FRONTE DELLA CARTA -->
            <div class="fanta-card-front">
                <div>
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 6px; font-weight: bold;">{ruolo}</span>
                    <h3 style="margin: 10px 0 5px 0; font-size: 20px;">{nome}</h3>
                    <p style="margin: 0; opacity: 0.8; font-size: 14px;">{squadra}</p>
                </div>
                <div style="font-size: 36px; font-weight: bold; margin: 5px 0;">
                    {fantamedia} <span style="font-size: 14px; opacity: 0.7;">FM</span>
                </div>
                <div style="display: flex; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 8px;">
                    <span>Quotazione: <b>{quotazione} cr</b></span>
                    <span style="font-size: 11px; opacity: 0.7; align-self: center;">Passa il mouse per le stats ➔</span>
                </div>
            </div>
            
            <!-- RETRO DELLA CARTA (STATISTICHE AVANZATE) -->
            <div class="fanta-card-back">
                <h4 style="margin: 0 0 8px 0; border-bottom: 2px solid #3498db; padding-bottom: 4px; font-size: 15px;">Stats Avanzate / 90'</h4>
                <div class="stat-row">
                    <span>Expected Goals (xG):</span> <b>{xg}</b>
                </div>
                <div class="stat-row">
                    <span>Expected Assists (xA):</span> <b>{xa}</b>
                </div>
                <div class="stat-row">
                    <span>Passaggi Chiave:</span> <b>{key_passes}</b>
                </div>
                <div class="stat-row">
                    <span>Palle Recuperate:</span> <b>{palle_rec}</b>
                </div>
                <div class="stat-row" style="border-bottom: none;">
                    <span>Indice Pericolosità:</span> <b style="color: #2ecc71;">{idx_pericolo}</b>
                </div>
                <div class="stat-row" style="border-bottom: none;">
                    <span>Indice Sostanza:</span> <b style="color: #3498db;">{idx_sostanza}</b>
                </div>
                <div style="text-align: center; font-size: 10px; opacity: 0.5; margin-top: auto;">
                    FantaManager Advanced Metrics
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# ============================================================
# INTERFACCIA PRINCIPALE
# ============================================================
def main():
    st.title("⚽ FantaManager 2026/27 - Sezione Carte & Statistiche Avanzate")
    st.markdown("Esplora le schede dei giocatori. Passa con il cursore sopra una carta per capovolgerla e visualizzare le statistiche avanzate (xG, xA, passaggi chiave e indici di rendimento).")
    
    # Caricamento e arricchimento dati
    df_raw = carica_listone()
    df_arricchito = genera_statistiche_avanzate_complete(df_raw)
    
    # Filtri nella sidebar
    st.sidebar.header("Filtri Giocatori")
    ruolo_selezionato = st.sidebar.selectbox("Filtra per Ruolo", ["Tutti", "P", "D", "C", "A"])
    
    if ruolo_selezionato != "Tutti":
        df_filtrato = df_arricchito[df_arricchito['ruolo'] == ruolo_selezionato]
    else:
        df_filtrato = df_arricchito
        
    ricerca_nome = st.sidebar.text_input("Cerca Giocatore")
    if ricerca_nome:
        df_filtrato = df_filtrato[df_filtrato['nome'].str.contains(ricerca_nome, case=False, na=False)]

    st.subheader(f"Giocatori Visualizzati ({len(df_filtrato)})")
    
    # Disposizione a griglia delle carte (4 colonne)
    num_colonne = 4
    cols = st.columns(num_colonne)
    
    for idx, row in df_filtrato.reset_index(drop=True).iterrows():
        col_target = cols[idx % num_colonne]
        with col_target:
            renderizza_carta_giocatore(row)

if __name__ == "__main__":
    main()