#!/usr/bin/env python3
"""
Gera os ícones do aplicativo desenhando o logo do FastAccess
programaticamente com Pillow (sem depender de arquivos de imagem externos).

Saídas:
  - mobile_app/assets/icon.png            -> ícone mestre 512px (ficha Play Store)
  - mobile_app/android/.../mipmap-*/      -> ícones Android em todas as densidades
  - mobile_app/ios/.../AppIcon.appiconset -> ícones iOS + Contents.json

Uso (local ou CI):
    pip install pillow
    python tools/generate_icons.py
"""
import json
import os
from PIL import Image, ImageDraw

BG = (30, 82, 111, 255)       # azul do app
ARC = (127, 212, 193, 255)    # verde-água (arcos de Wi-Fi)
BOLT = (255, 209, 102, 255)   # âmbar (raio = rapidez)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANDROID_RES = os.path.join(ROOT, "mobile_app", "android", "app", "src", "main", "res")
IOS_ASSETS = os.path.join(
    ROOT, "mobile_app", "ios", "Runner", "Assets.xcassets", "AppIcon.appiconset"
)
MASTER_ICON = os.path.join(ROOT, "mobile_app", "assets", "icon.png")


def draw_logo(size, rounded=True, opaque=False):
    """Logo: fundo azul, dois arcos de Wi-Fi e um raio (conexão rápida)."""
    img = Image.new("RGBA", (size, size), BG if opaque else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded and not opaque:
        d.rounded_rectangle([0, 0, size - 1, size - 1],
                            radius=int(size * 0.22), fill=BG)
    else:
        d.rectangle([0, 0, size, size], fill=BG)

    cx, cy = size / 2, size * 0.62
    for radius in (0.30, 0.19):
        r = size * radius
        d.arc([cx - r, cy - r, cx + r, cy + r], start=205, end=335,
              fill=ARC, width=max(2, int(size * 0.055)))

    s = size
    bolt = [(0.545, 0.58), (0.435, 0.78), (0.505, 0.78), (0.460, 0.90),
            (0.585, 0.715), (0.512, 0.715), (0.565, 0.58)]
    d.polygon([(x * s, y * s) for x, y in bolt], fill=BOLT)
    return img


def generate_android():
    densities = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for name, px in densities.items():
        out_dir = os.path.join(ANDROID_RES, f"mipmap-{name}")
        os.makedirs(out_dir, exist_ok=True)
        icon = draw_logo(px, rounded=True)
        icon.save(os.path.join(out_dir, "ic_launcher.png"))
        icon.save(os.path.join(out_dir, "ic_launcher_round.png"))
    print(f"Android: {len(densities) * 2} ícones gerados")


def generate_ios():
    # iOS exige ícones opacos e sem cantos arredondados (o sistema aplica a máscara)
    entries = [
        ("iphone", "20x20", [2, 3]), ("iphone", "29x29", [2, 3]),
        ("iphone", "40x40", [2, 3]), ("iphone", "60x60", [2, 3]),
        ("ipad", "20x20", [1, 2]), ("ipad", "29x29", [1, 2]),
        ("ipad", "40x40", [1, 2]), ("ipad", "76x76", [1, 2]),
        ("ipad", "83.5x83.5", [2]), ("ios-marketing", "1024x1024", [1]),
    ]
    os.makedirs(IOS_ASSETS, exist_ok=True)
    images = []
    for idiom, size, scales in entries:
        base = int(float(size.split("x")[0]))
        for scale in scales:
            px = base * scale
            filename = f"Icon-App-{size}@{scale}x.png"
            draw_logo(px, rounded=False, opaque=True).convert("RGB").save(
                os.path.join(IOS_ASSETS, filename)
            )
            images.append({"size": size, "idiom": idiom,
                           "filename": filename, "scale": f"{scale}x"})
    contents = {"images": images, "info": {"version": 1, "author": "generate_icons.py"}}
    with open(os.path.join(IOS_ASSETS, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print(f"iOS: {len(images)} ícones gerados")


def generate_master():
    os.makedirs(os.path.dirname(MASTER_ICON), exist_ok=True)
    draw_logo(512, rounded=True).save(MASTER_ICON)
    print(f"Ícone mestre: {MASTER_ICON}")


def generate_feature_graphic():
    """Imagem de destaque 1024x500 exigida na ficha da Play Store."""
    w, h = 1024, 500
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)

    # Logo à esquerda
    logo = draw_logo(360, rounded=True)
    img.paste(logo, (70, 70), logo)

    # Texto à direita (fonte padrão do Pillow; trocável por .ttf se desejado)
    d.text((480, 190), "FastAccess", fill=(255, 255, 255))
    d.text((480, 230), "Wi-Fi da UEMA sem login repetitivo", fill=ARC)

    out = os.path.join(ROOT, "mobile_app", "assets", "feature_graphic.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print(f"Imagem de destaque Play Store: {out}")


if __name__ == "__main__":
    generate_master()
    generate_android()
    generate_ios()
    generate_feature_graphic()
    print("Concluído.")
