# 🔔 Er Yazılım • Okul Zili & Tören Yönetim Sistemi

[![Platform](https://img.shields.io/badge/Platform-Pardus%20%7C%20Linux%20%7C%20Windows-blue.svg)](https://github.com)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%20v3-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stabil%20v2.7.0-brightgreen.svg)](https://github.com)

**Er Yazılım Okul Zili & Tören Yönetim Sistemi**, Milli Eğitim Bakanlığı (MEB) müfredatına, ilkokul, ortaokul ve liselerin günlük zil, tören, anons ve teneffüs müzik yayını ihtiyaçlarına göre tasarlanmış açık kaynaklı, modern ve kararlı bir masaüstü uygulamasıdır.

Pardus, Lubuntu, Ubuntu, Debian ve Windows 7/10/11 sistemlerinde sorunsuz çalışır.

---

## ✨ Temel Özellikler

- 🎙️ **Yapay Zeka Anons Stüdyosu (Yeni!):**
  - Mikrofon veya harici kayda gerek olmadan doğrudan program içinden anons metnini yazıp seslendirme.
  - Doğal Türkçe yapay zeka modelleri (Kadın & Erkek Öğretmen tonlamaları).
  - İlkokul için neşeli/tatlı tonlama, konuşma hızı ve duygu ayarları.
  - Dinleyip önizleme ve tek tıkla canlı duyuru paneline ekleme.

- ⏰ **Akıllı Zil Çizelgesi:**
  - 7 gün bağımsız programlama (Hafta İçi, Hafta Sonu, Kurslar).
  - Öğrenci Zili, Öğretmen Zili, Teneffüs Çıkış Zili ve Gün Sonu Çıkış Zili ayrımı.
  - Tek tıkla günün programını haftaya kopyalama ve Sihirbaz ile otomatik ders saatleri üretme.
  - JSON formatında **Çizelge Yedekleme / Dışa Aktar** ve **İçe Aktarma**.

- 🔕 **Sınav / Sessiz Mod:**
  - Deneme sınavları, LGS, YKS ve ortak sınav günlerinde tek tıkla zilleri susturabilme.
  - Durum çubuğunda canlı kırmızı sınav modu uyarısı ve geri sayım.

- 📻 **Teneffüs Müzik Çaları & Okul Radyosu:**
  - İstediğiniz klasörden müzikleri otomatik veya manuel çalma.
  - Karışık (Shuffle) ve Sıralı çalma modları.
  - Ana ekranda mini oynatıcı ve özel Müzik Çalar sekmesi.
  - Zil çaldığında müziği otomatik durdurma ve zil bitiminde devam etme.

- 🇹🇷 **Resmi Tören & Anma Modülü:**
  - İstiklal Marşı, 1 Dakika / 2 Dakika Saygı Duruşu ve Deprem/Sivil Savunma Sireni.
  - Klavyeden özelleştirilebilir hızlı kısayol tuşları (`F1`-`F12`, `Space`).

- 📢 **Özel Sesli Anonslar:**
  - "Toplantı Duyurusu", "Tören Çağrısı", "Yağmur Uyarısı" vb. anonsları tek tıkla yayınlama.
  - Yeni anons ekleme, düzenleme ve dosya atama desteği.

- 🎛️ **Gelişmiş Ses Kartı / Amfi Yönlendirme:**
  - Çoklu ses kartı desteği: Zili doğrudan amfiye bağlı ses çıkışına yönlendirebilme.
  - Zil seviyesi ve teneffüs müzik seviyesini ayrı ayrı ayarlayabilme.

---

## ⌨️ Klavye Kısayolları

| Tuş | Fonksiyon |
| :---: | :--- |
| **Space (Boşluk)** | Çalan tüm sesleri / müzikleri anında sustur (**Acil Durdur**) |
| **F9** | 🇹🇷 İstiklal Marşı'nı Başlat |
| **F10** | ⏱️ Saygı Duruşu + İstiklal Marşı |
| **F11** | 🚨 Sivil Savunma / Deprem Sireni |
| **F8** | 🔕 Sınav Modunu Aç / Kapat |

*(Tüm kısayol tuşları **Sistem Ayarları** sekmesinden değiştirilebilir.)*

---

## 📥 Kurulum

### 🐧 Linux (Pardus / Ubuntu / Debian / Lubuntu)

#### 1. `.deb` Paketi ile Kurulum (Önerilen)
Releases sayfasından indirilen `.deb` paketine çift tıklayarak veya terminalden:
```bash
sudo dpkg -i okul-zili_2.6.0_all.deb
sudo apt-get install -f   # Eksik bağımlılıkları tamamlar
```

#### 2. Kaynak Koddan Çalıştırma:
```bash
sudo apt update
sudo apt install python3 python3-tk python3-pil python3-pil.imagetk mpg123
python3 okul_zili.py
```

---

### 🪟 Windows (7 / 10 / 11)

#### 1. Kurulumsuz (Portable) EXE:
Releases bölümünden **`OkulZili-v2.6.0-Windows-Portable.zip`** dosyasını indirin, klasöre çıkartın ve **`OkulZili.exe`** dosyasına çift tıklayarak çalıştırın.

#### 2. Kaynak Koddan Çalıştırma:
```cmd
pip install pillow PyQt5 edge-tts
python okul_zili.py
```

---

## 🛠️ Kendiniz Paketleyin

### Debian (.deb) Paketi Üretme (Windows veya Linux'ta):
```bash
python build_deb.py
```
*(Harici hiçbir Linux aracına ihtiyaç duymadan geçerli standart `.deb` paketi üretir.)*

### Windows (.exe) Paketi Üretme:
```cmd
python build_windows.py
# veya
build_exe.bat
```

---

## 📄 Lisans

Bu proje **GNU General Public License v3.0 (GPL-3.0)** ile lisanslanmıştır. Eğitim kurumlarında ve ticari olmayan tüm ortamlarda özgürce kullanılabilir, dağıtılabilir ve geliştirilebilir.
