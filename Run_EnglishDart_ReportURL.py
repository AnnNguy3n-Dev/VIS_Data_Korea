import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from io import StringIO
from Crawler import English_Dart
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import os


def process(code):
    try:
        if os.path.exists(f"TEMP/Report_URL/{code}.csv"): return

        df = English_Dart.get_df_reporturl(code)
        if df is None: pass
        else: df.to_csv(f"TEMP/Report_URL/{code}.csv", index=False)
        print("Done", code)
    except:
        print(code, "!!!!!!")
        raise


if __name__ == "__main__":
    df_Listed = pd.read_csv("TEMP/Listed_companies.csv", dtype=str)
    df_Delisted = pd.read_csv("TEMP/Delisted_companies.csv", dtype=str)

    list_code = list(np.unique(df_Listed["isu_cd"].to_list() + df_Delisted["isu_cd"].to_list()))
    print(len(list_code))

    with Pool(processes=4) as p:
        p.map(process, list_code)
