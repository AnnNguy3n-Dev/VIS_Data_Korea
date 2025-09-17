import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from io import StringIO
import os


def search_textCrpCik(code: str):
    for _ in range(60):
        try:
            r = requests.post(
                url="https://englishdart.fss.or.kr/corp/searchExistAll.ax",
                data={"textCrpNm": code}
            )
        except:
            time.sleep(1)
            continue

        if r.status_code == 200:
            return r.content.decode().strip()
        else: time.sleep(1)
    else:
        raise Exception("Timeout waiting englishdart search_textCrpCik response!")


def request_search_report(formdata):
    for _ in range(60):
        try:
            r = requests.post(
                url="https://englishdart.fss.or.kr/dsbd002/search.ax",
                data = formdata
            )
        except:
            time.sleep(1)
            continue

        if r.status_code == 200:
            return r
        else: time.sleep(1)
    else:
        raise Exception("Timeout waiting englishdart search_report response!")


def get_df_reporturl_from_response(r):
    soup = BeautifulSoup(r.content, "html.parser")
    tables = soup.find_all("table")
    assert len(tables) == 1

    df = pd.read_html(StringIO(tables[0].prettify()))[0]
    df["Report_url"] = None
    list_tr = tables[0].find("tbody").find_all("tr")
    assert len(list_tr) == df.shape[0], len(list_tr)

    for i, tr in enumerate(list_tr):
        list_td = tr.find_all("td")
        try:
            assert len(list_td) == df.shape[1] - 1
        except:
            assert len(list_td) == 1
            assert "No search result!!" in list_td[0].text
            return pd.DataFrame({"Result": ["No search result!!"]})

        list_a = list_td[3].find_all("a")
        assert len(list_a) == 1

        df.loc[i, "Report_url"] = list_a[0]["href"]

    return df


def get_df_reporturl(code, start_date="20000101"):
    textCrpCik = search_textCrpCik(code)
    if textCrpCik == "null": return None

    today = datetime.now().strftime("%Y%m%d")
    to_date = today

    formdata = {
        "currentPage": "1",
        "maxResults": "15",
        "maxLinks": "10",
        "sort": "",
        "series": "",
        "textCrpCik": textCrpCik,
        "opendartUrl": "https://engopendart.fss.or.kr",
        "textCrpNm": code,
        "startDate": start_date,
        "endDate": to_date,
        "closingAccounts": "0401",
        "taxonomy": [
            "0311,0315",
            "0312",
            "0313",
            "0314",
            "0316,0317,0318"
        ]
    }

    r = request_search_report(formdata)
    list_df = [get_df_reporturl_from_response(r)]
    if list_df[0].shape == (1,1): return list_df[0]

    soup = BeautifulSoup(r.content, "html.parser")
    list_pageSkip = soup.find_all("div", {"class": "pageSkip"})
    assert len(list_pageSkip) == 1
    list_ul = list_pageSkip[0].find_all("ul")
    assert len(list_ul) == 1
    list_pageSkip = list_ul[0].find_all("li")

    if len(list_pageSkip) == 1:
        return list_df[0]

    for li in list_pageSkip[1:]:
        formdata["currentPage"] = li.text
        r = request_search_report(formdata)
        list_df.append(get_df_reporturl_from_response(r))

    rs = pd.concat(list_df, ignore_index=True)
    assert (rs["No."] - rs.index - 1 == 0).all()
    return rs


##### Phân tích url
def openXbrlViewerNew(args):
    opendartUrl, rcpNo, stat, preview = args
    if stat == "Y":
        return opendartUrl + "/xbrl/viewer/main.do?rcpNo=" + rcpNo +"&lang=en"
    elif stat == "N":
        if preview == "Y":
            return "/dsbh002/main.do?rcpNo=" + rcpNo


def get_df_true_url(report_url_folder):
    # Đọc và ghép file
    list_df = []
    for path in os.listdir(report_url_folder):
        filepath = os.path.join(report_url_folder, path)
        df = pd.read_csv(filepath)
        if df.shape == (1,1):
            continue
        df["Code"] = path[:-4]
        list_df.append(df)

    df = pd.concat(list_df, ignore_index=True)

    # Phân loại url
    df["Check"] = None
    for i in range(len(df)):
        report_url = df.loc[i, "Report_url"]

        if report_url.startswith("javascript:openXbrlViewerNew(") \
        and report_url.endswith(");")\
        and len(report_url.split(",")) == 4:
            df.loc[i, "Check"] = 0
        elif report_url.startswith("/dsbh002/main.do?rcpNo="):
            df.loc[i, "Check"] = 1

    # True url
    df["True_url"] = None
    for i in range(len(df)):
        report_url = df.loc[i, "Report_url"]
        check = df.loc[i, "Check"]
        if check is None: continue

        if check == 1:
            df.loc[i, "True_url"] = "https://englishdart.fss.or.kr" + report_url
        elif check == 0:
            text = report_url[29:-2]
            params = text.split(",")
            for ii, p in enumerate(params):
                assert p[0] == "'" and p[-1] == "'", (report_url, p)
                params[ii] = p[1:-1]

            url = openXbrlViewerNew(params)
            if url is None:
                pass
            elif url.startswith("/"):
                df.loc[i, "True_url"] = "https://englishdart.fss.or.kr" + url
            else:
                df.loc[i, "True_url"] = url

    return df[(df["Report"].str.startswith("Annual Report")) & (~df["Report"].str.endswith("[Revised]"))].reset_index(drop=True)


##### Lấy dữ liệu của nút download
def get_download_button_onclick(url):
    for _ in range(60):
        try:
            r = requests.get(url)
        except:
            time.sleep(1)
            continue

        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            btnDown = soup.find("button", {"class": "btnDown"})
            assert btnDown.text.strip() == "Download"
            onclick = btnDown.get("onclick")
            assert onclick is not None
            return onclick
        else: time.sleep(1)
    else:
        raise Exception("Timeout waiting englishdart get_download_button response!")
