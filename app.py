import requests
import time
import os
import json
from datetime import datetime

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

SENT_FILE = "sent_comments.json"


# ===============================
# 送信済みコメントID保存
# ===============================
def load_sent_ids():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r") as f:
        return set(json.load(f))


def save_sent_ids(ids):
    with open(SENT_FILE, "w") as f:
        json.dump(list(ids), f)


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
# 直近100動画取得
# ===============================
def get_latest_100_videos(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"

    params = {
        "key": API_KEY,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": 50
    }

    videos = []
    while len(videos) < 100:
        r = requests.get(url, params=params).json()

        for item in r["items"]:
            videos.append({
                "id": item["snippet"]["resourceId"]["videoId"],
                "title": item["snippet"]["title"]
            })

        if "nextPageToken" not in r:
            break

        params["pageToken"] = r["nextPageToken"]

    return videos[:100]


# ===============================
# 初回起動時の初期化
# ===============================
def initialize_if_needed(videos):
    sent_ids = load_sent_ids()
    if sent_ids:
        return

    print("Initializing comment IDs...", flush=True)

    for video in videos:
        video_id = video["id"]

        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": API_KEY,
            "videoId": video_id,
            "part": "snippet",
            "maxResults": 3,
            "order": "time"
        }

        r = requests.get(url, params=params).json()

        if "items" not in r:
            continue

        for item in r["items"]:
            sent_ids.add(item["id"])

    save_sent_ids(sent_ids)
    print("Initialization complete", flush=True)


# ===============================
# コメントチェック
# ===============================
def check_comments(videos):

    print("Checking videos:", len(videos), flush=True)

    sent_ids = load_sent_ids()

    for video in videos:
        video_id = video["id"]
        title = video["title"]

        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": API_KEY,
            "videoId": video_id,
            "part": "snippet",
            "maxResults": 5,
            "order": "time"
        }

        r = requests.get(url, params=params).json()

        if "items" not in r:
            continue

        for item in reversed(r["items"]):

            comment_id = item["id"]

            if comment_id in sent_ids:
                continue

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            author = snippet["authorDisplayName"]
            text = snippet["textDisplay"]

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            payload = {
                "content": f"🎬 **{title}**\n\n🔗 {video_url}\n\n👤 {author}\n💬 {text}"
            }

            requests.post(DISCORD_WEBHOOK, json=payload)

            print("Sent new comment:", comment_id, flush=True)

            sent_ids.add(comment_id)

    save_sent_ids(sent_ids)


# ===============================
# メインループ
# ===============================
def main():
    print("==== Running main ====", flush=True)

    playlist_id = get_uploads_playlist()
    print("Playlist ID:", playlist_id, flush=True)

    videos = get_latest_100_videos(playlist_id)
    print("Videos fetched:", len(videos), flush=True)

    initialize_if_needed(videos)
    check_comments(videos)


print("==== Bot Starting ====", flush=True)

while True:
    try:
        main()
    except Exception as e:
        print("ERROR:", e, flush=True)

    time.sleep(60)
