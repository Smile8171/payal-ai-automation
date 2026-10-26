import os
import requests

GRAPH_API = "https://graph.facebook.com/v19.0"


def post_photo(image_path: str, caption: str):
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    url = f"{GRAPH_API}/{page_id}/photos"

    with open(image_path, "rb") as file:
        response = requests.post(
            url,
            data={"access_token": token, "published": "true", "message": caption},
            files={"source": file},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()


def post_video(video_path: str, caption: str):
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    url = f"{GRAPH_API}/{page_id}/videos"

    with open(video_path, "rb") as file:
        response = requests.post(
            url,
            data={"access_token": token, "published": "true", "description": caption},
            files={"source": file},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()


def get_comments(post_id: str):
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    url = f"{GRAPH_API}/{post_id}/comments"
    response = requests.get(
        url,
        params={"access_token": token, "fields": "id,message,from{id,name}"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def reply_to_comment(comment_id: str, message: str):
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    url = f"{GRAPH_API}/{comment_id}/replies"
    response = requests.post(
        url,
        data={"access_token": token, "message": message},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()
