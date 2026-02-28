import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
BASE = "https://suki-kira.com"
VOTE_URL = BASE + "/people/vote/DJ%20SHIGE"
RESULT_URL = BASE + "/people/result/DJ%20SHIGE"

session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

sent = set()

while True:
    try:
        print("requesting vote page...", flush=True)
        session.get(VOTE_URL, headers=headers)

        print("sending vote...", flush=True)
        session.post(VOTE_URL, headers=headers, data={"vote": "dislike"})

        print("getting result page...", flush=True)
        r = session.get(RESULT_URL, headers=headers)
        print("final url:", r.url, flush=True)

        soup = BeautifulSoup(r.text, "html.parser")
        comments = soup.select(".comment")

        print("comment count:", len(comments), flush=True)

        for c in comments:
            text = c.get_text(strip=True)
            if text not in sent:
                requests.post(WEBHOOK_URL, json={"content": text})
                sent.add(text)

    except Exception as e:
        print("error:", e)

    time.sleep(60)
