cat << 'EOF' > ~/okul_zili_gui.py
import os
import json
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DATA_FILE = os.path.expanduser("~/zil_ayarlari_v2.json")
DEFAULT_SES_DIR = "/home/okul/e-zil-ses/Ses"

VARSAYILAN_AYARLAR = {
    "sesler": {
        "ogrenci": os.path.join(DEFAULT_SES_DIR, "muzik1.mp3") if os.path.exists(os.path.join(DEFAULT_SES_DIR, "muzik1.mp3")) else "",
        "ogretmen": os.path.join(DEFAULT_SES_DIR, "ogretmenanons.mp3") if os.path.exists(os.path.join(DEFAULT_SES_DIR, "ogretmenanons.mp3")) else "",
        "cikis": os.path.join(DEFAULT_SES_DIR, "muzik2.mp3") if os.path.exists(os.path.join(DEFAULT_SES_DIR, "muzik2.mp3")) else ""
    },
    "program": [
        {"saat": "08:40", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "08:50", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "09:30", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "09:40", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "09:50", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "10:30", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "10:40", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "10:50", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "11:30", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "11:40", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "11:50", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)"},
        {"saat": "12:30", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)"}
    ]
}

TUR_ISIMLERI = {
    "ogrenci": "Öğrenci Giriş",
    "ogretmen": "Öğretmen Giriş",
    "cikis": "Teneffüs / Çıkış"
}

def ayar_oku():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return VARSAYILAN_AYARLAR

