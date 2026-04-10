import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

# --- 2. KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. LOGIN ÉS APP ELVÁLASZTÁSA (A hiba fixálása) ---
# Létrehozunk egy üres helyet a teljes oldalnak
main_container = st.empty()

if 'username' not in st.session_state:
    # CSAK A LOGIN JELENIK MEG
    with main_container.container():
        st.title("🛡️ IRL LOGISTIC - LOGIN")
        with st.form("login_form"):
            u = st.text_input("Felhasználónév").lower().strip()
            p = st.text_input("Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                if u in USERS and USERS[u] == p:
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Hibás adatok!")
    st.stop() # ITT MEGÁLL A KÓD, ha nincs belépve. Semmi nem kerülhet alá!

# --- HA IDÁIG ELJUT A KÓD, AKKOR BE VAN LÉPVE ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Itt már a main_container-be vagy alá rajzolunk
with st.sidebar:
    st.title(f"Üdv, {current_user.capitalize()}!")
    online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 15]
    st.write(f"🟢 Online: {', '.join(online_now)}")
    st.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Ft")
    if st.button("Kijelentkezés"):
        del st.session_state.username
        st.rerun()


# --- STREAMLIT "SZAR" ELTÜNTETÉSE ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_unsafe_content=True)

# --- APP INTERFACE ---
tabs = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL"])

with tabs[0]:
    st.subheader("Csomag Küldése")
    # Ide jön a küldési interface... (a többi kódod változatlan)
    target = st.selectbox("Címzett", [u for u in online_now if u != current_user])
    item = st.text_input("Termék neve")
    if st.button("🚀 KÜLDÉS") and item:
        st.success(f"Küldve: {item}")

# --- AUTO REFRESH ---
time.sleep(3)
st.rerun()
