import os
import uuid
import json
from datetime import datetime

import renew_token
from gpt_utils import get_gpt_content
from image_utils import download_images_from_content_json, generate_final_images
from instagram.instagram_poster import post_carousel
from aws_utils import upload_images_from_folder, save_image_urls
from telegram_utils import send_telegram_message



def create_folder():
    today = datetime.now().strftime('%Y-%m-%d')
    unique_id = str(uuid.uuid4())[:8]
    folder = os.path.join("outputs", f"{today}_{unique_id}")
    os.makedirs(folder, exist_ok=True)
    return folder

def save_to_json(folder, data):
    path = os.path.join(folder, "content.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"📁 İçerik kaydedildi: {path}")

def run_once():
    print("📡 Main fonksiyonu çalışıyor...")
    data, full_prompt = get_gpt_content()
    if not data:
        print("⚠️ Veri alınamadı. İşlem iptal edildi.")
        return

    folder = create_folder()
    save_to_json(folder, data)
    
    # Gönderilen prompt'u da kaydet
    prompt_path = os.path.join(folder, "prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(full_prompt.strip())
    print(f"📝 Prompt kaydedildi: {prompt_path}")

    print("📷 Görseller indiriliyor...")
    download_images_from_content_json(folder)

    print("🖋️ Görseller yazılandırılıyor...")
    generate_final_images(folder)

    print("☁️ Görseller S3'e yükleniyor...")
    final_folder = os.path.join(folder, "final")
    image_urls = upload_images_from_folder(final_folder)
    save_image_urls(final_folder, image_urls)

    print("📤 Instagram'a gönderiliyor...")
    description = data.get("description", "İçerik açıklaması")
    hashtags = data.get("hashtags", ["#english", "#dailyword", "#vocabulary"])
    caption = f"{description}\n\n{' '.join(hashtags)}"
    post_carousel(image_urls, caption)

    print("✅ Tüm işlemler başarıyla tamamlandı!")
    
    # Telegram bildirimi
    title = data.get("title", "Başlık bulunamadı")
    send_telegram_message(
        bot_token="7564621839:AAGYsmsL4Y0w7YAo9wfc7A_l7mj_bn1rDjM",
        chat_id="2017774678",
        message=f"✅ Yeni içerik hazırlandı: {title}"
    )


if __name__ == "__main__":
    run_once()
