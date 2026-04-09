import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="LOGISTIC CONTROL CENTER", layout="wide")

# --- KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "active_trades": {}, 
        "trade_history": [],
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000},
        "base_gallery": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ LOGISTIC HUB LOGIN")
    u = st.text_input("Név").lower().strip()
    p = st.text_input("PW", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

current_user = st.session_state.username

# --- SIDEBAR ---
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
others = [u for u in ["admin", "peti", "adel"] if u != current_user]

menu = st.tabs(["🚀 ÚJ TRADE", "🎮 IRÁNYÍTÓKÖZPONT", "📜 HISTORY"])

# --- 1. ÚJ TRADE INDÍTÁSA ---
with menu[0]:
    st.header("Szállítás előkészítése")
    target = st.selectbox("Címzett", others)
    price = st.number_input("Termék ára (Ft)", min_value=0, value=1000)
    item = st.text_input("Tárgy neve")
    photo = st.file_uploader("Fotó", type=['jpg', 'png'])
    
    if st.button("Trade létrehozása"):
        if item and photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user,
                "receiver": target,
                "item": item,
                "price": price,
                "status": "WAITING", # Vár az elfogadásra
                "state_text": "Csomagolás alatt...",
                "photo": photo,
                "eta_dt": None,
                "started": False
            }
            st.success("Létrehozva! Várj, amíg a címzett elfogadja.")

# --- 2. IRÁNYÍTÓKÖZPONT (Itt történik minden) ---
with menu[1]:
    # A) ELFOGADÁS (Címzett látja)
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user and t["status"] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** küldeménye: {t['item']} ({t['price']} Ft)")
            if st.button("ELFOGADOM", key=f"acc_{tid}"):
                global_data["balances"][t["sender"]] -= (t["price"] + 990)
                t["status"] = "ACCEPTED"
                st.rerun()

    st.divider()
    
    # B) KONTROLL (Feladó látja és állítja az időt)
    st.subheader("🚚 Aktív Szállítások Vezérlése")
    my_trades = {tid: t for tid, t in global_data["active_trades"].items() if t["sender"] == current_user and t["status"] == "ACCEPTED"}
    
    for tid, t in my_trades.items():
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** -> {t['receiver']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # MANUÁLIS STÁTUSZ ÁLLÍTÁS
                st.write("📍 Fázis beállítása:")
                s1 = st.button("Levegőben ✈️", key=f"air_{tid}")
                s2 = st.button("Repülőtéren 🏢", key=f"port_{tid}")
                s3 = st.button("Kapu előtt 🚪", key=f"gate_{tid}")
                if s1: t["state_text"] = "A csomagod a levegőben van! ✈️"; st.rerun()
                if s2: t["state_text"] = "A csomagod megérkezett a repülőtérre! 🏢"; st.rerun()
                if s3: t["state_text"] = "A futár a kapu előtt áll! 🚪"; st.rerun()

            with col2:
                # MANUÁLIS IDŐZÍTŐ (ETA)
                st.write("⏱️ Időzítő beállítása:")
                mins = st.number_input("Hány perc múlva érkezzen meg?", 1, 60, 5, key=f"min_{tid}")
                if st.button("INDÍTÁS / ÚJRAINDÍTÁS", key=f"go_{tid}"):
                    t["eta_dt"] = datetime.now() + timedelta(minutes=mins)
                    t["started"] = True
                    st.rerun()

            with col3:
                # SZÁMLA
                with st.expander("Digitális Számla"):
                    st.image(t["photo"], width=150)
                    st.write(f"Vevő: {t['receiver']}")
                    st.write(f"Összesen: {t['price'] + 990} Ft")

    # C) ÉLŐ VISSZASZÁMLÁLÓ (Mindenki látja)
    st.divider()
    st.subheader("📢 Élő Szállítási Állapot")
    
    for tid, t in global_data["active_trades"].items():
        if t["status"] == "ACCEPTED" and t["started"]:
            with st.container(border=True):
                # Kiszámoljuk a hátralévő időt
                now = datetime.now()
                rem = (t["eta_dt"] - now).total_seconds()
                
                st.info(f"🚚 {t['item']} | Állapot: **{t['state_text']}**")
                
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"⏳ Visszaszámláló: {m:02d}:{s:02d}")
                    st.progress(min(1.0, rem / 600)) # Csík
                    time.sleep(1) # Emiatt fog "ketyegni"
                    st.rerun()
                else:
                    st.success("✅ A CSOMAG ÁTVEHETŐ!")
                    if current_user == t["receiver"]:
                        if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"fin_{tid}"):
                            t["status"] = "DONE"
                            st.rerun()

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt szállítások")
    done = [t for t in global_data["active_trades"].values() if t["status"] == "DONE"]
    if done:
        st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])
