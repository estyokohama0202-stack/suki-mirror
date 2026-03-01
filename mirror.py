import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

VOTE_URL = "https://suki-kira.com/people/vote/DJ%20SHIGE"
RESULT_URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

sent = set()

headers = {
    "User-Agent": "Mozilla/5.0"
}

while True:
    try:
        session = requests.Session()
        session.headers.update(headers)

        print("requesting vote page...", flush=True)
        session.get(VOTE_URL, timeout=10)

        print("sending vote...", flush=True)
        session.post(VOTE_URL, data={"vote": "like"}, timeout=10)

        print("getting result page...", flush=True)
        r = session.get(RESULT_URL, timeout=10)

        print("final url:", r.url, flush=True)

        soup = BeautifulSoup(r.text, "html.parser")

        # ★ ここを修正
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
