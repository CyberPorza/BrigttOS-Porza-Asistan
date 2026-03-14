# setup.py
# CyberPorza - Otomatik Kurulum Aracı

import subprocess
import sys

print("[PORZA-SETUP] 📦 Gerekli kütüphaneler kuruluyor kankam, biraz bekle...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("[PORZA-SETUP] 🌐 Playwright tarayıcı motorları yükleniyor...")
subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)

print("\n[PORZA-SETUP] ✅ Kurulum tamamlandı kankam! Sistemi ateşlemek için terminale 'python main.py' yazman yeterli.")