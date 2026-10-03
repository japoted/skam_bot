"""Замена баннеров на синие (те, что дал пользователь).
Положи 5 файлов в new_blue/ и запусти: python swap_blue.py
  new_blue/support.jpg  -> ПОДДЕРЖКА (5379983559935860452.jpg)
  new_blue/deposit.jpg  -> ПОПОЛНЕНИЕ БАЛАНСА + BUY (пополнение.jfif)
  new_blue/welcome.jpg  -> ДОБРО ПОЖАЛОВАТЬ + монеты (5438570968302427672.jpg)
  new_blue/profile.jpg  -> ПРОФИЛЬ + Username (провиль.jfif)
  new_blue/catalog.jpg  -> КАТАЛОГ ТОВАРОВ (каталог.jfif)
Старые лежат как *.bak (уже есть). Остальные баннеры не трогаем.
"""
import os, shutil
BASE = os.path.dirname(__file__)
MAP = {
    "support.jpg": "5379983559935860452.jpg",
    "deposit.jpg": "пополнение.jfif",
    "welcome.jpg": "5438570968302427672.jpg",
    "profile.jpg": "провиль.jfif",
    "catalog.jpg": "каталог.jfif",
}
for src, dst in MAP.items():
    s = os.path.join(BASE, "new_blue", src)
    d = os.path.join(BASE, dst)
    if os.path.isfile(s):
        shutil.copyfile(s, d)
        print(f"OK {src} -> {dst}")
    else:
        print(f"НЕТ ФАЙЛА new_blue/{src} — пропустил")
