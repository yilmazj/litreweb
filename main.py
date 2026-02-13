import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

# --- AYARLAR ---
# Gerçek bir tarayıcı gibi görünmek şart
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Şehir Adlarını URL Yapısına Uygun Hale Getirme
# CanlıDöviz slug yapısı: 'afyon' değil 'afyonkarahisar', 'agri' vb.
SEHIR_SLUGS = {
    1: "adana", 2: "adiyaman", 3: "afyonkarahisar", 4: "agri", 5: "amasya", 6: "ankara", 7: "antalya", 8: "artvin", 9: "aydin", 10: "balikesir",
    11: "bilecik", 12: "bingol", 13: "bitlis", 14: "bolu", 15: "burdur", 16: "bursa", 17: "canakkale", 18: "cankiri", 19: "corum", 20: "denizli",
    21: "diyarbakir", 22: "edirne", 23: "elazig", 24: "erzincan", 25: "erzurum", 26: "eskisehir", 27: "gaziantep", 28: "giresun", 29: "gumushane", 30: "hakkari",
    31: "hatay", 32: "isparta", 33: "mersin", 34: "istanbul-avrupa", 35: "izmir", 36: "kars", 37: "kastamonu", 38: "kayseri", 39: "kirklareli", 40: "kirsehir",
    41: "kocaeli", 42: "konya", 43: "kutahya", 44: "malatya", 45: "manisa", 46: "kahramanmaras", 47: "mardin", 48: "mugla", 49: "mus", 50: "nevsehir",
    51: "nigde", 52: "ordu", 53: "rize", 54: "sakarya", 55: "samsun", 56: "siirt", 57: "sinop", 58: "sivas", 59: "tekirdag", 60: "tokat",
    61: "trabzon", 62: "tunceli", 63: "sanliurfa", 64: "usak", 65: "van", 66: "yozgat", 67: "zonguldak", 68: "aksaray", 69: "bayburt", 70: "karaman",
    71: "kirikkale", 72: "batman", 73: "sirnak", 74: "bartin", 75: "ardahan", 76: "igdir", 77: "yalova", 78: "karabuk", 79: "kilis", 80: "osmaniye",
    81: "duzce", 934: "istanbul-anadolu"
}

def temizle_fiyat(fiyat_txt):
    """ '44,50 TL' -> 44.50 """
    if not fiyat_txt: return 0.0
    try:
        temiz = fiyat_txt.lower().replace('tl', '').replace('₺', '').strip()
        temiz = temiz.replace(',', '.')
        return float(temiz)
    except:
        return 0.0

def fetch_city_data(slug):
    """ Belirtilen şehrin tablosunu kazır """
    url = f"https://canlidoviz.com/akaryakit-fiyatlari/{slug}"
    
    data = {}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Tabloyu Bul: Genelde 'table' tag'i içindedir.
            # Tablonun satırlarını (tr) al
            rows = soup.select("table tbody tr")
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 2: continue # Boş satırsa geç
                
                # 1. Sütun: Marka Adı (Resim alt etiketi veya metin olabilir)
                marka_adi = cols[0].get_text(strip=True).lower()
                
                # Eğer marka adı metin olarak yoksa, img alt tagına bak
                if not marka_adi:
                    img = cols[0].find("img")
                    if img and img.get("alt"):
                        marka_adi = img.get("alt").lower()

                # Marka Eşleştirme
                key = None
                if "opet" in marka_adi: key = "Opet"
                elif "shell" in marka_adi: key = "Shell"
                elif "petrol ofisi" in marka_adi or "po" in marka_adi: key = "Petrol Ofisi"
                elif "bp" in marka_adi: key = "Petrol Ofisi" # BP -> PO Oldu
                elif "total" in marka_adi: key = "Total Energies"
                elif "aytemiz" in marka_adi: key = "Aytemiz"
                elif "türkiye petrolleri" in marka_adi or "tp" in marka_adi: key = "Turkiye Petrolleri"
                
                if key:
                    # Sütun Sırası Genelde: Marka | Benzin | Motorin | LPG
                    # Siteden siteye değişebilir, CanliDoviz'de genelde böyledir.
                    try:
                        benzin = temizle_fiyat(cols[1].get_text())
                        motorin = temizle_fiyat(cols[2].get_text())
                        
                        # LPG bazen 3. bazen 4. sütun olabiliyor, kontrol edelim
                        lpg = 0.0
                        if len(cols) > 3:
                            lpg = temizle_fiyat(cols[3].get_text())
                        
                        data[key] = {
                            "Benzin": benzin,
                            "Motorin": motorin,
                            "LPG": lpg
                        }
                    except:
                        continue # Hatalı satırı atla
            
            return data
            
    except Exception as e:
        print(f"Hata ({slug}): {e}")
    
    return None

def main():
    print("🚀 Marka Bazlı 81 İl Taraması Başlıyor...")
    all_data = []
    
    # 81 İl + İst Anadolu
    plaka_listesi = list(range(1, 82)) + [934]
    
    # Hızlı test için şimdilik sadece büyükleri açıyorum, sen yukarıdakini açarsın.
    plaka_listesi = [34, 934, 6, 35, 1, 16] 

    for plaka in plaka_listesi:
        slug = SEHIR_SLUGS.get(plaka)
        sehir_adi = slug.replace("-", " ").upper()
        
        # print(f"⏳ Taranıyor: {sehir_adi}...")
        
        istasyon_verileri = fetch_city_data(slug)
        
        # Eğer veri boş geldiyse (site yapısı değişmiş veya engel yemiş olabilir)
        if not istasyon_verileri:
            istasyon_verileri = {} # Boş obje dön, kod patlamasın
        
        # Veriyi Hazırla
        il_objesi = {
            "plaka": plaka,
            "sehir": sehir_adi,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "istasyonlar": istasyon_verileri
        }
        
        all_data.append(il_objesi)
        time.sleep(0.5) # IP ban yememek için bekleme

    print(json.dumps(all_data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()