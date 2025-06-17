# instagram/instagram_poster.py
import requests
import time
from api_keys import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID

def post_carousel(image_urls, caption):
    print("📤 Carousel post hazırlanıyor...")
    creation_ids = []

    for url in image_urls:
        print(f"📤 Media yükleniyor: {url}")
        res = requests.post(
            f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media",
            data={
                "image_url": url,
                "is_carousel_item": True,
                "access_token": INSTAGRAM_ACCESS_TOKEN
            }
        )
        data = res.json()
        if "id" in data:
            creation_ids.append(data["id"])
        else:
            print(f"❌ Yükleme hatası: {data}")
        time.sleep(2)

    if not creation_ids:
        print("❌ Hiçbir görsel yüklenemedi!")
        return

    # Carousel Container
    res = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(creation_ids),
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    container_data = res.json()
    if "id" not in container_data:
        print(f"❌ Carousel container hatası: {container_data}")
        return

    # Yayınla
    time.sleep(2)
    publish_res = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media_publish",
        data={
            "creation_id": container_data["id"],
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    if publish_res.status_code == 200:
        print("🎉 Carousel başarıyla yayınlandı!")
    else:
        print(f"❌ Yayın hatası: {publish_res.text}")
