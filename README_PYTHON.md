# 🔔 E-Zil • Okul Zil ve Tören Sistemi (Python Sürümü)

Bu sürüm, **Lubuntu LXQt (1.4.0)**, eski bilgisayarlar ve düşük donanımlı (2 GB RAM) sistemlerde çökmeyecek, **ultra hafif (~20 MB RAM)** ve kesintisiz çalışacak şekilde geliştirilmiştir.

---

## 🌟 Öne Çıkan Özellikler

1. **Canlı Durum & Geri Sayım:**
   * Büyük dijital saat, tarih ve gün bilgisi.
   * Bir sonraki zilin çalmasına kalan süreyi **dakika ve saniye bazında canlı geri sayım**.
2. **Resmi Tören & Acil Durum Butonları (Tek Tuşla Çalma):**
   * 🇹🇷 İstiklal Marşı
   * ⏱️ Saygı Duruşu + İstiklal Marşı
   * 📯 Saygı Duruşu (Ti Sesi)
   * 🚨 **Acil Durum / Siren** (Deprem, yangın veya tahliye anonsu)
3. **🛑 Acil Durdurma Butonu:** Çalan zili, marşı veya yanlışlıkla başlatılan anonsu anında kesebilme.
4. **⚡ Otomatik Çizelge Sihirbazı:**
   * 1. ders saati, ders süresi, teneffüs süresi ve öğle arası girilerek **tüm haftalık zil programını 1 saniyede otomatik oluşturma**.
5. **Ses Motoru Güvenliği:**
   * Sesleri arka planda izole hafif `mpv` veya `ffmpeg` üzerinden çalar. Ses dosyasında bozukluk olsa dahi arayüz asla çökmez.
6. **Teneffüs Müzik Yayını (Opsiyonel):**
   * Teneffüs başladığında seçilen bir müzik klasöründen arka planda hafif müzik çalar, ders zili çaldığında müziği otomatik durdurur.
7. **Hafif Bellek Tüketimi:**
   * Python 3 + `tkinter` mimarisi sayesinde sadece **~15-20 MB RAM** kullanır.

---

## 💻 Lubuntu / Linux Kurulumu

Eski laptopunuzda terminali (LXTerminal) açıp proje klasörüne gidin ve şu komutu çalıştırın:

```bash
bash kurulum_ve_calistir.sh
```

Bu script:
1. Gerekli kütüphaneleri (`python3-tk`, `mpv`, `ffmpeg`) otomatik kurar.
2. Dahili sesleri (`musics/e-zil-ses`) `~/.config/okul_zili/sesler` konumuna kopyalar.
3. Masaüstünüze ve Uygulama Menünüze **"Okul Zili"** kısayolu ekler.
4. Bilgisayar her açıldığında otomatik başlama ayarını yapar.

---

## 🚀 Manuel Çalıştırma

İsterseniz hiçbir şey yüklemeden doğrudan şu komutla da başlatabilirsiniz:

```bash
python3 okul_zili.py
```
