import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ÉS TISZTÍTÁS ---
st.set_page_config(
    page_title="Tréd🔥🔥🔥", 
    layout="wide", 
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTq9xFPrGZcuBi4sGho51wcEmiwO7M_cN35kQ&s"
)

# Drasztikus CSS tisztítás: Eltünteti a Streamlit sávokat és promókat
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #stDecoration {display:none;}
            [data-testid="stHeader"] {display:none;}
            .stApp [data-testid="stToolbar"] {display:none;}
            [data-testid="manage-app-button"] {display: none;}
            .viewerBadge_container__1QSob {display: none;}
            .block-container {padding-top: 2rem !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000, "ddnemet": 50000, "kormuranusz": 50000},
        "base_gallery": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99", "kormuranusz": "kormicica", "ddnemet": "koficcica"}

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
    c.drawString(50, height - 70, f"Tranzakció azonosító: {tid}")
    c.drawString(50, height - 85, f"Elfogadás ideje: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 95, width - 50, height - 95)
    y = height - 120
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "SZÁLLÍTÁSI ADATOK")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Feladó: {t['sender'].capitalize()}")
    y -= 15; c.drawString(60, y, f"Címzett: {t['receiver'].capitalize()}")
    y -= 15; c.drawString(60, y, f"Útvonal: {t['start_loc']}  ---->>>  {t['end_loc']}")
    y -= 40; c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "TERMÉK INFORMÁCIÓ")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Megnevezés: {t['item']}")
    y -= 15; c.setFont("Helvetica-Oblique", 10)
    c.drawString(60, y, f"Leírás: {t.get('description', 'Nincs leírás')}")
    y -= 50; c.line(50, y+10, width - 50, y+10)
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "KÖLTSÉGVETÉS")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Termék eredeti ára: {t['price']} Cam")
    y -= 15; c.drawString(60, y, f"Szállítási díj: 990 Cam")
    y -= 30; c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.red)
    c.drawString(50, y, f"TELJES FIZETETT ÖSSZEG: {t['price'] + 990} Cam")
    c.save(); buf.seek(0)
    return buf

# --- 4. LOGIN KEZELÉS ---
placeholder = st.empty()

if 'username' not in st.session_state:
    with placeholder.container():
        st.title("🛡️ Bejelentkezés")
        u = st.text_input("Felhasználónév", key="login_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="login_p")
        if st.button("Belépés", key="login_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

# --- 5. HA BE VAN LÉPVE, CSAK EZ FUT LE ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# SIDEBAR
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Cam")

if st.sidebar.button("Kijelentkezés"):
    del st.session_state.username
    st.rerun()

# FŐ APP FELÜLET
menu = st.tabs(["🚀 KÜLDÉS", "📋 FELRAKTAM A KEZEM", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        locations = ["Budapest HUB", "Catánia", "London", "New York", "Codeland" , "Catániai Félszigetek", "Nyauperth", "Macskatelep", "Tarantulai Fészkek"]
        start = c1.selectbox("Indulás", locations)
        end = c1.selectbox("Célállomás", locations)
        price = c2.number_input("Ár (Cam)", min_value=0, value=1000)
        item = c2.text_input("Termék neve")
        desc = st.text_area("Termék leírása")
        photo = st.file_uploader("Fotó", type=['jpg', 'png'])
        
        if st.button("🚀 KÜLDÉS") and item and photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item, "description": desc,
                "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                "photo": photo, "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            st.success("Küldve!"); st.rerun()

with menu[1]:
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> {t['item']}")
            if st.button(f"ELFOGADOM ({t['price']+990} Cam)", key=f"acc_{tid}"):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.rerun()
                else:
                    st.error("Nincs elég fedezeted!")

    st.divider()

    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            c_ctrl, c_info = st.columns(2)
            with c_ctrl:
                if t["sender"] == current_user:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    new_s = st.selectbox("Státusz", states, index=states.index(t["state_text"]) if t["state_text"] in states else 0, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s; st.rerun()
                    with st.expander("⏱️ ETA módosítása"):
                        new_eta = st.number_input("Perc:", 1, 120, 5, key=f"eta_{tid}")
                        if st.button("Mentés", key=f"etab_{tid}"):
                            t["eta_time"] = datetime.now() + timedelta(minutes=new_eta); st.rerun()
                else:
                    st.info(f"📍 Helyzet: {t['state_text']}")

            with c_info:
                rem = (t["eta_time"] - datetime.now()).total_seconds()
                if rem > 0:
                    st.subheader(f"⏳ {int(rem//60):02d}:{int(rem%60):02d}")
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t["receiver"] and st.button("ÁTVÉTEL", key=f"done_{tid}"):
                        t["status"] = "DONE"; st.rerun()
                
                pdf = create_pdf(t, tid)
                st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

with menu[2]:
    done = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]
    if done: 
        st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])
    else:
        st.info("Még nincs lezárt tranzakció.")

# Automatikus frissítés 3 másodpercenként
time.sleep(3); st.rerun()
