import os
import time
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

RESULT_URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

while True:
    try:
        print("fetching page...", flush=True)

        res = requests.get(RESULT_URL, headers={
            "User-Agent": "Mozilla/5.0"
        })

        print("status:", res.status_code, flush=True)

        print(res.text[:2000], flush=True)  # ← ここ追加（最初の2000文字）

        break  # 1回で止める

    except Exception as e:
        print("error:", e, flush=True)

    time.sleep(30)
