import os
import re
import json
import urllib.parse
import requests
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

# API anahtarlarını ayrı bir dosyadan alıyoruz.
from api_keys import PIXABAY_API_KEY, PEXELS_API_KEY

# ================= SABİTLER =================
IMAGE_WIDTH, IMAGE_HEIGHT = 1080, 1080               # Çıktı görseli boyutu
TOP_HEIGHT_RATIO = 0.6                               # Üst alanın (blur ve center resim) oranı
PADDING = 50                                         # Kenar boşluğu (metin alanı için)
SPACING = 35                                         # Satırlar arası boşluk
SIDE_BY_SIDE_SPACING = 80                            # Yan yana bloklar arası boşluk
ICON_SIZE = (50, 50)                                 # İkon boyutu (genişlik, yükseklik)
ICON_VERTICAL_OFFSET = 8                             # İkonların dikey kaydırma değeri
ICON_HORIZONTAL_OFFSET = 0                           # İkonların yatay (sola) kaydırma değeri

# Font ayarları
MAIN_FONT_MAX_SIZE = 44              # Ana metin için başlangıç fontu
EXAMPLE_FONT_MAX_SIZE = 36           # Örnek metin için başlangıç fontu
MIN_FONT_SIZE = 14                   # İzin verilen minimum font boyutu
WORD_COUNT_THRESHOLD = 6             # English metni, kelime sayısı bu değerin altındaysa bold, üstündeyse regular

# Renk ayarları
OVERLAY_COLOR = (0, 0, 0, 153)       # (Title için overlay, words için kullanılmıyor)
TEXT_COLOR = (255, 255, 255)         # Yazı rengi (beyaz)
SHADOW_COLOR = (0, 0, 0, 180)        # Yazı gölgesi rengi

# İkon klasörleri
LEFT_ICON_FOLDER = "icons/left"      # Sol ok ikonları
PENCIL_ICON_FOLDER = "icons/pencil"  # Kalem (örnek cümle anlamı) ikonları
TR_ICON_FOLDER = "icons/tr"          # Türkçe ikonları
EN_ICON_FOLDER = "icons/en"          # İngilizce ikonları (örnek cümle anlamı için)

# BACKGROUND klasörü (words görsellerinde yazı alanının arka planı için)
BACKGROUND_FOLDER = "background"

# ================= GLOBAL DEĞİŞKENLER =================
SELECTED_LEFT_ICON = None
SELECTED_PENCIL_ICON = None
SELECTED_TR_ICON = None
SELECTED_EN_ICON = None
SELECTED_BACKGROUND = None  # BACKGROUND klasöründen seçilen arka plan resmi

