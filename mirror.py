import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

VOTE_URL = "https://suki-kira.com/people/vote/DJ%20SHIGE"
RESULT_URL = "https://suki-kira.com/people/result/DJ%20SHIGE"

sent = set()

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

while True:
    try:
        print("opening vote page...", flush=True)
        driver.get(VOTE_URL)

        time.sleep(3)

        print("clicking vote button...", flush=True)
        vote_button = driver.find_element(By.CLASS_NAME, "vote-like")
        vote_button.click()

        time.sleep(5)

        print("getting result page...", flush=True)
        driver.get(RESULT_URL)

        time.sleep(5)

        comments = driver.find_elements(By.CLASS_NAME, "comment-container")

        print("comment count:", len(comments), flush=True)

        for c in comments:
            text = c.text.strip()

            if text and text not in sent:
                requests.post(WEBHOOK_URL, json={"content": text})
                sent.add(text)

        print("checked...", flush=True)

    except Exception as e:
        print("error:", e, flush=True)

    time.sleep(30)
