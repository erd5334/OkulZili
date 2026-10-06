#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Okul Zili - Debian (.deb) Paket Oluşturucu (Windows / Linux Uyumlu)
Python standart kütüphanesi ile harici araç (dpkg) gerektirmeden .deb paketi üretir.
"""

import os
import io
import time
import tarfile
import struct
import shutil

PACKAGE_NAME = "okul-zili"
VERSION = "2.6.0"
ARCHITECTURE = "all"
MAINTAINER = "Er Yazılım <info@eryazilim.com>"
DESCRIPTION = """Er Yazılım Okul Zil ve Tören Sistemi
 Milli Eğitim Bakanlığı (MEB) müfredatına ve okul ihtiyaçlarına tam uyumlu;
 sınav modu, teneffüs radyo müziği, özel anonslar, tören/istiklal marşı,
 gelişmiş zil çizelgesi ve amfi ses kartı seçimi içeren profesyonel okul zili.
 Pardus, Lubuntu, Ubuntu, Debian ve tüm Linux dağıtımlarıyla tam uyumludur."""

def create_ar_member(name, data, mode=0o100644, mtime=None, uid=0, gid=0):
    """Standart Unix ar (Debian) arşiv üyesi başlığı ve verisi üretir."""
    if mtime is None:
        mtime = int(time.time())
    
    # 16 char name, padded with spaces, slash appended
    name_field = (name.strip() + "/").ljust(16)[:16]
    mtime_field = str(mtime).ljust(12)[:12]
    uid_field = str(uid).ljust(6)[:6]
    gid_field = str(gid).ljust(6)[:6]
    mode_field = oct(mode)[2:].ljust(8)[:8]
    size_field = str(len(data)).ljust(10)[:10]
    magic = b"`\n"
    
    header = (name_field + mtime_field + uid_field + gid_field + mode_field + size_field).encode("ascii") + magic
    
    body = data
    if len(body) % 2 != 0:
        body += b"\n"  # 2-byte boundary padding
        
    return header + body

def make_deb_package(output_deb_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not output_deb_path:
        output_deb_path = os.path.join(base_dir, f"{PACKAGE_NAME}_{VERSION}_{ARCHITECTURE}.deb")
        
    print(f"[*] Debian paketi hazırlanıyor: {output_deb_path}")
    
    # 1. debian-binary
    debian_binary_data = b"2.0\n"
    
    # 2. control.tar.gz
    control_content = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: sound
Priority: optional
Architecture: {ARCHITECTURE}
Depends: python3, python3-tk, python3-pil, python3-pil.imagetk | python3-pillow, mpg123 | vlc | ffmpeg
Recommends: python3-pyqt5 | python3-pyqt6
Maintainer: {MAINTAINER}
Installed-Size: 15000
Description: {DESCRIPTION}
"""
    postinst_content = """#!/bin/sh
set -e
chmod +x /usr/bin/okul-zili || true
chmod +x /usr/share/okul-zili/okul_zili.py || true
if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi
if which gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
"""
    prerm_content = """#!/bin/sh
set -e
pkill -f "/usr/share/okul-zili/okul_zili.py" || true
exit 0
"""

    control_tar_io = io.BytesIO()
    with tarfile.open(fileobj=control_tar_io, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        # ./
        t = tarfile.TarInfo("./")
        t.type = tarfile.DIRTYPE
        t.mode = 0o755
        t.uid = 0
        t.gid = 0
        t.uname = "root"
        t.gname = "root"
        t.mtime = int(time.time())
        tar.addfile(t)
        
        # ./control
        data_c = control_content.encode("utf-8")
        t = tarfile.TarInfo("./control")
        t.size = len(data_c)
        t.mode = 0o644
        t.uid = 0
        t.gid = 0
        t.uname = "root"
        t.gname = "root"
        t.mtime = int(time.time())
        tar.addfile(t, io.BytesIO(data_c))
        
        # ./postinst
        data_p = postinst_content.encode("utf-8")
        t = tarfile.TarInfo("./postinst")
        t.size = len(data_p)
        t.mode = 0o755
        t.uid = 0
        t.gid = 0
        t.uname = "root"
        t.gname = "root"
        t.mtime = int(time.time())
        tar.addfile(t, io.BytesIO(data_p))
        
        # ./prerm
        data_pr = prerm_content.encode("utf-8")
        t = tarfile.TarInfo("./prerm")
        t.size = len(data_pr)
        t.mode = 0o755
        t.uid = 0
        t.gid = 0
        t.uname = "root"
        t.gname = "root"
        t.mtime = int(time.time())
        tar.addfile(t, io.BytesIO(data_pr))
        
    control_tar_data = control_tar_io.getvalue()
    
    # 3. data.tar.gz
    launcher_script = """#!/bin/sh
exec python3 /usr/share/okul-zili/okul_zili.py "$@"
"""
    desktop_file = """[Desktop Entry]
Name=Er Yazılım Okul Zili
GenericName=Er Yazılım Okul Zil ve Tören Sistemi
Comment=Milli Eğitim Bakanlığı Uyumlu Okul Zil ve Tören Sistemi - Er Yazılım
Exec=/usr/bin/okul-zili
Icon=okul-zili
Terminal=false
Type=Application
Categories=Education;Audio;AudioVideo;Utility;
StartupNotify=true
"""

    data_tar_io = io.BytesIO()
    with tarfile.open(fileobj=data_tar_io, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        def add_dir(path):
            t = tarfile.TarInfo(path)
            t.type = tarfile.DIRTYPE
            t.mode = 0o755
            t.uid = 0
            t.gid = 0
            t.uname = "root"
            t.gname = "root"
            t.mtime = int(time.time())
            tar.addfile(t)
            
        def add_file(path, content_bytes, mode=0o644):
            t = tarfile.TarInfo(path)
            t.size = len(content_bytes)
            t.mode = mode
            t.uid = 0
            t.gid = 0
            t.uname = "root"
            t.gname = "root"
            t.mtime = int(time.time())
            tar.addfile(t, io.BytesIO(content_bytes))
            
        def add_fs_file(tar_path, src_path, mode=0o644):
            if not os.path.exists(src_path):
                return
            with open(src_path, "rb") as f:
                content = f.read()
            add_file(tar_path, content, mode=mode)

        # Temel dizinler
        for d in [
            "./usr", "./usr/bin", "./usr/share",
            "./usr/share/applications",
            "./usr/share/icons", "./usr/share/icons/hicolor",
            "./usr/share/icons/hicolor/256x256", "./usr/share/icons/hicolor/256x256/apps",
            "./usr/share/okul-zili", "./usr/share/okul-zili/musics"
        ]:
            add_dir(d)
            
        # Başlatıcı ve masaüstü dosyası
        add_file("./usr/bin/okul-zili", launcher_script.encode("utf-8"), mode=0o755)
        add_file("./usr/share/applications/okul-zili.desktop", desktop_file.encode("utf-8"), mode=0o644)
        
        # İkon
        icon_src = os.path.join(base_dir, "ezil0.png")
        if os.path.exists(icon_src):
            add_fs_file("./usr/share/icons/hicolor/256x256/apps/okul-zili.png", icon_src)
            
        # okul_zili.py ana kaynak kodu
        main_py = os.path.join(base_dir, "okul_zili.py")
        add_fs_file("./usr/share/okul-zili/okul_zili.py", main_py, mode=0o755)
        
        # PNG görseller
        for f in os.listdir(base_dir):
            if f.startswith("ezil") and f.endswith(".png"):
                add_fs_file(f"./usr/share/okul-zili/{f}", os.path.join(base_dir, f))
                
        # musics/ klasörü içeriği (tüm alt klasörlerle birlikte)
        musics_dir = os.path.join(base_dir, "musics")
        if os.path.exists(musics_dir):
            for root, dirs, files in os.walk(musics_dir):
                rel_dir = os.path.relpath(root, base_dir).replace("\\", "/")
                add_dir(f"./usr/share/okul-zili/{rel_dir}")
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, base_dir).replace("\\", "/")
                    add_fs_file(f"./usr/share/okul-zili/{rel_p}", full_p)
                    
    data_tar_data = data_tar_io.getvalue()
    
    # 4. .deb dosyasını (ar formatında) birleştir
    with open(output_deb_path, "wb") as deb_file:
        deb_file.write(b"!<arch>\n")
        deb_file.write(create_ar_member("debian-binary", debian_binary_data))
        deb_file.write(create_ar_member("control.tar.gz", control_tar_data))
        deb_file.write(create_ar_member("data.tar.gz", data_tar_data))
        
    print(f"[+] Başarıyla oluşturuldu: {output_deb_path} ({os.path.getsize(output_deb_path) // 1024} KB)")
    return output_deb_path

if __name__ == "__main__":
    make_deb_package()
