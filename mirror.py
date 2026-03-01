import os
import time
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

RESULT_URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

sent = set()

while True:
    try:
        print("fetching page...", flush=True)

        res = requests.get(RESULT_URL, headers={
            "User-Agent": "Mozilla/5.0"
        })

        soup = BeautifulSoup(res.text, "html.parser")

        comments = soup.select(".comment-container")

        print("comment count:", len(comments), flush=True)

        for c in comments:
            text = c.get_text(strip=True)

            if text and text not in sent:
                requests.post(WEBHOOK_URL, json={"content": text})
                sent.add(text)

        print("checked...", flush=True)

    except Exception as e:
        print("error:", e, flush=True)

    time.sleep(30)
