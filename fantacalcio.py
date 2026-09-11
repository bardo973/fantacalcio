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
        
    # Fallback sul listone di default integrato se non ci sono sorgenti esterne
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
        df['key_passes'] = np.where(df['ruolo'] == 'C', np.random.uniform(1.0, 3.2, num_giquatori := num_giocatori),
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