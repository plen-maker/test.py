import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

st.components.v1.html("""
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js"></script>

<script>

const firebaseConfig = {
  apiKey: "AIzaSyDZb9bdfMFfzBRKM7bMO7GbvIH5CutYZB0",
  authDomain: "cattrade-591fb.firebaseapp.com",
  projectId: "cattrade-591fb",
  messagingSenderId: "168227931827",
  appId: "1:168227931827:web:07fb9c3de0be56395252c6"
};

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

Notification.requestPermission().then(permission => {
  if (permission === "granted") {
    messaging.getToken().then(token => {
      console.log("TOKEN:", token);
      alert("TOKEN:\\n" + token);
    });
  }
});

</script>
""", height=0)

st.set_page_config(
    page_title="Tréd🔥🔥🔥", layout="wide",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTq9xFPrGZcuBi4sGho51wcEmiwO7M_cN35kQ&s"
)

# ─────────────────────────────────────────────
# JAVASCRIPT — Sound + Vibration + NFC + Alerts
# ─────────────────────────────────────────────
JS_ALL = """
<script>
// ── SOUNDS ──────────────────────────────────
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
            gain.gain.setValueAtTime(0.4,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
            osc.start(t); osc.stop(t+0.5);
        } else if (type==='receive'){
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.connect(gain2); gain2.connect(ctx.destination);
            osc.frequency.setValueAtTime(880,t);
            gain.gain.setValueAtTime(0.5,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.25);
            osc.start(t); osc.stop(t+0.25);
            osc2.frequency.setValueAtTime(1100,t+0.3);
            gain2.gain.setValueAtTime(0.5,t+0.3);
            gain2.gain.exponentialRampToValueAtTime(0.01,t+0.55);
            osc2.start(t+0.3); osc2.stop(t+0.55);
        } else if (type==='alert'){
            osc.frequency.setValueAtTime(600,t);
            osc.frequency.linearRampToValueAtTime(1200,t+0.15);
            osc.frequency.setValueAtTime(600,t+0.25);
            osc.frequency.linearRampToValueAtTime(1200,t+0.4);
            gain.gain.setValueAtTime(0.5,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
            osc.start(t); osc.stop(t+0.5);
        } else if (type==='done'){
            osc.frequency.setValueAtTime(500,t);
            osc.frequency.linearRampToValueAtTime(1000,t+0.2);
            osc.frequency.linearRampToValueAtTime(1500,t+0.4);
            gain.gain.setValueAtTime(0.4,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
            osc.start(t); osc.stop(t+0.5);
        } else if (type==='nfc'){
            osc.frequency.setValueAtTime(300,t);
            osc.frequency.linearRampToValueAtTime(1400,t+0.25);
            gain.gain.setValueAtTime(0.4,t);
            gain.gain.exponentialRampToValueAtTime(0.01,t+0.35);
            osc.start(t); osc.stop(t+0.35);
        }
    } catch(e){}
}

// ── VIBRATION ────────────────────────────────
function vibrate(pattern) {
    try { if (navigator.vibrate) navigator.vibrate(pattern); } catch(e){}
}

// ── SCREEN FLASH ─────────────────────────────
function flashScreen(color) {
    const el = document.createElement('div');
    el.style.cssText = 'position:fixed;inset:0;z-index:99999;pointer-events:none;background:' + (color||'rgba(102,126,234,0.35)') + ';transition:opacity 0.4s';
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity='0'; setTimeout(()=>el.remove(),400); }, 200);
}

// ── FULL ALERT ───────────────────────────────
function fullAlert(type) {
    if (type==='receive') {
        playCatSound('receive'); vibrate([200,100,200,100,400]); flashScreen('rgba(67,233,123,0.3)');
    } else if (type==='alert') {
        playCatSound('alert');  vibrate([300,100,300,100,300]); flashScreen('rgba(245,87,108,0.35)');
    } else if (type==='done') {
        playCatSound('done');   vibrate([100,50,100,50,600]);   flashScreen('rgba(67,233,123,0.25)');
    } else if (type==='nfc') {
        playCatSound('nfc');    vibrate([50,30,50,30,200]);     flashScreen('rgba(102,126,234,0.4)');
    } else {
        playCatSound(type); vibrate([150]);
    }
}

// ── PAGE TITLE BLINK ─────────────────────────
let _origTitle = document.title;
let _titleInterval = null;
function alertTitle(msg) {
    if (_titleInterval) return;
    let on = true;
    _titleInterval = setInterval(() => {
        document.title = on ? ('🔔 ' + msg) : _origTitle; on = !on;
    }, 900);
}
function clearTitleAlert() {
    if (_titleInterval) { clearInterval(_titleInterval); _titleInterval = null; }
    document.title = _origTitle;
}

// ── NFC ──────────────────────────────────────
// FIX for vnd.android bug: we use recordType="text" (plain text NDEF record)
// NOT "url" or MIME — Android will NOT intercept plain text records as intents.
window._nfcAbort = null;

async function startNFCWrite(amount, orderId, statusId) {
    const el = document.getElementById('nfc-status-' + statusId);
    const set = (m,c) => { if(el){ el.innerHTML=m; if(c) el.style.color=c; } };
    if (!('NDEFReader' in window)) { set('❌ Web NFC nem támogatott. Chrome Android 89+ kell.','#f5576c'); return; }
    try {
        set('🔐 NFC engedély kérése...','#ffc107');
        const ndef = new NDEFReader();
        // Plain text payload — no vnd.android, no URL interception
        const payload = JSON.stringify({ tred:1, amount:amount, order:orderId, ts:Date.now() });
        await ndef.write({ records:[{ recordType:"text", data:payload, lang:"hu" }] });
        set('✅ Adat kiírva! Közelítsd a másik telefont...','#43e97b');
        fullAlert('nfc');
    } catch(e) {
        if (e.name==='NotAllowedError') set('🔒 NFC engedély megtagadva.','#f5576c');
        else set('❌ '+e.message,'#f5576c');
    }
}

async function startNFCRead(statusId, confirmBtnId) {
    const el = document.getElementById('nfc-status-' + statusId);
    const set = (m,c) => { if(el){ el.innerHTML=m; if(c) el.style.color=c; } };
    if (!('NDEFReader' in window)) { set('❌ Web NFC nem támogatott.','#f5576c'); return; }
    try {
        set('📡 NFC olvasó aktív – érintsd a terminál telefonját...','#ffc107');
        const ndef = new NDEFReader();
        if (window._nfcAbort) window._nfcAbort.abort();
        window._nfcAbort = new AbortController();
        await ndef.scan({ signal: window._nfcAbort.signal });
        ndef.addEventListener("reading", ({ message }) => {
            try {
                const rec = message.records[0];
                const txt = new TextDecoder(rec.encoding||'utf-8').decode(rec.data);
                const data = JSON.parse(txt);
                if (data.tred) {
                    set('✅ Tréd fizetés! Összeg: ' + data.amount + ' Cam','#43e97b');
                    fullAlert('receive');
                    // auto-click confirm button
                    const btn = document.getElementById(confirmBtnId);
                    if (btn) setTimeout(()=>btn.click(), 600);
                } else {
                    set('⚠️ Ismeretlen NFC adat.','#ffc107');
                }
            } catch(e) { set('⚠️ Hiba: '+e.message,'#ffc107'); }
        });
        ndef.addEventListener("readingerror", () => set('⚠️ NFC olvasási hiba.','#ffc107'));
    } catch(e) {
        if (e.name==='AbortError') { set('⏹️ Leállítva.','#888'); return; }
        if (e.name==='NotAllowedError') { set('🔒 NFC engedély megtagadva.','#f5576c'); return; }
        set('❌ '+e.message,'#f5576c');
    }
}

function stopNFC(statusId) {
    if (window._nfcAbort) { window._nfcAbort.abort(); window._nfcAbort=null; }
    const el = document.getElementById('nfc-status-'+(statusId||''));
    if(el) el.innerHTML='⏹️ NFC leállítva.';
}
</script>
"""

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* FIX: hide the _arrow_right / double_arrow_right text that leaks from expander */
[data-testid="stExpander"] summary > div > p { display: none !important; }
[data-testid="stExpander"] summary svg { display: inline !important; }
details > summary { list-style: none !important; }
details > summary::-webkit-details-marker { display: none !important; }

