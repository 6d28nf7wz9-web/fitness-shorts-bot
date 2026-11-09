"""Create animated, topic-matched science diagrams for FitFuel Shorts.

Uses Pillow + FFmpeg only (already available in the pipeline). Each scene gets
an original motion-graphics explainer; failures leave the Pixabay scene intact.
"""
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 540, 960
FPS = 15
OUT = Path("output/science")
BG = (241, 246, 250)
PANEL = (250, 252, 254)
WHITE = (28, 43, 58)
MUTED = (91, 111, 130)
CYAN = (0, 112, 145)
ORANGE = (190, 99, 35)
GREEN = (38, 125, 82)


def font(size, bold=False):
    candidates = ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def centered(draw, xy, text, f, fill=WHITE):
    draw.text(xy, text, font=f, fill=fill, anchor="mm")


def arrow(draw, start, end, color=CYAN, width=5):
    draw.line([start, end], fill=color, width=width)
    a = math.atan2(end[1]-start[1], end[0]-start[0])
    r = 14
    p1 = (end[0]-r*math.cos(a-0.55), end[1]-r*math.sin(a-0.55))
    p2 = (end[0]-r*math.cos(a+0.55), end[1]-r*math.sin(a+0.55))
    draw.polygon([end, p1, p2], fill=color)


