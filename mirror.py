import requests
import time

API_KEY = "ここにあなたのYouTube APIキー"
CHANNEL_ID = "UCm5zSNcVsNzMPB8aeIakpHA"
WEBHOOK_URL = "ここにDiscordWebhookURL"

sent_comments = set()

def get_video_ids():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "channelId": CHANNEL_ID,
        "part": "id",
        "order": "date",
        "maxResults": 50,
        "type": "video"
    }
    r = requests.get(url, params=params).json()
    return [item["id"]["videoId"] for item in r.get("items", [])]

def get_comments(video_id):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": API_KEY,
        "videoId": video_id,
        "part": "snippet",
        "order": "time",
        "maxResults": 20
    }
    r = requests.get(url, params=params).json()
    return r.get("items", [])

while True:
    try:
        videos = get_video_ids()

        for vid in videos:
            comments = get_comments(vid)

            for c in comments:
                snippet = c["snippet"]["topLevelComment"]["snippet"]
                text = snippet["textDisplay"]
                author = snippet["authorDisplayName"]
                published = snippet["publishedAt"]

                unique_id = vid + published

                if unique_id not in sent_comments:
                    message = f"🎥 https://youtu.be/{vid}\n**{author}**:\n{text}"
                    requests.post(WEBHOOK_URL, json={"content": message})
                    sent_comments.add(unique_id)

        print("checked")

    except Exception as e:
        print("error:", e)

    time.sleep(60)
