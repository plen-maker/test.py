import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Tréd🔥🔥🔥", layout="wide",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTq9xFPrGZcuBi4sGho51wcEmiwO7M_cN35kQ&s"
)

# ─────────────────────────────────────────────
# SOUND JS
# ─────────────────────────────────────────────
CAT_SOUND_JS = """
<script>
function playCatSound(type) {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        const t = ctx.currentTime;
        if (type==='send'){
            osc.frequency.setValueAtTime(400,t);
            osc.frequency.linearRampToValueAtTime(800,t+0.2);
            osc.frequency.linearRampToValueAtTime(600,t+0.4);
            gain.gain.setValueAtTime(0.3,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
            osc.start(t); osc.stop(t+0.5);
        } else if (type==='receive'){
            osc.frequency.setValueAtTime(700,t);
            osc.frequency.linearRampToValueAtTime(350,t+0.3);
            osc.frequency.linearRampToValueAtTime(500,t+0.5);
            gain.gain.setValueAtTime(0.3,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.6);
            osc.start(t); osc.stop(t+0.6);
        } else if (type==='alert'){
            osc.frequency.setValueAtTime(600,t);
            osc.frequency.linearRampToValueAtTime(900,t+0.15);
            osc.frequency.setValueAtTime(600,t+0.25);
            osc.frequency.linearRampToValueAtTime(900,t+0.4);
            gain.gain.setValueAtTime(0.25,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
            osc.start(t); osc.stop(t+0.5);
        } else if (type==='done'){
            osc.frequency.setValueAtTime(500,t);
            osc.frequency.linearRampToValueAtTime(1000,t+0.3);
            osc.frequency.linearRampToValueAtTime(800,t+0.5);
            gain.gain.setValueAtTime(0.3,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.6);
            osc.start(t); osc.stop(t+0.6);
        }
    } catch(e){}
}
</script>
"""

# ─────────────────────────────────────────────
# NFC JS — Real contactless payment via Web NFC API
# Works on Chrome Android (>=89) in WebView with NFC permission
# Falls back to manual confirm on unsupported devices
# ─────────────────────────────────────────────
NFC_JS = """
<script>
// Global NFC state
window._nfcReader = null;
window._nfcActive = false;

async function startNFCScan(amount, orderId, callbackId) {
    const statusEl = document.getElementById('nfc-status-' + callbackId);
    const setStatus = (msg, color) => {
        if(statusEl) { statusEl.innerHTML = msg; if(color) statusEl.style.color = color; }
    };

    if (!('NDEFReader' in window)) {
        setStatus('❌ Web NFC nem támogatott ezen az eszközön.<br><small>Szükséges: Chrome Android + NFC engedély</small>', '#f5576c');
        return false;
    }

    try {
        setStatus('📡 NFC engedély kérése...', '#ffc107');
        const ndef = new NDEFReader();
        window._nfcReader = ndef;
        window._nfcActive = true;

        // Listen for incoming NFC tag / phone tap
        await ndef.scan();
        setStatus('📲 NFC aktív – közelítsd a fizető telefonját!', '#43e97b');

        ndef.addEventListener("reading", ({ message, serialNumber }) => {
            setStatus('✅ NFC érintés érzékelve! Feldolgozás...', '#43e97b');
            window._nfcActive = false;
            // Trigger Streamlit callback via URL fragment trick
            setTimeout(() => {
                const btn = document.getElementById('nfc-confirm-btn-' + callbackId);
                if(btn) btn.click();
            }, 600);
        });

        ndef.addEventListener("readingerror", () => {
            setStatus('⚠️ NFC olvasási hiba. Próbáld újra.', '#ffc107');
        });

        return true;
    } catch(e) {
        if(e.name === 'NotAllowedError') {
            setStatus('🔒 NFC engedély megtagadva. Engedélyezd az app beállításokban.', '#f5576c');
        } else if(e.name === 'NotSupportedError') {
            setStatus('❌ Az NFC nem elérhető ezen az eszközön.', '#f5576c');
        } else {
            setStatus('❌ Hiba: ' + e.message, '#f5576c');
        }
        return false;
    }
}

function stopNFCScan(callbackId) {
    window._nfcActive = false;
    const statusEl = document.getElementById('nfc-status-' + callbackId);
    if(statusEl) statusEl.innerHTML = '⏹️ NFC leállítva.';
}
</script>
"""

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Fix Streamlit expander arrow rendering bug */
.streamlit-expanderHeader svg { display: inline-block !important; }
details > summary { list-style: none !important; }
details > summary::-webkit-details-marker { display: none !important; }
.streamlit-expanderHeader { padding-left: 8px !important; }

/* Fix file uploader double label bug */
[data-testid="stFileUploader"] label { display: block !important; }
[data-testid="stFileUploader"] label + label { display: none !important; }

