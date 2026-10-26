import os

import numpy as np
from PIL import Image, ImageDraw

OUT = "avatar"
W, H, S = 800, 1000, 2

SKIN = (244, 200, 165, 255)
SHADE = (226, 172, 135, 255)
HAIR = (48, 36, 30, 255)
SHIRT = (22, 140, 205, 255)
DARK = (40, 30, 35, 255)
WHITE = (255, 255, 255, 255)
MOUTH = (95, 25, 38, 255)
TONGUE = (214, 92, 108, 255)
LIP = (170, 70, 70, 255)


def box(*v):
    return [int(x * S) for x in v]


def draw(mouth, blink):
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    d.rounded_rectangle(box(90, 735, 710, 1160), radius=150 * S, fill=SHIRT)
    d.polygon(box(345, 735, 400, 815, 455, 735), fill=SHADE)
    d.rectangle(box(345, 600, 455, 745), fill=SHADE)
    d.ellipse(box(185, 360, 235, 470), fill=SKIN)
    d.ellipse(box(565, 360, 615, 470), fill=SKIN)
    d.ellipse(box(180, 115, 620, 540), fill=HAIR)
    d.ellipse(box(205, 185, 595, 655), fill=SKIN)
    d.chord(box(205, 170, 595, 430), 180, 360, fill=HAIR)

    for cx in (325, 475):
        if blink:
            d.arc(box(cx - 34, 405, cx + 34, 440), 0, 180, fill=DARK, width=8 * S)
        else:
            d.ellipse(box(cx - 34, 395, cx + 34, 445), fill=WHITE)
            d.ellipse(box(cx - 15, 402, cx + 15, 438), fill=DARK)
            d.ellipse(box(cx - 6, 408, cx + 4, 418), fill=WHITE)

    d.line(box(280, 360, 372, 350), fill=HAIR, width=14 * S)
    d.line(box(428, 350, 520, 360), fill=HAIR, width=14 * S)
    d.line(box(400, 445, 390, 505, 415, 510), fill=SHADE, width=7 * S)

    if mouth == "closed":
        d.arc(box(340, 535, 460, 610), 25, 155, fill=LIP, width=10 * S)
    elif mouth == "mid":
        d.ellipse(box(366, 555, 434, 597), fill=MOUTH)
        d.ellipse(box(382, 580, 418, 595), fill=TONGUE)
    else:
        d.ellipse(box(350, 540, 450, 615), fill=MOUTH)
        d.rectangle(box(376, 546, 424, 557), fill=WHITE)
        d.ellipse(box(372, 585, 428, 613), fill=TONGUE)

    im = im.resize((W, H), Image.LANCZOS)
    arr = np.array(im)
    fade = 150
    ramp = np.linspace(1.0, 0.0, fade)[:, None]
    arr[-fade:, :, 3] = (arr[-fade:, :, 3] * ramp).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def main():
    os.makedirs(OUT, exist_ok=True)
    draw("closed", False).save(f"{OUT}/closed.png")
    draw("mid", False).save(f"{OUT}/mid.png")
    draw("open", False).save(f"{OUT}/open.png")
    draw("closed", True).save(f"{OUT}/blink.png")
    print("Saved 4 images to avatar/: closed.png, mid.png, open.png, blink.png")


main()