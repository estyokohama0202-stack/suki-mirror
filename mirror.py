import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

sent = set()

while True:
    try:
        r = requests.get(URL)
        soup = BeautifulSoup(r.text, "html.parser")

        comments = soup.select(".comment")

        for c in comments:
            text = c.get_text(strip=True)

            if text and text not in sent:
                requests.post(WEBHOOK_URL, json={"content": text})
                sent.add(text)

        print("checked...")
        time.sleep(30)  # 5分

    except Exception as e:
        print("error:", e)
        time.sleep(60)
