import os
import time
import random
import subprocess
import sys

def run_once():
    # Gerçek işlemleri yapan ana script çağrılır
    subprocess.run([sys.executable, "main_job.py"])

if __name__ == "__main__":
    while True:
        run_once()

        # ⏱️ Rastgele bekleme süresi (örnek: 30-50 dakika)
        wait_minutes = random.randint(30, 50)
        wait_seconds = wait_minutes * 60
        print(f"⏳ {wait_minutes} dakika ({wait_seconds} saniye) bekleniyor...")
        time.sleep(wait_seconds)
        
        # 🔁 Yeni döngü başında ekranı temizle
        os.system("cls")
