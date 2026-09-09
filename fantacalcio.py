import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Fanta-Assistant", page_icon="⚽", layout="wide"
)

# Stile CSS personalizzato per le card e il layout
st.markdown(
    """
    <style>
    .player-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .player-name {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 5px;
    }
    .player-role {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stat-badge {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 5px;
        margin-top: 5px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Funzione di caricamento dati con statistiche avanzate integrate automaticamente
@st.cache_data
def load_data():
    data = {
        "Nome": [
            "Lautaro Martinez",
            "Dušan Vlahović",
            "Rafael Leão",
            "Khvicha Kvaratskhelia",
            "Hakan Çalhanoğlu",
            "Christian Pulisic",
            "Teun Koopmeiners",
            "Paulo Dybala",
            "Alessandro Bastoni",
        ],
        "Ruolo": ["A", "A", "A", "C", "C", "C", "C", "A", "D"],
        "Squadra": [
            "Inter",
            "Juventus",
            "Milan",
            "Napoli",
            "Inter",
            "Milan",
            "Juventus",
            "Roma",
            "Inter",
        ],
        "FVM": [250, 210, 190, 200, 180, 175, 170, 185, 45],
        "Fantamedia": [8.75, 8.30, 7.90, 8.10, 7.85, 7.95, 7.70, 8.20, 6.70],
        "Indice_Pericolosita": [9.4, 8.9, 8.5, 9.1, 8.2, 8.6, 8.0, 8.8, 6.5],
        "Expected_Goals": [0.65, 0.58, 0.45, 0.52, 0.30, 0.42, 0.28, 0.40, 0.05],
    }
    return pd.DataFrame(data)


# Inizializzazione dati
df = load_data()

# Header principale dell'applicazione
st.title("⚽ Fanta-Assistant")
st.markdown(
    "Gestione avanzata della rosa, statistiche e visualizzazione a card."
)

# Sidebar per i filtri di ricerca e navigazione
st.sidebar.header("Filtri di Ricerca")
ruolo_selezionato = st.sidebar.selectbox(
    "Filtra per Ruolo", ["Tutti", "P", "D", "C", "A"]
)
search_query = st.sidebar.text_input("Cerca Giocatore", "")

# Filtraggio del DataFrame in base ai controlli della sidebar
df_filtered = df.copy()
if ruolo_selezionato != "Tutti":
    df_filtered = df_filtered[df_filtered["Ruolo"] == ruolo_selezionato]
if search_query:
    df_filtered = df_filtered[
        df_filtered["Nome"].str.contains(search_query, case=False, na=False]
    ]

st.markdown(f"### Risultati ({len(df_filtered)})")

# Visualizzazione a griglia con card (3 colonne per riga)
if df_filtered.empty:
    st.info("Nessun giocatore trovato con i criteri attuali.")
else:
    cols_per_row = 3
    rows = [
        df_filtered.iloc[i : i + cols_per_row]
        for i in range(0, len(df_filtered), cols_per_row)
    ]

    for row in rows:
        cols = st.columns(cols_per_row)
        for index, (_, player) in enumerate(row.iterrows()):
            with cols[index]:
                st.markdown(
                    f"""
                    <div class="player-card">
                        <div class="player-name">{player['Nome']}</div>
                        <div class="player-role">{player['Squadra']} &bull; Ruolo: {player['Ruolo']}</div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #dee2e6;">
                        <div>
                            <span class="stat-badge">FVM: {player['FVM']}</span>
                            <span class="stat-badge">FM: {player['Fantamedia']}</span>
                            <span class="stat-badge">Danger: {player['Indice_Pericolosita']}</span>
                            <span class="stat-badge">xG: {player['Expected_Goals']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# Sezione inferiore per l'esportazione dei dati
st.markdown("---")
st.subheader("Esportazione Dati")
csv_data = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Scarica dati filtrati in CSV",
    data=csv_data,
    file_name="fanta_statistiche_avanzate.csv",
    mime="text/csv",
)