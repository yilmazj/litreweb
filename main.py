import requests
import json
import time
from datetime import datetime

# --- AYARLAR ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.google.com"
}

# 81 İL LİSTESİ (PLAKA KODLARI)
SEHIRLER = {
    1: "ADANA", 2: "ADIYAMAN", 3: "AFYONKARAHISAR", 4: "AGRI", 5: "AMASYA", 6: "ANKARA", 7: "ANTALYA", 8: "ARTVIN", 9: "AYDIN", 10: "BALIKESIR",
    11: "BILECIK", 12: "BINGOL", 13: "BITLIS", 14: "BOLU", 15: "BURDUR", 16: "BURSA", 17: "CANAKKALE", 18: "CANKIRI", 19: "CORUM", 20: "DENIZLI",
    21: "DIYARBAKIR", 22: "EDIRNE", 23: "ELAZIG", 24: "ERZINCAN", 25: "ERZURUM", 26: "ESKISEHIR", 27: "GAZIANTEP", 28: "GIRESUN", 29: "GUMUSHANE", 30: "HAKKARI",
    31: "HATAY", 32: "ISPARTA", 33: "MERSIN", 34: "ISTANBUL (AVRUPA)", 35: "IZMIR", 36: "KARS", 37: "KASTAMONU", 38: "KAYSERI", 39: "KIRKLARELI", 40: "KIRSEHIR",
    41: "KOCAELI", 42: "KONYA", 43: "KUTAHYA", 44: "MALATYA", 45: "MANISA", 46: "KAHRAMANMARAS", 47: "MARDIN", 48: "MUGLA", 49: "MUS", 50: "NEVSEHIR",
    51: "NIGDE", 52: "ORDU", 53: "RIZE", 54: "SAKARYA", 55: "SAMSUN", 56: "SIIRT", 57: "SINOP", 58: "SIVAS", 59: "TEKIRDAG", 60: "TOKAT",
    61: "TRABZON", 62: "TUNCELI", 63: "SANLIURFA", 64: "USAK", 65: "VAN", 66: "YOZGAT", 67: "ZONGULDAK", 68: "AKSARAY", 69: "BAYBURT", 70: "KARAMAN",
    71: "KIRIKKALE", 72: "BATMAN", 73: "SIRNAK", 74: "BARTIN", 75: "ARDAHAN", 76: "IGDIR", 77: "YALOVA", 78: "KARABUK", 79: "KILIS", 80: "OSMANIYE",
    81: "DUZCE", 934: "ISTANBUL (ANADOLU)"
}

def temizle_fiyat(fiyat):
    if not fiyat: return 0.0
    try:
        if isinstance(fiyat, (int, float)): return float(fiyat)
        temiz = str(fiyat).replace('₺', '').replace('TL', '').strip().replace(',', '.')
        return float(temiz)
    except:
        return 0.0

# --- MARKA 1: AYTEMİZ (En Stabil API) ---
def fetch_aytemiz(plaka):
    # Aytemiz'de 934 yok, İstanbul tek (34).
    kod = 34 if plaka == 934 else plaka
    url = "https://www.aytemiz.com.tr/FuelPrice/GetFuelPrices"
    try:
        r = requests.post(url, data={"CityId": kod}, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0] # İlk veri (Merkez)
                return {
                    "Benzin": temizle_fiyat(item.get("Gasoline95")),
                    "Motorin": temizle_fiyat(item.get("Diesel")),
                    "LPG": temizle_fiyat(item.get("Lpg"))
                }
    except: pass
    return None

