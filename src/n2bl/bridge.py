import time, json, os, io
from typing import Optional, List
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .auth import get_youtube_service
from . import logger as log

RETRYABLE_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 8

def _backoff(i):
    delay = min(60, (2 ** i))
    time.sleep(delay)

def upload_video(file_path: str, title: str, description:str="", tags:Optional[List[str]]=None,
                 categoryId:str="22", privacy:str="private", show_progress:bool=True) -> dict:
    yt = get_youtube_service()
    body = {
        "snippet": {"title": title, "description": description, "tags": tags or [], "categoryId": categoryId},
        "status": {"privacyStatus": privacy},
    }
    media = MediaFileUpload(file_path, chunksize=1024*1024*8, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    last_pct = -1
    attempt = 0
    while response is None:
        try:
            status, response = req.next_chunk()
            if status and show_progress:
                pct = int(status.progress() * 100)
                if pct != last_pct:
                    log.info(f"{os.path.basename(file_path)} {pct}%")
                    last_pct = pct
        except HttpError as e:
            if e.resp.status in RETRYABLE_STATUS and attempt < MAX_RETRIES:
                attempt += 1
                log.warn(f"Retryable error {e.resp.status}. Backing off #{attempt}")
                _backoff(attempt)
                continue
            raise
    return response

def update_metadata(video_id:str, title:Optional[str]=None, description:Optional[str]=None,
                    tags:Optional[List[str]]=None, categoryId:Optional[str]=None, privacy:Optional[str]=None):
    yt = get_youtube_service()
    # fetch existing to preserve fields
    current = yt.videos().list(part="snippet,status", id=video_id).execute()["items"][0]
    snippet = current["snippet"]
    status = current["status"]
    if title is not None: snippet["title"] = title
    if description is not None: snippet["description"] = description
    if tags is not None: snippet["tags"] = tags
    if categoryId is not None: snippet["categoryId"] = categoryId
    if privacy is not None: status["privacyStatus"] = privacy
    body = {"id": video_id, "snippet": snippet, "status": status}
    return yt.videos().update(part="snippet,status", body=body).execute()

def set_thumbnail(video_id:str, image_path:str):
    yt = get_youtube_service()
    media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=False)
    return yt.thumbnails().set(videoId=video_id, media_body=media).execute()

def list_my_channels():
    yt = get_youtube_service()
    return yt.channels().list(part="snippet,contentDetails,statistics", mine=True).execute().get("items", [])

def list_my_uploads(max_results=10):
    yt = get_youtube_service()
    channels = yt.channels().list(part="contentDetails", mine=True).execute()
    uploads_playlist_id = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_playlist_id, maxResults=max_results).execute()
    return items.get("items", [])

def get_video_details(video_id):
    yt = get_youtube_service()
    return yt.videos().list(part="snippet,contentDetails,statistics,status", id=video_id).execute().get("items", [])
