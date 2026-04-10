import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

# --- 2. KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000},
        "base_gallery": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. HANG ÉS PDF FUNKCIÓK ---
def play_notification_sound():
    audio_url = "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Samples/master/notification.mp3"
    st.components.v1.html(f'<audio autoplay style="display:none;"><source src="{audio_url}" type="audio/mp3"></audio>', height=0)

def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "LOGISTIC INVOICE / SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 780, f"Dátum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.line(50, 770, 550, 770)
    
    y = 740
    lines = [
        f"Tranzakció ID: {tid}",
        f"Feladó: {t['sender'].capitalize()}",
        f"Címzett: {t['receiver'].capitalize()}",
        f"Termék: {t['item']}",
        f"Leírás: {t.get('description', 'Nincs leírás')}",
        f"Útvonal: {t['start_loc']} -> {t['end_loc']}",
        f"Alapár: {t['price']} Ft",
        f"Szállítási díj: 990 Ft",
        "",
        f"ÖSSZESEN FIZETVE: {t['price'] + 990} Ft"
    ]
    for line in lines:
        if "ÖSSZESEN" in line: c.setFont("Helvetica-Bold", 14)
        c.drawString(60, y, line)
        y -= 25
    c.save()
    buf.seek(0)
    return buf

# --- 4. LOGIN RENDSZER ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGISTIC - LOGIN")
    u = st.text_input("Felhasználónév").lower().strip()
    p = st.text_input("Jelszó", type="password")
    if st.button("Belépés") and u in USERS and USERS[u] == p:
        st.session_state.username = u
        st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- 5. ESEMÉNYFIGYELŐ (HANGOKHOZ) ---
if 'prev_states' not in st.session_state:
    st.session_state.prev_states = {}

# --- 6. SIDEBAR ---
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.subheader("🟢 Online futárok")
for o in online_now: st.sidebar.write(f"• {o.capitalize()}")
st.sidebar.divider()
st.sidebar.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Ft")

# --- 7. FŐ TARTALOM ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE HQ"])

# --- TAB 1: KÜLDÉS ---
with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs más online futár.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulási pont", ["Budapest", "Catánia", "London", "New York"])
        end = c1.selectbox("Célállomás", ["Budapest", "Catánia", "London", "New York"])
        price = c2.number_input("Termék értéke (Ft)", min_value=0, value=1000)
        item = c2.text_input("Csomag tartalma")
        desc = st.text_area("Termék leírása")
        up_photo = st.file_uploader("Termékfotó", type=['jpg', 'png'])
        
        if st.button("🚀 Kérelem küldése") and item and up_photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item, "description": desc,
                "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                "photo": up_photo, "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            play_notification_sound()
            st.success("Elküldve!")
            st.rerun()

# --- TAB 2: CONTROL PANEL ---
with menu[1]:
    # Bejövő kérelmek
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t.get("receiver") == current_user and t.get("status") == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1: st.image(t["photo"], use_container_width=True)
            with col2:
                st.write(f"**Küldő:** {t['sender']} | **Tárgy:** {t['item']}")
                st.write(f"**Ár:** {t['price'] + 990} Ft (szállítással)")
                if st.button("ELFOGADOM ÉS FIZETEK ✅", key=f"acc_{tid}"):
                    cost = t["price"] + 990
                    if global_data["balances"][current_user] >= cost:
                        global_data["balances"][current_user] -= cost
                        # Feladó megkapja az árat + a szállítás FELÉT (495 Ft)
                        global_data["balances"][t["sender"]] += (t["price"] + 495)
                        t["status"] = "ACCEPTED"
                        play_notification_sound()
                        st.rerun()
                    else: st.error("Nincs elég egyenleged!")

    st.divider()

    # Aktív Szállítások
    active = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    for tid, t in active.items():
        # Hangjelzés ha változik a státusz
        state_key = f"{tid}_{t['state_text']}"
        if tid in st.session_state.prev_states and st.session_state.prev_states[tid] != state_key:
            play_notification_sound()
        st.session_state.prev_states[tid] = state_key

        with st.container(border=True):
            st.write(f"📦 **{t['item']}** | {t['start_loc']} ➔ {t['end_loc']}")
            c_l, c_r = st.columns(2)
            with c_l:
                if t["sender"] == current_user:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                    new_s = st.selectbox("Státusz állítása", states, index=curr_idx, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        st.rerun()
                else:
                    st.info(f"📍 Helyzet: **{t['state_text']}**")
            
            with c_r:
                if current_user == t["receiver"]:
                    if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"rec_{tid}"):
                        t["status"] = "DONE"
                        st.rerun()
                
                with st.expander("Számla"):
                    st.image(t["photo"], width=100)
                    pdf = create_pdf(t, tid)
                    st.download_button("📥 PDF Letöltés", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

# --- TAB 3: HISTORY ---
with menu[2]:
    done = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "DONE"}
    for tid, t in done.items():
        if t["sender"] == current_user:
            if st.button(f"Lezárás: {t['item']}", key=f"b_{tid}"):
                global_data["trade_history"].append({"Idő": datetime.now().strftime("%H:%M"), "Küldő": t["sender"], "Vevő": t["receiver"], "Tárgy": t["item"]})
                del global_data["active_trades"][tid]
                st.rerun()
    if global_data["trade_history"]: st.table(pd.DataFrame(global_data["trade_history"]))

# --- TAB 4: BASE ---
with menu[3]:
    nb = st.file_uploader("Kép", type=['jpg', 'png'], key="base")
    if st.button("Feltöltés") and nb:
        global_data["base_gallery"].append({"photo": nb, "user": current_user, "time": datetime.now().strftime("%H:%M")})
        st.rerun()
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"{entry['user']} | {entry['time']}")

# --- AUTO-REFRESH (3 másodperc) ---
time.sleep(3)
st.rerun()
