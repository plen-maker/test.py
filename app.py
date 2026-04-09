import streamlit as st
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="IRL TRADE - LIVE", layout="wide")

# --- KÖZÖS MEMÓRIA (Ez minden felhasználó számára ugyanaz a szerveren) ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {},  # Felhasználónév: utolsó aktivitás
        "trade_history": []   # Közös lista a trade-eknek
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név").lower().strip()
    p = st.text_input("PW", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

# --- ONLINE ÁLLAPOT FRISSÍTÉSE ---
current_user = st.session_state.username
# Beírjuk a közös memóriába, hogy itt vagyunk
global_data["online_users"][current_user] = time.time()

# Töröljük azokat, akik több mint 20 másodperce nem frissítettek (offline-nak tűnnek)
now = time.time()
inactive_users = [u for u, t in global_data["online_users"].items() if now - t > 20]
for u in inactive_users:
    del global_data["online_users"][u]

# --- OLDALSÁV (Sidebar) ---
st.sidebar.title(f"Szia {current_user.capitalize()}!")
# Ki van még itt? (Csak a többiek)
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

if not others_online:
    st.sidebar.warning("Várj a barátodra... (nincs más online)")
    # Automatikus frissítés, hogy lásd, ha belép
    time.sleep(2)
    st.rerun()
else:
    st.sidebar.subheader("Online partnerek:")
    for u in others_online:
        st.sidebar.success(f"🟢 {u.capitalize()}")

# --- LAPOK (Tabs) ---
menu = st.tabs(["🚀 TRADE", "📜 HISTORY", "🏠 BASE"])

with menu[0]:
    if not others_online:
        st.info("Amint a barátod is belép a saját gépén/mobilján, itt meg fog jelenni!")
    else:
        target = st.selectbox("Partner kiválasztása", others_online)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Honnan", ["Catánia", "New York", "Planeland", "Codeland", "London"])
            end = st.selectbox("Hová", ["Catánia", "New York", "Planeland", "Codeland", "London"])
        with c2:
            item = st.text_input("Tartalom")
            pkg = st.text_input("Final Package (csomagolás)")
        
        photo = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
        
        if st.button("🚀 TRADING INDÍTÁSA"):
            if item and photo:
                # Mentés a közös history-ba
                new_entry = {
                    "Idő": datetime.now().strftime("%H:%M"),
                    "Küldő": current_user,
                    "Fogadó": target,
                    "Tárgy": item,
                    "Útvonal": f"{start} ➔ {end}"
                }
                global_data["trade_history"].append(new_entry)
                
                # FULL SCREEN TIMER
                placeholder = st.empty()
                for i in range(10, 0, -1):
                    with placeholder.container():
                        st.markdown(f"""
                        <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:999;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                            <h1 style="color:red;font-size:120px;font-family:sans-serif;">{i}s</h1>
                            <h2 style="color:white;font-family:sans-serif;">SZÁLLÍTÁS: {target.upper()} RÉSZÉRE</h2>
                            <p style="color:gray;font-size:20px;">{start} >>> {end}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    time.sleep(1)
                placeholder.empty()
                st.success(f"✅ A csomag sikeresen megérkezett {target} részére!")
            else:
                st.error("Kérlek adj meg leírást és fotót!")

with menu[1]:
    st.header("Közös Trade History")
    if global_data["trade_history"]:
        # A legfrissebb legyen felül
        st.table(pd.DataFrame(global_data["trade_history"][::-1]))
    else:
        st.write("Még nincs rögzített trade.")

with menu[2]:
    st.header("The Base Update")
    st.image("https://images.unsplash.com/photo-1587293855946-90419e3c79a2?q=80&w=1000", caption="Bázis fotó")
