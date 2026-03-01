import requests
import time
import os
import json
from datetime import datetime

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

TIME_FILE = "last_comment_time.json"


# ===============================
# 最終時間読み込み
# ===============================
def load_last_time():
    if not os.path.exists(TIME_FILE):
        return None
    with open(TIME_FILE, "r") as f:
        return datetime.fromisoformat(json.load(f))


# ===============================
# 最終時間保存
# ===============================
def save_last_time(dt):
    with open(TIME_FILE, "w") as f:
        json.dump(dt.isoformat(), f)


# ===============================
# Uploadsプレイリスト取得
# ===============================
def get_uploads_playlist():
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "key": API_KEY,
        "id": CHANNEL_ID,
        "part": "contentDetails"
    }

    r = requests.get(url, params=params).json()
    return r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


# ===============================
# 直近30動画取得（クォータ節約）
# ===============================
def get_latest_30_videos(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"

    params = {
        "key": API_KEY,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": 30
    }

    r = requests.get(url, params=params).json()

    videos = []
    if "items" not in r:
        print("PLAYLIST ERROR:", r, flush=True)
        return videos

    for item in r["items"]:
        videos.append({
            "id": item["snippet"]["resourceId"]["videoId"],
            "title": item["snippet"]["title"]
        })

    return videos


# ===============================
# コメントチェック
# ===============================
def check_comments(videos):

    last_time = load_last_time()
    newest_time = last_time

    print("Checking comments...", flush=True)

    for video in videos:

        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": API_KEY,
            "videoId": video["id"],
            "part": "snippet",
            "maxResults": 5,
            "order": "time"
        }

        response = requests.get(url, params=params)
        r = response.json()

        if response.status_code != 200:
            print("COMMENT API ERROR:", r, flush=True)
            continue

        if "items" not in r:
            continue

        for item in reversed(r["items"]):

            snippet = item["snippet"]["topLevelComment"]["snippet"]
            published = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

            if last_time and published <= last_time:
                continue

            payload = {
                "content": f"🎬 **{video['title']}**\n\n"
                           f"https://www.youtube.com/watch?v={video['id']}\n\n"
                           f"👤 {snippet['authorDisplayName']}\n"
                           f"💬 {snippet['textDisplay']}"
            }

            print("Sending to Discord...", flush=True)
            discord_response = requests.post(DISCORD_WEBHOOK, json=payload)

            print("Discord status:", discord_response.status_code, flush=True)

            if not newest_time or published > newest_time:
                newest_time = published

    if newest_time:
        save_last_time(newest_time)


# ===============================
# メイン
# ===============================
def main():
    print("==== Running main ====", flush=True)

    playlist_id = get_uploads_playlist()
    videos = get_latest_30_videos(playlist_id)

    print("Videos fetched:", len(videos), flush=True)

    check_comments(videos)


print("==== Bot Starting ====", flush=True)

while True:
    try:
        main()
    except Exception as e:
        print("ERROR:", e, flush=True)

    time.sleep(600)  # ← 10分
