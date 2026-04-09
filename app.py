import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="LOGISTIC CONTROL CENTER", layout="wide")

# --- KÖZÖS MEMÓRIA (Hogy ne vesszenek el az adatok frissítéskor) ---
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

# --- LOGIN RENDSZER ---
if 'username' not in st.session_state:
    st.title("🛡️ LOGISTIC HUB LOGIN")
    u = st.text_input("Név (admin/peti/adel)").lower().strip()
    p = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

current_user = st.session_state.username

# --- OLDALSÁV (Egyenleg kijelzés) ---
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
st.sidebar.metric("Saját Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
others = [u for u in ["admin", "peti", "adel"] if u != current_user]

# --- MENÜPONTOK ---
menu = st.tabs(["🚀 ÚJ SZÁLLÍTÁS", "🎮 IRÁNYÍTÓKÖZPONT", "📜 HISTORY", "🏠 BASE HQ"])

# --- 1. ÚJ SZÁLLÍTÁS LÉTREHOZÁSA ---
with menu[0]:
    st.header("Csomag rögzítése a rendszerben")
    target = st.selectbox("Címzett kiválasztása", others)
    col_a, col_b = st.columns(2)
    with col_a:
        price = st.number_input("Termék ára (Ft)", min_value=0, value=1000)
        item = st.text_input("Tárgy megnevezése")
    with col_b:
        photo = st.file_uploader("Termékfotó (Számlához)", type=['jpg', 'png'], key="upload_main")
    
    if st.button("Trade létrehozása és küldése"):
        if item and photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user,
                "receiver": target,
                "item": item,
                "price": price,
                "status": "WAITING", 
                "state_text": "Csomagolás alatt... 📦",
                "photo": photo,
                "eta_dt": None,
                "started": False
            }
            st.success("Sikeresen beküldve! Várj, amíg a címzett elfogadja.")
        else:
            st.error("Kérlek tölts fel fotót és írd be a tárgy nevét!")

# --- 2. IRÁNYÍTÓKÖZPONT (Vezérlés és Visszaszámláló) ---
with menu[1]:
    # --- A) ELFOGADÁS (Címzettnek jelenik meg) ---
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user and t["status"] == "WAITING"}
    if reqs:
        st.subheader("📩 Bejövő kérelmeid")
        for tid, t in reqs.items():
            with st.container(border=True):
                st.write(f"**{t['sender']}** küldeménye: **{t['item']}** | Érték: **{t['price']} Ft**")
                if st.button("SZÁLLÍTÁS ELFOGADÁSA ✅", key=f"acc_{tid}"):
                    global_data["balances"][t["sender"]] -= (t["price"] + 990)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()
    
    # --- B) VEZÉRLÉS (Feladónak jelenik meg) ---
    st.subheader("🚚 Futár Vezérlőpult")
    my_trades = {tid: t for tid, t in global_data["active_trades"].items() if t["sender"] == current_user and t["status"] == "ACCEPTED"}
    
    if not my_trades:
        st.write("Nincs jelenleg aktív szállításod.")

    for tid, t in my_trades.items():
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** -> Címzett: **{t['receiver']}**")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**📍 Státusz váltása:**")
                if st.button("Levegőben ✈️", key=f"air_{tid}"): t["state_text"] = "A csomagod a levegőben van! ✈️"; st.rerun()
                if st.button("Repülőtéren 🏢", key=f"port_{tid}"): t["state_text"] = "A csomagod megérkezett a repülőtérre! 🏢"; st.rerun()
                if st.button("Kapu előtt 🚪", key=f"gate_{tid}"): t["state_text"] = "A futár a kapu előtt áll! 🚪"; st.rerun()

            with c2:
                st.write("**⏱️ Manuális Időzítő:**")
                m_input = st.number_input("Hány perc múlva érkezzen meg?", 1, 60, 5, key=f"min_{tid}")
                if st.button("IDŐZÍTŐ INDÍTÁSA 🚀", key=f"go_{tid}"):
                    t["eta_dt"] = datetime.now() + timedelta(minutes=m_input)
                    t["started"] = True
                    st.rerun()

            with c3:
                with st.expander("Digitális Számla / Kép"):
                    st.image(t["photo"], use_container_width=True)
                    st.write(f"Termék: {t['price']} Ft")
                    st.write(f"Szállítás: 990 Ft")
                    st.write(f"**Összesen: {t['price'] + 990} Ft**")

    # --- C) ÉLŐ VISSZASZÁMLÁLÓ (Mindenki látja) ---
    st.divider()
    st.subheader("📢 Élő Szállítási Állapot")
    
    for tid, t in global_data["active_trades"].items():
        if t["status"] == "ACCEPTED" and t["started"]:
            with st.container(border=True):
                now = datetime.now()
                rem = (t["eta_dt"] - now).total_seconds()
                
                st.info(f"🚚 **{t['item']}** | Állapot: **{t['state_text']}**")
                
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"⏳ HÁTRALÉVŐ IDŐ: {m:02d}:{s:02d}")
                    st.progress(min(1.0, 1.0 - (rem / (m_input * 60)) if 'm_input' in locals() else 0.5))
                    time.sleep(1) # Ez frissíti másodpercenként
                    st.rerun()
                else:
                    st.success("✅ A CSOMAG MEGÉRKEZETT! ÁTVEHETŐ.")
                    if current_user == t["receiver"]:
                        if st.button("ÁTVÉTEL IGAZOLÁSA ✍️", key=f"fin_{tid}"):
                            t["status"] = "DELIVERED"
                            st.rerun()

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt szállítások")
    # Szatyor visszaigazolás
    delivered = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "DELIVERED" and t["sender"] == current_user}
    for tid, t in delivered.items():
        if st.button(f"Szatyor visszaérkezett: {t['item']}", key=f"bag_{tid}"):
            global_data["trade_history"].append({
                "Idő": datetime.now().strftime("%H:%M"),
                "Küldő": t["sender"],
                "Vevő": t["receiver"],
                "Tárgy": t["item"],
                "Ár": t["price"] + 990
            })
            del global_data["active_trades"][tid]
            st.rerun()
            
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- 4. BASE HQ ---
with menu[3]:
    st.header("Bázis Galéria")
    b_photo = st.file_uploader("Kép feltöltése a bázisról", type=['jpg', 'png'], key="base_up")
    if st.button("Feltöltés", key="base_btn"):
        if b_photo:
            global_data["base_gallery"].append({"photo": b_photo, "user": current_user, "time": datetime.now().strftime("%H:%M")})
            st.rerun()
    
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"👤 {entry['user']} | 🕒 {entry['time']}")
