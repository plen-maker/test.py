import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# --- FELHASZNÁLÓK KEZELÉSE ---
# Itt add meg a te és a barátod adatait
VALID_USERS = {
    "te_neved": "jelszo1",
    "baratod_neve": "jelszo2"
}

def login_screen():
    st.title("🔐 IRL Trade Login")
    user = st.text_input("Felhasználónév")
    pw = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if user in VALID_USERS and VALID_USERS[user] == pw:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
        else:
            st.error("Hibás adatok!")

# --- FŐ INTERFÉSZ ---
def main_app():
    st.sidebar.title(f"Üdv, {st.session_state.username}!")
    
    tab1, tab2 = st.tabs(["Új Trade", "Aktív Szállítások"])

    with tab1:
        st.header("📦 Trade Indítása")
        # A partner automatikusan a másik user lesz
        partner = [u for u in VALID_USERS.keys() if u != st.session_state.username][0]
        st.info(f"Célpont: **{partner}**")

        col1, col2 = st.columns(2)
        with col1:
            honnan = st.selectbox("Indulás", ["Catánia", "New York", "Planeland", "Codeland", "London"])
            hova = st.selectbox("Érkezés", ["Catánia", "New York", "Planeland", "Codeland", "London"])
        
        with col2:
            leiras = st.text_area("Mi van a csomagban?")
            csomagolas = st.text_input("Hogy néz ki a doboz?")

        kep = st.file_uploader("Fotó a tartalomról", type=['jpg', 'png'])
        
        if st.button("Küldés indítása"):
            perc = random.randint(5, 10)
            st.success(f"Siker! A csomag úton van. Menetidő: {perc} perc.")
            # Itt egy igazi appban elmentenénk egy adatbázisba (pl. CSV vagy Google Sheets)

    with tab2:
        st.header("🚚 Folyamatban lévő ügyek")
        st.write("Itt látszódnának a közös trade-ek.")

# --- FUTTATÁS ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
