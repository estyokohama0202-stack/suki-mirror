import os
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

LAST_FILE = "last_time.txt"


def get_uploads_playlist():
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "key": API_KEY,
        "id": CHANNEL_ID,
        "part": "contentDetails"
    }
    r = requests.get(url, params=params).json()
    return r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_latest_100_video_ids(playlist_id):
    video_ids = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": API_KEY,
        "playlistId": playlist_id,
        "part": "snippet",
        "maxResults": 50
    }

    while len(video_ids) < 100:
        r = requests.get(url, params=params).json()

        for item in r["items"]:
            video_ids.append(item["snippet"]["resourceId"]["videoId"])
            if len(video_ids) >= 100:
                break

        if "nextPageToken" in r and len(video_ids) < 100:
            params["pageToken"] = r["nextPageToken"]
        else:
            break

    return video_ids


def get_last_time():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return datetime.fromisoformat(f.read().strip())
    return None


def save_last_time(dt):
    with open(LAST_FILE, "w") as f:
        f.write(dt.isoformat())


def check_comments(video_ids):
    last_time = get_last_time()
    newest_time = last_time

    for video_id in video_ids:
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
                "content": f"🔗 {video_url}\n💬 {author}: {text}"
            }

            requests.post(DISCORD_WEBHOOK, json=payload)

            if not newest_time or published > newest_time:
                newest_time = published

    if newest_time:
        save_last_time(newest_time)


def main():
    playlist_id = get_uploads_playlist()
    video_ids = get_latest_100_video_ids(playlist_id)

    if not os.path.exists(LAST_FILE):
        save_last_time(datetime.now(timezone.utc))
        print("Initialized timestamp")
        return

    check_comments(video_ids)


while True:
    main()
    time.sleep(60)
