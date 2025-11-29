import requests
import time
from bs4 import BeautifulSoup

url = "https://www.amazon.in/gp/browse.html?node=1805560031&ref_=abn_hmenu_in_ab_nav_mobiles_telephones_accessories_smart_phones_0_2_3_3"

#https://unagi.amazon.in/1/events/com.amazon.csm.csa.prod
# Add browser-like headers
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

par=requests.get(url,headers=headers)
print(par.status_code)
soup=BeautifulSoup(par.text,"html.parser")
print(soup.prettify())
fil=soup.find_all("div",class_='a-section octopus-pc-card octopus-best-seller-card')
print("filtered is :")
print("")
time.sleep(5)
print(fil[0].prettify())