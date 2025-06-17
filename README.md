🧠 Instagram Auto Content Bot

🌍 English
What is This Project?
Auto Content Bot is a Python-based automation tool that generates content using AI and images from open APIs, then processes and optionally publishes it to Instagram. The tool creates a complete content cycle: text generation, image matching, composition, and output — all without manual intervention.

How It Works
A scheduled loop in main.py runs every 30–50 minutes.

Each cycle triggers main_job.py, where the real work happens.

Text is generated using OpenAI (based on prompts in the prompts/ folder).

Matching images are downloaded from Pixabay or Pexels.

The text is rendered onto the image using a custom font.

Final images are saved to the outputs/ folder.

Optionally, the image and its caption are uploaded or shared via integrations.

Folder & File Breakdown
main.py: Controls time-based execution. Think of it as the bot scheduler.

main_job.py: Core logic. Handles content creation, image generation, saving, etc.

prompts/: Contains text generation templates for OpenAI.

outputs/: Stores final rendered images, ready to be shared.

image_utils.py: Manages text overlay and image processing.

aws_utils.py: Prepares image upload to cloud storage if needed.

instagram/: Contains functions to post content automatically.

telegram_utils.py: Optional module for sending logs or updates via Telegram.

used_prompts.txt, used_titles/: Track used content to avoid repetition.

Who is it for?
Perfect for anyone looking to automate content production — especially social media managers, digital marketers, and AI enthusiasts.

🌐 Türkçe
Bu Proje Nedir?
Auto Content Bot, Python ile geliştirilmiş bir otomasyon aracıdır. Yapay zeka kullanarak metin üretir, açık API’lerden görseller alır, bu görsellere metin ekler ve isteğe bağlı olarak Instagram’a gönderir. Tamamen otomatik çalışan bir içerik döngüsü sunar: yazı üretimi, görsel bulma, görsel işleme ve çıktı üretimi.

Nasıl Çalışır?
main.py dosyası, her 30–50 dakikada bir çalışacak şekilde planlanmıştır.

Her döngüde main_job.py çağrılır ve tüm işlemler bu dosyada yürütülür.

prompts/ klasöründeki şablonlara göre OpenAI üzerinden metin üretilir.

Üretilen metne uygun görseller Pixabay veya Pexels’ten indirilir.

Yazı, özel font ile görselin üzerine yerleştirilir.

Oluşan son görseller outputs/ klasörüne kaydedilir.

İsteğe bağlı olarak bu görseller ve açıklamalar çeşitli platformlara yüklenebilir veya paylaşılabilir.

Klasör & Dosya Açıklamaları
main.py: Zamanlama döngüsünü kontrol eder. Otomatik çalışma burada başlar.

main_job.py: Tüm işlemlerin yürütüldüğü ana dosya.

prompts/: OpenAI için içerik şablonlarının bulunduğu klasör.

outputs/: Oluşturulan son görseller burada saklanır.

image_utils.py: Görsel işleme ve yazı ekleme işlemlerini yapar.

aws_utils.py: Görseli bulut ortamına yüklemek için kullanılır.

instagram/: İçeriği otomatik olarak Instagram’a göndermek için gereken işlemler.

telegram_utils.py: (isteğe bağlı) Telegram’a log veya bildirim gönderimi.

used_prompts.txt, used_titles/: Tekrar kullanılmaması gereken içerikleri kaydeder.

Kimler İçin Uygun?
Sosyal medya yöneticileri, dijital pazarlama uzmanları ya da yapay zeka destekli içerik üretmek isteyen herkes için uygundur.


📄 License MIT — free to use, extend, and adapt for your platform.
