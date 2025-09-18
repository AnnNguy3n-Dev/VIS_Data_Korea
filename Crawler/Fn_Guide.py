import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO


def get_data_volume(code: str):
    for _ in range(60):
        try:
            r = requests.get(f"https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?gicode=A{code}")
        except:
            time.sleep(1)
            continue

        if r.status_code == 200:
            break
        else: time.sleep(1)
    else:
        raise Exception("Timeout waiting fn_guide!!!!!!")
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    dict_data = {}
    table = soup.find("div", {"id": "svdMainGrid1"})
    dict_data["T1"] = pd.read_html(StringIO(table.prettify()))[0]
    table = soup.find("div", {"id": "svdMainGrid5"})
    dict_data["T2"] = pd.read_html(StringIO(table.prettify()))[0]

    return dict_data
