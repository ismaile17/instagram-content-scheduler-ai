import openai
import json
import os
import random

# OpenAI API anahtarını içe aktar
from api_keys import OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

# Klasör ve dosya yolları
PROMPTS_DIR = "prompts"
USED_TITLES_DIR = "used_titles"
USED_PROMPTS_PATH = "used_prompts.txt"

# Gerekli klasörlerin oluşturulması
os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(USED_TITLES_DIR, exist_ok=True)

# ------------------ Prompt Seçimi ------------------

def get_next_prompt():
    """
    Tüm prompt dosyaları bir kez kullanıldıysa used_prompts.txt sıfırlanır.
    Geriye kalanlardan rastgele birini seçer ve kaydeder.
    """
    all_prompts = [f for f in os.listdir(PROMPTS_DIR) if f.endswith(".txt")]
    
    # Kullanılmışları oku
    used_prompts = []
    if os.path.exists(USED_PROMPTS_PATH):
        with open(USED_PROMPTS_PATH, "r", encoding="utf-8") as f:
            used_prompts = [line.strip() for line in f if line.strip()]
    
    # Kalanları filtrele
    remaining_prompts = list(set(all_prompts) - set(used_prompts))

    if not remaining_prompts:
        print("🔁 Tüm promptlar kullanıldı, liste sıfırlanıyor...")
        open(USED_PROMPTS_PATH, "w").close()
        remaining_prompts = all_prompts

    selected = random.choice(remaining_prompts)

    # Kayıt et
    with open(USED_PROMPTS_PATH, "a", encoding="utf-8") as f:
        f.write(selected + "\n")

    return selected

def get_prompt_content():
    """
    Yeni kullanılmamış bir prompt dosyası getirir ve içeriğini döndürür.
    """
    selected_file = get_next_prompt()
    with open(os.path.join(PROMPTS_DIR, selected_file), "r", encoding="utf-8") as f:
        content = f.read().strip()
    return selected_file, content

# ------------------ Başlık Takibi ------------------

def load_used_titles(prompt_filename):
    """
    Belirtilen prompt dosyasına ait daha önce kullanılan başlıkları getirir.
    """
    title_file = os.path.join(USED_TITLES_DIR, prompt_filename)
    if not os.path.exists(title_file):
        return []
    with open(title_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_new_title(prompt_filename, title):
    """
    Yeni başlık varsa ilgili used_titles dosyasına kaydeder.
    """
    title_file = os.path.join(USED_TITLES_DIR, prompt_filename)
    with open(title_file, "a", encoding="utf-8") as f:
        f.write(title.strip() + "\n")

# ------------------ GPT Kullanımı ------------------

def clean_response_content(content):
    """
    GPT yanıtında varsa ``` işaretlerini temizler.
    """
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content

def get_gpt_content():
    """
    - Kullanılmamış prompt dosyasını seçer.
    - O prompta ait daha önce kullanılan başlıkları yükler.
    - GPT'ye gönderir.
    - Yeni başlık varsa kaydeder.
    """
    prompt_filename, prompt_body = get_prompt_content()
    used_titles = load_used_titles(prompt_filename)

    used_titles_text = "\n".join(f"- {title}" for title in used_titles) if used_titles else "Henüz başlık yok."

    full_prompt = f"""

Aşağıda daha önce kullandığım başlıklar var. Lütfen bu başlıkları tekrar etme ve özgün, farklı bir günlük durum seç!
{used_titles_text}

***Alışveriş veya market konularına değinme, daha genel veya spesifik konular seç***

***Descrption alanında kurulan cümlelerde bu gönderiyi kaydedin gibi emrivaki cümleler değil de biraz daha ikna edici cümleler kur, 
işinize yarıyorsa kayıt edebilir veya arkadaşınızla paylaşabilirsiniz gibi ama bu örnek cümlelere de bağlı kalma farklı cümleler oluştur***

***Kurulan cümleler konu başlığından asla bağımsız olmasın. İngilizce cümle ve türkçe cümle anlamsız saçma cümleler olmasın. Günlük hayatta kullanılabilecek standart cümleler olsun.***

***Title için oluşturulan başlıkları kelimeler veya cümleler diye bitirme. ifadeler veya farklı bir belirtmeyle bitirebilirsin.***

 konu:

{prompt_body}
    """

    print("📡 GPT'den veri alınıyor...")
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.9
    )

    content = response['choices'][0]['message']['content']
    content = clean_response_content(content)

    try:
        parsed = json.loads(content)
        title = parsed.get("title", "").strip()
        if title and title not in used_titles:
            save_new_title(prompt_filename, title)
        return parsed, full_prompt
    except json.JSONDecodeError:
        print("❌ JSON parse hatası:")
        print(content)
        return None, None

# ------------------ Test Amaçlı ------------------

if __name__ == "__main__":
    result = get_gpt_content()
    if result:
        print(json.dumps(result, indent=4, ensure_ascii=False))
