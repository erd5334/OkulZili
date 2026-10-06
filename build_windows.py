#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Okul Zili - Windows Portable EXE ve Paket Derleyici
PyInstaller kullanarak tek tıkla çalışabilen bağımsız Windows sürümünü derler.
"""

import os
import sys
import shutil
import subprocess
import zipfile
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "WINDOWS_KURULUMSUZ_OKUL_ZILI")
ZIP_OUTPUT = os.path.join(BASE_DIR, "OkulZili-v2.6.0-Windows-Portable.zip")

def prepare_icon():
    ico_path = os.path.join(BASE_DIR, "app_icon.ico")
    png_path = os.path.join(BASE_DIR, "ezil0.png")
    if not os.path.exists(ico_path) and os.path.exists(png_path):
        try:
            img = Image.open(png_path)
            img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("[+] app_icon.ico oluşturuldu.")
        except Exception as e:
            print(f"[!] İkon oluşturma hatası: {e}")
    return ico_path if os.path.exists(ico_path) else None

def build_exe():
    print("=" * 60)
    print("   Okul Zili v2.6.0 - Windows EXE Derleme Aracı")
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
    
    print(f"[*] PyInstaller çalıştırılıyor...")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        print("[!] PyInstaller derleme hatası oluştu!")
        return False
        
    dist_folder = os.path.join(BASE_DIR, "dist", "OkulZili")
    
    # Hedef klasörü hazırla
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"[*] Dosyalar paketleniyor -> {OUTPUT_DIR}")
    # Dist içeriğini kopyala
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
    print(f"[*] Taşınabilir ZIP paketi oluşturuluyor -> {ZIP_OUTPUT}")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BASE_DIR)
                zipf.write(file_path, arcname)
                
    print(f"[+] Başarıyla tamamlandı!")
    print(f"    - Klasör: {OUTPUT_DIR}")
    print(f"    - ZIP Dosyası: {ZIP_OUTPUT} ({os.path.getsize(ZIP_OUTPUT) // 1024 // 1024} MB)")
    return True

if __name__ == "__main__":
    build_exe()
