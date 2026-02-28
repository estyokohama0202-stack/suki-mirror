import requests
from bs4 import BeautifulSoup
import time
import os

print("STARTED", flush=True)

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

sent = set()

while True:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        
        print("requesting...", flush=True)
        r = requests.get(URL, headers=headers, timeout=10)
        
        print("final url:", r.url, flush=True)
        print("got response", flush=True)
        
        soup = BeautifulSoup(r.text, "html.parser")

        comments = soup.select(".comment")
        print("comment count:", len(comments), flush=True)
        
        for c in comments:
            text = c.get_text(strip=True)

            if text not in sent:
                requests.post(WEBHOOK_URL, json={"content": text})
                sent.add(text)

        print("checked...")

    except Exception as e:
        print("error:", e)

    time.sleep(30)
