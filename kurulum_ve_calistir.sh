#!/bin/bash
# =============================================================================
# E-Zil • Lubuntu / Pardus / Debian / Ubuntu Otomatik Kurulum ve Başlatma Betiği
# =============================================================================

set -e

echo "========================================================"
echo "    E-ZİL (Okul Zil & Tören Sistemi) Kurulumu Başlıyor   "
echo "========================================================"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
HEDEF_DIZIN="$HOME/.config/okul_zili"
HEDEF_SESLER="$HEDEF_DIZIN/sesler"

mkdir -p "$HEDEF_DIZIN"
mkdir -p "$HEDEF_SESLER"

echo "1) Gerekli paketler kontrol ediliyor ve kuruluyor..."
sudo apt-get update -y || true
sudo apt-get install -y python3 python3-tk mpv ffmpeg curl wget

echo "2) Ses ve medya dosyaları yapılandırılıyor..."
if [ -d "$SCRIPT_DIR/musics/e-zil-ses" ]; then
    cp -r "$SCRIPT_DIR/musics/e-zil-ses/"* "$HEDEF_SESLER/" 2>/dev/null || true
elif [ -d "$SCRIPT_DIR/musics" ]; then
    cp -r "$SCRIPT_DIR/musics/"* "$HEDEF_SESLER/" 2>/dev/null || true
fi

# Program dosyasını hedefe kopyala
cp "$SCRIPT_DIR/okul_zili.py" "$HEDEF_DIZIN/okul_zili.py"
chmod +x "$HEDEF_DIZIN/okul_zili.py"

# Simgeyi kopyala
if [ -f "$SCRIPT_DIR/icons/bell.svg" ]; then
    cp "$SCRIPT_DIR/icons/bell.svg" "$HEDEF_DIZIN/bell.svg"
elif [ -f "$SCRIPT_DIR/ezil1.png" ]; then
    cp "$SCRIPT_DIR/ezil1.png" "$HEDEF_DIZIN/bell.png"
fi

echo "3) Masaüstü Kısayolu ve Başlatıcı Oluşturuluyor..."
DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=Okul Zili
GenericName=Okul Zil ve Tören Sistemi
Comment=Otomatik Okul Zili ve Tören Yönetim Sistemi
Exec=python3 $HEDEF_DIZIN/okul_zili.py
Icon=$HEDEF_DIZIN/bell.svg
Terminal=false
Categories=Education;Utility;
StartupNotify=true"

# Masaüstü klasörüne yaz (Varsa)
if [ -d "$HOME/Desktop" ]; then
    echo "$DESKTOP_ENTRY" > "$HOME/Desktop/okul_zili.desktop"
    chmod +x "$HOME/Desktop/okul_zili.desktop"
elif [ -d "$HOME/Masaüstü" ]; then
    echo "$DESKTOP_ENTRY" > "$HOME/Masaüstü/okul_zili.desktop"
    chmod +x "$HOME/Masaüstü/okul_zili.desktop"
fi

# Uygulamalar menüsüne yaz
mkdir -p "$HOME/.local/share/applications"
echo "$DESKTOP_ENTRY" > "$HOME/.local/share/applications/okul_zili.desktop"
chmod +x "$HOME/.local/share/applications/okul_zili.desktop"

# Açılışta otomatik başlama (Autostart)
mkdir -p "$HOME/.config/autostart"
echo "$DESKTOP_ENTRY" > "$HOME/.config/autostart/okul_zili.desktop"

echo "========================================================"
echo "    Kurulum Başarıyla Tamamlandı!                       "
echo "    Masaüstündeki 'Okul Zili' simgesine tıklayabilirsiniz."
echo "========================================================"

# Uygulamayı başlat
python3 "$HEDEF_DIZIN/okul_zili.py" &
