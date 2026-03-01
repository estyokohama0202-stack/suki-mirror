import os
import time
import requests

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

SENT_FILE = "sent_ids.txt"


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

        if "items" not in r:
            break

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
# コメントID管理
# ===============================
def load_sent_ids():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()


def save_sent_id(comment_id):
    with open(SENT_FILE, "a") as f:
        f.write(comment_id + "\n")


# ===============================
# コメントチェック
# ===============================
def check_comments(videos):

    print("Checking videos:", len(videos))
    print("Newest video:", videos[0]["title"])
    
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

            save_sent_id(comment_id)
            sent_ids.add(comment_id)


# ===============================
# 初回起動時の初期化
# ===============================
def initialize_if_needed(videos):
    if os.path.exists(SENT_FILE):
        return

    sent_ids = set()

    for video in videos:
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": API_KEY,
            "videoId": video["id"],
            "part": "snippet",
            "maxResults": 5,
            "order": "time"
        }

        r = requests.get(url, params=params).json()
        if "items" not in r:
            continue

        for item in r["items"]:
            sent_ids.add(item["id"])

    with open(SENT_FILE, "w") as f:
        for cid in sent_ids:
            f.write(cid + "\n")

    print("Initialized comment IDs")


# ===============================
# メインループ
# ===============================
def main():
    playlist_id = get_uploads_playlist()
    videos = get_latest_100_videos(playlist_id)

    initialize_if_needed(videos)
    check_comments(videos)


while True:
    main()
    time.sleep(60)
