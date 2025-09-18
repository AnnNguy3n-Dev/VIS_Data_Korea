import requests
import json
import time


def get_data_dividend(code):
    for _ in range(60):
        try:
            r = requests.get(
                f"https://wts-info-api.tossinvest.com/api/v1/stock-infos/dividend/A{code}/years?years=2147483647"
            )
        except:
            time.sleep(1)
            continue

        if r.status_code == 200:
            return json.loads(r.content.decode())
        else: time.sleep(1)
    else:
        raise Exception("Timeout waiting Tos_Invest!!!!!!")
