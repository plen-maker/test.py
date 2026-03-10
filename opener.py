import os

# 1. Lekérjük a felhasználó mappáját (pl. C:\Users\Valaki)
user_home = os.path.expanduser("~")

# 2. Összerakjuk a Roblox útvonalát ebből
# A Roblox általában az AppData\Local mappába települ
roblox_path = os.path.join(user_home, "AppData", "Local", "Roblox", "Versions")

# Mivel a verzió mappája (version-d599...) mindig változik, 
# megkeressük az első olyan mappát, amiben van .exe
try:
    for root, dirs, files in os.walk(roblox_path):
        if "RobloxPlayerBeta.exe" in files:
            teljes_utvonal = os.path.join(root, "RobloxPlayerBeta.exe")
            os.startfile(teljes_utvonal)
            print("Roblox elindítva!")
            break
except Exception as e:
    print(f"Nem sikerült elindítani: {e}")