def ayar_kaydet(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class OkulZilAppGelistirilmis:
    def __init__(self, root):
        self.root = root
        self.root.title("Gelişmiş Okul Zil Sistemi")
        self.root.geometry("640x620")
        self.root.minsize(580, 560)

        self.ayarlar = ayar_oku()
        self.calinanlar = set()

        self.arayuz_kur()

        self.th = threading.Thread(target=self.zamanlayici_dongusu, daemon=True)
        self.th.start()

    def arayuz_kur(self):
        # 1. Ses Dosyaları Bölümü
        f_sesler = ttk.LabelFrame(self.root, text="Zil Sesleri Tanımları", padding=10)
        f_sesler.pack(fill="x", padx=10, pady=5)

        self.ses_etiketleri = {}
        for i, (tur_kod, tur_ad) in enumerate(TUR_ISIMLERI.items()):
            row = ttk.Frame(f_sesler)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{tur_ad}:", width=16, font=("Helvetica", 9, "bold")).pack(side="left")
            lbl = ttk.Label(row, text=os.path.basename(self.ayarlar["sesler"].get(tur_kod, "")) or "Seçilmedi", foreground="#0055aa")
            lbl.pack(side="left", fill="x", expand=True)
            self.ses_etiketleri[tur_kod] = lbl

            ttk.Button(row, text="Seç", width=6, command=lambda t=tur_kod: self.ses_dosyasi_sec(t)).pack(side="right", padx=2)
            ttk.Button(row, text="▶ Çal", width=6, command=lambda t=tur_kod: self.ses_cal(t)).pack(side="right", padx=2)

        # 2. Zil Saati Ekleme Bölümü
        f_ekle = ttk.LabelFrame(self.root, text="Yeni Zil Ekle", padding=10)
        f_ekle.pack(fill="x", padx=10, pady=5)

        ttk.Label(f_ekle, text="Saat (SS:DD):").pack(side="left", padx=2)
        self.ent_saat = ttk.Entry(f_ekle, width=7, font=("Helvetica", 11))
        self.ent_saat.insert(0, "08:40")
        self.ent_saat.pack(side="left", padx=5)

        ttk.Label(f_ekle, text="Zil Türü:").pack(side="left", padx=2)
        self.cmb_tur = ttk.Combobox(f_ekle, values=list(TUR_ISIMLERI.values()), state="readonly", width=14)
        self.cmb_tur.current(0)
        self.cmb_tur.pack(side="left", padx=5)

        ttk.Label(f_ekle, text="Gün:").pack(side="left", padx=2)
        self.cmb_gun = ttk.Combobox(f_ekle, values=["Hafta İçi (Pzt-Cum)", "Pazartesi-Perşembe", "Sadece Cuma"], state="readonly", width=18)
        self.cmb_gun.current(0)
        self.cmb_gun.pack(side="left", padx=5)

        ttk.Button(f_ekle, text="➕ Ekle", command=self.zil_ekle).pack(side="right", padx=5)

        # 3. Tablo (Zil Programı)
        f_tablo = ttk.LabelFrame(self.root, text="Haftalık Zil Zaman Çizelgesi", padding=10)
        f_tablo.pack(fill="both", expand=True, padx=10, pady=5)

        kolonlar = ("saat", "tur", "gunler")
        self.tree = ttk.Treeview(f_tablo, columns=kolonlar, show="headings", selectmode="browse")
        self.tree.heading("saat", text="Zil Saati")
        self.tree.heading("tur", text="Zil Türü / Melodi")
        self.tree.heading("gunler", text="Uygulanan Günler")
        self.tree.column("saat", width=90, anchor="center")
        self.tree.column("tur", width=180, anchor="center")
        self.tree.column("gunler", width=220, anchor="center")

        scroll = ttk.Scrollbar(f_tablo, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Buton Barı (Sil vb.)
        f_alt_btn = ttk.Frame(self.root)
        f_alt_btn.pack(fill="x", padx=10, pady=2)
        ttk.Button(f_alt_btn, text="🗑️ Seçili Zili Sil", command=self.zil_sil).pack(side="left")

        # Durum Barı
        self.lbl_durum = ttk.Label(self.root, text="Sistem devrede. Ziller bekleniyor...", relief="sunken", padding=6)
        self.lbl_durum.pack(fill="x", side="bottom")

        self.tabloyu_doldur()

    def tabloyu_doldur(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.ayarlar["program"].sort(key=lambda x: x["saat"])
        for item in self.ayarlar["program"]:
            tur_ad = TUR_ISIMLERI.get(item["tur"], item["tur"])
            self.tree.insert("", "end", values=(item["saat"], tur_ad, item["gunler"]))

    def ses_dosyasi_sec(self, tur_kod):
        yol = filedialog.askopenfilename(
            title=f"{TUR_ISIMLERI[tur_kod]} Ses Dosyasını Seçin",
            initialdir=DEFAULT_SES_DIR,
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.ogg")]
        )
        if yol:
            self.ayarlar["sesler"][tur_kod] = yol
            ayar_kaydet(self.ayarlar)
            self.ses_etiketleri[tur_kod].config(text=os.path.basename(yol))

    def ses_cal(self, tur_kod):
        yol = self.ayarlar["sesler"].get(tur_kod, "")
        if yol and os.path.exists(yol):
            threading.Thread(target=lambda: os.system(f'mpv --no-video "{yol}"'), daemon=True).start()
        else:
            messagebox.showwarning("Uyarı", f"{TUR_ISIMLERI[tur_kod]} için ses dosyası bulunamadı!")

    def zil_ekle(self):
        saat = self.ent_saat.get().strip()
        try:
            datetime.strptime(saat, "%H:%M")
        except ValueError:
            messagebox.showerror("Hata", "Saat formatı SS:DD şeklinde olmalıdır (Örn: 09:15)")
            return

        secilen_tur_ad = self.cmb_tur.get()
        tur_kod = [k for k, v in TUR_ISIMLERI.items() if v == secilen_tur_ad][0]
        gun = self.cmb_gun.get()

        # Aynı saat ve gün varsa mükerrer ekleme
        for z in self.ayarlar["program"]:
            if z["saat"] == saat and z["gunler"] == gun:
                messagebox.showinfo("Bilgi", "Bu saat ve gün kombinasyonu zaten listede var.")
                return

        self.ayarlar["program"].append({"saat": saat, "tur": tur_kod, "gunler": gun})
        ayar_kaydet(self.ayarlar)
        self.tabloyu_doldur()

    def zil_sil(self):
        secili = self.tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz bir zil satırını seçin.")
            return
        degerler = self.tree.item(secili[0])["values"]
        saat = degerler[0]
        gunler = degerler[2]

        self.ayarlar["program"] = [z for z in self.ayarlar["program"] if not (z["saat"] == saat and z["gunler"] == gunler)]
        ayar_kaydet(self.ayarlar)
        self.tabloyu_doldur()

    def zamanlayici_dongusu(self):
        while True:
            now = datetime.now()
            su_an = now.strftime("%H:%M")
            haftanin_gunu = now.weekday()  # 0: Pzt, 1: Sal, ..., 4: Cum, 5: Cmt, 6: Paz

            if haftanin_gunu < 5:  # Sadece hafta içi
                for z in self.ayarlar["program"]:
                    saat = z["saat"]
                    gun_kurali = z["gunler"]

                    uygun_mu = False
                    if gun_kurali == "Hafta İçi (Pzt-Cum)":
                        uygun_mu = True
                    elif gun_kurali == "Pazartesi-Perşembe" and haftanin_gunu in [0, 1, 2, 3]:
                        uygun_mu = True
                    elif gun_kurali == "Sadece Cuma" and haftanin_gunu == 4:
                        uygun_mu = True

                    if uygun_mu and su_an == saat:
                        anahtar = f"{su_an}_{z['tur']}"
                        if anahtar not in self.calinanlar:
                            self.calinanlar.add(anahtar)
                            tur_adi = TUR_ISIMLERI.get(z['tur'], '')
                            self.lbl_durum.config(text=f"Son Çalan: {su_an} ({tur_adi})")
                            self.ses_cal(z['tur'])

                # Dakika değiştiğinde geçmiş kilitleri temizle
                if len(self.calinanlar) > 0:
                    gecerli_saatler = {z["saat"] for z in self.ayarlar["program"]}
                    if su_an not in gecerli_saatler:
                        self.calinanlar.clear()
                        self.lbl_durum.config(text="Sistem devrede. Sıradaki zil bekleniyor...")

            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = OkulZilAppGelistirilmis(root)
    root.mainloop()
EOF


