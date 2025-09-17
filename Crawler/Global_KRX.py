from Crawler.Base import Base, Chrome
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import pandas as pd
import gzip
import json
from datetime import datetime


def convert_response_to_dataframe(request):
    raw = request.response.body
    raw = gzip.decompress(raw)
    return pd.DataFrame(json.loads(raw.decode())["block1"])


def click_search_button(br: Base):
    btn_search = br.find_item(By.CLASS_NAME, "btn-board-search")
    assert btn_search.get_attribute("class") == "btn-board btn-board-search"
    btn_search.click()
    time.sleep(1)


def get_Listed_companies():
    br = Base()

    br.driver.get("https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp")
    time.sleep(60)
    last_time_update = br.find_item(By.CLASS_NAME, "func-icon-time ").text

    for exchange_button in br.driver.find_elements(By.CLASS_NAME, "schdate"):
        exchange_code = exchange_button.get_attribute("value")
        assert exchange_code in ["0", "1", "2", "6"], exchange_code
        if exchange_code not in ["1", "2", "6"]: continue

        exchange_button.click()
        time.sleep(0.5)

        click_search_button(br)

        for _ in range(60):
            new_time_update = br.find_item(By.CLASS_NAME, "func-icon-time ").text
            if new_time_update != last_time_update:
                break
            else:
                time.sleep(1)
        else:
            raise Exception("Time out waiting for KRX Listed to be created!")

        time.sleep(15)
        last_time_update = new_time_update


    list_df = []
    for exchange_code in ["1", "2", "6"]:
        if exchange_code == "1":
            exchange = "KOSPI"
        elif exchange_code == "2":
            exchange = "KOSDAQ"
        else:
            exchange = "KONEX"

        list_rq = []
        for rq in br.driver.requests:
            if rq.method == "POST" and rq.path.endswith(".jspx")\
                and rq.body.decode().startswith(f"market_gubun={exchange_code}"):
                list_rq.append(rq)

        assert len(list_rq) == 2, (len(list_rq), exchange_code)
        assert list_rq[0].body.decode().__contains__("bldcode")
        assert not list_rq[1].body.decode().__contains__("bldcode")

        df = convert_response_to_dataframe(list_rq[1])
        df["Exchange"] = exchange
        list_df.append(df)

    br.quit_crawler()
    del br
    return pd.concat(list_df, ignore_index=True)


##### Delisted
def check_Delisted_fromdate_todate(driver: Chrome, from_date, to_date):
    for rq in driver.requests:
        if rq.method == "POST":
            try: formdata = rq.body.decode()
            except: continue

            if formdata.startswith("market_gubun=0")\
                and f"fromdate={from_date}" in formdata\
                and f"todate={to_date}" in formdata:
                return convert_response_to_dataframe(rq)


def get_Delisted_companies(start_date="20000101"):
    br = Base()
    br.driver.get("https://global.krx.co.kr/contents/GLB/03/0306/0306050000/GLB0306050000.jsp")

    today = datetime.now().strftime("%Y%m%d")

    list_df = []
    while True:
        to_date = str(int(start_date[:4]) + 1) + start_date[4:]
        if to_date > today:
            to_date = today

        print(start_date, to_date)

        start_date_btn = br.find_item(By.NAME, "fromdate")
        to_date_btn = br.find_item(By.NAME, "todate")
        start_date_btn.clear()
        start_date_btn.send_keys(start_date)
        to_date_btn.clear()
        to_date_btn.send_keys(to_date)
        time.sleep(1)

        click_search_button(br)

        for _ in range(60):
            df = check_Delisted_fromdate_todate(br.driver, start_date, to_date)
            if df is None:
                time.sleep(1)
            else:
                list_df.append(df)
                break
        else:
            raise Exception("Time out waiting for KRX Delisted to be created!")
        
        start_date = to_date
        if to_date == today:
            break
    
    br.quit_crawler()
    del br
    return pd.concat(list_df, ignore_index=True).sort_values("chg_dt", ignore_index=True)
