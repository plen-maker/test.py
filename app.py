import streamlit as st
import time
from datetime import datetime, timedelta
import random

# --- KONFIGURÁCIÓ ÉS STÍLUS ---
st.set_page_config(page_title="IRL Trade Interface", layout="centered")

# --- MOCK ADATOK (Felhasználók és Városok) ---
USERS = {"admin": "password123", "trader_joe": "trade456", "szallito_pisti": "pisti01"}
ONLINE_USERS = ["Trader_Joe", "Szallito_Pisti", "Catania_King", "CodeMaster"]
CITIES = ["Catánia", "New York", "Planeland", "Codeland", "London"]

# --- SESSION STATE INICIALIZÁLÁS ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN INTERFACE ---
def login():
    st.title("🔐 IRL Trade Belépés")
    with st.form("login_form"):
        username = st.text_input("Felhasználónév")
        password = st.text_input("Jelszó", type="password")
        submit = st.form_submit_button("Bejelentkezés")
        
        if submit:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Helytelen adatok!")

# --- TRADE INTERFACE ---
def trade_interface():
    st.sidebar.success(f"Bejelentkezve: {st.session_state.username}")
    if st.sidebar.button("Kijelentkezés"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📦 Új IRL Trade Indítása")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Partner adatai")
        target_user = st.selectbox("Válassz online partnert:", ONLINE_USERS)
        origin = st.selectbox("Honnan?", CITIES)
        destination = st.selectbox("Hová?", CITIES)

    with col2:
        st.subheader("Csomag részletei")
        item_desc = st.text_area("Mi van benne? (Tartalom leírása)")
        final_package_desc = st.text_input("Final Package kinézete (becsomagolva)")

    st.divider()
    
    st.subheader("Vizuális igazolás")
    uploaded_file = st.file_uploader("Kép feltöltése a termékről", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Feltöltött termék", use_container_width=True)

    if st.button("🚀 Trade Indítása"):
        if not item_desc or not uploaded_file:
            st.warning("Kérlek tölts fel képet és írj leírást!")
        else:
            # Szállítási idő generálása (5-10 perc között)
            delivery_minutes = random.randint(5, 10)
            arrival_time = datetime.now() + timedelta(minutes=delivery_minutes)
            
            st.success(f"Trade regisztrálva! Partner: {target_user}")
            st.info(f"Útvonal: {origin} ➡️ {destination}")
            
            # Élő visszaszámláló szimuláció (Streamlitben a progress bar-ral látványos)
            st.write(f"Várható érkezés: {arrival_time.strftime('%H:%M:%S')}")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for percent_complete in range(100):
                time.sleep(0.1)  # Ez csak egy gyorsított demó a vizualizációhoz
                progress_bar.progress(percent_complete + 1)
                status_text.text(f"Szállítás folyamatban... {percent_complete + 1}%")
            
            st.balloons()
            st.success("A csomag megérkezett a célállomásra!")

# --- MAIN LOGIC ---
if not st.session_state.logged_in:
    login()
else:
    trade_interface()
