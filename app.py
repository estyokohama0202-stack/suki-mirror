import os
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

LAST_FILE = "last_time.txt"


# ===============================
# アップロード動画（直近100本）
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


def get_latest_100_videos(playlist_id):
    videos = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": API_KEY,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": 50
    }

    while len(videos) < 100:
        r = requests.get(url, params=params).json()

        for item in r["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]
            videos.append({"id": video_id, "title": title})

            if len(videos) >= 100:
                break

        if "nextPageToken" in r and len(videos) < 100:
            params["pageToken"] = r["nextPageToken"]
        else:
            break

    return videos


# ===============================
# 時刻保存
# ===============================
def get_last_time():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return datetime.fromisoformat(f.read().strip())
    return None


def save_last_time(dt):
    with open(LAST_FILE, "w") as f:
        f.write(dt.isoformat())


# ===============================
# コメントチェック
# ===============================
def check_comments(videos):
    last_time = get_last_time()
    newest_time = last_time

    for video in videos:
        video_id = video["id"]
        title = video["title"]

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

            requests.post(DISCORD_WEBHOOK, json=payload)

            if not newest_time or published > newest_time:
                newest_time = published

    if newest_time:
        save_last_time(newest_time)


# ===============================
# メイン
# ===============================
def main():
    playlist_id = get_uploads_playlist()
    videos = get_latest_100_videos(playlist_id)

    if not os.path.exists(LAST_FILE):
        save_last_time(datetime.now(timezone.utc))
        print("Initialized timestamp")
        return

    check_comments(videos)


while True:
    main()
    time.sleep(60)
