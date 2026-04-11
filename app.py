import streamlit as st

st.set_page_config(page_title="Update in Progress", page_icon="⚙️")

# CSS a sallangok eltüntetéséhez
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .update-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 80vh;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    <div class="update-container">
        <h1>🛠️ AZ APP FRISSÍTÉS ALATT ÁLL</h1>
        <p>Éppen kalapáljuk a rendszert. Kérlek nézz vissza 858736875673ö567ö93563578656735698475673456346345734645634563436 perc múlva!</p>
        <img src="https://cdn2.cdnstep.com/Ml7lEe4GqrgiS74oO07o/cover.thumb256.webp">
    </div>
    """, unsafe_allow_html=True)
