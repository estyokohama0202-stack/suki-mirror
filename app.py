import os
import time
import requests

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

seen_comments = set()


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
            videos.append({
                "id": item["snippet"]["resourceId"]["videoId"],
                "title": item["snippet"]["title"]
            })

            if len(videos) >= 100:
                break

        if "nextPageToken" in r and len(videos) < 100:
            params["pageToken"] = r["nextPageToken"]
        else:
            break

    return videos


def check_comments(videos):
    global seen_comments

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

        for item in r["items"]:
            comment_id = item["id"]

            if comment_id in seen_comments:
                continue

            snippet = item["snippet"]["topLevelComment"]["snippet"]
            author = snippet["authorDisplayName"]
            text = snippet["textDisplay"]

            payload = {
                "content": f"🎬 **{title}**\n\n👤 {author}\n💬 {text}"
            }

            requests.post(DISCORD_WEBHOOK, json=payload)

            seen_comments.add(comment_id)


def main():
    playlist_id = get_uploads_playlist()
    videos = get_latest_100_videos(playlist_id)
    check_comments(videos)


while True:
    main()
    time.sleep(60)
