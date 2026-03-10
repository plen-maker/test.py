import time


leader1 = input("Who is the best leader in the world?")
print("The best leader in the world is " + leader1)
time.sleep(2)
print("Wrong as fuck! Its osama bin laden ")
time.sleep(2)
print("Answer: Shut the fuck up! Or get the fuck out! ")
time.sleep(2)
print("The first one or the second one?")
choice = input("1 or 2? ")
if choice == "1":
    print("That was right!")
elif choice == "2":
    print("That was wrong!")
    print("So osama will rizzup your brainrot dih")
    print("Answer 1 Ill still remain nonchalant Answer 2 I'll be like 'yo, that's a good point! '")
    choice = input("3 or 4? ")
    if choice == "3":
        print("Hell nah ")
    elif choice == "4":
        print("That was right!")
import ctypes, urllib.request, os

url = "https://wallpaperaccess.com/full/2022519.jpg"
kep_utvonal = os.path.join(os.getenv("TEMP"), "hatterkep.jpg")

# 1. Letöltés "böngészőnek álcázva"
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36')]
urllib.request.install_opener(opener)

try:
    urllib.request.urlretrieve(url, kep_utvonal)
    
    # 2. Beállítás háttérképnek
    ctypes.windll.user32.SystemParametersInfoW(20, 0, kep_utvonal, 3)
    print("Siker! A háttér megváltozott.")
except Exception as e:
    print(f"Hiba történt: {e}")
