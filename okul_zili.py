#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 Er Yazılım • Okul Zil Sistemi
 Lubuntu LXQt ve Düşük Donanımlı (2 GB RAM) Sistemler İçin Optimize Edilmiştir
 Hem Windows Hem Linux Ortamlarında Sorunsuz Çalışır
=============================================================================
"""

import os
import sys
import json
import time
import shutil
import random
import threading
import subprocess
import warnings
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Failed to disconnect.*")

def _global_excepthook(exc_type, exc_value, exc_traceback):
    try:
        print(f"[HATA / EXCEPTION] {exc_type.__name__}: {exc_value}")
    except Exception:
        pass

sys.excepthook = _global_excepthook
if hasattr(threading, "excepthook"):
    threading.excepthook = lambda args: _global_excepthook(args.exc_type, args.exc_value, args.exc_traceback)

# Uygulama Dizinleri
APP_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser("~")

if sys.platform == "win32":
    DATA_DIR = os.path.join(os.environ.get("APPDATA", HOME_DIR), "okul_zili")
else:
    DATA_DIR = os.path.join(HOME_DIR, ".config", "okul_zili")

CONFIG_FILE = os.path.join(DATA_DIR, "ayarlar.json")
SES_HEDEF_DIR = os.path.join(DATA_DIR, "sesler")
ANONSLAR_USER_DIR = os.path.join(DATA_DIR, "anonslar")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SES_HEDEF_DIR, exist_ok=True)
os.makedirs(ANONSLAR_USER_DIR, exist_ok=True)

# Dahili ses dosyalarının varsayılan yolları
DEFAULT_SOUNDS_CANDIDATES = [
    os.path.join(APP_DIR, "musics", "e-zil-ses", "Anonslar"),
    os.path.join(APP_DIR, "musics", "e-zil-ses", "Ses"),
    os.path.join(APP_DIR, "musics", "e-zil-ses", "Resmi"),
    os.path.join(APP_DIR, "musics", "e-zil-ses"),
    os.path.join(APP_DIR, "musics"),
    "/usr/share/okul-zili/musics/e-zil-ses/Anonslar",
    "/usr/share/okul-zili/musics/e-zil-ses/Ses",
    "/usr/share/okul-zili/musics/e-zil-ses/Resmi",
    "/usr/share/okul-zili/musics",
    "/usr/share/e-zil/musics",
    "/usr/share/okul_zili/sesler",
    os.path.join(HOME_DIR, "e-zil-ses"),
    ANONSLAR_USER_DIR,
    SES_HEDEF_DIR
]

def varsayilan_ses_bul(alt_yol):
    """Sistemde veya proje içinde ses dosyasını arar."""
    parcalar = alt_yol.replace("\\", "/").split("/")
    for base in DEFAULT_SOUNDS_CANDIDATES:
        tam_yol = os.path.normpath(os.path.join(base, *parcalar))
        if os.path.exists(tam_yol):
            return tam_yol
    return ""

def anons_kayit_dizini_getir():
    """Linux ve Windows'ta her zaman güvenli yazma izni olan anons klasörünü döndürür."""
    # 1. Proje içindeki musics/e-zil-ses/Anonslar yazılabilir mi?
    yerel_anons_dir = os.path.join(APP_DIR, "musics", "e-zil-ses", "Anonslar")
    if os.path.exists(yerel_anons_dir) and os.access(yerel_anons_dir, os.W_OK):
        return yerel_anons_dir
    yerel_musics = os.path.join(APP_DIR, "musics")
    if os.path.exists(yerel_musics) and os.access(yerel_musics, os.W_OK):
        return yerel_musics
    # 2. Linux /usr/share altında kuruluysa kullanıcı ev dizini altındaki anonslar klasörünü döndür
    os.makedirs(ANONSLAR_USER_DIR, exist_ok=True)
    return ANONSLAR_USER_DIR

def ai_anons_sentezle(metin, cikti_yolu, ses_modeli="tr-TR-EmelNeural", rate="+0%", pitch="+0Hz"):
    """
    edge-tts kullanarak metni sese dönüştürür ve cikti_yolu'na kaydeder.
    SSL sertifikası hatalarına karşı esnek (MEB / antivirüs SSL inspection korumalı) çalışır.
    """
    import ssl
    import asyncio
    try:
        import edge_tts
        import edge_tts.communicate
        import edge_tts.voices
        
        # SSL sertifika doğrulamasını bypass et (Okul MEB ağı / self-signed proxy uyumu)
        ssl_ctx = ssl._create_unverified_context()
        edge_tts.communicate._SSL_CTX = ssl_ctx
        if hasattr(edge_tts, "voices") and hasattr(edge_tts.voices, "_SSL_CTX"):
            edge_tts.voices._SSL_CTX = ssl_ctx
            
        async def _uret():
            communicate = edge_tts.Communicate(metin, ses_modeli, rate=rate, pitch=pitch)
            await communicate.save(cikti_yolu)
            
        asyncio.run(_uret())
        return True, "Başarılı"
    except ImportError:
        return False, "edge-tts kütüphanesi kurulu değil. Lütfen 'pip install edge-tts' çalıştırın."
    except Exception as e:
        return False, f"Ses sentezleme hatası: {e}"

# Zil Türleri ve İsimleri
ZIL_TURLERI = {
    "ogrenci": "Öğrenci Giriş Zili",
    "ogretmen": "Öğretmen Giriş Zili",
    "cikis": "Teneffüs Zili",
    "gun_sonu_cikis": "🏠 Okul Çıkış / Gün Sonu Müziği",
    "istiklal": "İstiklal Marşı",
    "saygi_istiklal": "Saygı Duruşu + İstiklal",
    "saygi": "Saygı Duruşu (Ti Sesi)",
    "siren": "Acil Durum / Siren"
}

GUN_SECENEKLERI = [
    "Hafta İçi (Pzt-Cum)",
    "Pazartesi-Perşembe",
    "Sadece Cuma",
    "Haftanın Her Günü",
    "Pazartesi",
    "Salı",
    "Çarşamba",
    "Perşembe",
    "Cuma",
    "Cumartesi",
    "Pazar"
]