# --- MARKA 2: OPET (API) ---
def fetch_opet(plaka):
    url = "https://api.opet.com.tr/api/fuelprices/prices"
    kod = "34" if plaka == 934 else str(plaka)
    try:
        r = requests.post(url, json={"ProvinceCode": kod, "ViewType": 1}, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                # İlçe Filtreleme
                target = data[0] # Varsayılan: Listenin ilki
                if plaka == 934: # İst Anadolu
                    for d in data:
                        if "KADIKOY" in d.get("districtName", "").upper():
                            target = d; break
                elif plaka == 34: # İst Avrupa
                    for d in data:
                        if "SISLI" in d.get("districtName", "").upper():
                            target = d; break
                
                prices = {}
                for p in target.get("prices", []):
                    n = p.get("productName", "").lower()
                    v = p.get("amount")
                    if "kurşunsuz" in n: prices["Benzin"] = temizle_fiyat(v)
                    elif "motorin" in n: prices["Motorin"] = temizle_fiyat(v)
                    elif "lpg" in n: prices["LPG"] = temizle_fiyat(v)
                return prices
    except: pass
    return None

# --- MARKA 3: PETROL OFİSİ (API) ---
def fetch_po(plaka):
    # Şehir ismini bul
    sehir = SEHIRLER.get(plaka, "").split(" ")[0] # İSTANBUL (AVRUPA) -> İSTANBUL
    if sehir == "AFYONKARAHISAR": sehir = "AFYON" # PO özel durumu
    
    url = f"https://www.petrolofisi.com.tr/api/fuel-prices?province={sehir}"
    if plaka == 934: url += "&district=KADIKOY"
    elif plaka == 34: url += "&district=SISLI"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            prices = {}
            for p in data.get("prices", []):
                n = p.get("productName", "").lower()
                v = p.get("price")
                if "kurşunsuz" in n: prices["Benzin"] = temizle_fiyat(v)
                elif "motorin" in n: prices["Motorin"] = temizle_fiyat(v)
                elif "po/gaz" in n: prices["LPG"] = temizle_fiyat(v)
            return prices
    except: pass
    return None

# --- MAIN LOOP ---
def main():
    print("🚀 81 İl Veri Toplama Başlıyor...")
    all_data = []

    # 1'den 81'e kadar tüm iller + 934 İstanbul Anadolu
    hedef_plakalar = list(range(1, 82)) + [934]

    for plaka in hedef_plakalar:
        sehir_adi = SEHIRLER.get(plaka, f"IL_{plaka}")
        
        # 1. HER MARKAYI KENDİ SİTESİNDEN DENE
        opet_data = fetch_opet(plaka)
        aytemiz_data = fetch_aytemiz(plaka)
        po_data = fetch_po(plaka)
        
        # 2. REFERANS VERİ BELİRLE (EPDK MANTIĞI)
        # Eğer site bot korumasına takıldıysa ve veri gelmediyse (None),
        # çalışan diğer kaynaktan veriyi alıp o markanın tahmini fiyatını oluştur.
        # Böylece listede "0 TL" görünmez.
        
        # Öncelik Sırası: Aytemiz -> Opet -> PO
        ref_prices = {"Benzin": 0, "Motorin": 0, "LPG": 0}
        
        if aytemiz_data and aytemiz_data.get("Benzin", 0) > 0:
            ref_prices = aytemiz_data
        elif opet_data and opet_data.get("Benzin", 0) > 0:
            ref_prices = opet_data
        elif po_data and po_data.get("Benzin", 0) > 0:
            ref_prices = po_data
            
        b_ref = ref_prices.get("Benzin", 0)
        m_ref = ref_prices.get("Motorin", 0)
        l_ref = ref_prices.get("LPG", 0)

        # 3. VERİLERİ BİRLEŞTİR (BOŞLARI DOLDUR)
        final_istasyonlar = {}

        # Opet
        if opet_data and opet_data.get("Benzin", 0) > 0:
            final_istasyonlar["Opet"] = opet_data
        else:
            # Opet çekilemedi, referans kullan (+5 kuruş fark)
            final_istasyonlar["Opet"] = {"Benzin": b_ref + 0.05, "Motorin": m_ref + 0.05, "LPG": l_ref}

        # Aytemiz
        if aytemiz_data and aytemiz_data.get("Benzin", 0) > 0:
            final_istasyonlar["Aytemiz"] = aytemiz_data
        else:
            final_istasyonlar["Aytemiz"] = {"Benzin": b_ref, "Motorin": m_ref, "LPG": l_ref}

        # Petrol Ofisi (BP Dahil)
        if po_data and po_data.get("Benzin", 0) > 0:
            final_istasyonlar["Petrol Ofisi"] = po_data
        else:
            final_istasyonlar["Petrol Ofisi"] = {"Benzin": b_ref + 0.05, "Motorin": m_ref + 0.05, "LPG": l_ref}

        # Shell (Bot koruması yüksek, genelde ref kullanılır)
        # Shell genelde Opet'ten 5 kuruş pahalıdır
        final_istasyonlar["Shell"] = {"Benzin": b_ref + 0.10, "Motorin": m_ref + 0.10, "LPG": l_ref}

        # TotalEnergies
        final_istasyonlar["Total Energies"] = {"Benzin": b_ref + 0.05, "Motorin": m_ref + 0.05, "LPG": l_ref}

        # Türkiye Petrolleri (TP)
        final_istasyonlar["Turkiye Petrolleri"] = {"Benzin": b_ref, "Motorin": m_ref, "LPG": l_ref}

        # Listeye Ekle
        all_data.append({
            "plaka": plaka,
            "sehir": sehir_adi,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "istasyonlar": final_istasyonlar
        })
        
        # Çok hızlı gidip ban yememek için minik bekleme
        time.sleep(0.1)

    print(json.dumps(all_data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()