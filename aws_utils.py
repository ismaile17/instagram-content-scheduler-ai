# aws_utils.py
import boto3
import os
import json
from api_keys import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

BUCKET_NAME = "english.amiral"

def upload_file_to_s3(local_path, s3_path):
    try:
        s3 = boto3.client('s3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

        # İçeriğin dosya uzantısına göre ContentType belirle
        content_type = "image/jpeg" if local_path.lower().endswith(".jpg") else "application/octet-stream"

        s3.upload_file(
            Filename=local_path,
            Bucket=BUCKET_NAME,
            Key=s3_path,
            ExtraArgs={
                "ContentType": content_type,
                "ContentDisposition": "inline"
            }
        )

        url = f"https://s3.{AWS_REGION}.amazonaws.com/{BUCKET_NAME}/{s3_path}"

        print(f"☁️ Yüklendi: {url}")
        return url
    except Exception as e:
        print(f"❌ S3 yükleme hatası: Failed to upload {local_path} to {BUCKET_NAME}/{s3_path}: {e}")
        return None


def upload_images_from_folder(folder_path, s3_prefix="instagram"):
    urls = []
    # örnek: outputs/2025-04-03_abc123/final → sadece 2025-04-03_abc123'ü alalım
    unique_folder = folder_path.split(os.sep)[1]
    s3_base = f"{s3_prefix}/{unique_folder}"

    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".jpg")])
    for file_name in files:
        local_path = os.path.join(folder_path, file_name)
        s3_path = f"{s3_base}/{file_name}"
        url = upload_file_to_s3(local_path, s3_path)
        if url:
            urls.append(url)
    return urls


def save_image_urls(folder_path, urls):
    output_path = os.path.join(folder_path, "image_urls.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
