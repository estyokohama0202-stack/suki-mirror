import os
import time
import requests

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

last_comment_id = None

def get_latest_video():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "channelId": CHANNEL_ID,
        "part": "id",
        "order": "date",
        "maxResults": 1
    }
    r = requests.get(url, params=params).json()
    return r["items"][0]["id"]["videoId"]

def check_comments():
    global last_comment_id
    video_id = get_latest_video()

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": API_KEY,
        "videoId": video_id,
        "part": "snippet",
        "maxResults": 5
    }

    r = requests.get(url, params=params).json()

    for item in r["items"]:
        comment_id = item["id"]
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        author = snippet["authorDisplayName"]
        text = snippet["textDisplay"]

        if comment_id != last_comment_id:
            payload = {"content": f"💬 {author}: {text}"}
            requests.post(DISCORD_WEBHOOK, json=payload)
            last_comment_id = comment_id

while True:
    check_comments()
    time.sleep(60)