/* FIX: file uploader double label */
[data-testid="stFileUploader"] label + label { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] div + div { display: none !important; }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

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
    animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(102,126,234,0.8); transform:scale(1); }
    50%      { box-shadow: 0 0 0 20px rgba(102,126,234,0); transform:scale(1.05); }
}
.payment-modal {
    background: linear-gradient(180deg,#1a1a2e,#0f0f1a);
    border-radius: 24px; padding: 28px; border: 1px solid rgba(255,255,255,0.12);
    text-align: center; margin: 8px 0;
}
.msg-bubble { background: rgba(102,126,234,0.12); border-left: 3px solid #667eea; border-radius: 0 10px 10px 0; padding: 9px 14px; margin: 6px 0; font-size: 12px; color: #ddd; }
.msg-bubble.alert { background: rgba(245,87,108,0.1); border-left-color: #f5576c; }
.paper-sign {
    background: linear-gradient(145deg,#fefefe,#f0efe6); border: 2px solid #d4c5a0;
    border-radius: 4px; padding: 28px; color: #2c2c2c;
    box-shadow: 3px 3px 10px rgba(0,0,0,0.15); position: relative; overflow: hidden;
}
.paper-sign::before {
    content:''; position:absolute; inset:0;
    background: repeating-linear-gradient(transparent,transparent 27px,#e8e0d0 27px,#e8e0d0 28px);
    opacity:0.35; pointer-events:none;
}
.pill { display:inline-block; padding:3px 10px; border-radius:20px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; }
.pill-waiting  { background:rgba(255,193,7,.2);   color:#ffc107; }
.pill-accepted { background:rgba(102,126,234,.2); color:#667eea; }
.pill-done     { background:rgba(67,233,123,.2);  color:#43e97b; }
.tx-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.pos { color:#43e97b; font-weight:700; }
.neg { color:#f5576c; font-weight:700; }
.eta-timer { text-align:right; font-size:28px; font-weight:900; color:#667eea; }
.eta-soon  { text-align:right; color:#ffc107; font-weight:700; font-size:14px; }
.notif-banner {
    background: linear-gradient(90deg,#f5576c,#c0392b); border-radius:12px;
    padding:12px 16px; margin:8px 0; color:white; font-weight:700; font-size:14px;
    animation: bannerPulse 0.8s ease-in-out infinite alternate;
}
@keyframes bannerPulse {
    from { box-shadow: 0 0 0 0 rgba(245,87,108,0.6); }
    to   { box-shadow: 0 0 16px 4px rgba(245,87,108,0.3); }
}
</style>
"""

# ─────────────────────────────────────────────
# BLOCKLIST
# ─────────────────────────────────────────────
BLOCKED_WORDS = ["nigger","nigga","neger","negro","faggot","retard","kike","spic","chink","gook","tranny","cunt","slut","whore"]
def contains_blocked(text):
    lo = text.lower()
    return any(w in lo for w in BLOCKED_WORDS)

# ─────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, "active_trades": {},
        "balances": {"admin":50000,"peti":50000,"adel":50000,"ddnemet":50000,"kormuranusz":50000},
        "messages": {}, "eta_notified": set(), "order_counter": [1000],
        "bank_pins": {}, "bank_sessions": {}, "last_msg_count": {}
    }

global_data = get_global_data()
USERS = {"admin":"1234","peti":"pisti77","adel":"trade99","kormuranusz":"kormicica","ddnemet":"koficcica"}

def next_order_id():
    global_data["order_counter"][0] += 1
    return f"ORD-{global_data['order_counter'][0]}"

def send_msg(user, text, mtype="info"):
    global_data["messages"].setdefault(user, []).append(
        {"text":text,"type":mtype,"ts":datetime.now().strftime("%H:%M:%S"),"read":False})

def unread(user):
    return [m for m in global_data["messages"].get(user,[]) if not m["read"]]

def mark_read(user):
    for m in global_data["messages"].get(user,[]): m["read"] = True

# ─────────────────────────────────────────────
# IMPROVED PDF
# ─────────────────────────────────────────────
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # Header
    c.setFillColor(colors.HexColor("#0f3460"))
    c.rect(0, H-90, W, 90, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#667eea"))
    c.rect(0, H-90, 10, 90, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 28); c.setFillColor(colors.white)
    c.drawString(30, H-55, "TRÉD")
    c.setFont("Helvetica", 11); c.setFillColor(colors.HexColor("#a8edea"))
    c.drawString(30, H-72, "Kereskedési Platform")
    c.setFont("Helvetica-Bold", 20); c.setFillColor(colors.white)
    c.drawRightString(W-30, H-50, "SZÁMLA")
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#a8edea"))
    oid = t.get("order_id", tid)
    c.drawRightString(W-30, H-66, f"Order: {oid}")

    # Info bar
    y = H-115
    c.setFillColor(colors.HexColor("#f0f4ff"))
    c.rect(30, y-12, W-60, 44, fill=1, stroke=0)
    labels = ["Kiállítva", "Feladó", "Címzett", "Fizetési mód"]
    vals = [
        t.get("accepted_at", datetime.now().strftime("%Y-%m-%d %H:%M"))[:16],
        t["sender"].capitalize(), t["receiver"].capitalize(),
        t.get("payment_method","–")
    ]
    xs = [40, 160, 290, 420]
    for lbl, val, x in zip(labels, vals, xs):
        c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.HexColor("#888"))
        c.drawString(x, y+18, lbl)
        c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#111"))
        c.drawString(x, y+4, str(val)[:20])

    # Section: Szállítási adatok
    y -= 36
    c.setFillColor(colors.HexColor("#667eea")); c.rect(30,y,W-60,22,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",10); c.setFillColor(colors.white)
    c.drawString(40,y+6,"SZÁLLÍTÁSI ADATOK")

    rows_data = [
        ("Útvonal", f"{t.get('start_loc','?')}  →  {t.get('end_loc','?')}"),
        ("Termék neve", t.get("item","–")),
        ("Leírás", (t.get("description","–") or "–")[:65]),
        ("TID", tid),
    ]
    y -= 2
    for i,(lbl,val) in enumerate(rows_data):
        bg = colors.HexColor("#f7f9ff") if i%2==0 else colors.white
        c.setFillColor(bg); c.rect(30,y-16,W-60,20,fill=1,stroke=0)
        c.setFont("Helvetica-Bold",9); c.setFillColor(colors.HexColor("#555"))
        c.drawString(40,y-8,lbl+":")
        c.setFont("Helvetica",9); c.setFillColor(colors.HexColor("#111"))
        c.drawString(165,y-8,str(val))
        y -= 20

    # Section: Összesítő
    y -= 14
    c.setFillColor(colors.HexColor("#0f3460")); c.rect(30,y,W-60,22,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",10); c.setFillColor(colors.white)
    c.drawString(40,y+6,"ÖSSZESÍTŐ")

    line_items = [("Termék ára",f"{t['price']:,} Cam"),("Szállítási díj","990 Cam")]
    y -= 2
    for i,(lbl,val) in enumerate(line_items):
        bg = colors.HexColor("#f7f9ff") if i%2==0 else colors.white
        c.setFillColor(bg); c.rect(30,y-16,W-60,20,fill=1,stroke=0)
        c.setFont("Helvetica",10); c.setFillColor(colors.HexColor("#333"))
        c.drawString(40,y-8,lbl)
        c.drawRightString(W-38,y-8,val)
        y -= 20

    # Total
    y -= 6
    c.setFillColor(colors.HexColor("#43e97b")); c.rect(30,y-4,W-60,28,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",14); c.setFillColor(colors.HexColor("#0a2a1a"))
    c.drawString(40,y+8,"VÉGÖSSZEG")
    c.drawRightString(W-38,y+8,f"{t['price']+990:,} Cam")

    # Signature
    if t.get("signature"):
        y -= 40
        c.setFillColor(colors.HexColor("#fff8e7")); c.rect(30,y-8,W-60,30,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor("#d4c5a0")); c.rect(30,y-8,W-60,30,fill=0,stroke=1)
        c.setFont("Helvetica-Bold",9); c.setFillColor(colors.HexColor("#888"))
        c.drawString(40,y+14,"ÁTVÉTELI ALÁÍRÁS:")
        c.setFont("Helvetica",12); c.setFillColor(colors.HexColor("#222"))
        c.drawString(190,y+14,t["signature"])

    # Status badge
    y -= 48
    sc = colors.HexColor("#43e97b") if t.get("status")=="DONE" else colors.HexColor("#667eea")
    c.setFillColor(sc); c.roundRect(30,y,100,22,8,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",9); c.setFillColor(colors.white)
    c.drawString(40,y+6,"✓ TELJESÍTVE" if t.get("status")=="DONE" else "● AKTÍV")

    # Watermark
    if t.get("status")=="DONE":
        c.saveState()
        c.translate(W/2,H/2); c.rotate(32)
        c.setFont("Helvetica-Bold",80)
        c.setFillColor(colors.HexColor("#43e97b"))
        c.setFillAlpha(0.06)
        c.drawCentredString(0,0,"TELJESÍTVE")
        c.restoreState()

    # Footer
    c.setFillColor(colors.HexColor("#1a1a2e")); c.rect(0,0,W,42,fill=1,stroke=0)
    c.setFillColor(colors.HexColor("#667eea")); c.rect(0,0,6,42,fill=1,stroke=0)
    c.setFont("Helvetica",8); c.setFillColor(colors.HexColor("#aaa"))
    c.drawString(20,26,"TRÉD Platform  •  Automatikusan generált számla  •  Minden jog fenntartva")
    c.drawRightString(W-20,26,f"Generálva: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.setFillColor(colors.HexColor("#555"))
    c.drawString(20,12,f"TID: {tid}")
    c.drawRightString(W-20,12,f"Order: {oid}")

    c.save(); buf.seek(0)
    return buf

# ─────────────────────────────────────────────
# INJECT
# ─────────────────────────────────────────────
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(JS_ALL, unsafe_allow_html=True)

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
        </div>""", unsafe_allow_html=True)
        u = st.text_input("Felhasználónév", key="lu").lower().strip()
        p = st.text_input("Jelszó", type="password", key="lp")
        if st.button("🐾 Belépés", use_container_width=True):
            if u in USERS and USERS[u]==p:
                st.session_state.username=u; placeholder.empty(); st.rerun()
            else:
                st.error("Hibás adatok! 🙀")
    st.stop()

# ─────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()
online_now = [u for u,ts in global_data["online_users"].items() if time.time()-ts<10]

# New message alert
prev_count = global_data["last_msg_count"].get(current_user, 0)
cur_unreads = unread(current_user)
cur_count = len(cur_unreads)
if cur_count > prev_count:
    latest = cur_unreads[-1]
    atype = "alert" if latest["type"]=="alert" else "receive"
    st.markdown(f"<script>fullAlert('{atype}'); alertTitle('ÚJ ÉRTESÍTÉS');</script>", unsafe_allow_html=True)
    global_data["last_msg_count"][current_user] = cur_count

# ETA check
for tid, t in list(global_data["active_trades"].items()):
    if t["status"]=="ACCEPTED":
        rem = (t["eta_time"]-datetime.now()).total_seconds()
        if rem<=0 and tid not in global_data["eta_notified"]:
            global_data["eta_notified"].add(tid)
            oid = t.get("order_id",tid)
            send_msg(t["sender"], f"🕐 {oid} – ETA lejárt! A csomag hamarosan megérkezik. 🐾","alert")
            send_msg(t["receiver"],f"🕐 {oid} – ETA lejárt! A csomagod hamarosan ott lesz! 🐾","alert")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    bal = global_data["balances"].get(current_user,0)
    st.markdown(f"""
    <div class="rev-card">
        <div class="rev-label">Főszámla</div>
        <div class="rev-balance">{bal:,} Cam</div>
        <div style="margin-top:10px;font-size:13px;color:rgba(255,255,255,0.55);">👤 {current_user.capitalize()}</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:#555;margin-bottom:12px;'>🟢 Online: {', '.join(online_now)}</div>", unsafe_allow_html=True)

    if cur_unreads:
        st.markdown(f'<div class="notif-banner">🔔 {len(cur_unreads)} új értesítés!</div>', unsafe_allow_html=True)
        for m in cur_unreads[-6:]:
            icon="🙀" if m["type"]=="alert" else "😺"
            css="alert" if m["type"]=="alert" else ""
            st.markdown(f'<div class="msg-bubble {css}">{icon} <b>{m["ts"]}</b><br>{m["text"]}</div>', unsafe_allow_html=True)
        if st.button("✓ Olvasottnak jelöl", use_container_width=True):
            mark_read(current_user)
            global_data["last_msg_count"][current_user]=0
            st.markdown("<script>clearTitleAlert();</script>", unsafe_allow_html=True)
            st.rerun()
    else:
        st.markdown("<div style='color:#444;font-size:12px;'>Nincs új értesítés 😸</div>", unsafe_allow_html=True)

    st.divider()
    my_done = [t for t in global_data["active_trades"].values()
               if t["status"]=="DONE" and current_user in (t["sender"],t["receiver"])]
    if my_done:
        st.markdown("#### 📊 Saját tranzakciók")
        for t in my_done[-5:]:
            amt = -(t["price"]+990) if t["receiver"]==current_user else (t["price"]+495)
            cls="pos" if amt>0 else "neg"; sign="+" if amt>0 else ""
            st.markdown(f"""
            <div class="tx-row">
                <div><div style='font-size:12px;font-weight:600;'>{t['item']}</div>
                     <div style='font-size:10px;color:#555;'>{t.get('order_id','?')}</div></div>
                <div class="{cls}">{sign}{amt:,} Cam</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Kijelentkezés", use_container_width=True):
        del st.session_state.username
        global_data["bank_sessions"].pop(current_user,None)
        st.rerun()

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
menu = st.tabs(["🚀 KÜLDÉS","📋 BEJÖVŐ & AKTÍV","🏦 BANK","📜 HISTORY"])

# ════════════════════════════════════════════
# TAB 1 – KÜLDÉS
# ════════════════════════════════════════════
with menu[0]:
    targets = [u for u in online_now if u!=current_user]
    if not targets:
        st.info("Nincs online partner. Várj egy macskát... 😴")
    else:
        st.markdown("### 📦 Új szállítási ajánlat")
        col_form, col_prev = st.columns([3,2])
        with col_form:
            target = st.selectbox("Címzett", targets, key="send_target")
            LOCATIONS = ["Budapest HUB","Catánia","London","New York","Codeland",
                         "Catániai Félszigetek","Nyauperth","Macskatelep","Tarantulai Fészkek"]
            lc1,lc2 = st.columns(2)
            with lc1: start = st.selectbox("Indulás", LOCATIONS, key="send_start")
            with lc2: end   = st.selectbox("Célállomás", LOCATIONS, key="send_end")
            pc1,pc2 = st.columns(2)
            with pc1: price = st.number_input("Ár (Cam)", min_value=0, value=1000, key="send_price")
            with pc2: item  = st.text_input("Termék neve", key="send_item", placeholder="pl. Arany lánc")
            desc = st.text_area("Termék leírása", key="send_desc", placeholder="Opcionális...")

            # FIX double label: hide label via label_visibility, show our own bold label
            st.markdown("**📷 Fotó feltöltése**")
            photo = st.file_uploader("foto", type=["jpg","jpeg","png"],
                                     key="send_photo", label_visibility="collapsed")
            if photo: st.image(photo, caption="Előnézet", use_container_width=True)

            if st.button("🚀 KÜLDÉS", use_container_width=True, key="send_btn"):
                if not item.strip():
                    st.warning("Add meg a termék nevét! 😾")
                elif contains_blocked(item):
                    st.error("⛔ A termék neve nem megfelelő!")
                elif not photo:
                    st.warning("Tölts fel egy fotót! 😾")
                else:
                    tid = f"TID-{int(time.time())}"
                    oid = next_order_id()
                    global_data["active_trades"][tid] = {
                        "order_id":oid,"sender":current_user,"receiver":target,
                        "item":item.strip(),"description":desc,"price":price,
                        "status":"WAITING","state_text":"Csomagolás alatt...",
                        "photo":photo,"start_loc":start,"end_loc":end,
                        "eta_time":datetime.now()+timedelta(minutes=5),
                        "payment_method":None,"confirm_requested":False,
                        "confirmed":False,"signature":None,"accepted_at":None
                    }
                    send_msg(target, f"😺 {current_user.capitalize()} küldött neked egy ajánlatot! • {oid} • {item.strip()} • {price+990:,} Cam","info")
                    st.markdown("<script>fullAlert('send');</script>", unsafe_allow_html=True)
                    st.success(f"🐾 Elküldve! Order: {oid}")
                    st.rerun()

        with col_prev:
            p = st.session_state.get("send_price",1000)
            st.markdown(f"""
            <div class="rev-card">
                <div class="rev-label">Összesítő</div>
                <div class="tx-row"><span style="color:#aaa">Termék</span><span style="font-weight:600">{p:,} Cam</span></div>
                <div class="tx-row"><span style="color:#aaa">Szállítás</span><span style="font-weight:600">990 Cam</span></div>
                <div style="display:flex;justify-content:space-between;padding:14px 0 0;">
                    <span style="color:white;font-weight:800;font-size:16px;">ÖSSZESEN</span>
                    <span class="pos" style="font-size:20px;">{p+990:,} Cam</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# TAB 2 – BEJÖVŐ & AKTÍV
# ════════════════════════════════════════════
with menu[1]:
    reqs = {tid:t for tid,t in global_data["active_trades"].items()
            if t["receiver"]==current_user and t["status"]=="WAITING"}
    if reqs: st.markdown("### 📩 Bejövő ajánlatok")

    for tid,t in reqs.items():
        with st.container(border=True):
            oid=t.get("order_id",tid); cost=t["price"]+990
            ia,ib=st.columns([3,1])
            with ia:
                st.markdown(f"""<div>
                  <span style='font-size:17px;font-weight:700;'>📦 {t['item']}</span>
                  <span class='pill pill-waiting' style='margin-left:8px;'>VÁRAKOZIK</span><br>
                  <span style='color:#888;font-size:12px;'>Feladó: {t['sender'].capitalize()} • {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>Order: {oid}</span>
                </div>""", unsafe_allow_html=True)
            with ib:
                st.markdown(f"<div style='text-align:right;font-size:18px;font-weight:800;color:#f5576c;'>{cost:,} Cam</div>", unsafe_allow_html=True)

            st.markdown("#### 💳 Fizetési mód")
            pc1,pc2 = st.columns(2)
            with pc1:
                if st.button("💳 Kártyával", key=f"card_{tid}", use_container_width=True):
                    if global_data["balances"].get(current_user,0)>=cost:
                        global_data["balances"][current_user]-=cost
                        global_data["balances"][t["sender"]]=global_data["balances"].get(t["sender"],0)+t["price"]+495
                        t["status"]="ACCEPTED"; t["payment_method"]="💳 Kártya"
                        t["accepted_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        send_msg(t["sender"],f"😸 {current_user.capitalize()} elfogadta! • {oid} • Kártyával • {cost:,} Cam","info")
                        send_msg(current_user,f"✅ {oid} • Kártyás fizetés sikeres! {cost:,} Cam levonva.","info")
                        st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                        st.rerun()
                    else: st.error("Nincs elég egyenleg! 😿")
            with pc2:
                if st.button("📲 NFC fizetés", key=f"nfc_{tid}", use_container_width=True):
                    st.session_state[f"nfc_open_{tid}"]=True

            if st.session_state.get(f"nfc_open_{tid}"):
                nfc_id=f"pay_{tid}"
                confirm_btn_id=f"nfc-confirm-{nfc_id}"
                st.markdown(f"""
                <div class="payment-modal">
                    <div class="rev-label" style="color:#a8edea;">NFC ÉRINTÉSES FIZETÉS</div>
                    <div class="nfc-pulse">📲</div>
                    <div style="color:white;font-size:17px;font-weight:700;margin:8px 0;">Érintéses fizetés</div>
                    <div style="color:#888;font-size:13px;">Összeg: <b style="color:#43e97b;">{cost:,} Cam</b></div>
                    <div style="color:#555;font-size:11px;margin-top:4px;">Order: {oid}</div>
                    <div id="nfc-status-{nfc_id}" style="font-size:13px;margin-top:14px;color:#667eea;">Válassz módot ↓</div>
                </div>
                <div style="background:rgba(255,193,7,0.08);border:1px solid rgba(255,193,7,0.2);border-radius:10px;padding:10px;font-size:12px;color:#aaa;margin:8px 0;">
                    ✏️ <b>Postás:</b> NFC Írás → tartsd a másik telefont<br>
                    📡 <b>Fizető:</b> NFC Olvasás → érintsd a terminált<br>
                    ✅ <b>Nincs NFC?</b> Kézi Jóváhagyás gomb
                </div>""", unsafe_allow_html=True)

                na,nb,nc,nd=st.columns(4)
                with na:
                    if st.button("✏️ Írás", key=f"nfc_write_{tid}", use_container_width=True):
                        st.markdown(f"<script>startNFCWrite({cost},'{oid}','{nfc_id}');</script>", unsafe_allow_html=True)
                with nb:
                    if st.button("📡 Olvasás", key=f"nfc_read_{tid}", use_container_width=True):
                        st.markdown(f"<script>startNFCRead('{nfc_id}','{confirm_btn_id}');</script>", unsafe_allow_html=True)
                with nc:
                    # This button is also auto-clicked by JS on NFC tap
                    btn_clicked = st.button("✅ Jóváhagyás", key=f"nfc_ok_{tid}", use_container_width=True)
                    st.markdown(f'<span id="{confirm_btn_id}" style="display:none"></span>', unsafe_allow_html=True)
                    if btn_clicked:
                        if global_data["balances"].get(current_user,0)>=cost:
                            global_data["balances"][current_user]-=cost
                            global_data["balances"][t["sender"]]=global_data["balances"].get(t["sender"],0)+t["price"]+495
                            t["status"]="ACCEPTED"; t["payment_method"]="📲 NFC"
                            t["accepted_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.pop(f"nfc_open_{tid}",None)
                            send_msg(t["sender"],f"😸 {current_user.capitalize()} NFC-vel fizetett! • {oid} • {cost:,} Cam","info")
                            send_msg(current_user,f"✅ {oid} • NFC fizetés sikeres! 📲","info")
                            st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                            st.rerun()
                        else: st.error("Nincs elég egyenleg! 😿")
                with nd:
                    if st.button("❌ Mégse", key=f"nfc_cancel_{tid}", use_container_width=True):
                        st.markdown(f"<script>stopNFC('{nfc_id}');</script>", unsafe_allow_html=True)
                        st.session_state.pop(f"nfc_open_{tid}",None); st.rerun()

    st.divider()
    active={tid:t for tid,t in global_data["active_trades"].items() if t["status"]=="ACCEPTED"}
    if active: st.markdown("### 🚚 Aktív szállítások")

    for tid,t in active.items():
        with st.container(border=True):
            oid=t.get("order_id",tid)
            rem=(t["eta_time"]-datetime.now()).total_seconds()
            hc1,hc2=st.columns([3,1])
            with hc1:
                st.markdown(f"""<div>
                  <span style='font-size:15px;font-weight:700;'>🚚 {t['item']}</span>
                  <span class='pill pill-accepted' style='margin-left:8px;'>AKTÍV</span><br>
                  <span style='color:#888;font-size:12px;'>{oid} • {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>{t['sender'].capitalize()} → {t['receiver'].capitalize()} • {t.get('payment_method','–')}</span>
                </div>""", unsafe_allow_html=True)
            with hc2:
                if rem>0:
                    st.markdown(f"<div class='eta-timer'>⏳ {int(rem//60):02d}:{int(rem%60):02d}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='eta-soon'>⏰ Hamarosan megérkezik!</div>", unsafe_allow_html=True)

            ctrl_col,info_col=st.columns(2)
            with ctrl_col:
                if t["sender"]==current_user:
                    STATES=["Csomagolás alatt...","Úton a reptérre","A levegőben ✈️","Kiszállítás alatt","A kapu előtt 🚪"]
                    cur_idx=STATES.index(t["state_text"]) if t["state_text"] in STATES else 0
                    new_s=st.selectbox("📍 Státusz",STATES,index=cur_idx,key=f"s_{tid}")
                    if new_s!=t["state_text"]:
                        old=t["state_text"]; t["state_text"]=new_s
                        send_msg(t["receiver"],f"🐾 {oid} • Státusz: {new_s} (volt: {old})","info")
                        st.markdown("<script>fullAlert('send');</script>", unsafe_allow_html=True)
                        st.rerun()

                    # ETA — no expander to avoid arrow bug
                    st.markdown("**⏱️ ETA módosítás**")
                    ec1,ec2=st.columns([3,1])
                    with ec1: new_eta=st.number_input("Perc",min_value=1,max_value=120,value=5,key=f"eta_{tid}",label_visibility="collapsed")
                    with ec2:
                        if st.button("🕐",key=f"etab_{tid}",use_container_width=True):
                            t["eta_time"]=datetime.now()+timedelta(minutes=new_eta)
                            global_data["eta_notified"].discard(tid)
                            send_msg(t["receiver"],f"⏱️ {oid} • ETA frissítve: {new_eta} perc!","info")
                            st.rerun()

                    if not t.get("confirm_requested") and not t.get("confirmed"):
                        if st.button("📋 Visszaigazolás kérése",key=f"creq_{tid}",use_container_width=True):
                            t["confirm_requested"]=True
                            send_msg(t["receiver"],f"✍️ {oid} • {t['sender'].capitalize()} kéri az aláírásodat! 🐾","alert")
                            st.markdown("<script>fullAlert('alert');</script>", unsafe_allow_html=True)
                            st.rerun()
                    elif t.get("confirm_requested") and not t.get("confirmed"):
                        st.info("⏳ Várakozás az aláírásra...")
                    elif t.get("confirmed"):
                        st.success(f"✅ Aláírva: *{t.get('signature','')}*")
                else:
                    st.info(f"📍 {t['state_text']}")

            with info_col:
                if t["receiver"]==current_user and t.get("confirm_requested") and not t.get("confirmed"):
                    st.markdown(f"""
                    <div class="paper-sign">
                      <div style="text-align:center;font-size:15px;font-weight:700;margin-bottom:12px;position:relative;z-index:1;">
                          🐾 ÁTVÉTELI ELISMERVÉNY
                      </div>
                      <div style="position:relative;z-index:1;line-height:1.9;font-size:13px;">
                          Alulírott <b>{current_user.capitalize()}</b> igazolom, hogy a(z)
                          <b>{t['item']}</b> nevű küldeményt ({oid}) a mai napon
                          ({datetime.now().strftime('%Y.%m.%d')}) átvettem.
                      </div>
                    </div>""", unsafe_allow_html=True)
                    sig=st.text_input("✍️ Írd alá:",key=f"sig_{tid}",placeholder="pl. Peti...")
                    if st.button("🖊️ ALÁÍR & VISSZAIGAZOL",key=f"sign_{tid}",use_container_width=True):
                        if sig.strip():
                            t.update({"confirmed":True,"signature":sig.strip(),"status":"DONE","done_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                            send_msg(t["sender"],f"😺 {oid} • {current_user.capitalize()} aláírta! ✍️ {sig} 🎉","info")
                            send_msg(current_user,f"✅ {oid} • Ügylet lezárva! 🐾","info")
                            st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                            st.rerun()
                        else: st.warning("Írd be a neved! 😾")
                pdf=create_pdf(t,tid)
                st.download_button("📥 SZÁMLA PDF",data=pdf,file_name=f"szamla_{oid}.pdf",key=f"pdf_{tid}",use_container_width=True)

# ════════════════════════════════════════════
# TAB 3 – BANK
# ════════════════════════════════════════════
with menu[2]:
    bank_in=global_data["bank_sessions"].get(current_user,False)
    if not bank_in:
        st.markdown("### 🏦 Tréd Bank")
        has_pin=current_user in global_data["bank_pins"]
        _,cc,_=st.columns([1,2,1])
        with cc:
            st.markdown(f"""
            <div class="rev-card" style="text-align:center;">
                <div style="font-size:52px;margin-bottom:8px;">🔐</div>
                <div class="rev-label">{"BANK PIN BELÉPÉS" if has_pin else "PIN BEÁLLÍTÁSA"}</div>
            </div>""", unsafe_allow_html=True)
            if not has_pin:
                p1=st.text_input("Új PIN (4 szám)",type="password",max_chars=4,key="bp1")
                p2=st.text_input("PIN megerősítése",type="password",max_chars=4,key="bp2")
                if st.button("🔐 PIN beállítása",use_container_width=True):
                    if len(p1)==4 and p1.isdigit() and p1==p2:
                        global_data["bank_pins"][current_user]=p1; st.success("✅ PIN beállítva!"); st.rerun()
                    else: st.error("4 számjegy kell, és egyezzen! 😾")
            else:
                entered=st.text_input("PIN",type="password",max_chars=4,key="blp",label_visibility="collapsed",placeholder="••••")
                b1,b2=st.columns(2)
                with b1:
                    if st.button("🏦 Belépés",use_container_width=True):
                        if entered==global_data["bank_pins"].get(current_user):
                            global_data["bank_sessions"][current_user]=True; st.rerun()
                        else: st.error("Hibás PIN! 😿")
                with b2:
                    if st.button("PIN törlése",use_container_width=True):
                        global_data["bank_pins"].pop(current_user,None); st.rerun()
    else:
        bal=global_data["balances"].get(current_user,0)
        bh1,bh2=st.columns([5,1])
        with bh1: st.markdown("### 🏦 Tréd Bank")
        with bh2:
            if st.button("🔒 Zár",use_container_width=True):
                global_data["bank_sessions"][current_user]=False; st.rerun()

        card_num=f"{abs(hash(current_user))%9000+1000}"
        st.markdown(f"""
        <div class="rev-card" style="min-height:200px;position:relative;overflow:hidden;">
            <div style="position:absolute;right:-30px;top:-30px;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,0.04);"></div>
            <div class="rev-label">Tréd Premium Számla</div>
            <div class="rev-balance" style="font-size:46px;margin:14px 0 8px;">{bal:,} Cam</div>
            <div style="display:flex;gap:40px;margin-top:8px;">
                <div><div class="rev-label">Tulajdonos</div><div style="color:white;font-weight:600;margin-top:3px;">{current_user.capitalize()}</div></div>
                <div><div class="rev-label">Típus</div><div style="color:#a8edea;font-weight:600;margin-top:3px;">Premium 🐾</div></div>
            </div>
            <div style="margin-top:18px;font-size:20px;letter-spacing:5px;color:rgba(255,255,255,0.3);">•••• •••• •••• {card_num}</div>
        </div>""", unsafe_allow_html=True)

        bt=st.tabs(["📲 NFC Terminál","💳 Kártya küldés","📊 Kimutatás"])

        with bt[0]:
            st.markdown("#### 📲 NFC Terminál")
            st.markdown("""
            <div style="background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);border-radius:12px;padding:14px;font-size:13px;color:#aaa;margin-bottom:16px;">
                <b>Postás (terminál):</b> Add meg összeget → <b>NFC Írás</b> → tartsd a másik telefont<br>
                <b>Fizető:</b> <b>NFC Olvasás</b> → érintsd a terminál telefonját → automatikus jóváhagyás<br><br>
                ✅ <b>A vnd.android hiba javítva</b> — plain TEXT rekordot írunk, nem URL-t,
                ezért Android nem nyitja meg semmilyen alkalmazásban.
            </div>""", unsafe_allow_html=True)
            tc1,tc2=st.columns(2)
            nfc_amt=tc1.number_input("Összeg (Cam)",min_value=1,value=500,key="nfc_bank_amount")
            nfc_to=tc2.selectbox("Fizető fél",[u for u in USERS if u!=current_user],key="nfc_bank_to")
            nfc_oid_in=st.text_input("Order ID (opcionális)",placeholder="ORD-...",key="nfc_bank_oid")
            nfc_ref=nfc_oid_in.strip() if nfc_oid_in.strip() else "BANK"
            nb_id=f"bank_{current_user}"
            nb_confirm_id=f"nfc-confirm-bank-{current_user}"

            st.markdown(f"""
            <div class="payment-modal">
                <div class="nfc-pulse">📲</div>
                <div style="color:white;font-size:16px;font-weight:700;">NFC Terminál</div>
                <div style="color:#888;font-size:13px;margin:8px 0;">
                    Összeg: <b style="color:#43e97b;">{nfc_amt:,} Cam</b> • Fizető: <b style="color:#a8edea;">{nfc_to.capitalize()}</b>
                </div>
                <div id="nfc-status-{nb_id}" style="color:#667eea;font-size:13px;margin-top:10px;">Várakozás...</div>
            </div>""", unsafe_allow_html=True)

            bn1,bn2,bn3,bn4=st.columns(4)
            with bn1:
                if st.button("✏️ NFC Írás",use_container_width=True,key="nfc_write_bank"):
                    st.markdown(f"<script>startNFCWrite({nfc_amt},'{nfc_ref}','{nb_id}');</script>", unsafe_allow_html=True)
            with bn2:
                if st.button("📡 NFC Olvasás",use_container_width=True,key="nfc_read_bank"):
                    st.markdown(f"<script>startNFCRead('{nb_id}','{nb_confirm_id}');</script>", unsafe_allow_html=True)
            with bn3:
                bank_confirm=st.button("✅ Jóváhagyás",use_container_width=True,key="nfc_bank_ok")
                st.markdown(f'<span id="{nb_confirm_id}" style="display:none"></span>', unsafe_allow_html=True)
                if bank_confirm:
                    if global_data["balances"].get(nfc_to,0)>=nfc_amt:
                        global_data["balances"][nfc_to]-=nfc_amt
                        global_data["balances"][current_user]=global_data["balances"].get(current_user,0)+nfc_amt
                        send_msg(nfc_to,f"📲 NFC: {nfc_amt:,} Cam levonva → {current_user.capitalize()}","info")
                        send_msg(current_user,f"✅ NFC beérkezett: {nfc_amt:,} Cam ← {nfc_to.capitalize()}","info")
                        st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                        st.success(f"✅ {nfc_amt:,} Cam beérkezett!")
                        st.rerun()
                    else: st.error("A fizető félnek nincs elég egyenlege! 😿")
            with bn4:
                if st.button("⏹️ Stop",use_container_width=True,key="nfc_stop_bank"):
                    st.markdown(f"<script>stopNFC('{nb_id}');</script>", unsafe_allow_html=True)

        with bt[1]:
            st.markdown("#### 💳 Kártya küldés")
            ka,kb=st.columns(2)
            k_to=ka.selectbox("Kinek",[u for u in USERS if u!=current_user],key="k_to")
            k_amt=kb.number_input("Összeg (Cam)",min_value=1,value=200,key="k_amt")
            k_note=st.text_input("Megjegyzés (opcionális)",key="k_note")
            if st.button("💳 Küldés",use_container_width=True,key="k_send"):
                if global_data["balances"].get(current_user,0)>=k_amt:
                    global_data["balances"][current_user]-=k_amt
                    global_data["balances"][k_to]=global_data["balances"].get(k_to,0)+k_amt
                    note_txt=f" • {k_note}" if k_note else ""
                    send_msg(k_to,f"💳 {current_user.capitalize()} küldött {k_amt:,} Cam-et{note_txt}","info")
                    send_msg(current_user,f"✅ {k_amt:,} Cam elküldve → {k_to.capitalize()}{note_txt}","info")
                    st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                    st.success(f"✅ Elküldve! {k_amt:,} Cam → {k_to.capitalize()}")
                    st.rerun()
                else: st.error("Nincs elég egyenleg! 😿")

        with bt[2]:
            st.markdown("#### 📊 Saját kimutatás")
            my_trades=[t for t in global_data["active_trades"].values() if current_user in (t["sender"],t["receiver"])]
            if not my_trades:
                st.info("Még nincs tranzakció.")
            else:
                rows=[]
                for t in my_trades:
                    is_recv=t["receiver"]==current_user
                    amt=-(t["price"]+990) if is_recv else (t["price"]+495)
                    rows.append({"Order":t.get("order_id","?"),"Termék":t["item"],
                        "Partner":t["sender"].capitalize() if is_recv else t["receiver"].capitalize(),
                        "Összeg":f"{'+' if amt>0 else ''}{amt:,} Cam","Státusz":t["status"],
                        "Fizetés":t.get("payment_method","–")})
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ════════════════════════════════════════════
# TAB 4 – HISTORY
# ════════════════════════════════════════════
with menu[3]:
    st.markdown("### 📜 Lezárt ügyletek")
    done=[t for t in global_data["active_trades"].values() if t["status"]=="DONE"]
    if not done:
        st.info("Még nincs lezárt ügylet. 😴")
    else:
        for t in reversed(done):
            oid=t.get("order_id","?")
            with st.container(border=True):
                hh1,hh2=st.columns([4,1])
                with hh1:
                    sig_html=f"<br><span style='color:#888;font-size:12px;'>✍️ {t['signature']}</span>" if t.get("signature") else ""
                    st.markdown(f"""<div>
                      <span style='font-weight:700;'>✅ {t['item']}</span>
                      <span class='pill pill-done' style='margin-left:8px;'>LEZÁRVA</span><br>
                      <span style='color:#888;font-size:12px;'>{oid} • {t['sender'].capitalize()} → {t['receiver'].capitalize()}</span><br>
                      <span style='color:#888;font-size:12px;'>{t['start_loc']} → {t['end_loc']} • {t.get('payment_method','–')}</span>
                      {sig_html}
                    </div>""", unsafe_allow_html=True)
                with hh2:
                    st.markdown(f"<div style='text-align:right;color:#43e97b;font-weight:800;font-size:18px;'>{t['price']+990:,} Cam</div>", unsafe_allow_html=True)
                pdf=create_pdf(t,oid)
                st.download_button("📥 Számla PDF",data=pdf,file_name=f"szamla_{oid}.pdf",key=f"hist_{oid}_{id(t)}",use_container_width=True)

time.sleep(3)
st.rerun()