# ------------------ Rastgele ikon seçimi ------------------
def get_random_icon(icon_folder):
    """
    Verilen klasördeki .png, .jpg, .jpeg uzantılı dosyalardan rastgele bir tanesinin yolunu döndürür.
    """
    try:
        files = [f for f in os.listdir(icon_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            return os.path.join(icon_folder, random.choice(files))
    except Exception as e:
        print(f"Icon random seçimi hatası ({icon_folder}): {e}")
    return None

# ------------------ Global ikonların başlatılması ------------------
def initialize_selected_icons():
    """
    Eğer global ikonlar henüz seçilmemişse, ilgili klasörlerden rastgele ikon seçimi yapar.
    Artık 'okunuş' ile ilgili ikonlar kaldırıldı.
    """
    global SELECTED_LEFT_ICON, SELECTED_PENCIL_ICON, SELECTED_TR_ICON, SELECTED_EN_ICON
    if SELECTED_LEFT_ICON is None:
        SELECTED_LEFT_ICON = get_random_icon(LEFT_ICON_FOLDER)
    if SELECTED_PENCIL_ICON is None:
        SELECTED_PENCIL_ICON = get_random_icon(PENCIL_ICON_FOLDER)
    if SELECTED_TR_ICON is None:
        SELECTED_TR_ICON = get_random_icon(TR_ICON_FOLDER)
    if SELECTED_EN_ICON is None:
        SELECTED_EN_ICON = get_random_icon(EN_ICON_FOLDER)

# ------------------ Global background seçiminin başlatılması ------------------
def initialize_selected_background():
    """
    BACKGROUND klasöründen rastgele bir arka plan resmi seçer ve global SELECTED_BACKGROUND değişkenine atar.
    """
    global SELECTED_BACKGROUND
    if SELECTED_BACKGROUND is None:
        SELECTED_BACKGROUND = get_random_background()

# ------------------ Dosya adını temizleme ------------------
def sanitize_filename(text):
    """
    Dosya adlarında kullanılmak üzere, verilen metnin ilk kelimesini alır ve 
    sadece harf, rakam, alt çizgi ve tire karakterlerini bırakır.
    """
    if text and text.strip():
        first_word = text.strip().split()[0]
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', first_word)
        return sanitized
    return "kelime"

# ------------------ Metin ölçümü ------------------
def get_text_size(draw, text, font):
    """
    Verilen metnin genişlik ve yüksekliğini döndürür.
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

# ------------------ Metni kenarlıklı çizme ------------------
def draw_text_with_outline(draw, position, text, font, fill, outline_color, outline_width=2):
    """
    Metni belirtilen konumda çizip, kenarına outline (gölge) ekler.
    """
    x, y = position
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill)

# ------------------ Metni satırlara bölme ve sığdırma fonksiyonları ------------------
def wrap_text(text, draw, font, max_width):
    """
    Greedy algoritma kullanarak metni kelimelere bölüp, ilk satıra maksimum kadar sığdırır;
    geri kalan kelimeler ikinci satıra alınır. Eğer tek satırda sığarsa tek satır döner.
    """
    words = text.split()
    if not words:
        return []
    # İlk satıra sığdırma denemesi:
    line1 = words[0]
    i = 1
    while i < len(words):
        test_line = line1 + " " + words[i]
        w, _ = get_text_size(draw, test_line, font)
        if w <= max_width:
            line1 = test_line
            i += 1
        else:
            break
    # Eğer tüm kelimeler sığdıysa tek satır döneriz.
    if i == len(words):
        return [line1]
    # Kalan kelimeler ikinci satıra eklenir.
    line2 = " ".join(words[i:])
    # Kontrol: İkinci satırın da max_width içinde olup olmadığını kontrol edelim.
    w2, _ = get_text_size(draw, line2, font)
    if w2 <= max_width:
        return [line1, line2]
    # Eğer ikinci satır sığmıyorsa, bu font boyutuyla uygun değil.
    return None

def fit_text_in_box(draw, text, max_width, font_path, start_size, max_lines=2, min_size=MIN_FONT_SIZE, line_spacing=10):
    """
    Verilen metni, belirtilen genişlikte ve maksimum satır sayısı kadar sığdıracak en büyük font boyutunu
    belirler. Eğer metin 1 satırda sığmazsa 2 satıra bölerek hesaplama yapar.
    Dönen değer: {"font": font, "lines": [satır1, satır2, ...], "width": max_line_width, "height": total_text_height}
    """
    temp_draw = draw
    for size in range(start_size, min_size - 1, -1):
        font = ImageFont.truetype(font_path, size)
        wrapped = wrap_text(text, temp_draw, font, max_width)
        if wrapped is not None and len(wrapped) <= max_lines:
            # Her satırın yüksekliğini ölçüyoruz (varsayılan olarak hepsi aynı olabilir)
            line_heights = [get_text_size(temp_draw, line, font)[1] for line in wrapped]
            total_height = sum(line_heights) + (len(wrapped) - 1) * line_spacing
            line_widths = [get_text_size(temp_draw, line, font)[0] for line in wrapped]
            max_line_width = max(line_widths)
            return {"font": font, "lines": wrapped, "width": max_line_width, "height": total_height}
    # Eğer hiçbir font boyutuyla sığdıramazsak, en küçük boyutu kullan
    font = ImageFont.truetype(font_path, min_size)
    wrapped = wrap_text(text, temp_draw, font, max_width)
    if wrapped is None:
        # Kelimeleri bölmeden direkt kesme işlemi yapılabilir.
        wrapped = [text]
    line_heights = [get_text_size(temp_draw, line, font)[1] for line in wrapped]
    total_height = sum(line_heights) + (len(wrapped) - 1) * line_spacing
    line_widths = [get_text_size(temp_draw, line, font)[0] for line in wrapped]
    max_line_width = max(line_widths)
    return {"font": font, "lines": wrapped, "width": max_line_width, "height": total_height}

# ------------------ Blur uygulanmış resim oluşturma ------------------
def create_blurred_background(image_path, target_size):
    """
    Belirtilen resmin, hedef boyutlara yeniden boyutlandırılmış ve Gaussian blur uygulanmış halini oluşturur.
    """
    original_img = Image.open(image_path).convert("RGB")
    bg = original_img.resize(target_size)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
    return bg

# ------------------ BACKGROUND klasöründen rastgele arka plan resmi seçimi ------------------
def get_random_background():
    """
    BACKGROUND_FOLDER klasöründen .png, .jpg, .jpeg uzantılı dosyalardan rastgele bir tanesinin yolunu döndürür.
    """
    try:
        files = [f for f in os.listdir(BACKGROUND_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            return os.path.join(BACKGROUND_FOLDER, random.choice(files))
    except Exception as e:
        print(f"Background seçim hatası: {e}")
    return None

# ------------------ Görsel İndirme ------------------
def search_and_download_image(query, save_path, preferred_source="pixabay"):
    """
    Verilen sorguya göre Pixabay veya Pexels API'leri üzerinden görsel indirir.
    İlk API hata verirse, yedek API denenir.
    """
    query_encoded = urllib.parse.quote(query)
    if preferred_source == "pixabay":
        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query_encoded}&image_type=photo&per_page=3"
        fallback_url = f"https://api.pexels.com/v1/search?query={query_encoded}&per_page=1"
        headers = None
        fallback_headers = {"Authorization": PEXELS_API_KEY}
    else:
        url = f"https://api.pexels.com/v1/search?query={query_encoded}&per_page=1"
        fallback_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query_encoded}&image_type=photo&per_page=3"
        headers = {"Authorization": PEXELS_API_KEY}
        fallback_headers = None
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if preferred_source == "pixabay":
            image_url = data["hits"][0]["largeImageURL"]
        else:
            image_url = data["photos"][0]["src"]["large"]
        img_data = requests.get(image_url).content
        with open(save_path, "wb") as handler:
            handler.write(img_data)
        print(f"🖼️ [{'Pixabay' if preferred_source=='pixabay' else 'Pexels'}] {query} indirildi.")
        return
    except Exception as e:
        print(f"❌ {preferred_source.capitalize()} hatası: {e}")
    try:
        response = requests.get(fallback_url, headers=fallback_headers)
        response.raise_for_status()
        data = response.json()
        if preferred_source == "pixabay":
            image_url = data["photos"][0]["src"]["large"]
        else:
            image_url = data["hits"][0]["largeImageURL"]
        img_data = requests.get(image_url).content
        with open(save_path, "wb") as handler:
            handler.write(img_data)
        print(f"🖼️ [{'Pixabay' if preferred_source=='pexels' else 'Pexels'}] {query} indirildi.")
        return
    except Exception as e:
        print(f"❌ Yedek kaynak hatası: {e}")
    print(f"❌ {query} için görsel indirilemedi.")

# ------------------ Content JSON'dan görsel indirme ------------------
def download_images_from_content_json(folder_path, preferred_source="pixabay"):
    """
    Belirtilen klasördeki content.json dosyasına göre;
      - Title görseli ve
      - Her kelime için görselleri indirir.
    """
    with open(os.path.join(folder_path, "content.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    images_folder = os.path.join(folder_path, "images")
    os.makedirs(images_folder, exist_ok=True)
    search_and_download_image(data["topic_image_prompt"], os.path.join(images_folder, "00_title.jpg"), preferred_source)
    for i, word in enumerate(data["words"]):
        name = sanitize_filename(word.get("english", "kelime"))
        filename = f"{i+1:02d}_{name}.jpg"
        query = word.get("image_prompt", word.get("english", ""))
        search_and_download_image(query, os.path.join(images_folder, filename), preferred_source)

# ------------------ Title Görseli Oluşturma ------------------
def overlay_title_on_image(image_path, output_path, title, font_path="OpenSans-Bold.ttf"):
    """
    Title görseli oluşturur:
      - Girdi resmi, ImageOps.fit kullanılarak hedef boyuta (tam ekran) kesilip zoomlanır.
      - Metin alanı için, metnin toplam yüksekliğine göre tam genişlikte, %80 opak siyah bir şerit eklenir.
      - Title metni, satırlara bölünerek ortalanır ve outline (gölge) efektiyle çizilir.
    """
    # Hedef boyutlar (tam ekran)
    target_size = (IMAGE_WIDTH, IMAGE_HEIGHT)
    
    # Orijinal resmi, ImageOps.fit kullanarak kesip zoomlayarak hedef boyuta uyarla
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    # Metin alanı için kullanılacak fontu yükle
    font = ImageFont.truetype(font_path, MAIN_FONT_MAX_SIZE)
    
    # Metni satırlara bölmek için maksimum genişliği belirle (kenar boşlukları hariç)
    max_width = IMAGE_WIDTH - 2 * PADDING
    lines = []
    current_line = ""
    
    # Title metnini kelimelerine ayır ve satır satır oluştur
    for word in title.split():
        test_line = (current_line + " " + word).strip()
        if get_text_size(ImageDraw.Draw(img), test_line, font)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Toplam metin bloğu yüksekliğini hesapla (her satır için biraz boşluk ekleyerek)
    total_text_height = sum(get_text_size(ImageDraw.Draw(img), line, font)[1] + 10 for line in lines)
    
    # Yatay ve dikey olarak metin bloğunu ortalamak için başlangıç Y koordinatını hesapla
    y_start = (IMAGE_HEIGHT - total_text_height) // 2

    # Şerit yüksekliği: Metin bloğunun yüksekliğini biraz genişletmek için (örneğin ±20 piksel)
    stripe_top = y_start - 20
    stripe_bottom = y_start + total_text_height + 20

    # %80 opak siyah (255 * 0.8 = 204) renk (R, G, B, A)
    stripe_color = (0, 0, 0, 204)
    
    # Yeni bir overlay resmi oluşturup, tüm boyutta tamamen şeffaf başlatıyoruz.
    overlay = Image.new("RGBA", target_size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Soldan sağa tam genişlikte, hesaplanan stripe yüksekliğinde siyah şerit çiziyoruz.
    overlay_draw.rectangle([(0, stripe_top), (IMAGE_WIDTH, stripe_bottom)], fill=stripe_color)
    
    # Oluşturulan overlay'i orijinal resme alpha_composite ile ekleyerek metin alanını vurguluyoruz.
    composite = Image.alpha_composite(img.convert("RGBA"), overlay)
    
    # Metni çizmek için çizim objesi oluşturuyoruz.
    draw = ImageDraw.Draw(composite)
    y = y_start
    for line in lines:
        # Her satırın genişlik ve yüksekliğini ölçüyoruz.
        w, h = get_text_size(draw, line, font)
        # Satırı yatay olarak ortalamak için x koordinatını hesaplıyoruz.
        x = (IMAGE_WIDTH - w) // 2
        # Metni outline efektiyle çiziyoruz.
        draw_text_with_outline(draw, (x, y), line, font, TEXT_COLOR, SHADOW_COLOR, outline_width=2)
        y += h + 10  # Her satır arasında 10 piksel boşluk ekliyoruz.
    
    # Son olarak, composite resmi RGB formatına çevirip kaydediyoruz.
    composite.convert("RGB").save(output_path)
    print(f"🖋️ Başlık görseli hazır: {output_path}")

# ------------------ Word Görseli Oluşturma ------------------
def add_text_overlay(image_path, output_path, word_data, is_last=False,
                     font_path_regular="OpenSans-Regular.ttf", font_path_bold="OpenSans-Bold.ttf",
                     overlay_color=OVERLAY_COLOR):
    """
    Word görselleri için:
      - JSON'daki mevcut metin alanları (english, turkish, example_sentence, example_meaning) tespit edilir.
      - "english" metni, kelime sayısına göre bold veya regular fontla çizilir.
      - "turkish" metni artık sadece tek blok olarak işlenir (okunuş alanı kaldırıldı).
      - Örnek cümle ve örnek cümle anlamı varsa, alt satırlara eklenir.
      - Yazı alanı için BACKGROUND klasöründen rastgele seçilen arka plan resmi kullanılır.
      - Yazı alanı yüksekliği, blokların toplam yüksekliğine göre otomatik ayarlanır.
      - Üst alan için; girdi resminin blur uygulanmış versiyonu oluşturulur ve üzerine, orijinal resmin %80 boyutunda center edilmiş hali eklenir.
      - Metinler, belirlenen alana sığacak şekilde maksimum font boyutuyla ve gerekirse 2 satır olacak şekilde ayarlanır.
    """
    initialize_selected_icons()
    initialize_selected_background()  # BACKGROUND resmi global olarak seçiliyor.
    
    TOP_HEIGHT = int(IMAGE_HEIGHT * TOP_HEIGHT_RATIO)
    BOTTOM_HEIGHT = IMAGE_HEIGHT - TOP_HEIGHT

    # ------------------ Üst Alanın Oluşturulması ------------------
    # Girdi resminin tam ekran blur uygulanmış versiyonu (üst alan)
    top_blur = create_blurred_background(image_path, (IMAGE_WIDTH, TOP_HEIGHT))
    # Orijinal resmi, %80 oranında ölçeklendirip, üst alanın ortasına yerleştiriyoruz.
    original_img = Image.open(image_path).convert("RGB")
    center_size = (int(IMAGE_WIDTH * 0.8), int(TOP_HEIGHT * 0.8))
    center_img = ImageOps.contain(original_img, center_size)
    x_center = (IMAGE_WIDTH - center_img.width) // 2
    y_center = (TOP_HEIGHT - center_img.height) // 2
    composite_top = top_blur.copy()
    composite_top.paste(center_img, (x_center, y_center))
    
    # ------------------ Metin Bloklarının Tespiti ------------------
    eng_text = word_data.get("english")
    eng_text = eng_text.strip() if eng_text and eng_text.strip() else None

    tur_text = word_data.get("turkish")
    tur_text = tur_text.strip() if tur_text and tur_text.strip() else None

    ex_sent_text = word_data.get("example_sentence")
    ex_sent_text = ex_sent_text.strip() if ex_sent_text and ex_sent_text.strip() else None

    ex_mean_text = word_data.get("example_meaning") or word_data.get("example_sentence_sense")
    ex_mean_text = ex_mean_text.strip() if ex_mean_text and ex_mean_text.strip() else None

    blocks = []
    # English metni: kelime sayısına göre bold veya regular
    if eng_text:
        if len(eng_text.split()) > WORD_COUNT_THRESHOLD:
            blocks.append({"type": "english", "text": eng_text, "font_path": font_path_regular, "icon": SELECTED_EN_ICON})
        else:
            blocks.append({"type": "english", "text": eng_text, "font_path": font_path_bold, "icon": SELECTED_EN_ICON})
    # Türkçe metni: Artık okunuş alanı kaldırıldı, sadece tek blok olarak işleniyor.
    if tur_text:
        blocks.append({"type": "turkish", "text": tur_text, "font_path": font_path_regular, "icon": SELECTED_TR_ICON})
    # Örnek cümle ve örnek cümle anlamı
    if ex_sent_text:
        blocks.append({"type": "example_sentence", "text": ex_sent_text, "font_path": font_path_regular, "icon": SELECTED_EN_ICON})
    if ex_mean_text:
        blocks.append({"type": "example_meaning", "text": ex_mean_text, "font_path": font_path_regular, "icon": SELECTED_PENCIL_ICON})

    # ------------------ Blok Yüksekliklerinin Hesaplanması ------------------
    row_dimensions = []
    total_text_height = 0
    temp_draw = ImageDraw.Draw(Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT)))
    # Her bir metin bloğunu, belirlenen alana (PADDING'ler hariç) sığdırmak için 2 satır formatında hesaplıyoruz.
    for block in blocks:
        avail_width = IMAGE_WIDTH - 2 * PADDING
        dims = fit_text_in_box(temp_draw, block["text"], avail_width, block["font_path"], MAIN_FONT_MAX_SIZE, max_lines=2, min_size=MIN_FONT_SIZE, line_spacing=10)
        # Eğer ikon varsa, ikon genişliği ekleniyor.
        if block.get("icon"):
            dims["width"] += ICON_SIZE[0] + 10
        row_dimensions.append({"dims": dims, "type": block["type"], "icon": block.get("icon")})
        # Satır yüksekliği, metin bloğu yüksekliği ile ikon yüksekliği arasındaki maksimum değeri alır.
        row_height = max(dims["height"], ICON_SIZE[1] if block.get("icon") else dims["height"])
        total_text_height += row_height + SPACING

    # ------------------ Alt Alan Yüksekliğinin Belirlenmesi ------------------
    bottom_height = total_text_height + 2 * PADDING
    min_top_height = int(IMAGE_HEIGHT * 0.3)
    if (IMAGE_HEIGHT - bottom_height) < min_top_height:
        bottom_height = IMAGE_HEIGHT - min_top_height
    top_height = IMAGE_HEIGHT - bottom_height

    # ------------------ Üst Alanın (Top Area) Oluşturulması ------------------
    top_blur = create_blurred_background(image_path, (IMAGE_WIDTH, top_height))
    original_img = Image.open(image_path).convert("RGB")
    center_size = (int(IMAGE_WIDTH * 0.8), int(top_height * 0.8))
    center_img = ImageOps.contain(original_img, center_size)
    x_center = (IMAGE_WIDTH - center_img.width) // 2
    y_center = (top_height - center_img.height) // 2
    composite_top = top_blur.copy()
    composite_top.paste(center_img, (x_center, y_center))
    
    # ------------------ Alt Alanın (Bottom Area) Oluşturulması ------------------
    if SELECTED_BACKGROUND:
        bottom_bg = Image.open(SELECTED_BACKGROUND).convert("RGB")
        bottom_bg = ImageOps.fit(bottom_bg, (IMAGE_WIDTH, bottom_height), method=Image.Resampling.LANCZOS)
    else:
        bottom_bg = Image.new("RGB", (IMAGE_WIDTH, bottom_height), (255, 255, 255))
    
    # Final görsel, üst ve alt alanların birleşimi
    final_img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT))
    final_img.paste(composite_top, (0, 0))
    final_img.paste(bottom_bg, (0, top_height))
    draw = ImageDraw.Draw(final_img)

    # ------------------ Metin Bloklarının Yerleştirilmesi ------------------
    y_start = top_height + (bottom_height - total_text_height) // 2
    y_current = y_start
    for item in row_dimensions:
        dims = item["dims"]
        # Satır yüksekliği: ikon varsa, ikon yüksekliği ile metin bloğu yüksekliğinin maksimumu
        row_height = max(dims["height"], ICON_SIZE[1] if item.get("icon") else dims["height"])
        # Eğer ikon varsa, ikon ve metin birlikte ortalanacak şekilde hesaplama yapıyoruz.
        if item.get("icon"):
            # İkonun eklenmesi için metnin toplam genişliğine ikon genişliği ekleniyor.
            total_block_width = dims["width"]
            x_start = (IMAGE_WIDTH - total_block_width) // 2
            # İkonu yerleştiriyoruz.
            final_img.paste(Image.open(item["icon"]).resize(ICON_SIZE).convert("RGBA"), 
                            (x_start, y_current + (row_height - ICON_SIZE[1]) // 2 + ICON_VERTICAL_OFFSET), 
                            Image.open(item["icon"]).resize(ICON_SIZE).convert("RGBA"))
            x_text = x_start + ICON_SIZE[0] + 10
        else:
            x_text = (IMAGE_WIDTH - dims["width"]) // 2
        # Metni, satır satır outline efektiyle çiziyoruz.
        current_y = y_current
        for line in dims["lines"]:
            line_w, line_h = get_text_size(draw, line, dims["font"])
            draw_text_with_outline(draw, (x_text, current_y), line, dims["font"], TEXT_COLOR, SHADOW_COLOR, outline_width=2)
            current_y += line_h + 10  # Satırlar arası spacing
        y_current += row_height + SPACING

    # ------------------ Sol Ok İkonunun Eklenmesi ------------------
    if not is_last and SELECTED_LEFT_ICON:
        try:
            left_icon = Image.open(SELECTED_LEFT_ICON).resize(ICON_SIZE).convert("RGBA")
            final_img.paste(left_icon, (IMAGE_WIDTH - ICON_SIZE[0] - 10, IMAGE_HEIGHT - ICON_SIZE[1] - 10 + ICON_VERTICAL_OFFSET), left_icon)
        except Exception as e:
            print(f"Sol ok ikonu eklenemedi: {e}")
    
    final_img.convert("RGB").save(output_path)
    print(f"✅ Kelime görseli oluşturuldu: {output_path}")

# ------------------ Tüm Görselleri Oluşturma ------------------
def generate_final_images(folder_path, preferred_source="pixabay"):
    """
    Belirtilen klasördeki content.json dosyasına göre:
      - Title görselini oluşturur.
      - Her kelime için yukarıdaki düzenlemelere göre word görsellerini oluşturur.
    """
    initialize_selected_icons()
    initialize_selected_background()  # BACKGROUND resmi bir kez seçiliyor.
    with open(os.path.join(folder_path, "content.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    images_path = os.path.join(folder_path, "images")
    output_path = os.path.join(folder_path, "final")
    os.makedirs(output_path, exist_ok=True)
    
    # Title görseli oluşturuluyor.
    overlay_title_on_image(os.path.join(images_path, "00_title.jpg"),
                            os.path.join(output_path, "00_title.jpg"),
                            data["title"])
    
    # Her kelime için word görselleri oluşturuluyor.
    for i, word in enumerate(data["words"]):
        name = sanitize_filename(word.get("english", "kelime"))
        input_img = os.path.join(images_path, f"{i+1:02d}_{name}.jpg")
        output_img = os.path.join(output_path, f"{i+1:02d}_{name}.jpg")
        add_text_overlay(input_img, output_img, word_data=word, is_last=(i == len(data["words"]) - 1))
    
    print("Tüm görseller başarıyla oluşturuldu!")

# ------------------ ÖRNEK KULLANIM ------------------
# Örneğin: generate_final_images("your_folder_path", preferred_source="pexels")