VARSAYILAN_AYARLAR = {
    "genel": {
        "ses_seviyesi": 90,
        "teneffus_ses_seviyesi": 50,
        "teneffus_muzik_aktif": False,
        "arka_planda_calis": False,
        "ses_motoru": "otomatik",
        "ses_aygiti": "default",
        "sessiz_mod": False
    },
    "kisayollar": {
        "istiklal": "F9",
        "saygi_istiklal": "F10",
        "siren": "F11",
        "durdur": "Space",
        "sessiz_mod": "F8"
    },
    "anonslar": [
        {"id": "anons_1", "baslik": "📢 Toplantı Duyurusu", "dosya": ""},
        {"id": "anons_2", "baslik": "🇹🇷 Tören Çağrısı", "dosya": ""},
        {"id": "anons_3", "baslik": "☔ Yağmur / İçeri Giriş", "dosya": ""}
    ],
    "sesler": {
        "ogrenci": varsayilan_ses_bul("Ses/muzik1.mp3") or varsayilan_ses_bul("Ses/ogrencianons.mp3"),
        "ogretmen": varsayilan_ses_bul("Ses/ogretmenanons.mp3") or varsayilan_ses_bul("Ses/muzik1.mp3"),
        "cikis": varsayilan_ses_bul("Ses/muzik2.mp3"),
        "gun_sonu_cikis": varsayilan_ses_bul("Ses/muzik3.mp3") or varsayilan_ses_bul("Ses/muzik2.mp3"),
        "istiklal": varsayilan_ses_bul("Resmi/istiklalmarsi.mp3"),
        "saygi_istiklal": varsayilan_ses_bul("Resmi/saygi1dakika-istiklalmarsi.mp3") or varsayilan_ses_bul("Resmi/saygi2dakika-istiklalmarsi.mp3"),
        "saygi": varsayilan_ses_bul("Resmi/saygi-1dakika.mp3"),
        "siren": varsayilan_ses_bul("Resmi/siren30saniye.mp3"),
        "teneffus_klasoru": ""
    },
    "program": [
        {"saat": "08:28", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "08:30", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "09:10", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "09:18", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "09:20", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "10:00", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "10:08", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "10:10", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "10:50", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "10:58", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "11:00", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "11:40", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "12:28", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "12:30", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "13:10", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "13:18", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "13:20", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "14:00", "tur": "cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "14:08", "tur": "ogrenci", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "14:10", "tur": "ogretmen", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True},
        {"saat": "14:50", "tur": "gun_sonu_cikis", "gunler": "Hafta İçi (Pzt-Cum)", "aktif": True}
    ]
}


class SoundPlayer:
    """Hafif, sessiz, ultra kararlı ve çökmeyen ses oynatma motoru (Linux & Windows).
    Pygame SDL2 ve Çoklu Çıkış Motoru Desteği İçerir."""
    def __init__(self):
        self.process = None
        self.teneffus_process = None
        self.lock = threading.RLock()
        self.currently_playing_title = ""
        self.pygame_available = False
        self._init_pygame()
        self.available_engines = self._detect_engines()

    def _init_pygame(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                pygame.mixer.set_num_channels(8)
            self.pygame_available = True
            self.chan_zil = pygame.mixer.Channel(0)
            self.chan_teneffus = pygame.mixer.Channel(1)
        except Exception as e:
            self.pygame_available = False
            print(f"[PYGAME INIT UYARISI] {e}")

    def _detect_engines(self):
        engines = []
        if self.pygame_available:
            engines.append("pygame")
        for cmd in ["mpv", "ffplay", "mplayer", "cvlc", "paplay", "aplay"]:
            if shutil.which(cmd):
                engines.append(cmd)
        if sys.platform == "win32":
            engines.append("windows_media")
        return engines

    def get_audio_devices(self):
        """Sistemde mevcut olan tüm ses çıkış aygıtlarını listeler."""
        devices = [("Varsayılan Sistem Çıkışı", "default")]

        # 1. mpv --audio-device=help (Linux & Windows)
        if shutil.which("mpv"):
            try:
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                out = subprocess.check_output(["mpv", "--audio-device=help"], stderr=subprocess.STDOUT, creationflags=flags, text=True, timeout=3)
                for line in out.splitlines():
                    line = line.strip()
                    if line.startswith("'") and " - " in line:
                        parts = line.split(" - ", 1)
                        dev_id = parts[0].strip("'")
                        dev_name = parts[1].strip()
                        if dev_id != "auto" and dev_name not in [dev[0] for dev in devices]:
                            devices.append((f"{dev_name} ({dev_id})", dev_id))
            except Exception:
                pass

        # 2. Windows WinMM / DirectSound
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                winmm = ctypes.windll.winmm
                num_devs = winmm.waveOutGetNumDevs()
                class WAVEOUTCAPS(ctypes.Structure):
                    _fields_ = [
                        ('wMid', wintypes.WORD), ('wPid', wintypes.WORD),
                        ('vDriverVersion', wintypes.UINT), ('szPname', ctypes.c_wchar * 32),
                        ('dwFormats', wintypes.DWORD), ('wChannels', wintypes.WORD),
                        ('wReserved1', wintypes.WORD), ('dwSupport', wintypes.DWORD),
                    ]
                for i in range(num_devs):
                    caps = WAVEOUTCAPS()
                    if winmm.waveOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                        name = caps.szPname.strip()
                        if name and name not in [dev[0] for dev in devices]:
                            devices.append((name, name))
            except Exception:
                pass

        return devices

    def get_best_engine(self, preferred="otomatik"):
        if preferred != "otomatik" and preferred in self.available_engines:
            return preferred
        if self.pygame_available:
            return "pygame"
        for eng in ["mpv", "ffplay", "mplayer", "cvlc", "paplay", "aplay", "windows_media"]:
            if eng in self.available_engines:
                return eng
        return None

    def play(self, file_path, volume=90, title="Ses", on_finish=None, is_teneffus=False, preferred="otomatik", target_device="default"):
        file_path = os.path.normpath(file_path)
        if not file_path or not os.path.exists(file_path):
            print(f"[SES HATASI] Dosya bulunamadı: {file_path}")
            return False

        with self.lock:
            if not is_teneffus:
                self.stop_teneffus()
                self.stop()
            else:
                self.stop_teneffus()

            vol_val = max(0, min(100, int(volume)))

            # 1. Pygame SDL2 Audio (En Kararlı, Sıfır Çökme, Bağımsız Kanallar)
            if self.pygame_available and (preferred in ["otomatik", "pygame"] or not self.get_best_engine(preferred)):
                try:
                    import pygame
                    sound = pygame.mixer.Sound(os.path.abspath(file_path))
                    sound.set_volume(vol_val / 100.0)
                    target_chan = self.chan_teneffus if is_teneffus else self.chan_zil
                    target_chan.stop()
                    target_chan.play(sound)
                    if not is_teneffus:
                        self.currently_playing_title = title

                    def monitor_pygame(chan, is_ten):
                        try:
                            while chan.get_busy():
                                time.sleep(0.05)
                        except Exception:
                            pass
                        with self.lock:
                            if not is_ten:
                                self.currently_playing_title = ""
                        if on_finish:
                            try:
                                on_finish()
                            except Exception:
                                pass

                    threading.Thread(target=monitor_pygame, args=(target_chan, is_teneffus), daemon=True).start()
                    return True
                except Exception as e:
                    print(f"[PYGAME OYNATMA HATASI] {e}")

            # 2. Standart Harici Oynatıcı Motorlar
            engine = self.get_best_engine(preferred=preferred)
            if not engine:
                print("[SES HATASI] Sistemde ses oynatıcı bulunamadı!")
                return False

            cmd = []
            if engine == "mpv":
                cmd = ["mpv", "--no-video", "--no-terminal", f"--volume={vol_val}"]
                if target_device and target_device != "default":
                    cmd.append(f"--audio-device={target_device}")
                cmd.append(file_path)
            elif engine == "ffplay":
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-volume", str(vol_val), file_path]
            elif engine == "mplayer":
                cmd = ["mplayer", "-really-quiet", "-volume", str(vol_val), file_path]
            elif engine == "cvlc":
                cmd = ["cvlc", "--play-and-exit", "--gain", str(vol_val / 100.0), file_path]
            elif engine == "paplay":
                cmd = ["paplay", file_path]
            elif engine == "aplay":
                cmd = ["aplay", "-q", file_path]
            elif engine == "windows_media":
                ps_script = f"""
                Add-Type -AssemblyName presentationCore
                $player = New-Object System.Windows.Media.MediaPlayer
                $player.Open([System.Uri]'{file_path}')
                $player.Volume = {vol_val / 100.0}
                $player.Play()
                $timeout = 0
                while ($player.NaturalDuration.HasTimeSpan -eq $false -and $timeout -lt 25) {{
                    Start-Sleep -Milliseconds 100
                    $timeout++
                }}
                if ($player.NaturalDuration.HasTimeSpan) {{
                    $sec = [math]::Ceiling($player.NaturalDuration.TimeSpan.TotalSeconds)
                    Start-Sleep -Seconds $sec
                }} else {{
                    Start-Sleep -Seconds 10
                }}
                $player.Stop()
                $player.Close()
                """
                cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]

            try:
                popen_kwargs = {
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL
                }
                if sys.platform == "win32":
                    popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

                proc = subprocess.Popen(cmd, **popen_kwargs)

                if is_teneffus:
                    self.teneffus_process = proc
                else:
                    self.process = proc
                    self.currently_playing_title = title

                def monitor_worker(p, is_ten):
                    try:
                        p.wait()
                    except Exception:
                        pass
                    with self.lock:
                        if is_ten and self.teneffus_process == p:
                            self.teneffus_process = None
                        elif not is_ten and self.process == p:
                            self.process = None
                            self.currently_playing_title = ""
                    if on_finish:
                        try:
                            on_finish()
                        except Exception:
                            pass

                th = threading.Thread(target=monitor_worker, args=(proc, is_teneffus), daemon=True)
                th.start()
                return True
            except Exception as e:
                print(f"[SES ÇALMA HATASI] {e}")
                return False

    def stop(self):
        with self.lock:
            if self.pygame_available and hasattr(self, "chan_zil"):
                try:
                    self.chan_zil.stop()
                except Exception:
                    pass
            if self.process:
                try:
                    self.process.kill()
                except Exception:
                    pass
                self.process = None
            self.currently_playing_title = ""

    def stop_teneffus(self):
        with self.lock:
            if self.pygame_available and hasattr(self, "chan_teneffus"):
                try:
                    self.chan_teneffus.stop()
                except Exception:
                    pass
            if self.teneffus_process:
                try:
                    self.teneffus_process.kill()
                except Exception:
                    pass
                self.teneffus_process = None

    def stop_all(self):
        self.stop()
        self.stop_teneffus()

    def is_playing(self):
        with self.lock:
            if self.pygame_available:
                try:
                    if self.chan_zil.get_busy() or self.chan_teneffus.get_busy():
                        return True
                except Exception:
                    pass
            return self.process is not None or self.teneffus_process is not None


class OkulZilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Er Yazılım • Okul Zil Sistemi")
        self.root.geometry("820x680")
        self.root.minsize(760, 600)

        # İkon yükleme
        self._ikon_yukle()

        self.player = SoundPlayer()
        self.ayarlar = self.ayarlari_yukle()
        self.calinanlar_set = set()
        self.son_calan_bilgi = "-"
        self.aktif_durum_metni = "Sistem Devrede"
        self.sessiz_mod = self.ayarlar.get("genel", {}).get("sessiz_mod", False)
        self.sessiz_mod_bitis = None
        self.sessiz_mod_aciklama = ""

        # Müzik Çalar / Okul Radyosu Durumu
        self.muzik_calma_listesi = []
        self.muzik_secili_indeks = -1
        self.muzik_caliyor = False
        self.muzik_modu = self.ayarlar.get("genel", {}).get("muzik_modu", "sirali")

        # Tema / Stil ayarları
        self._stil_kur()

        # Arayüzü oluştur
        self._arayuz_olustur()

        # Kısayolları bağla ve sessiz mod butonunu güncelle
        self._kisayollari_bagla()
        self._sessiz_mod_guncelle_ui()

        # Müzik listesini yükle
        self._muzik_listesini_yukle()

        # Otomatik ses dosyası kontrolü
        self._varsayilan_sesleri_kontrol_et()

        # Zamanlayıcı Döngüsünü Başlat
        self.calisiyor = True
        self.zamanlayici_thread = threading.Thread(target=self._zamanlayici_dongusu, daemon=True)
        self.zamanlayici_thread.start()

        # Periyodik GUI güncellemesi (1 saniye)
        self._gui_guncelle()

        # Kapatma protokolü
        self.root.protocol("WM_DELETE_WINDOW", self._on_kapat)

    def _ikon_yukle(self):
        for icon_name in ["ezil1.png", "ezil2.png", "ezil0.png"]:
            icon_path = os.path.join(APP_DIR, icon_name)
            if os.path.exists(icon_path):
                try:
                    img = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, img)
                    break
                except Exception:
                    pass

    def _stil_kur(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.c_bg = "#f4f6f9"
        self.c_card = "#ffffff"
        self.c_primary = "#1b4965"
        self.c_accent = "#62b6cb"
        self.c_danger = "#d90429"
        self.c_success = "#2b9348"
        self.c_warning = "#f77f00"
        self.c_text = "#2b2d42"

        self.root.configure(bg=self.c_bg)

        style.configure("TNotebook", background=self.c_bg)
        style.configure("TNotebook.Tab", font=("Helvetica", 10, "bold"), padding=[12, 6])
        style.configure("Card.TFrame", background=self.c_card, relief="raised")
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground=self.c_primary, background=self.c_card)
        style.configure("Clock.TLabel", font=("Helvetica", 28, "bold"), foreground=self.c_primary, background=self.c_card)
        style.configure("CountDown.TLabel", font=("Helvetica", 13, "bold"), foreground=self.c_danger, background=self.c_card)
        style.configure("Danger.TButton", font=("Helvetica", 10, "bold"), foreground="white", background=self.c_danger)
        style.configure("Success.TButton", font=("Helvetica", 10, "bold"), foreground="white", background=self.c_success)

    def ayarlari_yukle(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in VARSAYILAN_AYARLAR.items():
                        if k not in data:
                            data[k] = v
                        elif isinstance(v, dict):
                            for sub_k, sub_v in v.items():
                                if sub_k not in data[k]:
                                    data[k][sub_k] = sub_v
                    return data
            except Exception as e:
                print(f"Ayar okuma hatası: {e}")
        return json.loads(json.dumps(VARSAYILAN_AYARLAR))

    def ayarlari_kaydet(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.ayarlar, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {e}")

    def _varsayilan_sesleri_kontrol_et(self):
        degisiklik_oldu = False
        for tur, yol in list(self.ayarlar["sesler"].items()):
            if not yol or not os.path.exists(yol):
                yeni_yol = ""
                if tur == "ogrenci":
                    yeni_yol = varsayilan_ses_bul("Ses/muzik1.mp3") or varsayilan_ses_bul("Ses/ogrencianons.mp3")
                elif tur == "ogretmen":
                    yeni_yol = varsayilan_ses_bul("Ses/ogretmenanons.mp3") or varsayilan_ses_bul("Ses/muzik1.mp3")
                elif tur == "cikis":
                    yeni_yol = varsayilan_ses_bul("Ses/muzik2.mp3")
                elif tur == "gun_sonu_cikis":
                    yeni_yol = varsayilan_ses_bul("Ses/muzik3.mp3") or varsayilan_ses_bul("Ses/muzik2.mp3")
                elif tur == "istiklal":
                    yeni_yol = varsayilan_ses_bul("Resmi/istiklalmarsi.mp3")
                elif tur == "saygi_istiklal":
                    yeni_yol = varsayilan_ses_bul("Resmi/saygi1dakika-istiklalmarsi.mp3") or varsayilan_ses_bul("Resmi/saygi2dakika-istiklalmarsi.mp3")
                elif tur == "saygi":
                    yeni_yol = varsayilan_ses_bul("Resmi/saygi-1dakika.mp3")
                elif tur == "siren":
                    yeni_yol = varsayilan_ses_bul("Resmi/siren30saniye.mp3")

                if yeni_yol and os.path.exists(yeni_yol):
                    self.ayarlar["sesler"][tur] = yeni_yol
                    degisiklik_oldu = True

        if degisiklik_oldu:
            self.ayarlari_kaydet()

    def _arayuz_olustur(self):
        top_bar = tk.Frame(self.root, bg=self.c_primary, height=48)
        top_bar.pack(fill="x", side="top")

        lbl_logo = tk.Label(top_bar, text="🔔 ER YAZILIM • Okul Zil Sistemi", font=("Helvetica", 13, "bold"), fg="white", bg=self.c_primary)
        lbl_logo.pack(side="left", padx=15, pady=8)

        self.lbl_motor = tk.Label(top_bar, text=f"Ses Motoru: {self.player.get_best_engine() or 'Yok'}", font=("Helvetica", 9), fg="#e0e0e0", bg=self.c_primary)
        self.lbl_motor.pack(side="right", padx=15, pady=8)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_ana = ttk.Frame(self.tabs, padding=10)
        self.tab_program = ttk.Frame(self.tabs, padding=10)
        self.tab_muzik = ttk.Frame(self.tabs, padding=10)
        self.tab_sesler = ttk.Frame(self.tabs, padding=10)
        self.tab_anons_olustur = ttk.Frame(self.tabs, padding=10)
        self.tab_ayarlar = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.tab_ana, text="  🏠 Canlı Durum & Törenler  ")
        self.tabs.add(self.tab_program, text="  📅 Zil Çizelgesi  ")
        self.tabs.add(self.tab_muzik, text="  📻 Müzik Çalar (Radyo)  ")
        self.tabs.add(self.tab_sesler, text="  🎵 Sesler & Anonslar  ")
        self.tabs.add(self.tab_anons_olustur, text="  🎙️ Kendi Anonsunu Oluştur  ")
        self.tabs.add(self.tab_ayarlar, text="  ⚙️ Sistem Ayarları  ")

        self._kur_tab_ana()
        self._kur_tab_program()
        self._kur_tab_muzik()
        self._kur_tab_sesler()
        self._kur_tab_anons_olustur()
        self._kur_tab_ayarlar()

        self.status_bar = tk.Frame(self.root, bg="#e9ecef", height=28, relief="sunken", bd=1)
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(self.status_bar, text="Sistem aktif. Zamanlayıcı hazır.", font=("Helvetica", 9), bg="#e9ecef", fg="#495057")
        self.lbl_status.pack(side="left", padx=10, pady=4)

        self.lbl_calan = tk.Label(self.status_bar, text="", font=("Helvetica", 9, "bold"), bg="#e9ecef", fg=self.c_danger)
        self.lbl_calan.pack(side="right", padx=10, pady=4)

    # -------------------------------------------------------------
    # SEKME 1: CANLI DURUM & MANUEL TÖRENLER
    # -------------------------------------------------------------
    def _kur_tab_ana(self):
        pan_left = ttk.Frame(self.tab_ana)
        pan_left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        pan_right = ttk.Frame(self.tab_ana)
        pan_right.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # 1. KART: Dijital Saat
        f_saat = ttk.LabelFrame(pan_left, text="Canlı Saat ve Durum", padding=12)
        f_saat.pack(fill="x", pady=(0, 8))

        self.lbl_clock = ttk.Label(f_saat, text="00:00:00", style="Clock.TLabel", anchor="center")
        self.lbl_clock.pack(fill="x", pady=4)

        self.lbl_tarih = ttk.Label(f_saat, text="Pazartesi, 01 Ocak 2026", font=("Helvetica", 10), foreground="#6c757d", anchor="center")
        self.lbl_tarih.pack(fill="x")

        ttk.Separator(f_saat, orient="horizontal").pack(fill="x", pady=10)

        self.lbl_siradaki = ttk.Label(f_saat, text="Sıradaki Zil: Hesaplanıyor...", style="CountDown.TLabel", anchor="center", wraplength=340)
        self.lbl_siradaki.pack(fill="x", pady=2)

        self.lbl_kalan_sure = ttk.Label(f_saat, text="Kalan Süre: --:--", font=("Helvetica", 12, "bold"), foreground=self.c_primary, anchor="center")
        self.lbl_kalan_sure.pack(fill="x", pady=2)

        # 2. KART: Acil Durdurma, Sınav Modu ve Ses Seviyesi
        f_kontrol = ttk.LabelFrame(pan_left, text="Ses & Sınav Kontrolü", padding=10)
        f_kontrol.pack(fill="x", pady=(0, 8))

        btn_durdur = tk.Button(
            f_kontrol, text="🛑 ÇALAN SESİ ANINDA DURDUR", font=("Helvetica", 10, "bold"),
            bg=self.c_danger, fg="white", activebackground="#b7094c", activeforeground="white",
            relief="raised", bd=3, cursor="hand2", command=self.sesi_durdur
        )
        btn_durdur.pack(fill="x", ipady=6, pady=2)

        self.btn_sessiz_mod = tk.Button(
            f_kontrol, text="🔕 Sınav / Sessiz Modu Aç", font=("Helvetica", 10, "bold"),
            bg="#4a5568", fg="white", activebackground="#2d3748", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.toggle_sessiz_mod
        )
        self.btn_sessiz_mod.pack(fill="x", ipady=5, pady=4)

        f_vol = ttk.Frame(f_kontrol)
        f_vol.pack(fill="x", pady=4)
        ttk.Label(f_vol, text="Genel Ses:").pack(side="left", padx=4)
        init_vol = int(self.ayarlar["genel"].get("ses_seviyesi", 90))
        self.lbl_vol_val = ttk.Label(f_vol, text=f"%{init_vol}", width=5)
        self.scale_vol = ttk.Scale(f_vol, from_=0, to=100, orient="horizontal", command=self._on_vol_change)
        self.scale_vol.set(init_vol)
        self.scale_vol.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_vol_val.pack(side="right")

        # 3. KART (SOL): Mini Müzik Çalar / Okul Radyosu
        f_mini_muzik = ttk.LabelFrame(pan_left, text="📻 Okul Radyosu (Müzik Çalar)", padding=8)
        f_mini_muzik.pack(fill="x", pady=(0, 8))

        self.lbl_mini_muzik = ttk.Label(f_mini_muzik, text="Müzik Çalar: Durduruldu", font=("Helvetica", 9, "bold"), foreground="#1b4965", wraplength=340)
        self.lbl_mini_muzik.pack(fill="x", pady=(0, 4))

        f_mini_ctrl = ttk.Frame(f_mini_muzik)
        f_mini_ctrl.pack(fill="x", pady=2)

        btn_m_prev = ttk.Button(f_mini_ctrl, text="⏮", width=4, command=self.muzik_onceki)
        btn_m_prev.pack(side="left", padx=2)

        self.btn_mini_play = tk.Button(
            f_mini_ctrl, text="▶ Oynat", font=("Helvetica", 9, "bold"),
            bg="#2a9d8f", fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=1, cursor="hand2", width=8, command=self.muzik_oynat_veya_durdur
        )
        self.btn_mini_play.pack(side="left", padx=2)

        btn_m_stop = tk.Button(
            f_mini_ctrl, text="⏹ Durdur", font=("Helvetica", 9, "bold"),
            bg=self.c_danger, fg="white", activebackground="#b7094c", activeforeground="white",
            relief="raised", bd=1, cursor="hand2", width=8, command=self.muzik_durdur
        )
        btn_m_stop.pack(side="left", padx=2)

        btn_m_next = ttk.Button(f_mini_ctrl, text="⏭", width=4, command=self.muzik_sonraki)
        btn_m_next.pack(side="left", padx=2)

        self.btn_mini_mod = ttk.Button(f_mini_ctrl, text="🔁 Sıralı", width=8, command=self._muzik_modu_degistir)
        self.btn_mini_mod.pack(side="right", padx=2)

        # 4. KART (SOL ALT): Hızlı Özel Anonslar
        self.f_hizli_anons = ttk.LabelFrame(pan_left, text="📢 Özel Sesli Anonslar", padding=8)
        self.f_hizli_anons.pack(fill="both", expand=True, pady=(0, 0))
        self._guncelle_hizli_anonslar()

        # 4. KART (SAĞ ÜST): Hızlı Zil Butonları
        f_hizli_zil = ttk.LabelFrame(pan_right, text="Manuel Zil Çalma (Test)", padding=10)
        f_hizli_zil.pack(fill="x", pady=(0, 8))

        ziller = [
            ("🔔 Öğrenci Giriş Zili", "ogrenci", "#2a9d8f"),
            ("👨‍🏫 Öğretmen Giriş Zili", "ogretmen", "#457b9d"),
            ("🚪 Teneffüs Zili", "cikis", "#e76f51"),
            ("🏠 Okul Çıkış / Gün Sonu Müziği", "gun_sonu_cikis", "#d62828")
        ]
        for baslik, kod, renk in ziller:
            btn = tk.Button(
                f_hizli_zil, text=baslik, font=("Helvetica", 10, "bold"),
                bg=renk, fg="white", activebackground="#333333", activeforeground="white",
                bd=2, relief="groove", cursor="hand2",
                command=lambda k=kod, b=baslik: self.manuel_ses_cal(k, b)
            )
            btn.pack(fill="x", pady=2, ipady=3)

        # 5. KART (SAĞ ALT): Tören & Acil Durum Butonları
        f_toren = ttk.LabelFrame(pan_right, text="Resmi Tören & Acil Durum", padding=10)
        f_toren.pack(fill="both", expand=True, pady=(0, 0))

        torenler = [
            ("🇹🇷 İstiklal Marşı", "istiklal", "#b7094c"),
            ("⏱️ Saygı Duruşu + İstiklal Marşı", "saygi_istiklal", "#7209b7"),
            ("📯 Saygı Duruşu (Ti Sesi)", "saygi", "#3a0ca3"),
            ("🚨 ACİL DURUM / SİREN (Deprem-Yangın)", "siren", "#d90429")
        ]
        for baslik, kod, renk in torenler:
            btn = tk.Button(
                f_toren, text=baslik, font=("Helvetica", 10, "bold"),
                bg=renk, fg="white", activebackground="#222222", activeforeground="white",
                bd=2, relief="groove", cursor="hand2",
                command=lambda k=kod, b=baslik: self.manuel_ses_cal(k, b)
            )
            btn.pack(fill="x", pady=2, ipady=4)

    # -------------------------------------------------------------
    # SEKME 2: ZİL ZAMAN ÇİZELGESİ
    # -------------------------------------------------------------
    def _kur_tab_program(self):
        # 1. Filtre & Gün Seçim Çubuğu
        f_filtre = ttk.LabelFrame(self.tab_program, text="Gün Seçimi ve Toplu İşlemler", padding=8)
        f_filtre.pack(fill="x", pady=(0, 6))

        ttk.Label(f_filtre, text="📅 Görüntülenen / Düzenlenen Gün:", font=("Helvetica", 9, "bold")).pack(side="left", padx=4)

        self.filtre_gun_secenekleri = ["Tüm Günler", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.cmb_filtre_gun = ttk.Combobox(f_filtre, values=self.filtre_gun_secenekleri, state="readonly", width=16)
        self.cmb_filtre_gun.current(0)
        self.cmb_filtre_gun.pack(side="left", padx=6)
        self.cmb_filtre_gun.bind("<<ComboboxSelected>>", lambda e: self.tabloyu_doldur())

        btn_yay = tk.Button(
            f_filtre, text="📋 Bu Günü Tüm Haftaya Yay", font=("Helvetica", 9, "bold"),
            bg="#3a86ff", fg="white", activebackground="#2a66cc", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.secili_gunu_haftaya_yay
        )
        btn_yay.pack(side="right", padx=6, ipady=3)

        # 2. İşlem Butonları Çubuğu
        f_ust = ttk.Frame(self.tab_program)
        f_ust.pack(fill="x", pady=(0, 6))

        btn_sihirbaz = tk.Button(
            f_ust, text="⚡ Otomatik Çizelge Sihirbazı", font=("Helvetica", 10, "bold"),
            bg="#2b9348", fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.sihirbaz_penceresi_ac
        )
        btn_sihirbaz.pack(side="left", padx=(0, 6), ipady=4)

        btn_yeni = ttk.Button(f_ust, text="➕ Yeni Zil Ekle", command=self.manuel_zil_ekle_penceresi)
        btn_yeni.pack(side="left", padx=4)

        btn_duzenle = ttk.Button(f_ust, text="✏️ Seçileni Düzenle", command=self.zil_duzenle_penceresi)
        btn_duzenle.pack(side="left", padx=4)

        btn_sil = ttk.Button(f_ust, text="🗑️ Seçileni Sil", command=self.zil_sil)
        btn_sil.pack(side="left", padx=4)

        btn_disa_aktar = ttk.Button(f_ust, text="📤 Dışa Aktar (Yedekle)", command=self.cizelge_disa_aktar)
        btn_disa_aktar.pack(side="left", padx=4)

        btn_ice_aktar = ttk.Button(f_ust, text="📥 İçe Aktar (Yükle)", command=self.cizelge_ice_aktar)
        btn_ice_aktar.pack(side="left", padx=4)

        btn_temizle = ttk.Button(f_ust, text="⚠️ Tümünü Temizle", command=self.tum_zilleri_temizle)
        btn_temizle.pack(side="right", padx=4)

        # 3. Tablo Alanı
        f_tablo = ttk.Frame(self.tab_program)
        f_tablo.pack(fill="both", expand=True)

        kolonlar = ("durum", "saat", "tur", "gunler")
        self.tree = ttk.Treeview(f_tablo, columns=kolonlar, show="headings", selectmode="browse")
        self.tree.heading("durum", text="Durum")
        self.tree.heading("saat", text="Zil Saati")
        self.tree.heading("tur", text="Zil Türü / Görev")
        self.tree.heading("gunler", text="Uygulanan Günler")

        self.tree.column("durum", width=70, anchor="center")
        self.tree.column("saat", width=100, anchor="center")
        self.tree.column("tur", width=220, anchor="w")
        self.tree.column("gunler", width=260, anchor="w")

        scroll = ttk.Scrollbar(f_tablo, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tabloyu_doldur()

    def _get_secili_real_idx(self):
        item_id = self.tree.focus()
        if not item_id or not item_id.startswith("item_"):
            return None
        try:
            return int(item_id.split("_")[1])
        except Exception:
            return None

    def tabloyu_doldur(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        secili_gun = self.cmb_filtre_gun.get() if hasattr(self, "cmb_filtre_gun") else "Tüm Günler"
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        self.ayarlar["program"].sort(key=lambda x: x["saat"])

        for real_idx, item in enumerate(self.ayarlar["program"]):
            # Gün filtresi kontrolü
            if secili_gun != "Tüm Günler":
                gun_idx = gun_adlari.index(secili_gun)
                if not self._gun_uygun_mu(item.get("gunler", ""), gun_idx):
                    continue

            durum = "✅ Aktif" if item.get("aktif", True) else "❌ Pasif"
            tur_ad = ZIL_TURLERI.get(item["tur"], item["tur"])
            tree_iid = f"item_{real_idx}"
            self.tree.insert("", "end", iid=tree_iid, values=(durum, item["saat"], tur_ad, item["gunler"]))

    def _on_tree_double_click(self, event):
        real_idx = self._get_secili_real_idx()
        if real_idx is not None:
            self.zil_duzenle_penceresi()

    def zil_sil(self):
        real_idx = self._get_secili_real_idx()
        if real_idx is None:
            messagebox.showwarning("Uyarı", "Lütfen listeden silmek istediğiniz bir satırı seçin.", parent=self.root)
            return
        if 0 <= real_idx < len(self.ayarlar["program"]):
            del self.ayarlar["program"][real_idx]
            self.ayarlari_kaydet()
            self.tabloyu_doldur()

    def tum_zilleri_temizle(self):
        secili_gun = self.cmb_filtre_gun.get() if hasattr(self, "cmb_filtre_gun") else "Tüm Günler"
        if secili_gun == "Tüm Günler":
            if messagebox.askyesno("Onay", "TÜM günlere ait bütün zil saatleri silinecek. Emin misiniz?", parent=self.root):
                self.ayarlar["program"] = []
                self.ayarlari_kaydet()
                self.tabloyu_doldur()
        else:
            if messagebox.askyesno("Onay", f"Sadece '{secili_gun}' gününe ait zil kayıtları silinecek. Emin misiniz?", parent=self.root):
                gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                gun_idx = gun_adlari.index(secili_gun)
                yeni_program = []
                for z in self.ayarlar["program"]:
                    if not self._gun_uygun_mu(z.get("gunler", ""), gun_idx):
                        yeni_program.append(z)
                self.ayarlar["program"] = yeni_program
                self.ayarlari_kaydet()
                self.tabloyu_doldur()

    def _gunler_secimi_olustur(self, parent_frame, baslangic_gun_kurali="Hafta İçi (Pzt-Cum)"):
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        var_dict = {}

        f_gunler = ttk.LabelFrame(parent_frame, text="Uygulanacak Günler (Seçiniz)", padding=8)
        f_gunler.pack(fill="x", pady=6)

        # Checkbox'ların başlangıç durumunu belirle
        for idx, g in enumerate(gun_adlari):
            aktif_mi = self._gun_uygun_mu(baslangic_gun_kurali, idx)
            var_dict[g] = tk.BooleanVar(value=aktif_mi)

        # 2 Satır halinde Checkbox'ları diz
        f_chk = ttk.Frame(f_gunler)
        f_chk.pack(fill="x", pady=4)

        for i, g in enumerate(gun_adlari):
            r = 0 if i < 4 else 1
            c = i if i < 4 else i - 4
            chk = ttk.Checkbutton(f_chk, text=g, variable=var_dict[g])
            chk.grid(row=r, column=c, sticky="w", padx=6, pady=3)

        # Hızlı Seçim Butonları
        f_hizli = ttk.Frame(f_gunler)
        f_hizli.pack(fill="x", pady=(4, 0))

        def sec_hafta_ici():
            for g in gun_adlari:
                var_dict[g].set(g in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])

        def sec_tum_hafta():
            for g in gun_adlari:
                var_dict[g].set(True)

        def sec_temizle():
            for g in gun_adlari:
                var_dict[g].set(False)

        ttk.Button(f_hizli, text="Hafta İçi (Pzt-Cum)", command=sec_hafta_ici).pack(side="left", padx=2)
        ttk.Button(f_hizli, text="Tüm Hafta (7 Gün)", command=sec_tum_hafta).pack(side="left", padx=2)
        ttk.Button(f_hizli, text="Temizle", command=sec_temizle).pack(side="left", padx=2)

        def get_secilen_gunler_str():
            secilenler = [g for g in gun_adlari if var_dict[g].get()]
            if not secilenler:
                return ""
            if len(secilenler) == 7:
                return "Haftanın Her Günü"
            if secilenler == ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]:
                return "Hafta İçi (Pzt-Cum)"
            if secilenler == ["Pazartesi", "Salı", "Çarşamba", "Perşembe"]:
                return "Pazartesi-Perşembe"
            if secilenler == ["Cuma"]:
                return "Sadece Cuma"
            if secilenler == ["Cumartesi", "Pazar"]:
                return "Hafta Sonu (Cmt-Paz)"
            return ", ".join(secilenler)

        return f_gunler, var_dict, get_secilen_gunler_str

    def manuel_zil_ekle_penceresi(self):
        w = tk.Toplevel(self.root)
        w.title("Yeni Zil Saati Ekle")
        w.geometry("480x420")
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=15)
        f.pack(fill="both", expand=True)

        # Varsayılan gün kuralı: filtreden gelen gün
        secili_filtre = self.cmb_filtre_gun.get() if hasattr(self, "cmb_filtre_gun") else "Tüm Günler"
        varsayilan_gun = "Hafta İçi (Pzt-Cum)" if secili_filtre == "Tüm Günler" else secili_filtre

        ttk.Label(f, text="Zil Saati (SS:DD):").pack(anchor="w", pady=(0, 2))
        ent_saat = ttk.Entry(f, font=("Helvetica", 11))
        ent_saat.insert(0, "08:30")
        ent_saat.pack(fill="x", pady=(0, 8))

        ttk.Label(f, text="Zil Türü:").pack(anchor="w", pady=(0, 2))
        cmb_tur = ttk.Combobox(f, values=[ZIL_TURLERI["ogrenci"], ZIL_TURLERI["ogretmen"], ZIL_TURLERI["cikis"], ZIL_TURLERI["gun_sonu_cikis"]], state="readonly")
        cmb_tur.current(0)
        cmb_tur.pack(fill="x", pady=(0, 8))

        # Gün Seçimi Checkbox'ları
        _, _, get_gunler_str = self._gunler_secimi_olustur(f, baslangic_gun_kurali=varsayilan_gun)

        def kaydet():
            saat = ent_saat.get().strip()
            try:
                datetime.strptime(saat, "%H:%M")
            except ValueError:
                messagebox.showerror("Hata", "Saat formatı hatalı! (Örnek: 08:30 veya 14:05)", parent=w)
                return

            secili_tur_ad = cmb_tur.get()
            tur_kod = [k for k, v in ZIL_TURLERI.items() if v == secili_tur_ad][0]
            gunler_str = get_gunler_str()

            if not gunler_str:
                messagebox.showwarning("Uyarı", "Lütfen zilin çalacağı en az bir gün seçin!", parent=w)
                return

            self.ayarlar["program"].append({
                "saat": saat,
                "tur": tur_kod,
                "gunler": gunler_str,
                "aktif": True
            })
            self.ayarlari_kaydet()
            self.tabloyu_doldur()
            w.destroy()

        btn_kaydet = tk.Button(
            f, text="💾 Zili Kaydet ve Ekle", font=("Helvetica", 10, "bold"),
            bg="#2b9348", fg="white", relief="raised", bd=2, cursor="hand2", command=kaydet
        )
        btn_kaydet.pack(fill="x", ipady=5, pady=(10, 0))

    def zil_duzenle_penceresi(self):
        real_idx = self._get_secili_real_idx()
        if real_idx is None or real_idx >= len(self.ayarlar["program"]):
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz bir zil satırını seçin.", parent=self.root)
            return

        zil = self.ayarlar["program"][real_idx]

        w = tk.Toplevel(self.root)
        w.title("Zil Saatini ve Günlerini Düzenle")
        w.geometry("480x440")
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Zil Saati (SS:DD):").pack(anchor="w", pady=(0, 2))
        ent_saat = ttk.Entry(f, font=("Helvetica", 11))
        ent_saat.insert(0, zil.get("saat", "08:30"))
        ent_saat.pack(fill="x", pady=(0, 8))

        ttk.Label(f, text="Zil Türü:").pack(anchor="w", pady=(0, 2))
        cmb_tur = ttk.Combobox(f, values=[ZIL_TURLERI["ogrenci"], ZIL_TURLERI["ogretmen"], ZIL_TURLERI["cikis"], ZIL_TURLERI["gun_sonu_cikis"]], state="readonly")
        mevcut_tur_ad = ZIL_TURLERI.get(zil.get("tur", "ogrenci"), ZIL_TURLERI["ogrenci"])
        cmb_tur.set(mevcut_tur_ad)
        cmb_tur.pack(fill="x", pady=(0, 8))

        var_aktif = tk.BooleanVar(value=zil.get("aktif", True))
        chk_aktif = ttk.Checkbutton(f, text="Bu zil aktif olarak çalışsın", variable=var_aktif)
        chk_aktif.pack(anchor="w", pady=(0, 6))

        # Gün Seçimi Checkbox'ları
        _, _, get_gunler_str = self._gunler_secimi_olustur(f, baslangic_gun_kurali=zil.get("gunler", "Hafta İçi (Pzt-Cum)"))

        def guncelle():
            saat = ent_saat.get().strip()
            try:
                datetime.strptime(saat, "%H:%M")
            except ValueError:
                messagebox.showerror("Hata", "Saat formatı hatalı! (Örnek: 08:30 veya 14:05)", parent=w)
                return

            secili_tur_ad = cmb_tur.get()
            tur_kod = [k for k, v in ZIL_TURLERI.items() if v == secili_tur_ad][0]
            gunler_str = get_gunler_str()

            if not gunler_str:
                messagebox.showwarning("Uyarı", "Lütfen en az bir gün seçin!", parent=w)
                return

            self.ayarlar["program"][real_idx] = {
                "saat": saat,
                "tur": tur_kod,
                "gunler": gunler_str,
                "aktif": var_aktif.get()
            }
            self.ayarlari_kaydet()
            self.tabloyu_doldur()
            w.destroy()

        btn_guncelle = tk.Button(
            f, text="💾 Değişiklikleri Kaydet", font=("Helvetica", 10, "bold"),
            bg="#1b4965", fg="white", relief="raised", bd=2, cursor="hand2", command=guncelle
        )
        btn_guncelle.pack(fill="x", ipady=5, pady=(10, 0))

    def secili_gunu_haftaya_yay(self):
        secili_gun = self.cmb_filtre_gun.get() if hasattr(self, "cmb_filtre_gun") else "Tüm Günler"
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        if secili_gun == "Tüm Günler":
            messagebox.showwarning(
                "Gün Seçiniz",
                "Lütfen önce yukarıdaki 'Görüntülenen / Düzenlenen Gün' açılır kutusundan tüm haftaya yaymak istediğiniz kaynak günü seçin (Örnek: Pazartesi).",
                parent=self.root
            )
            return

        kaynak_gun_idx = gun_adlari.index(secili_gun)

        # Seçili günde çalan zilleri topla
        kaynak_ziller = []
        for z in self.ayarlar["program"]:
            if self._gun_uygun_mu(z.get("gunler", ""), kaynak_gun_idx):
                kaynak_ziller.append({
                    "saat": z["saat"],
                    "tur": z["tur"],
                    "aktif": z.get("aktif", True)
                })

        if not kaynak_ziller:
            messagebox.showwarning("Uyarı", f"'{secili_gun}' gününe ait hiçbir zil kaydı bulunamadı!", parent=self.root)
            return

        w = tk.Toplevel(self.root)
        w.title(f"'{secili_gun}' Gününün Programını Yay")
        w.geometry("480x420")
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text=f"📋 '{secili_gun}' Gününün Zil Programını Kopyala", font=("Helvetica", 11, "bold"), foreground=self.c_primary).pack(pady=(0, 6))
        ttk.Label(f, text=f"'{secili_gun}' gününde toplam {len(kaynak_ziller)} adet zil tanımlı. Bu ziller aşağıdaki seçtiğiniz günlere aynen uygulanacaktır:", wraplength=440).pack(pady=(0, 10))

        # Hedef Gün Checkbox'ları
        f_hedef = ttk.LabelFrame(f, text="Hedef Günler (Kopyalanacak Günleri Seçiniz)", padding=10)
        f_hedef.pack(fill="x", pady=6)

        hedef_vars = {}
        f_chk = ttk.Frame(f_hedef)
        f_chk.pack(fill="x", pady=4)

        for i, g in enumerate(gun_adlari):
            r = 0 if i < 4 else 1
            c = i if i < 4 else i - 4
            # Kaynak gün hariç hafta içi varsayılan seçili olsun
            varsayilan = (g in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]) and (g != secili_gun)
            hedef_vars[g] = tk.BooleanVar(value=varsayilan)
            chk = ttk.Checkbutton(f_chk, text=g, variable=hedef_vars[g])
            chk.grid(row=r, column=c, sticky="w", padx=6, pady=3)

        f_btn_hizli = ttk.Frame(f_hedef)
        f_btn_hizli.pack(fill="x", pady=(4, 0))

        def hedef_hafta_ici():
            for g in gun_adlari:
                hedef_vars[g].set(g in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])

        def hedef_tum_hafta():
            for g in gun_adlari:
                hedef_vars[g].set(True)

        ttk.Button(f_btn_hizli, text="Hafta İçi Günleri", command=hedef_hafta_ici).pack(side="left", padx=2)
        ttk.Button(f_btn_hizli, text="Tüm Hafta", command=hedef_tum_hafta).pack(side="left", padx=2)

        var_hedef_temizle = tk.BooleanVar(value=True)
        chk_hedef_temizle = ttk.Checkbutton(f, text="Hedef günlerdeki eski zilleri temizleyip yerine bu zilleri yaz", variable=var_hedef_temizle)
        chk_hedef_temizle.pack(pady=8, anchor="w")

        def uygula_yay():
            secilen_hedef_gunler = [g for g in gun_adlari if hedef_vars[g].get()]
            if not secilen_hedef_gunler:
                messagebox.showwarning("Uyarı", "Lütfen en az bir hedef gün seçin!", parent=w)
                return

            # Eğer kaynak gün de hedefte değilse onu da ekleyelim
            if secili_gun not in secilen_hedef_gunler:
                secilen_hedef_gunler.append(secili_gun)

            # Gün kuralı metnini oluştur
            if len(secilen_hedef_gunler) == 7:
                gunler_str = "Haftanın Her Günü"
            elif sorted(secilen_hedef_gunler) == ["Cuma", "Pazartesi", "Perşembe", "Salı", "Çarşamba"]:
                gunler_str = "Hafta İçi (Pzt-Cum)"
            else:
                gunler_str = ", ".join(secilen_hedef_gunler)

            # Temizleme seçildiyse hedef günlerde çalan mevcut zilleri kaldır
            yeni_program = []
            if var_hedef_temizle.get():
                hedef_indeksler = [gun_adlari.index(g) for g in secilen_hedef_gunler]
                for z in self.ayarlar["program"]:
                    # Eğer bu zil seçilen hedef günlerin hiçbirinde çalmıyorsa koru
                    calisiyor_mu = any(self._gun_uygun_mu(z.get("gunler", ""), h_idx) for h_idx in hedef_indeksler)
                    if not calisiyor_mu:
                        yeni_program.append(z)
            else:
                yeni_program = list(self.ayarlar["program"])

            # Kaynak zilleri yeni gün kuralıyla ekle
            for kz in kaynak_ziller:
                yeni_program.append({
                    "saat": kz["saat"],
                    "tur": kz["tur"],
                    "gunler": gunler_str,
                    "aktif": kz["aktif"]
                })

            self.ayarlar["program"] = yeni_program
            self.ayarlari_kaydet()
            self.tabloyu_doldur()
            messagebox.showinfo("Başarılı", f"'{secili_gun}' gününün zil programı seçilen günlere ({gunler_str}) başarıyla yayıldı!", parent=w)
            w.destroy()

        btn_onayla = tk.Button(
            f, text="🚀 Kopyala ve Tüm Haftaya Yay", font=("Helvetica", 10, "bold"),
            bg="#3a86ff", fg="white", relief="raised", bd=2, cursor="hand2", command=uygula_yay
        )
        btn_onayla.pack(fill="x", ipady=6, pady=(10, 0))

    def sihirbaz_penceresi_ac(self):
        w = tk.Toplevel(self.root)
        w.title("Otomatik Çizelge Oluşturma Sihirbazı")
        w.geometry("520x620")
        w.transient(self.root)
        w.grab_set()

        canvas = tk.Canvas(w, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(w, orient="vertical", command=canvas.yview)
        f = ttk.Frame(canvas, padding=15)

        f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=f, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(f, text="⚡ Otomatik Zil Programı Sihirbazı", font=("Helvetica", 12, "bold"), foreground=self.c_primary).pack(pady=(0, 6))
        ttk.Label(f, text="Okul saatlerinizi ve eğitim aldığınız günleri seçerek tüm haftalık zil programını tek tıkla oluşturabilirsiniz.", wraplength=460).pack(pady=(0, 10))

        grid_f = ttk.Frame(f)
        grid_f.pack(fill="x", pady=4)

        ttk.Label(grid_f, text="1. Ders Başlangıç Saati:").grid(row=0, column=0, sticky="w", pady=4)
        ent_baslangic = ttk.Entry(grid_f, width=10)
        ent_baslangic.insert(0, "08:30")
        ent_baslangic.grid(row=0, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Günlük Ders Sayısı:").grid(row=1, column=0, sticky="w", pady=4)
        spn_ders_sayisi = ttk.Spinbox(grid_f, from_=1, to=12, width=8)
        spn_ders_sayisi.set(7)
        spn_ders_sayisi.grid(row=1, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Ders Süresi (Dakika):").grid(row=2, column=0, sticky="w", pady=4)
        spn_ders_suresi = ttk.Spinbox(grid_f, from_=10, to=90, width=8)
        spn_ders_suresi.set(40)
        spn_ders_suresi.grid(row=2, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Öğrenci Zili Avansı (dk önce):").grid(row=3, column=0, sticky="w", pady=4)
        spn_avans = ttk.Spinbox(grid_f, from_=0, to=10, width=8)
        spn_avans.set(2)
        spn_avans.grid(row=3, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Normal Teneffüs Süresi (Dakika):").grid(row=4, column=0, sticky="w", pady=4)
        spn_teneffus = ttk.Spinbox(grid_f, from_=5, to=60, width=8)
        spn_teneffus.set(10)
        spn_teneffus.grid(row=4, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Öğle Arası Hangi Dersten Sonra?:").grid(row=5, column=0, sticky="w", pady=4)
        spn_ogle_ders = ttk.Spinbox(grid_f, from_=0, to=10, width=8)
        spn_ogle_ders.set(4)
        spn_ogle_ders.grid(row=5, column=1, sticky="e", pady=4)

        ttk.Label(grid_f, text="Öğle Arası Süresi (Dakika):").grid(row=6, column=0, sticky="w", pady=4)
        spn_ogle_sure = ttk.Spinbox(grid_f, from_=15, to=120, width=8)
        spn_ogle_sure.set(45)
        spn_ogle_sure.grid(row=6, column=1, sticky="e", pady=4)

        # Eğitim Alınan Günler Bölümü (7 Günlük Checkbox'lar)
        _, _, get_sihirbaz_gunler_str = self._gunler_secimi_olustur(f, baslangic_gun_kurali="Hafta İçi (Pzt-Cum)")

        var_son_ders_muzik = tk.BooleanVar(value=True)
        chk_son_muzik = ttk.Checkbutton(f, text="Son ders bitişinde normal zil yerine 'Okul Çıkış / Gün Sonu Müziği' çal", variable=var_son_ders_muzik)
        chk_son_muzik.pack(pady=4, anchor="w")

        var_eskiyi_sil = tk.BooleanVar(value=True)
        chk_eski = ttk.Checkbutton(f, text="Mevcut zil programının üzerine yaz (Eski programı temizle)", variable=var_eskiyi_sil)
        chk_eski.pack(pady=4, anchor="w")

        def olustur():
            try:
                baslangic_str = ent_baslangic.get().strip()
                t_cur = datetime.strptime(baslangic_str, "%H:%M")
                ders_sayisi = int(spn_ders_sayisi.get())
                ders_suresi = int(spn_ders_suresi.get())
                avans = int(spn_avans.get())
                teneffus_suresi = int(spn_teneffus.get())
                ogle_ders = int(spn_ogle_ders.get())
                ogle_suresi = int(spn_ogle_sure.get())
                gunler = get_sihirbaz_gunler_str()
            except Exception as e:
                messagebox.showerror("Hata", f"Girdi parametreleri geçersiz: {e}", parent=w)
                return

            if not gunler:
                messagebox.showwarning("Uyarı", "Lütfen eğitimin verildiği en az bir gün seçin!", parent=w)
                return

            yeni_program = [] if var_eskiyi_sil.get() else list(self.ayarlar["program"])

            for ders_no in range(1, ders_sayisi + 1):
                t_ogrenci = t_cur - timedelta(minutes=avans)
                yeni_program.append({
                    "saat": t_ogrenci.strftime("%H:%M"),
                    "tur": "ogrenci",
                    "gunler": gunler,
                    "aktif": True
                })

                yeni_program.append({
                    "saat": t_cur.strftime("%H:%M"),
                    "tur": "ogretmen",
                    "gunler": gunler,
                    "aktif": True
                })

                t_cikis = t_cur + timedelta(minutes=ders_suresi)

                # Son ders çıkışı ise 'gun_sonu_cikis' müziğini ata
                tur_cikis = "gun_sonu_cikis" if (ders_no == ders_sayisi and var_son_ders_muzik.get()) else "cikis"
                yeni_program.append({
                    "saat": t_cikis.strftime("%H:%M"),
                    "tur": tur_cikis,
                    "gunler": gunler,
                    "aktif": True
                })

                if ders_no < ders_sayisi:
                    if ogle_ders > 0 and ders_no == ogle_ders:
                        t_cur = t_cikis + timedelta(minutes=ogle_suresi)
                    else:
                        t_cur = t_cikis + timedelta(minutes=teneffus_suresi)

            self.ayarlar["program"] = yeni_program
            self.ayarlari_kaydet()
            self.tabloyu_doldur()
            messagebox.showinfo("Başarılı", f"{ders_sayisi} derslik zil programı ({gunler}) için başarıyla oluşturuldu!", parent=w)
            w.destroy()

        btn_calistir = tk.Button(
            f, text="🚀 Çizelgeyi Oluştur ve Kaydet", font=("Helvetica", 11, "bold"),
            bg=self.c_success, fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=olustur
        )
        btn_calistir.pack(fill="x", ipady=6, pady=8)

    # -------------------------------------------------------------
    # SEKME 3: OKUL RADYOSU & MÜZİK ÇALAR (PLAYLIST)
    # -------------------------------------------------------------
    def _kur_tab_muzik(self):
        # 1. Üst İşlem Çubuğu (Klasör & Dosya Seçimi)
        f_ust = ttk.LabelFrame(self.tab_muzik, text="Müzik Kaynağı & Çalma Listesi Yönetimi", padding=8)
        f_ust.pack(fill="x", pady=(0, 6))

        klasor = self.ayarlar["sesler"].get("teneffus_klasoru", "")
        gorunen_klasor = os.path.basename(klasor) or (klasor if klasor else "Klasör Seçilmedi")
        self.lbl_muzik_klasor = ttk.Label(f_ust, text=f"📁 Klasör: {gorunen_klasor}", font=("Helvetica", 9, "bold"), foreground="#0055aa")
        self.lbl_muzik_klasor.pack(side="left", padx=4)

        btn_klasor = ttk.Button(f_ust, text="📁 Klasör Seç", command=self._muzik_klasor_sec_ve_yukle)
        btn_klasor.pack(side="right", padx=2)

        btn_dosya_ekle = ttk.Button(f_ust, text="➕ Şarkı Ekle", command=self._muzik_sarki_ekle)
        btn_dosya_ekle.pack(side="right", padx=2)

        btn_temizle = ttk.Button(f_ust, text="🗑️ Listeyi Temizle", command=self._muzik_listesini_temizle)
        btn_temizle.pack(side="right", padx=2)

        btn_yenile = ttk.Button(f_ust, text="🔄 Yenile", command=self._muzik_listesini_yukle)
        btn_yenile.pack(side="right", padx=2)

        # 2. Şarkı Listesi (Treeview)
        f_liste = ttk.Frame(self.tab_muzik)
        f_liste.pack(fill="both", expand=True, pady=(0, 6))

        kolonlar = ("no", "sarki", "konum")
        self.tree_muzik = ttk.Treeview(f_liste, columns=kolonlar, show="headings", selectmode="browse")
        self.tree_muzik.heading("no", text="#")
        self.tree_muzik.heading("sarki", text="🎵 Şarkı / Müzik Adı")
        self.tree_muzik.heading("konum", text="Dosya Konumu")

        self.tree_muzik.column("no", width=45, anchor="center")
        self.tree_muzik.column("sarki", width=340, anchor="w")
        self.tree_muzik.column("konum", width=350, anchor="w")

        scroll_m = ttk.Scrollbar(f_liste, orient="vertical", command=self.tree_muzik.yview)
        self.tree_muzik.configure(yscrollcommand=scroll_m.set)
        self.tree_muzik.pack(side="left", fill="both", expand=True)
        scroll_m.pack(side="right", fill="y")

        self.tree_muzik.bind("<Double-1>", self._on_muzik_tree_double_click)

        # 3. Alt Master Kontrol Paneli
        f_master = ttk.LabelFrame(self.tab_muzik, text="🎛️ Oynatıcı Kontrol Paneli", padding=10)
        f_master.pack(fill="x", pady=(0, 0))

        self.lbl_master_sarki = ttk.Label(f_master, text="Seçili Şarkı: -", font=("Helvetica", 11, "bold"), foreground=self.c_primary)
        self.lbl_master_sarki.pack(fill="x", pady=(0, 6))

        f_butonlar = ttk.Frame(f_master)
        f_butonlar.pack(fill="x", pady=4)

        btn_prev = tk.Button(
            f_butonlar, text="⏮ Önceki", font=("Helvetica", 9, "bold"),
            bg="#457b9d", fg="white", activebackground="#1d3557", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.muzik_onceki
        )
        btn_prev.pack(side="left", padx=3, ipady=3)

        self.btn_master_play = tk.Button(
            f_butonlar, text="▶ Oynat", font=("Helvetica", 10, "bold"),
            bg="#2a9d8f", fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", width=12, command=self.muzik_oynat_veya_durdur
        )
        self.btn_master_play.pack(side="left", padx=3, ipady=3)

        btn_stop = tk.Button(
            f_butonlar, text="⏹ Durdur", font=("Helvetica", 9, "bold"),
            bg=self.c_danger, fg="white", activebackground="#b7094c", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.muzik_durdur
        )
        btn_stop.pack(side="left", padx=3, ipady=3)

        btn_next = tk.Button(
            f_butonlar, text="⏭ Sonraki", font=("Helvetica", 9, "bold"),
            bg="#457b9d", fg="white", activebackground="#1d3557", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self.muzik_sonraki
        )
        btn_next.pack(side="left", padx=3, ipady=3)

        mod_metin = "🔀 Çalma Modu: Karışık" if self.muzik_modu == "karisik" else "🔁 Çalma Modu: Sıralı"
        self.btn_master_mod = tk.Button(
            f_butonlar, text=mod_metin, font=("Helvetica", 9, "bold"),
            bg="#3a86ff", fg="white", activebackground="#2a66cc", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self._muzik_modu_degistir
        )
        self.btn_master_mod.pack(side="right", padx=3, ipady=3)

        # Ses Seviyesi & Teneffüs Otomatik Başlatma Checkbox
        f_alt_satir = ttk.Frame(f_master)
        f_alt_satir.pack(fill="x", pady=(6, 0))

        ttk.Label(f_alt_satir, text="Müzik Sesi:").pack(side="left", padx=4)
        init_tvol = int(self.ayarlar["genel"].get("teneffus_ses_seviyesi", 50))
        self.scale_master_vol = ttk.Scale(f_alt_satir, from_=0, to=100, orient="horizontal", command=self._on_teneffus_vol_change)
        self.scale_master_vol.set(init_tvol)
        self.scale_master_vol.pack(side="left", fill="x", expand=True, padx=6)

        self.lbl_master_vol_val = ttk.Label(f_alt_satir, text=f"%{init_tvol}", width=5)
        self.lbl_master_vol_val.pack(side="left", padx=4)

        self.var_otomatik_teneffus = tk.BooleanVar(value=self.ayarlar["genel"].get("teneffus_muzik_aktif", False))
        chk_oto = ttk.Checkbutton(
            f_alt_satir, text="Teneffüs zili çaldığında otomatik başlat",
            variable=self.var_otomatik_teneffus, command=self._otomatik_teneffus_toggle
        )
        chk_oto.pack(side="right", padx=6)

    # -------------------------------------------------------------
    # MÜZİK ÇALAR / PLAYLIST YÖNETİM METODLARI
    # -------------------------------------------------------------
    def _muzik_listesini_yukle(self):
        klasor = self.ayarlar["sesler"].get("teneffus_klasoru", "")
        self.muzik_calma_listesi = []
        if klasor and os.path.isdir(klasor):
            try:
                for f in sorted(os.listdir(klasor)):
                    if f.lower().endswith(('.mp3', '.wav', '.ogg', '.aac', '.m4a', '.wma', '.flac')):
                        self.muzik_calma_listesi.append(os.path.normpath(os.path.join(klasor, f)))
            except Exception as e:
                print(f"Müzik listesi yükleme hatası: {e}")

        if hasattr(self, "lbl_muzik_klasor"):
            gorunen = os.path.basename(klasor) or (klasor if klasor else "Klasör Seçilmedi")
            self.lbl_muzik_klasor.config(text=f"📁 Klasör: {gorunen}")

        self._muzik_tree_doldur()

    def _muzik_tree_doldur(self):
        if not hasattr(self, "tree_muzik"):
            return
        for row in self.tree_muzik.get_children():
            self.tree_muzik.delete(row)

        for idx, yol in enumerate(self.muzik_calma_listesi):
            sarki_ad = os.path.basename(yol)
            self.tree_muzik.insert("", "end", iid=f"m_{idx}", values=(idx + 1, sarki_ad, yol))

    def _on_muzik_tree_double_click(self, event):
        item_id = self.tree_muzik.focus()
        if item_id and item_id.startswith("m_"):
            try:
                idx = int(item_id.split("_")[1])
                self.muzik_oynat(idx)
            except Exception:
                pass

    def _muzik_klasor_sec_ve_yukle(self):
        try:
            yol = filedialog.askdirectory(parent=self.root, title="Müziklerin Bulunduğu Klasörü Seçin")
            if yol:
                self.ayarlar["sesler"]["teneffus_klasoru"] = os.path.normpath(yol)
                self.ayarlari_kaydet()
                self._muzik_listesini_yukle()
                messagebox.showinfo("Başarılı", f"{len(self.muzik_calma_listesi)} şarkı listeye eklendi.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör seçilirken sorun oluştu: {e}", parent=self.root)

    def _muzik_sarki_ekle(self):
        try:
            dosyalar = filedialog.askopenfilenames(
                parent=self.root,
                title="Çalma Listesine Eklenecek Şarkıları Seçin",
                filetypes=[
                    ("Ses Dosyaları", "*.mp3 *.wav *.ogg *.aac *.m4a *.wma *.flac"),
                    ("Tüm Dosyalar", "*.*")
                ]
            )
            if dosyalar:
                for d in dosyalar:
                    nd = os.path.normpath(d)
                    if nd not in self.muzik_calma_listesi:
                        self.muzik_calma_listesi.append(nd)
                self._muzik_tree_doldur()
                messagebox.showinfo("Bilgi", f"{len(dosyalar)} yeni şarkı listeye eklendi.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Hata", f"Şarkı eklenirken sorun oluştu: {e}", parent=self.root)

    def _muzik_listesini_temizle(self):
        if messagebox.askyesno("Onay", "Çalma listesini temizlemek istediğinizden emin misiniz?", parent=self.root):
            self.muzik_durdur()
            self.muzik_calma_listesi = []
            self._muzik_tree_doldur()

    def _muzik_modu_degistir(self):
        if self.muzik_modu == "sirali":
            self.muzik_modu = "karisik"
        else:
            self.muzik_modu = "sirali"

        self.ayarlar["genel"]["muzik_modu"] = self.muzik_modu
        self.ayarlari_kaydet()

        mod_metin = "🔀 Çalma Modu: Karışık" if self.muzik_modu == "karisik" else "🔁 Çalma Modu: Sıralı"
        if hasattr(self, "btn_master_mod"):
            self.btn_master_mod.config(text=mod_metin)
        if hasattr(self, "btn_mini_mod"):
            self.btn_mini_mod.config(text="🔀 Karışık" if self.muzik_modu == "karisik" else "🔁 Sıralı")

    def _on_teneffus_vol_change(self, val):
        v = int(float(val))
        if hasattr(self, "lbl_master_vol_val"):
            self.lbl_master_vol_val.config(text=f"%{v}")
        if "genel" in self.ayarlar:
            self.ayarlar["genel"]["teneffus_ses_seviyesi"] = v

    def _otomatik_teneffus_toggle(self):
        self.ayarlar["genel"]["teneffus_muzik_aktif"] = self.var_otomatik_teneffus.get()
        self.ayarlari_kaydet()

    def muzik_oynat_veya_durdur(self):
        if self.muzik_caliyor:
            self.muzik_durdur()
        else:
            self.muzik_oynat()

    def muzik_oynat(self, index=None):
        if not self.muzik_calma_listesi:
            # Klasör kontrolü
            self._muzik_listesini_yukle()
            if not self.muzik_calma_listesi:
                messagebox.showwarning("Çalma Listesi Boş", "Çalma listesinde şarkı bulunamadı!\nLütfen 'Müzik Çalar' sekmesinden bir müzik klasörü seçin veya şarkı ekleyin.", parent=self.root)
                return

        if index is not None and 0 <= index < len(self.muzik_calma_listesi):
            self.muzik_secili_indeks = index
        else:
            if self.muzik_secili_indeks < 0 or self.muzik_secili_indeks >= len(self.muzik_calma_listesi):
                if self.muzik_modu == "karisik":
                    self.muzik_secili_indeks = random.randint(0, len(self.muzik_calma_listesi) - 1)
                else:
                    self.muzik_secili_indeks = 0

        hedef_dosya = self.muzik_calma_listesi[self.muzik_secili_indeks]
        if not os.path.exists(hedef_dosya):
            print(f"[MÜZİK BULUNAMADI] {hedef_dosya}")
            self.muzik_sonraki()
            return

        sarki_adi = os.path.basename(hedef_dosya)
        vol = self.ayarlar["genel"].get("teneffus_ses_seviyesi", 50)
        target_dev = self.ayarlar["genel"].get("ses_aygiti", "default")
        pref_engine = self.ayarlar["genel"].get("ses_motoru", "otomatik")

        self.muzik_caliyor = True
        self._guncelle_muzik_ui(sarki_adi)

        def bitti():
            self.root.after(0, self._muzik_otomatik_sonraki)

        self.player.play(hedef_dosya, volume=vol, title=sarki_adi, is_teneffus=True, on_finish=bitti, preferred=pref_engine, target_device=target_dev)

    def muzik_durdur(self):
        self.muzik_caliyor = False
        self.player.stop_teneffus()
        self._guncelle_muzik_ui("")

    def muzik_sonraki(self):
        if not self.muzik_calma_listesi:
            return
        if self.muzik_modu == "karisik" and len(self.muzik_calma_listesi) > 1:
            adaylar = [i for i in range(len(self.muzik_calma_listesi)) if i != self.muzik_secili_indeks]
            next_idx = random.choice(adaylar)
        else:
            next_idx = (self.muzik_secili_indeks + 1) % len(self.muzik_calma_listesi)
        self.muzik_oynat(next_idx)

    def muzik_onceki(self):
        if not self.muzik_calma_listesi:
            return
        prev_idx = (self.muzik_secili_indeks - 1) % len(self.muzik_calma_listesi)
        self.muzik_oynat(prev_idx)

    def _muzik_otomatik_sonraki(self):
        if self.muzik_caliyor:
            self.root.after(300, self.muzik_sonraki)

    def _guncelle_muzik_ui(self, sarki_adi=""):
        if self.muzik_caliyor and sarki_adi:
            if hasattr(self, "lbl_master_sarki"):
                self.lbl_master_sarki.config(text=f"▶ Çalıyor ({self.muzik_secili_indeks+1}/{len(self.muzik_calma_listesi)}): {sarki_adi}", foreground=self.c_success)
            if hasattr(self, "btn_master_play"):
                self.btn_master_play.config(text="⏸ Durdur", bg=self.c_danger)
            if hasattr(self, "lbl_mini_muzik"):
                self.lbl_mini_muzik.config(text=f"▶ Çalıyor: {sarki_adi}", foreground=self.c_success)
            if hasattr(self, "btn_mini_play"):
                self.btn_mini_play.config(text="⏸ Durdur", bg=self.c_danger)
            if hasattr(self, "tree_muzik"):
                item_id = f"m_{self.muzik_secili_indeks}"
                if self.tree_muzik.exists(item_id):
                    self.tree_muzik.selection_set(item_id)
                    self.tree_muzik.see(item_id)
        else:
            if hasattr(self, "lbl_master_sarki"):
                self.lbl_master_sarki.config(text="Müzik Çalar: Durduruldu", foreground=self.c_primary)
            if hasattr(self, "btn_master_play"):
                self.btn_master_play.config(text="▶ Oynat", bg="#2a9d8f")
            if hasattr(self, "lbl_mini_muzik"):
                self.lbl_mini_muzik.config(text="Müzik Çalar: Durduruldu", foreground="#1b4965")
            if hasattr(self, "btn_mini_play"):
                self.btn_mini_play.config(text="▶ Oynat", bg="#2a9d8f")

    # -------------------------------------------------------------
    # SEKME 4: SESLER & MARŞLAR & ÖZEL ANONSLAR
    # -------------------------------------------------------------
    def _kur_tab_sesler(self):
        canvas = tk.Canvas(self.tab_sesler, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_sesler, orient="vertical", command=canvas.yview)
        self.scrollable_frame_sesler = ttk.Frame(canvas)

        self.scrollable_frame_sesler.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame_sesler, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.ses_etiketleri = {}

        kategoriler = [
            ("Zil & Çıkış Melodileri", [
                ("ogrenci", "🔔 Öğrenci Giriş Zili"),
                ("ogretmen", "👨‍🏫 Öğretmen Giriş Zili"),
                ("cikis", "🚪 Teneffüs Zili"),
                ("gun_sonu_cikis", "🏠 Okul Çıkış / Gün Sonu Müziği")
            ]),
            ("Resmi Tören Marşları & Acil Durum", [
                ("istiklal", "🇹🇷 İstiklal Marşı"),
                ("saygi_istiklal", "⏱️ Saygı Duruşu + İstiklal"),
                ("saygi", "📯 Saygı Duruşu (Ti Sesi)"),
                ("siren", "🚨 Acil Durum / Siren")
            ]),
            ("Teneffüs Müzik Yayını Klasörü", [
                ("teneffus_klasoru", "📻 Teneffüs Müzikleri (Klasör)")
            ])
        ]

        for kat_baslik, ses_listesi in kategoriler:
            lf = ttk.LabelFrame(self.scrollable_frame_sesler, text=kat_baslik, padding=10)
            lf.pack(fill="x", expand=True, padx=5, pady=6)

            for kod, ad in ses_listesi:
                row = ttk.Frame(lf)
                row.pack(fill="x", pady=4)

                ttk.Label(row, text=ad, width=28, font=("Helvetica", 9, "bold")).pack(side="left")

                dosya_yolu = self.ayarlar["sesler"].get(kod, "")
                var_mi = os.path.exists(dosya_yolu) if dosya_yolu else False
                gorunen_ad = os.path.basename(dosya_yolu) if dosya_yolu else "Tanımlanmadı"
                fg_renk = "#0055aa" if var_mi else "#d90429"

                lbl = ttk.Label(row, text=gorunen_ad, foreground=fg_renk, width=24)
                lbl.pack(side="left", fill="x", expand=True, padx=4)
                self.ses_etiketleri[kod] = lbl

                if kod == "teneffus_klasoru":
                    ttk.Button(row, text="📁 Klasör Seç", command=self._teneffus_klasor_sec).pack(side="right", padx=2)
                else:
                    ttk.Button(row, text="📁 Seç", width=6, command=lambda k=kod, a=ad: self.ses_sec(k, a)).pack(side="right", padx=2)
                    ttk.Button(row, text="▶ Çal", width=6, command=lambda k=kod, a=ad: self.manuel_ses_cal(k, a)).pack(side="right", padx=2)

        # 4. ÖZEL SESLİ ANONSLAR BÖLÜMÜ
        self.lf_anonslar = ttk.LabelFrame(self.scrollable_frame_sesler, text="📢 Özel Sesli Anonslar (Mikrofon / MP3 Kayıtları)", padding=10)
        self.lf_anonslar.pack(fill="x", expand=True, padx=5, pady=6)
        self._ciz_anons_listesi()

    def ses_sec(self, kod, ad):
        mevcut_yol = self.ayarlar["sesler"].get(kod, "")
        init_dir = os.path.dirname(mevcut_yol) if (mevcut_yol and os.path.exists(mevcut_yol)) else None
        if not init_dir or not os.path.exists(init_dir):
            if os.path.exists(os.path.join(APP_DIR, "musics", "e-zil-ses", "Ses")):
                init_dir = os.path.join(APP_DIR, "musics", "e-zil-ses", "Ses")
            elif os.path.exists(os.path.join(APP_DIR, "musics")):
                init_dir = os.path.join(APP_DIR, "musics")
            else:
                init_dir = SES_HEDEF_DIR

        try:
            yol = filedialog.askopenfilename(
                parent=self.root,
                title=f"{ad} İçin Ses Dosyası Seçin",
                initialdir=init_dir,
                filetypes=[
                    ("Desteklenen Ses Dosyaları", "*.mp3 *.wav *.ogg *.aac *.m4a *.wma *.flac"),
                    ("MP3 Dosyaları", "*.mp3"),
                    ("WAV Dosyaları", "*.wav"),
                    ("Tüm Dosyalar", "*.*")
                ]
            )
            if yol:
                self.ayarlar["sesler"][kod] = os.path.normpath(yol)
                self.ayarlari_kaydet()
                if kod in self.ses_etiketleri:
                    self.ses_etiketleri[kod].config(text=os.path.basename(yol), foreground="#0055aa")
                self.root.update_idletasks()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya seçilirken bir sorun oluştu: {e}", parent=self.root)

    def _teneffus_klasor_sec(self):
        try:
            yol = filedialog.askdirectory(parent=self.root, title="Teneffüs Müziklerinin Bulunduğu Klasörü Seçin")
            if yol:
                self.ayarlar["sesler"]["teneffus_klasoru"] = os.path.normpath(yol)
                self.ayarlari_kaydet()
                if "teneffus_klasoru" in self.ses_etiketleri:
                    self.ses_etiketleri["teneffus_klasoru"].config(text=os.path.basename(yol) or yol, foreground="#0055aa")
                self.root.update_idletasks()
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör seçilirken bir sorun oluştu: {e}", parent=self.root)

    # -------------------------------------------------------------
    # ÖZEL SESLİ ANONSLAR YÖNETİMİ
    # -------------------------------------------------------------
    def _ciz_anons_listesi(self):
        for w in self.lf_anonslar.winfo_children():
            w.destroy()

        f_top = ttk.Frame(self.lf_anonslar)
        f_top.pack(fill="x", pady=(0, 6))

        ttk.Label(f_top, text="Mikrofon veya telefonla kaydettiğiniz duyuruları buradan ekleyip amfiden çalabilirsiniz:", font=("Helvetica", 9)).pack(side="left")

        btn_yeni_anons = tk.Button(
            f_top, text="➕ Yeni Anons Ekle", font=("Helvetica", 9, "bold"),
            bg=self.c_success, fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=1, cursor="hand2", command=self._anons_ekle_penceresi
        )
        btn_yeni_anons.pack(side="right")

        anonslar = self.ayarlar.get("anonslar", [])
        if not anonslar:
            ttk.Label(self.lf_anonslar, text="Henüz anons tanımlanmadı. 'Yeni Anons Ekle' butonuna basarak ekleyebilirsiniz.", foreground="#6c757d").pack(anchor="w", pady=4)
            return

        for idx, anons in enumerate(anonslar):
            row = ttk.Frame(self.lf_anonslar)
            row.pack(fill="x", pady=3)

            baslik = anons.get("baslik", f"Anons {idx+1}")
            dosya = anons.get("dosya", "")
            var_mi = os.path.exists(dosya) if dosya else False
            gorunen = os.path.basename(dosya) if var_mi else ("Dosya Seçilmedi" if not dosya else "Dosya Bulunamadı")
            fg = "#0055aa" if var_mi else "#d90429"

            ttk.Label(row, text=f"📢 {baslik}", width=24, font=("Helvetica", 9, "bold")).pack(side="left")
            lbl_gorunen = ttk.Label(row, text=gorunen, foreground=fg, width=22)
            lbl_gorunen.pack(side="left", fill="x", expand=True, padx=4)

            ttk.Button(row, text="📁 Seç", width=6, command=lambda i=idx: self._anons_dosya_sec(i)).pack(side="left", padx=2)
            ttk.Button(row, text="▶ Çal", width=6, command=lambda i=idx: self._anons_cal(i)).pack(side="left", padx=2)
            ttk.Button(row, text="✏️ Başlık", width=7, command=lambda i=idx: self._anons_duzenle(i)).pack(side="left", padx=2)
            ttk.Button(row, text="🗑️ Sil", width=5, command=lambda i=idx: self._anons_sil(i)).pack(side="left", padx=2)

    def _anons_ekle_penceresi(self):
        w = tk.Toplevel(self.root)
        w.title("➕ Yeni Özel Anons Ekle")
        w.geometry("400x180")
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=16)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Anons Başlığı (Örn: Toplantı / Tören Duyurusu):", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 4))
        ent_baslik = ttk.Entry(f, width=35, font=("Helvetica", 10))
        ent_baslik.pack(fill="x", pady=(0, 12))
        ent_baslik.focus()

        def kaydet():
            b = ent_baslik.get().strip()
            if not b:
                messagebox.showwarning("Uyarı", "Lütfen bir anons başlığı yazın!", parent=w)
                return
            yeni_anons = {
                "id": f"anons_{int(time.time())}",
                "baslik": b,
                "dosya": ""
            }
            if "anonslar" not in self.ayarlar:
                self.ayarlar["anonslar"] = []
            self.ayarlar["anonslar"].append(yeni_anons)
            self.ayarlari_kaydet()
            self._ciz_anons_listesi()
            self._guncelle_hizli_anonslar()
            w.destroy()

        btn_kaydet = tk.Button(
            f, text="💾 Anonsu Ekle", font=("Helvetica", 10, "bold"),
            bg=self.c_success, fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=kaydet
        )
        btn_kaydet.pack(fill="x", ipady=4)

    def _anons_dosya_sec(self, idx):
        anonslar = self.ayarlar.get("anonslar", [])
        if idx >= len(anonslar):
            return
        anons = anonslar[idx]
        try:
            yol = filedialog.askopenfilename(
                parent=self.root,
                title=f"'{anons.get('baslik')}' İçin Ses Dosyası Seçin",
                filetypes=[
                    ("Desteklenen Ses Dosyaları", "*.mp3 *.wav *.ogg *.aac *.m4a *.wma *.flac"),
                    ("Tüm Dosyalar", "*.*")
                ]
            )
            if yol:
                anons["dosya"] = os.path.normpath(yol)
                self.ayarlari_kaydet()
                self._ciz_anons_listesi()
                self._guncelle_hizli_anonslar()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya seçilirken sorun oluştu: {e}", parent=self.root)

    def _anons_cal(self, idx):
        anonslar = self.ayarlar.get("anonslar", [])
        if idx >= len(anonslar):
            return
        anons = anonslar[idx]
        yol = anons.get("dosya", "")
        baslik = anons.get("baslik", "Özel Anons")
        if not yol or not os.path.exists(yol):
            messagebox.showwarning("Dosya Yok", f"'{baslik}' için bir ses dosyası seçilmemiş veya dosya bulunamadı!\nLütfen '📁 Seç' butonuna basarak bir ses dosyası belirleyin.", parent=self.root)
            return

        vol = self.ayarlar["genel"].get("ses_seviyesi", 90)
        self.lbl_calan.config(text=f"▶ Çalıyor: {baslik}")
        self.lbl_status.config(text=f"Özel Anons Oynatılıyor: {baslik}")

        def bitti():
            self.root.after(0, lambda: self.lbl_calan.config(text=""))
            self.root.after(0, lambda: self.lbl_status.config(text="Anons tamamlandı."))

        target_dev = self.ayarlar["genel"].get("ses_aygiti", "default")
        pref_engine = self.ayarlar["genel"].get("ses_motoru", "otomatik")
        self.player.play(yol, volume=vol, title=baslik, on_finish=bitti, preferred=pref_engine, target_device=target_dev)

    def _anons_duzenle(self, idx):
        anonslar = self.ayarlar.get("anonslar", [])
        if idx >= len(anonslar):
            return
        anons = anonslar[idx]

        w = tk.Toplevel(self.root)
        w.title("✏️ Anons Başlığını Düzenle")
        w.geometry("380x160")
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=16)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Yeni Anons Başlığı:", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 4))
        ent = ttk.Entry(f, width=35, font=("Helvetica", 10))
        ent.insert(0, anons.get("baslik", ""))
        ent.pack(fill="x", pady=(0, 12))
        ent.focus()

        def guncelle():
            b = ent.get().strip()
            if b:
                anons["baslik"] = b
                self.ayarlari_kaydet()
                self._ciz_anons_listesi()
                self._guncelle_hizli_anonslar()
                w.destroy()

        btn_kaydet = tk.Button(
            f, text="💾 Güncelle", font=("Helvetica", 10, "bold"),
            bg=self.c_primary, fg="white", activebackground="#123040", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=guncelle
        )
        btn_kaydet.pack(fill="x", ipady=4)

    def _anons_sil(self, idx):
        anonslar = self.ayarlar.get("anonslar", [])
        if idx >= len(anonslar):
            return
        anons = anonslar[idx]
        if messagebox.askyesno("Onay", f"'{anons.get('baslik')}' anonsunu silmek istediğinizden emin misiniz?", parent=self.root):
            anonslar.pop(idx)
            self.ayarlari_kaydet()
            self._ciz_anons_listesi()
            self._guncelle_hizli_anonslar()

    def _guncelle_hizli_anonslar(self):
        if not hasattr(self, "f_hizli_anons"):
            return
        for w in self.f_hizli_anons.winfo_children():
            w.destroy()

        anonslar = self.ayarlar.get("anonslar", [])
        if not anonslar:
            ttk.Label(self.f_hizli_anons, text="Henüz anons tanımlanmadı.\n('Sesler & Anonslar' sekmesinden ekleyebilirsiniz)", font=("Helvetica", 8), foreground="#6c757d").pack(pady=4)
            return

        for idx, a in enumerate(anonslar):
            baslik = a.get("baslik", f"Anons {idx+1}")
            btn = tk.Button(
                self.f_hizli_anons, text=f"📢 {baslik}", font=("Helvetica", 9, "bold"),
                bg="#264653", fg="white", activebackground="#1d3557", activeforeground="white",
                bd=2, relief="groove", cursor="hand2",
                command=lambda i=idx: self._anons_cal(i)
            )
            btn.pack(fill="x", pady=2, ipady=3)

    # -------------------------------------------------------------
    # SINAV & SESSİZ MOD YÖNETİMİ
    # -------------------------------------------------------------
    def toggle_sessiz_mod(self):
        if self.sessiz_mod:
            self._sessiz_mod_kapat()
        else:
            self._sessiz_mod_penceresi()

    def _sessiz_mod_penceresi(self):
        w = tk.Toplevel(self.root)
        w.title("🔕 Sınav / Sessiz Modu Başlat")
        w.geometry("420x330")
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()

        f = ttk.Frame(w, padding=16)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="🔕 Sınav / Sessiz Mod Ayarı", font=("Helvetica", 12, "bold"), foreground=self.c_primary).pack(pady=(0, 6))
        ttk.Label(f, text="Sessiz mod devredeyken otomatik ziller çalmaz.\nLütfen susturma süresini seçin:", font=("Helvetica", 9), justify="center").pack(pady=(0, 10))

        secim = tk.StringVar(value="manuel")

        options = [
            ("manuel", "⏰ Manuel Kapatana Kadar (Süresiz)"),
            ("1saat", "⏱️ 1 Saat Boyunca (60 Dakika)"),
            ("2saat", "⏱️ 2 Saat Boyunca (Deneme Sınavı - 120 Dk)"),
            ("3saat", "⏱️ 3 Saat Boyunca (180 Dk)"),
            ("gun_sonu", "📅 Bugün Boyunca (Saat 23:59'a kadar)")
        ]

        for val, metin in options:
            ttk.Radiobutton(f, text=metin, value=val, variable=secim).pack(anchor="w", pady=3)

        def uygula():
            s = secim.get()
            now = datetime.now()
            if s == "manuel":
                self.sessiz_mod = True
                self.sessiz_mod_bitis = None
                self.sessiz_mod_aciklama = "Süresiz"
            elif s == "1saat":
                self.sessiz_mod = True
                self.sessiz_mod_bitis = now + timedelta(hours=1)
                self.sessiz_mod_aciklama = "1 Saat"
            elif s == "2saat":
                self.sessiz_mod = True
                self.sessiz_mod_bitis = now + timedelta(hours=2)
                self.sessiz_mod_aciklama = "2 Saat"
            elif s == "3saat":
                self.sessiz_mod = True
                self.sessiz_mod_bitis = now + timedelta(hours=3)
                self.sessiz_mod_aciklama = "3 Saat"
            elif s == "gun_sonu":
                self.sessiz_mod = True
                self.sessiz_mod_bitis = now.replace(hour=23, minute=59, second=59)
                self.sessiz_mod_aciklama = "Bugünlük"

            self.ayarlar["genel"]["sessiz_mod"] = True
            self.ayarlari_kaydet()
            self._sessiz_mod_guncelle_ui()
            w.destroy()
            messagebox.showinfo("Sessiz Mod Devrede", f"Sınav / Sessiz Mod başarıyla aktif edildi ({self.sessiz_mod_aciklama}).\nOtomatik ziller susturuldu.", parent=self.root)

        btn_onay = tk.Button(
            f, text="🔕 Sessiz Modu Başlat", font=("Helvetica", 10, "bold"),
            bg="#f77f00", fg="white", activebackground="#d66800", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=uygula
        )
        btn_onay.pack(fill="x", ipady=5, pady=(15, 0))

    def _sessiz_mod_kapat(self):
        self.sessiz_mod = False
        self.sessiz_mod_bitis = None
        self.sessiz_mod_aciklama = ""
        self.ayarlar["genel"]["sessiz_mod"] = False
        self.ayarlari_kaydet()
        self._sessiz_mod_guncelle_ui()
        self.lbl_status.config(text="Sınav / Sessiz Mod kapatıldı. Ziller normal çalmaya devam edecek.")
        messagebox.showinfo("Bilgi", "Sınav / Sessiz Mod devre dışı bırakıldı.\nZiller normal zamanında çalacaktır.", parent=self.root)

    def _sessiz_mod_guncelle_ui(self):
        if not hasattr(self, "btn_sessiz_mod"):
            return
        if self.sessiz_mod:
            self.btn_sessiz_mod.config(
                text="🔇 SINAV MODU DEVREDE (Kapatmak İçin Tıkla)",
                bg="#f77f00", fg="white", activebackground="#d66800"
            )
            self.lbl_status.config(text="🔇 Sınav Modu devrede - Ziller susturuldu.")
        else:
            self.btn_sessiz_mod.config(
                text="🔕 Sınav / Sessiz Modu Aç",
                bg="#4a5568", fg="white", activebackground="#2d3748"
            )

    # -------------------------------------------------------------
    # ÇİZELGE DIŞA & İÇE AKTARMA (YEDEKLE & YÜKLE)
    # -------------------------------------------------------------
    def cizelge_disa_aktar(self):
        try:
            varsayilan_ad = f"okul_zil_cizelgesi_{datetime.now().strftime('%Y%m%d')}.json"
            yol = filedialog.asksaveasfilename(
                parent=self.root,
                title="Zil Çizelgesini Dışa Aktar / Yedekle",
                initialfile=varsayilan_ad,
                defaultextension=".json",
                filetypes=[("JSON Zil Çizelgesi (*.json)", "*.json"), ("Tüm Dosyalar (*.*)", "*.*")]
            )
            if yol:
                yedek_veri = {
                    "versiyon": "2.6.0",
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "program": self.ayarlar.get("program", [])
                }
                with open(yol, "w", encoding="utf-8") as f:
                    json.dump(yedek_veri, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Başarılı", f"Zil çizelgesi ({len(self.ayarlar.get('program', []))} kayıt) başarıyla dışa aktarıldı:\n{yol}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu: {e}", parent=self.root)

    def cizelge_ice_aktar(self):
        try:
            yol = filedialog.askopenfilename(
                parent=self.root,
                title="Zil Çizelgesini İçe Aktar / Yükle",
                filetypes=[("JSON Zil Çizelgesi (*.json)", "*.json"), ("Tüm Dosyalar (*.*)", "*.*")]
            )
            if yol:
                with open(yol, "r", encoding="utf-8") as f:
                    data = json.load(f)

                program_listesi = None
                if isinstance(data, dict) and "program" in data and isinstance(data["program"], list):
                    program_listesi = data["program"]
                elif isinstance(data, list):
                    program_listesi = data

                if program_listesi is not None:
                    if messagebox.askyesno("Onay", f"Seçilen dosyada {len(program_listesi)} adet zil kaydı bulundu.\nMevcut çizelgenin üzerine yazılsın mı?", parent=self.root):
                        self.ayarlar["program"] = program_listesi
                        self.ayarlari_kaydet()
                        self.tabloyu_doldur()
                        messagebox.showinfo("Başarılı", f"{len(program_listesi)} adet zil kaydı başarıyla içe aktarıldı!", parent=self.root)
                else:
                    messagebox.showerror("Geçersiz Dosya", "Dosya içeriğinde geçerli bir zil programı bulunamadı.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarma sırasında hata oluştu: {e}", parent=self.root)

    # -------------------------------------------------------------
    # SEKME 5: KENDİ ANONSU OLUŞTURUCU (YAPAY ZEKA ANONS STÜDYOSU)
    # -------------------------------------------------------------
    def _kur_tab_anons_olustur(self):
        canvas = tk.Canvas(self.tab_anons_olustur, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_anons_olustur, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ÜST BİLGİ KARTI
        f_info = ttk.LabelFrame(scrollable_frame, text="🎙️ Yapay Zeka Doğal Seslendirme & Anons Stüdyosu", padding=10)
        f_info.pack(fill="x", expand=True, padx=5, pady=6)

        ttk.Label(
            f_info,
            text="Okulunuz için anons metnini yazın, kadın/erkek öğretmen ses modelleriyle seslendirin,\n"
                 "dinleyip önizleyin ve tek tıkla doğrudan programın anons kütüphanesine kaydedin.",
            font=("Helvetica", 9), foreground="#495057"
        ).pack(anchor="w")

        # 1. KART: METİN GİRİŞİ & HAZIR ŞABLONLAR
        f_metin = ttk.LabelFrame(scrollable_frame, text="✍️ Anons Metni", padding=10)
        f_metin.pack(fill="x", expand=True, padx=5, pady=6)

        ttk.Label(f_metin, text="Hazır Örnek Şablonlar (Tıklayarak Yükleyin):", font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 4))

        f_btn_sablon = ttk.Frame(f_metin)
        f_btn_sablon.pack(fill="x", pady=(0, 6))

        sablonlar = [
            ("🔔 Ders Bitişi", "Çay İlkokulu'nun Sevgili Öğrencileri ve Değerli Öğretmenleri! Derslerimiz sona ermiştir. Çay İlkokulu ailesi olarak iyi günler dileriz!"),
            ("🏫 Servis / Çıkış", "Sevgili öğrenciler, derslerimiz sona ermiştir. Servislerinize ve evinize dikkatli gidiniz. Hepinize iyi akşamlar."),
            ("☔ Yağmurlu Hava", "Dikkat! Dışarıda yağış olduğundan teneffüste bahçeye çıkılmayacaktır. Lütfen koridorlarda koşmadan sakin şekilde dinlenelim."),
            ("🇹🇷 Tören Çağrısı", "Değerli öğretmenlerimiz ve sevgili öğrencilerimiz! Bayrak töreni için lütfen sırayla okul bahçesinde toplanınız."),
            ("👥 Öğretmenler Kurulu", "Değerli öğretmenlerimiz, ders bitiminde öğretmenler odasında kısa bir kurul toplantısı yapılacaktır."),
            ("🧹 Temizle", "")
        ]

        for btn_adi, metin_icerik in sablonlar:
            if btn_adi == "🧹 Temizle":
                btn = ttk.Button(f_btn_sablon, text=btn_adi, command=lambda: self._anons_metni_yaz(""))
            else:
                btn = ttk.Button(f_btn_sablon, text=btn_adi, command=lambda m=metin_icerik: self._anons_metni_yaz(m))
            btn.pack(side="left", padx=2, pady=2)

        self.txt_anons_metin = tk.Text(f_metin, height=4, font=("Helvetica", 10), wrap="word")
        self.txt_anons_metin.pack(fill="x", expand=True, pady=4)
        self.txt_anons_metin.insert("1.0", "Çay İlkokulu'nun Sevgili Öğrencileri ve Değerli Öğretmenleri! Derslerimiz sona ermiştir. Çay İlkokulu ailesi olarak iyi günler dileriz!")

        # 2. KART: SES VE TONLAMA AYARLARI
        f_ses = ttk.LabelFrame(scrollable_frame, text="🎭 Seslendirmen ve Tonlama Ayarları", padding=10)
        f_ses.pack(fill="x", expand=True, padx=5, pady=6)

        row1 = ttk.Frame(f_ses)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Ses Modeli:", width=14, font=("Helvetica", 9, "bold")).pack(side="left")
        self.combo_ses_modeli = ttk.Combobox(row1, state="readonly", width=48)
        self.combo_ses_modeli["values"] = [
            "👩 Emel (Kadın Öğretmen - Tatlı & Neşeli İlkokul)",
            "👩 Emel (Kadın Öğretmen - Sıcak & Doğal)",
            "👩 Emel (Kadın Öğretmen - Resmi & Standart)",
            "👨 Ahmet (Erkek Öğretmen - Babacan & Neşeli)",
            "👨 Ahmet (Erkek Öğretmen - Sıcak & Sakin)",
            "👨 Ahmet (Erkek Öğretmen - Resmi & Standart)"
        ]
        self.combo_ses_modeli.current(0)
        self.combo_ses_modeli.pack(side="left", padx=5)

        row2 = ttk.Frame(f_ses)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Konuşma Hızı:", width=14, font=("Helvetica", 9)).pack(side="left")
        self.combo_anons_hiz = ttk.Combobox(row2, state="readonly", width=22)
        self.combo_anons_hiz["values"] = [
            "Çok Sakin / Yavaş (-10%)",
            "Sakin / İlkokul (-5%)",
            "Normal Hız (0%)",
            "Hafif Hızlı (+5%)",
            "Hızlı / Dinamik (+10%)"
        ]
        self.combo_anons_hiz.current(1)
        self.combo_anons_hiz.pack(side="left", padx=5)

        ttk.Label(row2, text="Neşe / Canlılık (Pitch):", font=("Helvetica", 9)).pack(side="left", padx=(12, 5))
        self.combo_anons_pitch = ttk.Combobox(row2, state="readonly", width=20)
        self.combo_anons_pitch["values"] = [
            "Çok Neşeli (+6Hz)",
            "Neşeli & Canlı (+3Hz)",
            "Standart / Doğal (0Hz)",
            "Tok / Ağırbaşlı (-3Hz)"
        ]
        self.combo_anons_pitch.current(0)
        self.combo_anons_pitch.pack(side="left", padx=5)

        # 3. KART: ÖNİZLEME & DİNLEME
        f_onizleme = ttk.LabelFrame(scrollable_frame, text="▶️ Dinleme & Önizleme", padding=10)
        f_onizleme.pack(fill="x", expand=True, padx=5, pady=6)

        row_play = ttk.Frame(f_onizleme)
        row_play.pack(fill="x", pady=3)

        self.btn_anons_onizle = tk.Button(
            row_play, text="▶️ Önizlemeyi Dinle", font=("Helvetica", 10, "bold"),
            bg="#0284c7", fg="white", activebackground="#0369a1", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", padx=12, pady=4,
            command=self._anons_onizleme_yap
        )
        self.btn_anons_onizle.pack(side="left", padx=(0, 8))

        self.btn_anons_durdur = tk.Button(
            row_play, text="⏹ Durdur", font=("Helvetica", 10, "bold"),
            bg="#ef4444", fg="white", activebackground="#dc2626", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", padx=12, pady=4,
            command=self._anons_onizleme_durdur
        )
        self.btn_anons_durdur.pack(side="left", padx=(0, 12))

        self.lbl_anons_durum = ttk.Label(row_play, text="Hazır. 'Önizlemeyi Dinle' butonuna basabilirsiniz.", font=("Helvetica", 9, "italic"), foreground="#4b5563")
        self.lbl_anons_durum.pack(side="left")

        # 4. KART: KAYDETME VE PROGRAMA EKLEME
        f_kayit = ttk.LabelFrame(scrollable_frame, text="💾 Anonsu Kaydet & Programa Tanıt", padding=10)
        f_kayit.pack(fill="x", expand=True, padx=5, pady=6)

        row_k1 = ttk.Frame(f_kayit)
        row_k1.pack(fill="x", pady=3)

        ttk.Label(row_k1, text="Dosya Adı:", width=14, font=("Helvetica", 9, "bold")).pack(side="left")
        self.ent_anons_dosya_adi = ttk.Entry(row_k1, width=28, font=("Helvetica", 10))
        self.ent_anons_dosya_adi.insert(0, "yeni_anons")
        self.ent_anons_dosya_adi.pack(side="left", padx=5)
        ttk.Label(row_k1, text=".mp3", font=("Helvetica", 10, "bold"), foreground="#6b7280").pack(side="left")

        row_k2 = ttk.Frame(f_kayit)
        row_k2.pack(fill="x", pady=3)

        kayit_yeri = anons_kayit_dizini_getir()
        ttk.Label(row_k2, text="Kayıt Klasörü:", width=14, font=("Helvetica", 9)).pack(side="left")
        self.lbl_kayit_klasoru = ttk.Label(row_k2, text=kayit_yeri, font=("Helvetica", 8), foreground="#2563eb")
        self.lbl_kayit_klasoru.pack(side="left", padx=5)

        row_k3 = ttk.Frame(f_kayit)
        row_k3.pack(fill="x", pady=4)

        self.var_anons_hizliya_ekle = tk.BooleanVar(value=True)
        chk_hizli = ttk.Checkbutton(
            row_k3,
            text="Ana Ekrandaki '📢 Özel Sesli Anonslar' hızlı duyuru butonlarına otomatik ekle",
            variable=self.var_anons_hizliya_ekle
        )
        chk_hizli.pack(side="left")

        row_k4 = ttk.Frame(f_kayit)
        row_k4.pack(fill="x", pady=6)

        btn_kaydet_anons = tk.Button(
            row_k4, text="💾 Anonslar Kütüphanesine Kaydet", font=("Helvetica", 10, "bold"),
            bg="#16a34a", fg="white", activebackground="#15803d", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", padx=14, pady=5,
            command=self._anons_kaydet_islemi
        )
        btn_kaydet_anons.pack(side="left")

    def _anons_metni_yaz(self, metin):
        self.txt_anons_metin.delete("1.0", "end")
        if metin:
            self.txt_anons_metin.insert("1.0", metin)

    def _anons_parametrelerini_al(self):
        secili_model = self.combo_ses_modeli.get()
        ses = "tr-TR-EmelNeural"
        if "Ahmet" in secili_model:
            ses = "tr-TR-AhmetNeural"

        hiz_str = self.combo_anons_hiz.get()
        rate = "-5%"
        if "-10%" in hiz_str: rate = "-10%"
        elif "-5%" in hiz_str: rate = "-5%"
        elif "0%" in hiz_str: rate = "+0%"
        elif "+5%" in hiz_str: rate = "+5%"
        elif "+10%" in hiz_str: rate = "+10%"

        pitch_str = self.combo_anons_pitch.get()
        pitch = "+5Hz"
        if "+6Hz" in pitch_str: pitch = "+6Hz"
        elif "+3Hz" in pitch_str: pitch = "+3Hz"
        elif "0Hz" in pitch_str: pitch = "+0Hz"
        elif "-3Hz" in pitch_str: pitch = "-3Hz"

        return ses, rate, pitch

    def _anons_onizleme_yap(self):
        metin = self.txt_anons_metin.get("1.0", "end").strip()
        if not metin:
            messagebox.showwarning("Uyarı", "Lütfen seslendirilecek bir anons metni yazın!", parent=self.root)
            return

        ses, rate, pitch = self._anons_parametrelerini_al()
        self.lbl_anons_durum.config(text="⏳ Yapay zeka seslendiriyor, lütfen bekleyin...", foreground="#d97706")
        self.btn_anons_onizle.config(state="disabled")

        import tempfile
        temp_mp3 = os.path.join(tempfile.gettempdir(), f"onizleme_anons_{int(time.time())}.mp3")

        def _arka_plan():
            ok, msg = ai_anons_sentezle(metin, temp_mp3, ses_modeli=ses, rate=rate, pitch=pitch)
            def _gui():
                self.btn_anons_onizle.config(state="normal")
                if ok:
                    self.lbl_anons_durum.config(text="▶️ Önizleme çalınıyor...", foreground="#16a34a")
                    motor = self.ayarlar["genel"].get("ses_motoru", "otomatik")
                    aygit = self.ayarlar["genel"].get("ses_aygiti", "default")
                    vol = self.ayarlar["genel"].get("ses_seviyesi", 90)
                    self.player.play(temp_mp3, volume=vol, title="Anons Önizleme", preferred=motor, target_device=aygit)
                else:
                    self.lbl_anons_durum.config(text=f"❌ Hata: {msg}", foreground="#dc2626")
                    messagebox.showerror("Hata", f"Ses oluşturulamadı:\n{msg}", parent=self.root)
            self.root.after(0, _gui)

        threading.Thread(target=_arka_plan, daemon=True).start()

    def _anons_onizleme_durdur(self):
        self.player.stop_all()
        self.lbl_anons_durum.config(text="⏹ Önizleme durduruldu.", foreground="#4b5563")

    def _anons_kaydet_islemi(self):
        metin = self.txt_anons_metin.get("1.0", "end").strip()
        if not metin:
            messagebox.showwarning("Uyarı", "Lütfen kaydedilecek bir anons metni yazın!", parent=self.root)
            return

        dosya_adi = self.ent_anons_dosya_adi.get().strip()
        if not dosya_adi:
            messagebox.showwarning("Uyarı", "Lütfen anons için bir dosya adı girin!", parent=self.root)
            return

        # Güvenli dosya adı yap
        for c in r'\/:*?"<>| ':
            dosya_adi = dosya_adi.replace(c, "_")
        if not dosya_adi.endswith(".mp3"):
            dosya_adi += ".mp3"

        kayit_klasoru = anons_kayit_dizini_getir()
        os.makedirs(kayit_klasoru, exist_ok=True)
        hedef_tam_yol = os.path.join(kayit_klasoru, dosya_adi)

        ses, rate, pitch = self._anons_parametrelerini_al()
        self.lbl_anons_durum.config(text="⏳ Dosya kaydediliyor...", foreground="#d97706")

        def _arka_plan():
            ok, msg = ai_anons_sentezle(metin, hedef_tam_yol, ses_modeli=ses, rate=rate, pitch=pitch)
            def _gui():
                if ok:
                    self.lbl_anons_durum.config(text=f"✅ Kaydedildi: {dosya_adi}", foreground="#16a34a")
                    if self.var_anons_hizliya_ekle.get():
                        baslik = dosya_adi.replace(".mp3", "").replace("_", " ").title()
                        yeni_anons = {
                            "id": f"anons_{int(time.time())}",
                            "baslik": f"📢 {baslik}",
                            "dosya": hedef_tam_yol
                        }
                        if "anonslar" not in self.ayarlar:
                            self.ayarlar["anonslar"] = []
                        self.ayarlar["anonslar"].append(yeni_anons)
                        self.ayarlari_kaydet()
                        self._ciz_anons_listesi()
                        self._guncelle_hizli_anonslar()

                    messagebox.showinfo(
                        "Başarılı",
                        f"Anons ses dosyası başarıyla üretildi ve kaydedildi!\n\n"
                        f"📁 Konum: {hedef_tam_yol}\n"
                        f"{'✅ Ana ekrandaki hızlı duyuru butonlarına eklendi.' if self.var_anons_hizliya_ekle.get() else ''}",
                        parent=self.root
                    )
                else:
                    self.lbl_anons_durum.config(text=f"❌ Hata: {msg}", foreground="#dc2626")
                    messagebox.showerror("Kayıt Hatası", f"Anons kaydedilemedi:\n{msg}", parent=self.root)
            self.root.after(0, _gui)

        threading.Thread(target=_arka_plan, daemon=True).start()

    # -------------------------------------------------------------
    # SEKME 6: SİSTEM & GELİŞMİŞ AYARLAR
    # -------------------------------------------------------------
    def _kur_tab_ayarlar(self):
        canvas = tk.Canvas(self.tab_ayarlar, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_ayarlar, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Ses Oynatıcı Motoru
        lf_motor = ttk.LabelFrame(scrollable_frame, text="Ses Oynatıcı Motoru", padding=10)
        lf_motor.pack(fill="x", expand=True, padx=5, pady=6)

        ttk.Label(lf_motor, text="Sistemde bulunan ve desteklenen ses motorları:").pack(anchor="w", pady=(0, 4))
        motor_str = ", ".join(self.player.available_engines) if self.player.available_engines else "Hiçbir oynatıcı bulunamadı!"
        ttk.Label(lf_motor, text=f"Tespit Edilenler: {motor_str}", font=("Helvetica", 9, "bold"), foreground=self.c_primary).pack(anchor="w", pady=(0, 6))

        f_sec = ttk.Frame(lf_motor)
        f_sec.pack(fill="x")
        ttk.Label(f_sec, text="Tercih Edilen Motor:").pack(side="left")
        motor_secenekler = ["otomatik"] + self.player.available_engines
        self.cmb_motor = ttk.Combobox(f_sec, values=motor_secenekler, state="readonly", width=15)
        self.cmb_motor.set(self.ayarlar["genel"].get("ses_motoru", "otomatik"))
        self.cmb_motor.pack(side="left", padx=8)

        # 2. Teneffüs Müzik Yayını
        lf_ten = ttk.LabelFrame(scrollable_frame, text="Teneffüs Müzik Yayını (Radyo)", padding=10)
        lf_ten.pack(fill="x", expand=True, padx=5, pady=6)

        self.var_ten_aktif = tk.BooleanVar(value=self.ayarlar["genel"].get("teneffus_muzik_aktif", False))
        chk_ten = ttk.Checkbutton(lf_ten, text="Teneffüslerde otomatik müzik yayını yap (Ders zilinde otomatik kesilir)", variable=self.var_ten_aktif)
        chk_ten.pack(anchor="w", pady=4)

        f_ten_vol = ttk.Frame(lf_ten)
        f_ten_vol.pack(fill="x", pady=4)
        ttk.Label(f_ten_vol, text="Teneffüs Müziği Ses Seviyesi:").pack(side="left")
        self.scale_ten_vol = ttk.Scale(f_ten_vol, from_=0, to=100, orient="horizontal")
        self.scale_ten_vol.set(self.ayarlar["genel"].get("teneffus_ses_seviyesi", 50))
        self.scale_ten_vol.pack(side="left", fill="x", expand=True, padx=8)

        # 3. Ses Çıkış Portu / Amfi Yönlendirme
        lf_yonlendirme = ttk.LabelFrame(scrollable_frame, text="🔊 Ses Çıkış Aygıtı (Hoparlör / Amfi / Ses Kartı Seçimi)", padding=10)
        lf_yonlendirme.pack(fill="x", expand=True, padx=5, pady=6)

        ttk.Label(lf_yonlendirme, text="Okul zil seslerinin çalınacağı ses kartı veya çıkış portunu seçin:\n(Örn: Anakart arka jakı amfiye bağlıysa arka çıkışı veya USB Ses Kartını seçebilirsiniz)", font=("Helvetica", 9)).pack(anchor="w", pady=(0, 6))

        f_aygit_row = ttk.Frame(lf_yonlendirme)
        f_aygit_row.pack(fill="x", pady=2)
        ttk.Label(f_aygit_row, text="Ses Çıkışı:").pack(side="left")

        self.audio_devices = self.player.get_audio_devices()
        aygit_etiketler = [ad for ad, val in self.audio_devices]
        self.cmb_aygit = ttk.Combobox(f_aygit_row, values=aygit_etiketler, state="readonly", width=38)

        kayitli_aygit = self.ayarlar["genel"].get("ses_aygiti", "default")
        secili_ad = aygit_etiketler[0] if aygit_etiketler else "Varsayılan Sistem Çıkışı"
        for ad, val in self.audio_devices:
            if val == kayitli_aygit or ad == kayitli_aygit:
                secili_ad = ad
                break
        self.cmb_aygit.set(secili_ad)
        self.cmb_aygit.pack(side="left", padx=8, fill="x", expand=True)

        btn_yenile = ttk.Button(f_aygit_row, text="🔄 Yenile", command=self._ses_aygitlarini_yenile)
        btn_yenile.pack(side="left", padx=4)

        btn_test_ses = tk.Button(
            f_aygit_row, text="▶ Test Et", font=("Helvetica", 9, "bold"),
            bg="#2a9d8f", fg="white", activebackground="#1e6b34", activeforeground="white",
            relief="raised", bd=1, cursor="hand2", command=self._test_sesi_cal
        )
        btn_test_ses.pack(side="left", padx=4)

        # 4. Klavye Kısayol Tuşları
        lf_kisayol = ttk.LabelFrame(scrollable_frame, text="⌨️ Klavye Kısayol Tuşları (Değiştirilebilir)", padding=10)
        lf_kisayol.pack(fill="x", expand=True, padx=5, pady=6)

        ttk.Label(lf_kisayol, text="Hızlı tören ve acil eylemler için klavyeden kısayol tuşları atayabilirsiniz:", font=("Helvetica", 9)).pack(anchor="w", pady=(0, 6))

        aksiyonlar = [
            ("istiklal", "🇹🇷 İstiklal Marşı", "F9"),
            ("saygi_istiklal", "⏱️ Saygı Duruşu + İstiklal", "F10"),
            ("siren", "🚨 Acil Durum / Siren", "F11"),
            ("durdur", "🛑 Çalan Sesi Durdur", "Space"),
            ("sessiz_mod", "🔕 Sınav / Sessiz Mod", "F8")
        ]

        tus_secenekleri = ["Kapalı", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "Space", "Escape"]
        self.cmb_kisayollar = {}

        for kod, ad, varsayilan in aksiyonlar:
            r = ttk.Frame(lf_kisayol)
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=ad, width=32, font=("Helvetica", 9, "bold")).pack(side="left")
            cmb = ttk.Combobox(r, values=tus_secenekleri, state="readonly", width=12)
            mevcut = self.ayarlar.get("kisayollar", {}).get(kod, varsayilan)
            cmb.set(mevcut if mevcut in tus_secenekleri else varsayilan)
            cmb.pack(side="right")
            self.cmb_kisayollar[kod] = cmb

        # 5. Genel Uygulama Davranışları
        lf_davranis = ttk.LabelFrame(scrollable_frame, text="Uygulama & Başlangıç Davranışı", padding=10)
        lf_davranis.pack(fill="x", expand=True, padx=5, pady=6)

        self.var_arkaplan = tk.BooleanVar(value=self.ayarlar["genel"].get("arka_planda_calis", False))
        chk_arkaplan = ttk.Checkbutton(lf_davranis, text="Pencere kapatıldığında arka planda çalışmaya devam et (Simge Durumu)", variable=self.var_arkaplan)
        chk_arkaplan.pack(anchor="w", pady=4)

        f_alt_btn = ttk.Frame(scrollable_frame)
        f_alt_btn.pack(fill="x", padx=5, pady=15)

        btn_kaydet_genel = tk.Button(
            f_alt_btn, text="💾 Ayarları Kaydet", font=("Helvetica", 10, "bold"),
            bg=self.c_primary, fg="white", activebackground="#123040", activeforeground="white",
            relief="raised", bd=2, cursor="hand2", command=self._ayarlari_uygula_ve_kaydet
        )
        btn_kaydet_genel.pack(side="left", padx=5, ipady=4)

        btn_sifirla = ttk.Button(f_alt_btn, text="🔄 Fabrika Ayarlarına Dön", command=self._fabrika_ayarlarina_don)
        btn_sifirla.pack(side="right", padx=5)

    def _kisayollari_bagla(self):
        tus_listesi = ["<F1>", "<F2>", "<F3>", "<F4>", "<F5>", "<F6>", "<F7>", "<F8>", "<F9>", "<F10>", "<F11>", "<F12>", "<space>", "<Escape>"]
        for t in tus_listesi:
            try:
                self.root.unbind_all(t)
            except Exception:
                pass

        kisayollar = self.ayarlar.get("kisayollar", {})
        tus_haritasi = {
            "Space": "<space>",
            "Escape": "<Escape>",
        }

        def _bagla(aksiyon, tus_adi):
            if not tus_adi or tus_adi == "Kapalı":
                return
            t_kod = tus_haritasi.get(tus_adi, f"<{tus_adi}>")

            def handler(event=None):
                if aksiyon == "durdur":
                    self.sesi_durdur()
                elif aksiyon == "istiklal":
                    self.manuel_ses_cal("istiklal", "İstiklal Marşı")
                elif aksiyon == "saygi_istiklal":
                    self.manuel_ses_cal("saygi_istiklal", "Saygı Duruşu + İstiklal")
                elif aksiyon == "siren":
                    self.manuel_ses_cal("siren", "Acil Durum / Siren")
                elif aksiyon == "sessiz_mod":
                    self.toggle_sessiz_mod()

            try:
                self.root.bind_all(t_kod, handler)
            except Exception as e:
                print(f"Kısayol bağlama hatası ({tus_adi}): {e}")

        for aksiyon, tus in kisayollar.items():
            _bagla(aksiyon, tus)

    def _ses_aygitlarini_yenile(self):
        self.audio_devices = self.player.get_audio_devices()
        aygit_etiketler = [ad for ad, val in self.audio_devices]
        self.cmb_aygit["values"] = aygit_etiketler
        if aygit_etiketler:
            self.cmb_aygit.set(aygit_etiketler[0])
        messagebox.showinfo("Bilgi", f"{len(aygit_etiketler)} ses çıkış aygıtı listelendi.", parent=self.root)

    def _test_sesi_cal(self):
        secili_metin = self.cmb_aygit.get()
        target_dev = "default"
        for ad, val in self.audio_devices:
            if ad == secili_metin:
                target_dev = val
                break

        test_ses = self.ayarlar["sesler"].get("ogrenci", "")
        if not test_ses or not os.path.exists(test_ses):
            test_ses = varsayilan_ses_bul("Ses/muzik1.mp3")

        if not test_ses or not os.path.exists(test_ses):
            messagebox.showwarning("Test", "Çalınacak test ses dosyası bulunamadı!", parent=self.root)
            return

        vol = self.ayarlar["genel"].get("ses_seviyesi", 90)
        pref_engine = self.cmb_motor.get() if hasattr(self, "cmb_motor") else "otomatik"
        ok = self.player.play(test_ses, volume=vol, title="Test Sesi", preferred=pref_engine, target_device=target_dev)
        if ok:
            self.lbl_calan.config(text=f"▶ Test Sesi Çalıyor ({secili_metin})")
        else:
            messagebox.showerror("Hata", "Test sesi başlatılamadı.", parent=self.root)

    def _ayarlari_uygula_ve_kaydet(self):
        self.ayarlar["genel"]["ses_motoru"] = self.cmb_motor.get()
        self.ayarlar["genel"]["teneffus_muzik_aktif"] = self.var_ten_aktif.get()
        self.ayarlar["genel"]["teneffus_ses_seviyesi"] = int(self.scale_ten_vol.get())
        self.ayarlar["genel"]["arka_planda_calis"] = self.var_arkaplan.get()

        secili_metin = self.cmb_aygit.get()
        target_dev = "default"
        for ad, val in self.audio_devices:
            if ad == secili_metin:
                target_dev = val
                break
        self.ayarlar["genel"]["ses_aygiti"] = target_dev

        # Kısayolları kaydet
        if "kisayollar" not in self.ayarlar:
            self.ayarlar["kisayollar"] = {}
        for kod, cmb in self.cmb_kisayollar.items():
            self.ayarlar["kisayollar"][kod] = cmb.get()

        self.ayarlari_kaydet()
        self._kisayollari_bagla()
        messagebox.showinfo("Bilgi", "Sistem ve kısayol ayarları başarıyla kaydedildi!")

    def _fabrika_ayarlarina_don(self):
        if messagebox.askyesno("Onay", "Tüm ayarlar varsayılana döndürülecek. Onaylıyor musunuz?"):
            self.ayarlar = json.loads(json.dumps(VARSAYILAN_AYARLAR))
            self._varsayilan_sesleri_kontrol_et()
            self.ayarlari_kaydet()
            self.tabloyu_doldur()
            self._ciz_anons_listesi()
            self._guncelle_hizli_anonslar()
            self._kisayollari_bagla()
            messagebox.showinfo("Bilgi", "Ayarlar varsayılan değerlere sıfırlandı.")

    # -------------------------------------------------------------
    # SES VE ÇALMA MANTIĞI
    # -------------------------------------------------------------
    def _on_vol_change(self, val):
        v = int(float(val))
        if hasattr(self, "lbl_vol_val") and self.lbl_vol_val:
            self.lbl_vol_val.config(text=f"%{v}")
        if "genel" in self.ayarlar:
            self.ayarlar["genel"]["ses_seviyesi"] = v

    def sesi_durdur(self):
        self.muzik_caliyor = False
        self.player.stop_all()
        self._guncelle_muzik_ui("")
        self.lbl_calan.config(text="")
        self.lbl_status.config(text="Ses manuel olarak durduruldu.")

    def manuel_ses_cal(self, kod, baslik="Ses"):
        yol = self.ayarlar["sesler"].get(kod, "")
        if not yol or not os.path.exists(yol):
            messagebox.showwarning("Ses Dosyası Yok", f"'{baslik}' için tanımlı ses dosyası bulunamadı!\nLütfen 'Sesler & Anonslar' sekmesinden bir dosya seçin.")
            return

        vol = self.ayarlar["genel"].get("ses_seviyesi", 90)
        self.lbl_calan.config(text=f"▶ Çalıyor: {baslik}")
        self.lbl_status.config(text=f"Manuel Oynatılıyor: {baslik}")

        def bitti():
            self.root.after(0, lambda: self.lbl_calan.config(text=""))
            self.root.after(0, lambda: self.lbl_status.config(text="Ses tamamlandı."))

        target_dev = self.ayarlar["genel"].get("ses_aygiti", "default")
        pref_engine = self.ayarlar["genel"].get("ses_motoru", "otomatik")
        ok = self.player.play(yol, volume=vol, title=baslik, on_finish=bitti, preferred=pref_engine, target_device=target_dev)
        if not ok:
            messagebox.showerror("Oynatma Hatası", f"Ses dosyası oynatılamadı. Sistemde ses motoru veya Qt Multimedia bileşenlerini kontrol edin.")

    def teneffus_muzigi_baslat(self):
        if not self.ayarlar["genel"].get("teneffus_muzik_aktif", False):
            return
        self.muzik_oynat()

    # -------------------------------------------------------------
    # ZAMANLAYICI & SAAT DÖNGÜSÜ
    # -------------------------------------------------------------
    def _gun_uygun_mu(self, gun_kurali, haftanin_gunu):
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        hedef_gun = gun_adlari[haftanin_gunu]

        if not gun_kurali:
            return False

        if isinstance(gun_kurali, list):
            return hedef_gun in gun_kurali

        if gun_kurali == "Hafta İçi (Pzt-Cum)":
            return haftanin_gunu < 5
        elif gun_kurali == "Pazartesi-Perşembe":
            return haftanin_gunu in [0, 1, 2, 3]
        elif gun_kurali == "Sadece Cuma":
            return haftanin_gunu == 4
        elif gun_kurali == "Haftanın Her Günü":
            return True
        elif gun_kurali == "Hafta Sonu (Cmt-Paz)":
            return haftanin_gunu in [5, 6]
        elif gun_kurali == hedef_gun:
            return True
        elif "," in gun_kurali:
            parcalar = [p.strip() for p in gun_kurali.split(",")]
            for p in parcalar:
                if p == hedef_gun:
                    return True
                if p == "Hafta İçi (Pzt-Cum)" and haftanin_gunu < 5:
                    return True
                if p == "Pazartesi-Perşembe" and haftanin_gunu in [0, 1, 2, 3]:
                    return True
                if p == "Sadece Cuma" and haftanin_gunu == 4:
                    return True
                if p == "Haftanın Her Günü":
                    return True
                if p == "Hafta Sonu (Cmt-Paz)" and haftanin_gunu in [5, 6]:
                    return True
        return False

    def _zamanlayici_dongusu(self):
        while self.calisiyor:
            now = datetime.now()
            su_an = now.strftime("%H:%M")
            saniye = now.second
            haftanin_gunu = now.weekday()

            # Sessiz mod süresi doldu mu kontrolü
            if self.sessiz_mod and self.sessiz_mod_bitis is not None:
                if now >= self.sessiz_mod_bitis:
                    self.sessiz_mod = False
                    self.sessiz_mod_bitis = None
                    self.sessiz_mod_aciklama = ""
                    self.ayarlar["genel"]["sessiz_mod"] = False
                    self.ayarlari_kaydet()
                    self.root.after(0, self._sessiz_mod_guncelle_ui)

            for z in self.ayarlar.get("program", []):
                if not z.get("aktif", True):
                    continue

                saat = z["saat"]
                gun_kurali = z["gunler"]
                tur = z["tur"]

                if self._gun_uygun_mu(gun_kurali, haftanin_gunu) and su_an == saat:
                    anahtar = f"{su_an}_{tur}_{now.strftime('%Y%m%d')}"
                    if anahtar not in self.calinanlar_set:
                        self.calinanlar_set.add(anahtar)
                        tur_adi = ZIL_TURLERI.get(tur, tur)
                        self.son_calan_bilgi = f"{su_an} - {tur_adi}"
                        print(f"[ZİL ÇALIYOR] {su_an} -> {tur_adi}")

                        if not self.sessiz_mod:
                            self._otomatik_zil_cal(tur, tur_adi)
                        else:
                            print(f"[SINAV MODU DEVREDE] {tur_adi} susturuldu.")

            if saniye == 0 and now.minute == 0:
                bugun_str = now.strftime('%Y%m%d')
                self.calinanlar_set = {k for k in self.calinanlar_set if k.endswith(bugun_str)}

            time.sleep(1)

    def _otomatik_zil_cal(self, tur, tur_adi):
        # Ders başlangıçlarında veya gün sonu çıkışında çalan müziği kes
        if tur != "cikis":
            self.muzik_durdur()

        vol = self.ayarlar["genel"].get("ses_seviyesi", 90)
        yol = self.ayarlar["sesler"].get(tur, "")
        if yol and os.path.exists(yol):
            self.root.after(0, lambda: self.lbl_calan.config(text=f"🔔 Çalıyor: {tur_adi}"))
            self.root.after(0, lambda: self.lbl_status.config(text=f"Otomatik Zil: {tur_adi}"))

            def bitti():
                self.root.after(0, lambda: self.lbl_calan.config(text=""))
                if tur == "cikis":
                    self.teneffus_muzigi_baslat()

            target_dev = self.ayarlar["genel"].get("ses_aygiti", "default")
            pref_engine = self.ayarlar["genel"].get("ses_motoru", "otomatik")
            self.player.play(yol, volume=vol, title=tur_adi, on_finish=bitti, preferred=pref_engine, target_device=target_dev)

    # -------------------------------------------------------------
    # CANLI GUI GÜNCELLEMESİ (1 Saniyede Bir)
    # -------------------------------------------------------------
    def _gui_guncelle(self):
        now = datetime.now()
        self.lbl_clock.config(text=now.strftime("%H:%M:%S"))

        gunler_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        aylar_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        tarih_str = f"{gunler_tr[now.weekday()]}, {now.day} {aylar_tr[now.month-1]} {now.year}"
        self.lbl_tarih.config(text=tarih_str)

        haftanin_gunu = now.weekday()
        en_yakin_fark = None
        en_yakin_zil = None

        for z in self.ayarlar.get("program", []):
            if not z.get("aktif", True):
                continue
            if not self._gun_uygun_mu(z["gunler"], haftanin_gunu):
                continue

            z_saat, z_dakika = map(int, z["saat"].split(":"))
            hedef_dt = now.replace(hour=z_saat, minute=z_dakika, second=0, microsecond=0)

            fark = (hedef_dt - now).total_seconds()
            if fark >= 0:
                if en_yakin_fark is None or fark < en_yakin_fark:
                    en_yakin_fark = fark
                    en_yakin_zil = z

        if self.sessiz_mod:
            if self.sessiz_mod_bitis:
                fark_sn = max(0, (self.sessiz_mod_bitis - now).total_seconds())
                dk = int(fark_sn // 60)
                sn = int(fark_sn % 60)
                self.lbl_siradaki.config(text=f"🔕 Sınav Modu Aktif (Kalan: {dk:02d} dk {sn:02d} sn)")
            else:
                self.lbl_siradaki.config(text="🔕 Sınav Modu Aktif (Süresiz)")
            self.lbl_kalan_sure.config(text="Ziller Susturuldu")
        elif en_yakin_zil is not None:
            tur_adi = ZIL_TURLERI.get(en_yakin_zil["tur"], en_yakin_zil["tur"])
            dakika = int(en_yakin_fark // 60)
            saniye = int(en_yakin_fark % 60)
            self.lbl_siradaki.config(text=f"Sıradaki Zil: {en_yakin_zil['saat']} ({tur_adi})")
            self.lbl_kalan_sure.config(text=f"Kalan Süre: {dakika:02d} dk {saniye:02d} sn")
        else:
            self.lbl_siradaki.config(text="Bugün için başka zil bulunmuyor.")
            self.lbl_kalan_sure.config(text="Mesai / Ders Dışı")

        self.root.after(1000, self._gui_guncelle)

    def _on_kapat(self):
        arka_plan = self.ayarlar["genel"].get("arka_planda_calis", False)
        if arka_plan:
            self.root.iconify()
        else:
            self.calisiyor = False
            self.player.stop_all()
            self.root.destroy()
            sys.exit(0)


def main():
    root = tk.Tk()
    app = OkulZilApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
