#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Er Yazilim Okul Zili - Windows Portable EXE ve Paket Derleyici
"""

import os
import sys
import shutil
import subprocess
import zipfile

# Set encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "WINDOWS_KURULUMSUZ_OKUL_ZILI")
ZIP_OUTPUT = os.path.join(BASE_DIR, "OkulZili-v2.6.0-Windows-Portable.zip")

def prepare_icon():
    ico_path = os.path.join(BASE_DIR, "app_icon.ico")
    png_path = os.path.join(BASE_DIR, "ezil0.png")
    if not os.path.exists(ico_path) and os.path.exists(png_path):
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("[+] app_icon.ico olusturuldu.")
        except Exception as e:
            print(f"[!] Ikon olusturma uyarisi: {e}")
    return ico_path if os.path.exists(ico_path) else None

def build_exe():
    print("=" * 60)
    print("   Er Yazilim Okul Zili v2.6.0 - Windows Derleme")
    print("=" * 60)
    
    ico_path = prepare_icon()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "OkulZili",
        "--clean",
    ]
    
    if ico_path:
        cmd.extend(["--icon", ico_path])
        
    cmd.append(os.path.join(BASE_DIR, "okul_zili.py"))
    
    print("[*] PyInstaller calistiriliyor...")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        print(f"[!] PyInstaller derleme hatasi! Kod: {result.returncode}")
        return False
        
    dist_folder = os.path.join(BASE_DIR, "dist", "OkulZili")
    if not os.path.exists(dist_folder):
        print(f"[!] Dist klasoru bulunamadi: {dist_folder}")
        return False
        
    # Hedef klasörü hazırla
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"[*] Dosyalar paketleniyor -> {OUTPUT_DIR}")
    for item in os.listdir(dist_folder):
        s = os.path.join(dist_folder, item)
        d = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
            
    # musics/ klasörünü ekle
    src_musics = os.path.join(BASE_DIR, "musics")
    dst_musics = os.path.join(OUTPUT_DIR, "musics")
    if os.path.exists(src_musics):
        shutil.copytree(src_musics, dst_musics, dirs_exist_ok=True)
        
    # ezil PNG görsellerini ekle
    for f in os.listdir(BASE_DIR):
        if f.startswith("ezil") and f.endswith(".png"):
            shutil.copy2(os.path.join(BASE_DIR, f), os.path.join(OUTPUT_DIR, f))
            
    # ZIP arşivi oluştur
    print(f"[*] Tasinabilir ZIP paketi olusturuluyor -> {ZIP_OUTPUT}")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BASE_DIR)
                zipf.write(file_path, arcname)
                
    if os.path.exists(ZIP_OUTPUT):
        size_mb = os.path.getsize(ZIP_OUTPUT) // (1024 * 1024)
        print(f"[+] Basariyla tamamlandi! ZIP Boyutu: {size_mb} MB")
        return True
    else:
        print("[!] ZIP dosyasi olusturulamadi!")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
