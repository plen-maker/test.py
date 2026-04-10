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

# --- 3. PROFI SZÁMLA GENERÁLÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.darkblue)
    c.drawString(50, height - 50, "HIVATALOS SZÁMLA / INVOICE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(50, height - 70, f"ID: {tid}")
    c.line(50, height - 95, width - 50, height - 95)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "SZÁLLÍTÁSI ADATOK")
    c.setFont("Helvetica", 11)
    c.drawString(60, height - 140, f"Feladó: {t['sender'].capitalize()}")
    c.drawString(60, height - 155, f"Címzett: {t['receiver'].capitalize()}")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(50, height - 250, f"VÉGÖSSZEG: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 4. TISZTA LOGIN ÉS APP LOGIKA ---
# Létrehozunk egy üres tárolót, ami az egész oldalt lefedi
main_container = st.empty()

if 'username' not in st.session_state:
    # CSAK a login látszik a tárolóban
    with main_container.container():
        st.title("🛡️ IRL LOGISTIC - LOGIN")
        u = st.text_input("Felhasználónév", key="l_user").lower().strip()
        p = st.text_input("Jelszó", type="password", key="l_pass")
        if st.button("Belépés", key="l_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                main_container.empty() # Itt töröljük ki a login felületet!
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop() # Eddig fut a kód, ha nincs belépve

# --- 5. HA BE VAN LÉPVE (Az app maradék része) ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Sidebar és a többi funkció (már a login nélkül!)
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés"):
    del st.session_state.username
    st.rerun()

menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "London", "New York"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "London", "New York"])
        price = c2.number_input("Ár (Ft)", min_value=0, value=1000)
        item = c2.text_input("Termék neve")
        photo = st.file_uploader("Fotó", type=['jpg', 'png'])
        
        if st.button("🚀 KÜLDÉS") and item and photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item,
                "price": price, "status": "WAITING", "state_text": "Csomagolás...",
                "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            st.success("Küldve!"); st.rerun()

with menu[1]:
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> {t['item']}")
            if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"acc_{tid}"):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.rerun()

    st.divider()
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            if t["sender"] == current_user:
                states = ["Csomagolás...", "Úton...", "A levegőben ✈️", "Kapu előtt 🚪"]
                curr = t["state_text"] if t["state_text"] in states else states[0]
                new_s = st.selectbox("Státusz", states, index=states.index(curr), key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s; st.rerun()
            else:
                st.info(f"📍 Helyzet: {t['state_text']}")
            
            pdf = create_pdf(t, tid)
            st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

with menu[2]:
    done = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]
    if done: st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])

time.sleep(3); st.rerun()
