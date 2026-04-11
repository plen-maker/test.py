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
        <p>Éppen kalapáljuk a rendszert. Kérlek nézz vissza 15 perc múlva!</p>
        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueGZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3/3o7TKMGpxxca6X3Sms/giphy.gif" width="300">
    </div>
    """, unsafe_allow_html=True)