.rev-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px; padding: 24px; color: white; margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08);
}
.rev-balance {
    font-size: 44px; font-weight: 900;
    background: linear-gradient(90deg, #fff 0%, #a8edea 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -2px;
}
.rev-label { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 2px; }
.nfc-pulse {
    width: 90px; height: 90px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    font-size: 40px; margin: 0 auto 16px;
    animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0   rgba(102,126,234,0.7); }
    70%  { box-shadow: 0 0 0 22px rgba(102,126,234,0); }
    100% { box-shadow: 0 0 0 0   rgba(102,126,234,0); }
}
.payment-modal {
    background: linear-gradient(180deg,#1a1a2e,#0f0f1a);
    border-radius: 24px; padding: 28px; border: 1px solid rgba(255,255,255,0.12);
    text-align: center; margin: 8px 0;
}
.msg-bubble { background: rgba(102,126,234,0.12); border-left: 3px solid #667eea; border-radius: 0 10px 10px 0; padding: 9px 14px; margin: 6px 0; font-size: 12px; color: #ddd; }
.msg-bubble.alert { background: rgba(245,87,108,0.1); border-left-color: #f5576c; }
.paper-sign {
    background: linear-gradient(145deg,#fefefe,#f0efe6);
    border: 2px solid #d4c5a0; border-radius: 4px; padding: 28px;
    color: #2c2c2c; box-shadow: 3px 3px 10px rgba(0,0,0,0.15); position: relative; overflow: hidden;
}
.paper-sign::before {
    content: ''; position: absolute; inset: 0;
    background: repeating-linear-gradient(transparent, transparent 27px, #e8e0d0 27px, #e8e0d0 28px);
    opacity: 0.35; pointer-events: none;
}
.pill { display:inline-block; padding:3px 10px; border-radius:20px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; }
.pill-waiting { background:rgba(255,193,7,.2); color:#ffc107; }
.pill-accepted { background:rgba(102,126,234,.2); color:#667eea; }
.pill-done { background:rgba(67,233,123,.2); color:#43e97b; }
.tx-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.pos { color:#43e97b; font-weight:700; }
.neg { color:#f5576c; font-weight:700; }

/* ETA timer display */
.eta-timer { text-align:right; font-size:26px; font-weight:900; color:#667eea; }
.eta-soon  { text-align:right; color:#ffc107; font-weight:700; font-size:14px; }

/* Hide streamlit default hamburger/toolbar in embedded mode */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
"""

# ─────────────────────────────────────────────
# BLOCKLIST for item names
# ─────────────────────────────────────────────
BLOCKED_WORDS = [
    "nigger","nigga","neger","negro","faggot","retard","kike","spic","chink",
    "gook","tranny","cunt","slut","whore","bitch"
]

def contains_blocked_word(text: str) -> bool:
    lower = text.lower()
    return any(w in lower for w in BLOCKED_WORDS)

# ─────────────────────────────────────────────
# KÖZÖS MEMÓRIA
# ─────────────────────────────────────────────
@st.cache_resource
def get_global_data():
    return {
        "online_users": {},
        "active_trades": {},
        "balances": {
            "admin": 50000, "peti": 50000, "adel": 50000,
            "ddnemet": 50000, "kormuranusz": 50000
        },
        "messages": {},
        "eta_notified": set(),
        "order_counter": [1000],
        "bank_pins": {},
        "bank_sessions": {}
    }

global_data = get_global_data()
USERS = {
    "admin": "1234", "peti": "pisti77", "adel": "trade99",
    "kormuranusz": "kormicica", "ddnemet": "koficcica"
}

def next_order_id():
    global_data["order_counter"][0] += 1
    return f"ORD-{global_data['order_counter'][0]}"

def send_msg(user, text, mtype="info"):
    global_data["messages"].setdefault(user, []).append({
        "text": text, "type": mtype,
        "ts": datetime.now().strftime("%H:%M:%S"), "read": False
    })

def unread(user):
    return [m for m in global_data["messages"].get(user, []) if not m["read"]]

def mark_read(user):
    for m in global_data["messages"].get(user, []):
        m["read"] = True

# ─────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    c.setFillColor(colors.HexColor("#1a1a2e"))
    c.rect(0, H-80, W, 80, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 20); c.setFillColor(colors.white)
    c.drawString(50, H-48, "TRED PLATFORM  •  HIVATALOS SZAMLA")
    c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#a8edea"))
    c.drawString(50, H-66, f"Order: {t.get('order_id', tid)}   |   TID: {tid}")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10); c.drawString(50, H-100, f"Kiallitva: {t.get('accepted_at','N/A')}")
    c.line(50, H-110, W-50, H-110)
    y = H-135
    for label, val in [
        ("Felado", t['sender'].capitalize()),
        ("Cimzett", t['receiver'].capitalize()),
        ("Utvonal", f"{t['start_loc']}  ->  {t['end_loc']}"),
        ("Termek", t['item']),
        ("Leiras", t.get('description','–')),
    ]:
        c.setFont("Helvetica-Bold", 10); c.drawString(50, y, label+":")
        c.setFont("Helvetica", 10); c.drawString(160, y, str(val))
        y -= 18
    y -= 12; c.line(50, y+6, W-50, y+6)
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y-14, "Termekár:")
    c.setFont("Helvetica", 12); c.drawString(160, y-14, f"{t['price']} Cam")
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y-32, "Szallitas:")
    c.setFont("Helvetica", 12); c.drawString(160, y-32, "990 Cam")
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#f5576c"))
    c.drawString(50, y-56, f"VEGOSSZEG: {t['price']+990} Cam")
    c.setFont("Helvetica", 11); c.setFillColor(colors.black)
    c.drawString(50, y-76, f"Fizetesi mod: {t.get('payment_method','–')}")
    if t.get('signature'):
        c.drawString(50, y-96, f"Alairasas: {t['signature']}")
    c.setFillColor(colors.HexColor("#f0f0f0")); c.rect(0, 0, W, 36, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#777")); c.setFont("Helvetica", 9)
    c.drawString(50, 12, "Tred Platform  •  Automatikusan generalt szamla  •  Minden jog fenntartva")
    c.save(); buf.seek(0)
    return buf

# ─────────────────────────────────────────────
# INJECT STYLES + JS
# ─────────────────────────────────────────────
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(CAT_SOUND_JS, unsafe_allow_html=True)
st.markdown(NFC_JS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
placeholder = st.empty()

if "username" not in st.session_state:
    with placeholder.container():
        st.markdown("""
        <div style='max-width:380px;margin:70px auto;text-align:center;'>
            <div style='font-size:64px;'>😼</div>
            <h1 style='font-size:36px;font-weight:900;background:linear-gradient(90deg,#667eea,#f5576c);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:8px 0 4px;'>TRÉD</h1>
            <p style='color:#666;margin-bottom:32px;font-size:14px;'>Macskás kereskedési platform</p>
        </div>
        """, unsafe_allow_html=True)
        u = st.text_input("Felhasználónév", key="lu").lower().strip()
        p = st.text_input("Jelszó", type="password", key="lp")
        if st.button("🐾 Belépés", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok! 🙀")
    st.stop()

# ─────────────────────────────────────────────
# BEJELENTKEZVE
# ─────────────────────────────────────────────
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()
online_now = [u for u, ts in global_data["online_users"].items() if time.time() - ts < 10]

# ETA lejárat figyelő
for tid, t in list(global_data["active_trades"].items()):
    if t["status"] == "ACCEPTED":
        rem = (t["eta_time"] - datetime.now()).total_seconds()
        if rem <= 0 and tid not in global_data["eta_notified"]:
            global_data["eta_notified"].add(tid)
            oid = t.get("order_id", tid)
            send_msg(t["sender"], f"🕐 {oid} – ETA lejárt! A csomag hamarosan megérkezik. 🐾", "alert")
            send_msg(t["receiver"], f"🕐 {oid} – ETA lejárt! A csomagod hamarosan ott lesz, légy türelemmel! 🐾", "alert")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    bal = global_data["balances"].get(current_user, 0)
    unreads = unread(current_user)

    st.markdown(f"""
    <div class="rev-card">
        <div class="rev-label">Főszámla</div>
        <div class="rev-balance">{bal:,} Cam</div>
        <div style="margin-top:10px;font-size:13px;color:rgba(255,255,255,0.55);">
            👤 {current_user.capitalize()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:12px;color:#555;margin-bottom:12px;'>🟢 Online: {', '.join(online_now)}</div>",
                unsafe_allow_html=True)

    if unreads:
        st.markdown(f"#### 🔔 Értesítések ({len(unreads)})")
        for m in unreads[-6:]:
            icon = "🙀" if m["type"] == "alert" else "😺"
            css = "alert" if m["type"] == "alert" else ""
            st.markdown(f'<div class="msg-bubble {css}">{icon} <b>{m["ts"]}</b><br>{m["text"]}</div>',
                        unsafe_allow_html=True)
        if st.button("✓ Olvasottnak jelöl", use_container_width=True):
            mark_read(current_user); st.rerun()
    else:
        st.markdown("<div style='color:#444;font-size:12px;'>Nincs új értesítés 😸</div>", unsafe_allow_html=True)

    st.divider()

    my_done = [t for t in global_data["active_trades"].values()
               if t["status"] == "DONE" and current_user in (t["sender"], t["receiver"])]
    if my_done:
        st.markdown("#### 📊 Saját tranzakciók")
        for t in my_done[-5:]:
            amt = -(t["price"]+990) if t["receiver"] == current_user else (t["price"]+495)
            cls = "pos" if amt > 0 else "neg"
            sign = "+" if amt > 0 else ""
            st.markdown(f"""
            <div class="tx-row">
                <div>
                    <div style='font-size:12px;font-weight:600;'>{t['item']}</div>
                    <div style='font-size:10px;color:#555;'>{t.get('order_id','?')}</div>
                </div>
                <div class="{cls}">{sign}{amt} Cam</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Kijelentkezés", use_container_width=True):
        del st.session_state.username
        global_data["bank_sessions"].pop(current_user, None)
        st.rerun()

# ─────────────────────────────────────────────
# FŐ TABEK
# ─────────────────────────────────────────────
menu = st.tabs(["🚀 KÜLDÉS", "📋 BEJÖVŐ & AKTÍV", "🏦 BANK", "📜 HISTORY"])

# ════════════════════════════════════════════
# TAB 1 – KÜLDÉS
# ════════════════════════════════════════════
with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs online partner. Várj egy macskát... 😴")
    else:
        st.markdown("### 📦 Új szállítási ajánlat")
        col_form, col_prev = st.columns([3, 2])

        with col_form:
            target = st.selectbox("Címzett", targets, key="send_target")

            LOCATIONS = ["Budapest HUB","Catánia","London","New York","Codeland",
                         "Catániai Félszigetek","Nyauperth","Macskatelep","Tarantulai Fészkek"]

            loc_col1, loc_col2 = st.columns(2)
            with loc_col1:
                start = st.selectbox("Indulás", LOCATIONS, key="send_start")
            with loc_col2:
                end = st.selectbox("Célállomás", LOCATIONS, key="send_end")

            price_col, item_col = st.columns(2)
            with price_col:
                price = st.number_input("Ár (Cam)", min_value=0, value=1000, key="send_price")
            with item_col:
                item = st.text_input("Termék neve", key="send_item")

            desc = st.text_area("Termék leírása", key="send_desc")

            # FIX: single uploader, no duplicate label
            photo = st.file_uploader(
                "Fotó feltöltése (jpg/png)",
                type=["jpg", "jpeg", "png"],
                key="send_photo",
                label_visibility="visible"
            )
            if photo:
                st.image(photo, caption="Előnézet", use_container_width=True)

            if st.button("🚀 KÜLDÉS", use_container_width=True, key="send_btn"):
                if not item.strip():
                    st.warning("Add meg a termék nevét! 😾")
                elif contains_blocked_word(item):
                    st.error("⛔ A termék neve nem megfelelő. Kérjük adj meg egy megfelelő nevet!")
                elif not photo:
                    st.warning("Tölts fel egy fotót! 😾")
                else:
                    tid = f"TID-{int(time.time())}"
                    oid = next_order_id()
                    global_data["active_trades"][tid] = {
                        "order_id": oid, "sender": current_user, "receiver": target,
                        "item": item.strip(), "description": desc, "price": price,
                        "status": "WAITING", "state_text": "Csomagolás alatt...",
                        "photo": photo, "start_loc": start, "end_loc": end,
                        "eta_time": datetime.now() + timedelta(minutes=5),
                        "payment_method": None, "confirm_requested": False,
                        "confirmed": False, "signature": None
                    }
                    send_msg(target,
                        f"😺 {current_user.capitalize()} küldött neked egy ajánlatot! • {oid} • {item} • {price+990} Cam",
                        "info")
                    st.markdown("<script>playCatSound('send')</script>", unsafe_allow_html=True)
                    st.success(f"🐾 Elküldve! Order: {oid}")
                    st.rerun()

        with col_prev:
            p = st.session_state.get("send_price", 1000)
            st.markdown(f"""
            <div class="rev-card">
                <div class="rev-label">Összesítő</div>
                <div class="tx-row"><span style="color:#aaa">Termék</span><span style="font-weight:600">{p} Cam</span></div>
                <div class="tx-row"><span style="color:#aaa">Szállítás</span><span style="font-weight:600">990 Cam</span></div>
                <div style="display:flex;justify-content:space-between;padding:14px 0 0;">
                    <span style="color:white;font-weight:800;font-size:16px;">ÖSSZESEN</span>
                    <span class="pos" style="font-size:20px;">{p+990} Cam</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════
# TAB 2 – BEJÖVŐ & AKTÍV
# ════════════════════════════════════════════
with menu[1]:

    reqs = {tid: t for tid, t in global_data["active_trades"].items()
            if t["receiver"] == current_user and t["status"] == "WAITING"}

    if reqs:
        st.markdown("### 📩 Bejövő ajánlatok")

    for tid, t in reqs.items():
        with st.container(border=True):
            oid = t.get("order_id", tid)
            cost = t["price"] + 990
            ia, ib = st.columns([3,1])
            with ia:
                st.markdown(f"""
                <div>
                  <span style='font-size:17px;font-weight:700;'>📦 {t['item']}</span>
                  <span class='pill pill-waiting' style='margin-left:8px;'>VÁRAKOZIK</span><br>
                  <span style='color:#888;font-size:12px;'>Feladó: {t['sender'].capitalize()} •
                  {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>Order: {oid}</span>
                </div>""", unsafe_allow_html=True)
            with ib:
                st.markdown(f"<div style='text-align:right;font-size:18px;font-weight:800;color:#f5576c;'>{cost} Cam</div>",
                            unsafe_allow_html=True)

            st.markdown("#### 💳 Fizetési mód")
            pc1, pc2 = st.columns(2)

            with pc1:
                if st.button(f"💳 Kártyával", key=f"card_{tid}", use_container_width=True):
                    if global_data["balances"].get(current_user, 0) >= cost:
                        global_data["balances"][current_user] -= cost
                        global_data["balances"][t["sender"]] = global_data["balances"].get(t["sender"], 0) + t["price"] + 495
                        t["status"] = "ACCEPTED"
                        t["payment_method"] = "💳 Kártya"
                        t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        send_msg(t["sender"],
                            f"😸 {current_user.capitalize()} elfogadta! • {oid} • Kártyával • {cost} Cam", "info")
                        send_msg(current_user, f"✅ {oid} • Kártyás fizetés sikeres! {cost} Cam levonva.", "info")
                        st.markdown("<script>playCatSound('receive')</script>", unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.error("Nincs elég egyenleg! 😿")

            with pc2:
                if st.button(f"📲 NFC fizetés", key=f"nfc_{tid}", use_container_width=True):
                    st.session_state[f"nfc_open_{tid}"] = True

            if st.session_state.get(f"nfc_open_{tid}"):
                nfc_id = f"pay_{tid}"
                st.markdown(f"""
                <div class="payment-modal">
                    <div class="rev-label" style="color:#a8edea;">NFC ÉRINTÉSES FIZETÉS</div>
                    <div class="nfc-pulse">📲</div>
                    <div style="color:white;font-size:17px;font-weight:700;margin:8px 0;">
                        Közelítsd a fizető telefonját
                    </div>
                    <div style="color:#888;font-size:13px;">
                        Összeg: <b style="color:#43e97b;">{cost} Cam</b>
                    </div>
                    <div style="color:#555;font-size:11px;margin-top:4px;">Order: {oid}</div>
                    <div id="nfc-status-{nfc_id}" style="font-size:13px;margin-top:14px;color:#667eea;">
                        Inicializálás...
                    </div>
                </div>
                """, unsafe_allow_html=True)

                nfc_a, nfc_b, nfc_c = st.columns(3)
                with nfc_a:
                    # Start real NFC scan
                    if st.button("📡 NFC Indítás", key=f"nfc_start_{tid}", use_container_width=True):
                        st.markdown(
                            f"<script>startNFCScan({cost}, '{oid}', '{nfc_id}');</script>",
                            unsafe_allow_html=True
                        )
                with nfc_b:
                    # Manual confirm (fallback for devices without NFC)
                    if st.button("✅ Jóváhagyás", key=f"nfc_ok_{tid}", use_container_width=True):
                        if global_data["balances"].get(current_user, 0) >= cost:
                            global_data["balances"][current_user] -= cost
                            global_data["balances"][t["sender"]] = global_data["balances"].get(t["sender"], 0) + t["price"] + 495
                            t["status"] = "ACCEPTED"
                            t["payment_method"] = "📲 NFC"
                            t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.pop(f"nfc_open_{tid}", None)
                            send_msg(t["sender"],
                                f"😸 {current_user.capitalize()} NFC-vel fizetett! • {oid} • {cost} Cam", "info")
                            send_msg(current_user, f"✅ {oid} • NFC fizetés sikeres! 📲", "info")
                            st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.error("Nincs elég egyenleg! 😿")
                with nfc_c:
                    if st.button("❌ Mégse", key=f"nfc_cancel_{tid}", use_container_width=True):
                        st.session_state.pop(f"nfc_open_{tid}", None); st.rerun()

    st.divider()

    active = {tid: t for tid, t in global_data["active_trades"].items()
              if t["status"] == "ACCEPTED"}
    if active:
        st.markdown("### 🚚 Aktív szállítások")

    for tid, t in active.items():
        with st.container(border=True):
            oid = t.get("order_id", tid)
            rem = (t["eta_time"] - datetime.now()).total_seconds()

            hc1, hc2 = st.columns([3,1])
            with hc1:
                st.markdown(f"""
                <div>
                  <span style='font-size:15px;font-weight:700;'>🚚 {t['item']}</span>
                  <span class='pill pill-accepted' style='margin-left:8px;'>AKTÍV</span><br>
                  <span style='color:#888;font-size:12px;'>{oid} • {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>{t['sender'].capitalize()} → {t['receiver'].capitalize()} • {t.get('payment_method','–')}</span>
                </div>""", unsafe_allow_html=True)
            with hc2:
                if rem > 0:
                    mins = int(rem // 60)
                    secs = int(rem % 60)
                    st.markdown(
                        f"<div class='eta-timer'>⏳ {mins:02d}:{secs:02d}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<div class='eta-soon'>⏰ Hamarosan megérkezik!</div>",
                        unsafe_allow_html=True
                    )

            ctrl_col, info_col = st.columns(2)

            with ctrl_col:
                if t["sender"] == current_user:
                    STATES = ["Csomagolás alatt...","Úton a reptérre","A levegőben ✈️","Kiszállítás alatt","A kapu előtt 🚪"]
                    new_s = st.selectbox(
                        "📍 Státusz", STATES,
                        index=STATES.index(t["state_text"]) if t["state_text"] in STATES else 0,
                        key=f"s_{tid}"
                    )
                    if new_s != t["state_text"]:
                        old = t["state_text"]; t["state_text"] = new_s
                        send_msg(t["receiver"], f"🐾 {oid} • Státusz: **{new_s}** (volt: {old})", "info")
                        st.markdown("<script>playCatSound('send')</script>", unsafe_allow_html=True)
                        st.rerun()

                    # FIX: replaced expander (which caused _arrow_right bug) with a clean section
                    st.markdown("**⏱️ ETA módosítás**")
                    eta_col1, eta_col2 = st.columns([3, 1])
                    with eta_col1:
                        new_eta = st.number_input("Percben:", min_value=1, max_value=120, value=5, key=f"eta_{tid}")
                    with eta_col2:
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                        if st.button("🕐", key=f"etab_{tid}", use_container_width=True, help="ETA mentése"):
                            t["eta_time"] = datetime.now() + timedelta(minutes=new_eta)
                            global_data["eta_notified"].discard(tid)
                            send_msg(t["receiver"], f"⏱️ {oid} • ETA frissítve: {new_eta} perc!", "info")
                            st.rerun()

                    if not t.get("confirm_requested") and not t.get("confirmed"):
                        if st.button("📋 Visszaigazolás kérése", key=f"creq_{tid}", use_container_width=True):
                            t["confirm_requested"] = True
                            send_msg(t["receiver"],
                                f"✍️ {oid} • {t['sender'].capitalize()} kéri az aláírásodat! 🐾", "alert")
                            st.markdown("<script>playCatSound('alert')</script>", unsafe_allow_html=True)
                            st.rerun()
                    elif t.get("confirm_requested") and not t.get("confirmed"):
                        st.info("⏳ Várakozás az aláírásra...")
                    elif t.get("confirmed"):
                        st.success(f"✅ Aláírva: *{t.get('signature','')}*")
                else:
                    st.info(f"📍 {t['state_text']}")

            with info_col:
                if t["receiver"] == current_user and t.get("confirm_requested") and not t.get("confirmed"):
                    st.markdown(f"""
                    <div class="paper-sign">
                      <div style="text-align:center;font-size:15px;font-weight:700;margin-bottom:12px;position:relative;z-index:1;">
                          🐾 ÁTVÉTELI ELISMERVÉNY
                      </div>
                      <div style="position:relative;z-index:1;line-height:1.9;font-size:13px;">
                          Alulírott <b>{current_user.capitalize()}</b> igazolom, hogy a(z)
                          <b>{t['item']}</b> nevű küldeményt ({oid}) a mai napon
                          ({datetime.now().strftime('%Y.%m.%d')}) átvettem.
                          A csomag épségben megérkezett.
                      </div>
                    </div>""", unsafe_allow_html=True)
                    sig = st.text_input("✍️ Írd alá (a neved):", key=f"sig_{tid}", placeholder="pl. Peti...")
                    if st.button("🖊️ ALÁÍR & VISSZAIGAZOL", key=f"sign_{tid}", use_container_width=True):
                        if sig.strip():
                            t.update({"confirmed": True, "signature": sig.strip(),
                                      "status": "DONE",
                                      "done_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                            send_msg(t["sender"],
                                f"😺 {oid} • {current_user.capitalize()} aláírta! Aláírás: *{sig}* 🎉", "info")
                            send_msg(current_user, f"✅ {oid} • Ügylet lezárva! 🐾", "info")
                            st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.warning("Írd be a neved! 😾")

                pdf = create_pdf(t, tid)
                st.download_button("📥 SZÁMLA", data=pdf, file_name=f"szamla_{oid}.pdf",
                                   key=f"pdf_{tid}", use_container_width=True)

# ════════════════════════════════════════════
# TAB 3 – BANK
# ════════════════════════════════════════════
with menu[2]:

    bank_in = global_data["bank_sessions"].get(current_user, False)

    if not bank_in:
        st.markdown("### 🏦 Tréd Bank")
        has_pin = current_user in global_data["bank_pins"]

        _, center_col, _ = st.columns([1,2,1])
        with center_col:
            st.markdown(f"""
            <div class="rev-card" style="text-align:center;">
                <div style="font-size:52px;margin-bottom:8px;">🔐</div>
                <div class="rev-label">{"BANK PIN BELÉPÉS" if has_pin else "PIN BEÁLLÍTÁSA"}</div>
                <div style="color:rgba(255,255,255,0.5);font-size:12px;margin-top:8px;">
                    {"Add meg a 4 jegyű bank PIN-ed" if has_pin else "Állíts be egy 4 jegyű PIN-t a bank eléréséhez"}
                </div>
            </div>""", unsafe_allow_html=True)

            if not has_pin:
                pin1 = st.text_input("Új PIN (4 szám)", type="password", max_chars=4, key="bank_pin_new1")
                pin2 = st.text_input("PIN megerősítése", type="password", max_chars=4, key="bank_pin_new2")
                if st.button("🔐 PIN beállítása", use_container_width=True):
                    if len(pin1) == 4 and pin1.isdigit() and pin1 == pin2:
                        global_data["bank_pins"][current_user] = pin1
                        st.success("✅ PIN beállítva!")
                        st.rerun()
                    else:
                        st.error("4 számjegy kell, és egyezzen! 😾")
            else:
                entered = st.text_input("PIN", type="password", max_chars=4, key="bank_login_pin",
                                        label_visibility="collapsed", placeholder="••••")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🏦 Belépés", use_container_width=True):
                        if entered == global_data["bank_pins"].get(current_user):
                            global_data["bank_sessions"][current_user] = True
                            st.rerun()
                        else:
                            st.error("Hibás PIN! 😿")
                with b2:
                    if st.button("PIN törlése", use_container_width=True):
                        global_data["bank_pins"].pop(current_user, None)
                        st.rerun()
    else:
        bal = global_data["balances"].get(current_user, 0)
        bh1, bh2 = st.columns([5,1])
        with bh1:
            st.markdown("### 🏦 Tréd Bank")
        with bh2:
            if st.button("🔒 Zár", use_container_width=True):
                global_data["bank_sessions"][current_user] = False
                st.rerun()

        card_num = f"{abs(hash(current_user)) % 9000 + 1000}"
        st.markdown(f"""
        <div class="rev-card" style="min-height:200px;position:relative;overflow:hidden;">
            <div style="position:absolute;right:-30px;top:-30px;width:180px;height:180px;
                border-radius:50%;background:rgba(255,255,255,0.04);"></div>
            <div class="rev-label">Tréd Premium Számla</div>
            <div class="rev-balance" style="font-size:46px;margin:14px 0 8px;">{bal:,} Cam</div>
            <div style="display:flex;gap:40px;margin-top:8px;">
                <div><div class="rev-label">Tulajdonos</div>
                     <div style="color:white;font-weight:600;margin-top:3px;">{current_user.capitalize()}</div></div>
                <div><div class="rev-label">Típus</div>
                     <div style="color:#a8edea;font-weight:600;margin-top:3px;">Premium 🐾</div></div>
            </div>
            <div style="margin-top:18px;font-size:20px;letter-spacing:5px;color:rgba(255,255,255,0.3);">
                •••• •••• •••• {card_num}
            </div>
        </div>
        """, unsafe_allow_html=True)

        bank_tabs = st.tabs(["📲 NFC Terminál", "💳 Kártya küldés", "📊 Kimutatás"])

        with bank_tabs[0]:
            st.markdown("#### 📲 NFC Terminál – Érintéses Fizetés")
            st.markdown("""
            <div style="background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);
                border-radius:12px;padding:14px;font-size:13px;color:#aaa;margin-bottom:16px;">
                🐾 <b>Hogyan működik:</b><br>
                1. Add meg az összeget és a fizető felet<br>
                2. Kattints az <b>NFC Indítás</b> gombra<br>
                3. A fizető közelíti a telefonját<br>
                4. Az app automatikusan érzékeli és jóváhagyja<br><br>
                ⚠️ <b>Valódi NFC:</b> Chrome Android szükséges, és NFC engedély.<br>
                Ha nem érhető el, használd a kézi <b>Jóváhagyás</b> gombot.
            </div>""", unsafe_allow_html=True)

            tc1, tc2 = st.columns(2)
            nfc_amt = tc1.number_input("Összeg (Cam)", min_value=1, value=500, key="nfc_bank_amount")
            nfc_to  = tc2.selectbox("Fizető fél", [u for u in USERS if u != current_user], key="nfc_bank_to")
            nfc_oid_input = st.text_input("Order ID (opcionális)", placeholder="ORD-...", key="nfc_bank_oid")
            nfc_ref = nfc_oid_input if nfc_oid_input.strip() else "BANK"

            nfc_bank_id = f"bank_{current_user}"
            st.markdown(f"""
            <div class="payment-modal">
                <div class="nfc-pulse">📲</div>
                <div style="color:white;font-size:16px;font-weight:700;">NFC Terminál</div>
                <div style="color:#888;font-size:13px;margin:8px 0;">
                    Összeg: <b style="color:#43e97b;">{nfc_amt} Cam</b>
                    &nbsp;•&nbsp; Fizető: <b style="color:#a8edea;">{nfc_to.capitalize()}</b>
                </div>
                <div id="nfc-status-{nfc_bank_id}" style="color:#667eea;font-size:13px;margin-top:10px;">
                    Várakozás...
                </div>
            </div>""", unsafe_allow_html=True)

            na, nb, nc = st.columns(3)
            with na:
                if st.button("📡 NFC Indítás", use_container_width=True, key="nfc_start_bank"):
                    st.markdown(
                        f"<script>startNFCScan({nfc_amt}, '{nfc_ref}', '{nfc_bank_id}');</script>",
                        unsafe_allow_html=True
                    )
            with nb:
                # Manual fallback confirm
                if st.button("✅ Jóváhagyás", use_container_width=True, key="nfc_bank_ok"):
                    if global_data["balances"].get(nfc_to, 0) >= nfc_amt:
                        global_data["balances"][nfc_to] -= nfc_amt
                        global_data["balances"][current_user] = global_data["balances"].get(current_user, 0) + nfc_amt
                        send_msg(nfc_to, f"📲 NFC: {nfc_amt} Cam levonva → {current_user.capitalize()}", "info")
                        send_msg(current_user, f"✅ NFC beérkezett: {nfc_amt} Cam ← {nfc_to.capitalize()}", "info")
                        st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                        st.success(f"✅ {nfc_amt} Cam beérkezett!")
                        st.rerun()
                    else:
                        st.error("A fizető félnek nincs elég egyenlege! 😿")
            with nc:
                st.markdown(
                    "<div style='color:#444;font-size:10px;text-align:center;padding-top:6px;'>Kézi mód:<br>NFC nélkül</div>",
                    unsafe_allow_html=True
                )

        with bank_tabs[1]:
            st.markdown("#### 💳 Kártya küldés")
            ka, kb = st.columns(2)
            k_to  = ka.selectbox("Kinek", [u for u in USERS if u != current_user], key="k_to")
            k_amt = kb.number_input("Összeg (Cam)", min_value=1, value=200, key="k_amt")
            k_note = st.text_input("Megjegyzés (opcionális)", key="k_note")
            if st.button("💳 Küldés", use_container_width=True, key="k_send"):
                if global_data["balances"].get(current_user, 0) >= k_amt:
                    global_data["balances"][current_user] -= k_amt
                    global_data["balances"][k_to] = global_data["balances"].get(k_to, 0) + k_amt
                    note_txt = f" • {k_note}" if k_note else ""
                    send_msg(k_to, f"💳 {current_user.capitalize()} küldött {k_amt} Cam-et{note_txt}", "info")
                    send_msg(current_user, f"✅ {k_amt} Cam elküldve → {k_to.capitalize()}{note_txt}", "info")
                    st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                    st.success(f"✅ Elküldve! {k_amt} Cam → {k_to.capitalize()}")
                    st.rerun()
                else:
                    st.error("Nincs elég egyenleg! 😿")

        with bank_tabs[2]:
            st.markdown("#### 📊 Saját kimutatás")
            my_trades = [t for t in global_data["active_trades"].values()
                         if current_user in (t["sender"], t["receiver"])]
            if not my_trades:
                st.info("Még nincs tranzakció.")
            else:
                rows = []
                for t in my_trades:
                    is_recv = t["receiver"] == current_user
                    amt = -(t["price"]+990) if is_recv else (t["price"]+495)
                    rows.append({
                        "Order": t.get("order_id","?"),
                        "Termék": t["item"],
                        "Partner": t["sender"].capitalize() if is_recv else t["receiver"].capitalize(),
                        "Összeg": f"{'+' if amt>0 else ''}{amt} Cam",
                        "Státusz": t["status"],
                        "Fizetés": t.get("payment_method","–")
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════
# TAB 4 – HISTORY
# ════════════════════════════════════════════
with menu[3]:
    st.markdown("### 📜 Lezárt ügyletek")
    done = [t for t in global_data["active_trades"].values() if t["status"] == "DONE"]

    if not done:
        st.info("Még nincs lezárt ügylet. 😴")
    else:
        for t in reversed(done):
            oid = t.get("order_id","?")
            with st.container(border=True):
                hh1, hh2 = st.columns([4,1])
                with hh1:
                    sig_html = f"<br><span style='color:#888;font-size:12px;'>✍️ {t['signature']}</span>" if t.get('signature') else ""
                    st.markdown(f"""
                    <div>
                      <span style='font-weight:700;'>✅ {t['item']}</span>
                      <span class='pill pill-done' style='margin-left:8px;'>LEZÁRVA</span><br>
                      <span style='color:#888;font-size:12px;'>{oid} • {t['sender'].capitalize()} → {t['receiver'].capitalize()}</span><br>
                      <span style='color:#888;font-size:12px;'>{t['start_loc']} → {t['end_loc']} • {t.get('payment_method','–')}</span>
                      {sig_html}
                    </div>""", unsafe_allow_html=True)
                with hh2:
                    st.markdown(f"<div style='text-align:right;color:#43e97b;font-weight:800;font-size:18px;'>{t['price']+990} Cam</div>",
                                unsafe_allow_html=True)

                pdf = create_pdf(t, oid)
                st.download_button("📥 Számla", data=pdf, file_name=f"szamla_{oid}.pdf",
                                   key=f"hist_{oid}_{id(t)}", use_container_width=True)

# Auto-refresh every 3 seconds
time.sleep(3)
st.rerun()
