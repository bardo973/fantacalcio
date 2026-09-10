import streamlit as st

# Configurazione della pagina
st.set_page_config(page_title="Fanta-Assistant", layout="wide")

# CSS personalizzato per la grafica originale (stile dark, glassmorphism e slot)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stApp {
        background-image: linear-gradient(to bottom right, #0e1117, #1a1c23);
    }
    .slot-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .slot-card.premium {
        border: 1px solid #ffd700;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Fanta-Assistant")
st.sidebar.title("Navigazione")

# Scelta della sezione dalla barra laterale
menu = st.sidebar.selectbox("Vai a", ["Gestione Rosa", "Asta", "Statistiche"])

if menu == "Gestione Rosa":
    st.header("Composizione Rosa e Slot")
    
    # Definizione degli slot richiesti
    slots = {
        "Portieri (Por)": 3,
        "Difensori (Dc)": 9,
        "Centrocampisti (Cen)": 9,
        "Attaccanti (Att)": 7
    }
    
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    
    for i, (ruolo, count) in enumerate(slots.items()):
        with cols[i]:
            st.subheader(ruolo)
            for slot_idx in range(1, count + 1):
                st.markdown(f"""
                    <div class="slot-card">
                        <b>Slot {slot_idx}</b><br>
                        <span style="color: #888; font-size: 0.9em;">Vuoto / Disponibile</span>
                    </div>
                """, unsafe_allow_html=True)

elif menu == "Asta":
    st.header("Sessione d'Asta")
    st.write("Interfaccia di chiamata e gestione offerte in tempo reale.")

elif menu == "Statistiche":
    st.header("Analisi Statistiche")
    st.write("Metriche e rendimento dei calciatori della Serie A.")