def base(title, subtitle, t):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # restrained grid + moving scan line
    for x in range(0, W, 45):
        d.line((x, 0, x, H), fill=(224, 232, 239), width=1)
    for y in range(0, H, 45):
        d.line((0, y, W, y), fill=(224, 232, 239), width=1)
    d.rounded_rectangle((28, 34, W-28, 104), radius=18, fill=PANEL, outline=(202, 215, 226), width=2)
    # Keep the legacy renderer consistent: the header is the topic of this slide.
    d.text((W//2, 69), title[:34].upper(), font=font(21, True), fill=WHITE, anchor="mm")
    d.text((W//2, 165), subtitle[:52], font=font(16), fill=MUTED, anchor="mm")
    # bottom timeline accent
    d.rounded_rectangle((45, H-62, W-45, H-48), radius=7, fill=(218, 228, 236))
    d.rounded_rectangle((45, H-62, 45+int((W-90)*((t%4)/4)), H-48), radius=7, fill=CYAN)
    return im, d


def muscle(d, t):
    d.rounded_rectangle((55, 290, 485, 560), radius=28, fill=PANEL, outline=(39, 76, 105), width=3)
    # muscle fibers expand and contract subtly
    pulse = 1 + 0.035*math.sin(t*2.4)
    for i in range(7):
        y = 330+i*31
        x0 = 100
        x1 = int(420*pulse)+x0
        d.rounded_rectangle((x0, y, min(x1, 465), y+17), radius=8, fill=(35, 135+min(i*8,60), 170))
        for x in range(125, min(x1-10,455), 45):
            d.ellipse((x, y+4, x+8, y+12), fill=(125, 245, 240))
    centered(d,(270,620),"RESISTANCE → SIGNAL",font(21,True),ORANGE)
    arrow(d,(270,660),(270,720),ORANGE)
    d.rounded_rectangle((95,735,445,825),radius=22,fill=(22,53,61),outline=GREEN,width=2)
    centered(d,(270,770),"PROTEIN BUILDING",font(22,True),GREEN)
    centered(d,(270,865),"Recovery + protein + repeat",font(17),MUTED)


def protein(d,t):
    # amino acid particles move toward a growing chain
    d.ellipse((115,315,425,625),fill=(20,46,67),outline=CYAN,width=4)
    centered(d,(270,410),"MUSCLE CELL",font(21,True))
    for i in range(9):
        x=145+((i*47+int(t*55))%250)
        y=500+((i*31)%75)
        d.ellipse((x,y,x+18,y+18),fill=[CYAN,ORANGE,GREEN][i%3])
    # chain
    pts=[]
    for i in range(8):
        pts.append((120+i*43,735+math.sin(i+t*2)*22))
    d.line(pts,fill=GREEN,width=8)
    for x,y in pts:
        d.ellipse((x-12,y-12,x+12,y+12),fill=GREEN)
    arrow(d,(270,650),(270,700),ORANGE,6)
    centered(d,(270,840),"AMINO ACIDS → NEW PROTEIN",font(18,True),WHITE)


def energy(d,t):
    # balance scale
    d.line((270,365,270,650),fill=WHITE,width=9)
    d.polygon([(230,650),(310,650),(270,590)],fill=CYAN)
    d.line((110,420,430,420),fill=ORANGE,width=8)
    for x in (145,395):
        d.line((x,420,x-45,535),fill=MUTED,width=4)
        d.line((x,420,x+45,535),fill=MUTED,width=4)
        d.arc((x-55,510,x+55,575),0,180,fill=CYAN,width=5)
    d.rounded_rectangle((55,285,220,360),radius=18,fill=(48,39,29),outline=ORANGE,width=2)
    centered(d,(137,322),"INTAKE",font(22,True),ORANGE)
    d.rounded_rectangle((320,285,485,360),radius=18,fill=(19,48,54),outline=CYAN,width=2)
    centered(d,(402,322),"OUTPUT",font(22,True),CYAN)
    centered(d,(270,730),"ENERGY BALANCE",font(27,True))
    centered(d,(270,790),"A pattern over time—not one meal",font(17),MUTED)


def hydration(d,t):
    # bottle and moving water level
    d.rounded_rectangle((195,310,345,680),radius=35,fill=(15,42,62),outline=CYAN,width=5)
    d.rounded_rectangle((225,270,315,325),radius=12,fill=(15,42,62),outline=CYAN,width=4)
    level=510+int(18*math.sin(t*2))
    d.rounded_rectangle((210,level,330,660),radius=22,fill=(22,145,205))
    for i in range(7):
        x=230+(i*37)%85
        y=level+35+(i*41)%100
        d.ellipse((x,y,x+12,y+12),fill=(115,235,255))
    centered(d,(270,750),"WATER + PERFORMANCE",font(23,True),CYAN)
    centered(d,(270,810),"Hydration supports normal function",font(17),MUTED)


def progression(d,t):
    # barbell + upward chart
    d.rounded_rectangle((85,350,455,415),radius=20,fill=(25,47,66),outline=CYAN,width=3)
    d.rectangle((245,325,295,440),fill=WHITE)
    d.rounded_rectangle((105,315,175,450),radius=12,fill=ORANGE)
    d.rounded_rectangle((365,315,435,450),radius=12,fill=ORANGE)
    d.line((105,720,435,720),fill=MUTED,width=3)
    d.line((105,720,105,520),fill=MUTED,width=3)
    pts=[(125,690),(205,650),(285,610),(365,550),(420,520)]
    d.line(pts,fill=GREEN,width=7)
    for x,y in pts:
        d.ellipse((x-9,y-9,x+9,y+9),fill=GREEN)
    arrow(d,(380,570),(430,510),GREEN,5)
    centered(d,(270,800),"PROGRESSIVE OVERLOAD",font(22,True),GREEN)
    centered(d,(270,850),"Small, repeatable increases",font(17),MUTED)


def generic(d,t):
    labels=["STIMULUS","ADAPTATION","RESULT"]
    xs=[100,270,440]
    for i,(x,label) in enumerate(zip(xs,labels)):
        d.rounded_rectangle((x-65,420,x+65,560),radius=20,fill=PANEL,outline=[ORANGE,CYAN,GREEN][i],width=3)
        centered(d,(x,490),label,font(15,True),[ORANGE,CYAN,GREEN][i])
    arrow(d,(170,490),(200,490),WHITE,4)
    arrow(d,(340,490),(370,490),WHITE,4)
    centered(d,(270,650),"THE MECHANISM",font(25,True))
    centered(d,(270,710),"Cause → process → outcome",font(18),MUTED)
    # pulsing point
    r=8+int(5*(1+math.sin(t*3)))
    d.ellipse((270-r,330-r,270+r,330+r),fill=CYAN)


def classify(text):
    s=text.lower()
    if any(k in s for k in ["protein","amino acid","synthesis","muscle grow","muscle growth","repair","mps"]):
        return "muscle", "MUSCLE ADAPTATION", "Training signal + recovery"
    if any(k in s for k in ["calorie","energy balance","fat loss","deficit","surplus","weight loss"]):
        return "energy", "ENERGY BALANCE", "Intake and expenditure over time"
    if any(k in s for k in ["water","hydration","drink","fluid","dehydrat"]):
        return "hydration", "HYDRATION", "Fluids support training"
    if any(k in s for k in ["progressive overload","progress","reps","strength","load","training volume"]):
        return "progression", "TRAINING PROGRESSION", "A measurable training stimulus"
    if any(k in s for k in ["amino","protein","food","eat","meal"]):
        return "protein", "NUTRIENTS", "Building blocks from food"
    return "generic", "THE SCIENCE", "A simple mechanism, made visual"


def render_scene(index, narration, seconds, visual_title="", visual_subtitle=""):
    kind,default_title,default_sub=classify(narration)
    title=str(visual_title or default_title).strip()[:34]
    sub=str(visual_subtitle or default_sub).strip()[:52]
    draw_fn={"muscle":muscle,"protein":protein,"energy":energy,"hydration":hydration,
             "progression":progression,"generic":generic}[kind]
    frames=max(2,int(seconds*FPS))
    with tempfile.TemporaryDirectory(prefix="fitfuel_science_") as tmp:
        for f in range(frames):
            t=f/FPS
            im,d=base(title,sub,t)
            draw_fn(d,t)
            # Animated editorial accent and scene-specific takeaway.
            pulse=0.5+0.5*math.sin(t*3.2)
            x=40+int(18*pulse)
            d.rounded_rectangle((x,245,500,258),radius=6,fill=(218,228,236))
            d.rounded_rectangle((x,245,x+int(460*(0.35+0.65*pulse)),258),radius=6,fill=ORANGE if index%2 else CYAN)
            d.rounded_rectangle((38,875,502,920),radius=14,fill=(250,252,254),outline=(202,215,226),width=2)
            d.text((270,897),f"TAKEAWAY / {sub[:38].upper()}",font=font(13,True),fill=GREEN if index%2 else CYAN,anchor="mm")
            # scale up for the existing 1080x1920 assembly pipeline
            im.resize((1080,1920),Image.Resampling.LANCZOS).save(f"{tmp}/f{f:05d}.png")
        out=OUT/f"scene_{index}.mp4"
        cmd=["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",f"{tmp}/f%05d.png",
             "-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","22",
             "-movflags","+faststart","-t",f"{seconds:.3f}",str(out)]
        subprocess.run(cmd,check=True)
    print(f"SCIENCE scene {index}: {kind} diagram ({seconds:.2f}s) -> {out}")


def main():
    if os.getenv("SCIENTIFIC_VISUALS","1").strip().lower() in {"0","false","no","off"}:
        print("Scientific visuals disabled by SCIENTIFIC_VISUALS")
        return
    with open("output/script.json",encoding="utf-8") as f:
        script=json.load(f)
    with open("output/audio_info.json",encoding="utf-8") as f:
        audio=json.load(f)
    scenes=script.get("scenes",[])
    if not scenes or len(scenes)!=len(audio):
        raise SystemExit("Science visuals: script/audio scene count mismatch")
    OUT.mkdir(parents=True,exist_ok=True)
    for i,(scene,a) in enumerate(zip(scenes,audio),1):
        dest=OUT/f"scene_{i}.mp4"
        if dest.exists():
            dest.unlink()
        try:
            render_scene(i,str(scene.get("narration","")),float(a.get("seconds",0)),
                          str(scene.get("visual_title","")),str(scene.get("visual_subtitle","")))
        except Exception as exc:
            print(f"WARN science scene {i} failed; Pixabay fallback will be used: {exc}")
            if dest.exists(): dest.unlink()
    print(f"Scientific visuals ready: {len(list(OUT.glob('scene_*.mp4')))} / {len(scenes)} scenes")


if __name__=="__main__":
    main()
