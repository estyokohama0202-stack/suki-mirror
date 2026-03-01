import requests
import time
import os
import json
from datetime import datetime, timezone

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

TIME_FILE = "last_comment_time.json"


# ===============================
# 最終コメント時間 読み込み
# ===============================
def load_last_time():
    if not os.path.exists(TIME_FILE):
        return None
    with open(TIME_FILE, "r") as f:
        data = json.load(f)
        return datetime.fromisoformat(data)


# ===============================
# 最終コメント時間 保存
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
# 初回起動時 初期化
# ===============================
def initialize_if_needed(videos):
    last_time = load_last_time()
    if last_time:
        return

    print("First run: Skipping old comments", flush=True)

    newest_time = None

    for video in videos:
        video_id = video["id"]

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

        for item in r["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            published = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

            if not newest_time or published > newest_time:
                newest_time = published

    if newest_time:
        save_last_time(newest_time)
        print("Initialization complete", flush=True)


# ===============================
# コメントチェック（時間管理）
# ===============================
def check_comments(videos):

    last_time = load_last_time()
    newest_time = last_time

    print("Checking comments...", flush=True)

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

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            published = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

            if last_time and published <= last_time:
                continue

            author = snippet["authorDisplayName"]
            text = snippet["textDisplay"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            payload = {
                "content": f"🎬 **{title}**\n\n🔗 {video_url}\n\n👤 {author}\n💬 {text}"
            }

            print("Sending to Discord...", flush=True)

            response = requests.post(DISCORD_WEBHOOK, json=payload)

            print("Discord status:", response.status_code, flush=True)
            print("Discord response:", response.text, flush=True)

            if not newest_time or published > newest_time:
                newest_time = published

    if newest_time:
        save_last_time(newest_time)


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
