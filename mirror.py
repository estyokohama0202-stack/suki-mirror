import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
options.binary_location = "/usr/bin/chromium"

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

while True:
    try:
        print("opening vote page...", flush=True)
        driver.get(VOTE_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )

        print("searching vote button...", flush=True)

        buttons = driver.find_elements(By.TAG_NAME, "button")

        for b in buttons:
            if "好き" in b.text:
                print("clicking like button", flush=True)
                b.click()
                break

        time.sleep(3)

        print("opening result page...", flush=True)
        driver.get(RESULT_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comment-container"))
        )

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
