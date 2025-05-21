import requests
import pickle

# Dicionário com os cookies que você compartilhou
cookies_dict = {
    '__utma': '241790293.938049207.1747479028.1747840173.1747849365.7',
    '__utmc': '241790293',
    '__utmz': '241790293.1747849365.7.7.utmcsr=jogar.lol|utmccn=(referral)|utmcmd=referral|utmcct=/',
    '_clck': '1235ydq%7C2%7Cfw3%7C0%7C1963',
    '_clsk': 'aml5hi%7C1747857664731%7C4%7C1%7Cb.clarity.ms%2Fcollect',
    '_dd_s': 'logs=1&id=74934538-03d2-42e0-b5da-f886b0d84e66&created=1747857411503&expire=1747858564165',
    '_ga': 'GA1.1.1367762491.1747479028',
    '_ga_TJC4TLHTVM': 'GS2.1.s1747855173$o8$g0$t1747855173$j0$l0$h0',
    'CLID': '291d79c3cfb547edbbcfe2b516ecffd9.20241205.20260521',
    'MUID': '031452393C6869B2378C47753D686822',
    'your_cookie_name': '4c9035904051f57fa16269f5bac70d81'
}

# Crie uma sessão
session = requests.Session()

# Adicione os cookies
for name, value in cookies_dict.items():
    session.cookies.set(name, value)

# Salve no formato que o seu código espera
with open("cookies.pkl", "wb") as f:
    pickle.dump(session.cookies, f)

print("✅ Cookies salvos em cookies.pkl")
