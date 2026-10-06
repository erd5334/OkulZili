import os
import shutil

src_dir = os.path.dirname(os.path.abspath(__file__))
usb_dir = r"D:\OKUL_ZILI_KURULUM"

print(f"Paket güncelleniyor: {usb_dir} ...")

os.makedirs(usb_dir, exist_ok=True)

# 1. okul_zili.py
shutil.copy2(os.path.join(src_dir, "okul_zili.py"), os.path.join(usb_dir, "okul_zili.py"))

# 2. musics klasörü
usb_musics = os.path.join(usb_dir, "musics")
if os.path.exists(usb_musics):
    shutil.rmtree(usb_musics)
shutil.copytree(os.path.join(src_dir, "musics"), usb_musics)

# 3. icons ve png resimleri
usb_icons = os.path.join(usb_dir, "icons")
if os.path.exists(usb_icons):
    shutil.rmtree(usb_icons)
shutil.copytree(os.path.join(src_dir, "icons"), usb_icons)

for png in ["ezil0.png", "ezil1.png", "ezil2.png", "ezil3.png", "ezil4.png"]:
    p = os.path.join(src_dir, png)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(usb_dir, png))

# 4. Lubuntu Kurulum Scripti (Akıllı Paket Kontrolü - İnternet Gerektirmez!)
sh_lines = [
    "#!/bin/bash",
    "# =============================================================================",
    "# E-Zil - Lubuntu LXQt Otomatik Kurulum ve Baslatma Betigi",
    "# =============================================================================",
    "",
    "set -e",
    "",
    'echo "========================================================"',
    'echo "    E-ZIL (Okul Zil ve Toren Sistemi) Kurulumu          "',
    'echo "========================================================"',
    "",
    'KAYNAK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"',
    'HEDEF_DIR="$HOME/okul_zili"',
    'CONFIG_DIR="$HOME/.config/okul_zili"',
    "",
    '# 1) Paketler zaten kurulu mu kontrol et (Kuruluysa internet istemez!)',
    'EKSIK_PAKETLER=""',
    'for pkg in python3 python3-tk mpv ffmpeg; do',
    '    if ! dpkg -s "$pkg" >/dev/null 2>&1; then',
    '        EKSIK_PAKETLER="$EKSIK_PAKETLER $pkg"',
    '    fi',
    'done',
    "",
    'if [ -n "$EKSIK_PAKETLER" ]; then',
    '    echo "Eksik paketler bulundu:$EKSIK_PAKETLER. Yukleniyor..."',
    '    sudo apt-get update -y || true',
    '    sudo apt-get install -y $EKSIK_PAKETLER',
    'else',
    '    echo "Gerekli tum paketler (python3, python3-tk, mpv, ffmpeg) zaten kurulu."',
    '    echo "Internet baglantisi aranmadan hizli kuruluma geciliyor..."',
    'fi',
    "",
    'echo "2) Dosyalar ev dizinine ($HEDEF_DIR) kopyalaniyor..."',
    'mkdir -p "$HEDEF_DIR"',
    'mkdir -p "$CONFIG_DIR/sesler"',
    "",
    'cp -r "$KAYNAK_DIR/"* "$HEDEF_DIR/" 2>/dev/null || true',
    'chmod +x "$HEDEF_DIR/okul_zili.py"',
    "",
    'echo "3) Masaustu ve Baslat Menusu Kisayolu Olusturuluyor..."',
    'DESKTOP_ENTRY="[Desktop Entry]',
    "Version=1.0",
    "Type=Application",
    "Name=Okul Zili",
    "GenericName=Okul Zil ve Toren Sistemi",
    "Comment=Otomatik Okul Zili ve Toren Yonetim Sistemi",
    'Exec=python3 $HEDEF_DIR/okul_zili.py',
    'Icon=$HEDEF_DIR/icons/bell.svg',
    "Terminal=false",
    "Categories=Education;Utility;",
    'StartupNotify=true"',
    "",
    'if [ -d "$HOME/Desktop" ]; then',
    '    echo "$DESKTOP_ENTRY" > "$HOME/Desktop/okul_zili.desktop"',
    '    chmod +x "$HOME/Desktop/okul_zili.desktop"',
    "fi",
    'if [ -d "$HOME/Masaüstü" ]; then',
    '    echo "$DESKTOP_ENTRY" > "$HOME/Masaüstü/okul_zili.desktop"',
    '    chmod +x "$HOME/Masaüstü/okul_zili.desktop"',
    "fi",
    "",
    'mkdir -p "$HOME/.local/share/applications"',
    'echo "$DESKTOP_ENTRY" > "$HOME/.local/share/applications/okul_zili.desktop"',
    'chmod +x "$HOME/.local/share/applications/okul_zili.desktop"',
    "",
    'mkdir -p "$HOME/.config/autostart"',
    'echo "$DESKTOP_ENTRY" > "$HOME/.config/autostart/okul_zili.desktop"',
    "",
    'echo "========================================================"',
    'echo "    KURULUM TAMAMLANDI!                                 "',
    'echo "========================================================"',
    "",
    'python3 "$HEDEF_DIR/okul_zili.py" &',
    ""
]

sh_content = "\n".join(sh_lines).encode("utf-8")
with open(os.path.join(usb_dir, "LUBUNTU_KURULUM.sh"), "wb") as f:
    f.write(sh_content)

# 5. HIZLI GÜNCELLEME BETİĞİ (Sadece 1 saniyede günceller, hiçbir şey sormaz)
guncelle_lines = [
    "#!/bin/bash",
    'KAYNAK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"',
    'HEDEF_DIR="$HOME/okul_zili"',
    'cp "$KAYNAK_DIR/okul_zili.py" "$HEDEF_DIR/okul_zili.py"',
    'chmod +x "$HEDEF_DIR/okul_zili.py"',
    'echo "========================================================"',
    'echo "   OKUL ZILI 1 SANIYEDE GUNCELLENDI! (Internetsiz)       "',
    'echo "========================================================"',
    'python3 "$HEDEF_DIR/okul_zili.py" &',
    ""
]
with open(os.path.join(usb_dir, "GUNCELLE.sh"), "wb") as f:
    f.write("\n".join(guncelle_lines).encode("utf-8"))

# 6. Windows Başlatıcı
bat_content = "@echo off\r\ntitle Okul Zili Baslatici\r\nstart pythonw okul_zili.py\r\nexit\r\n"
with open(os.path.join(usb_dir, "WINDOWS_BASLAT.bat"), "w", encoding="utf-8") as f:
    f.write(bat_content)

print("Tamamlandı! D:\\OKUL_ZILI_KURULUM güncellendi.")
