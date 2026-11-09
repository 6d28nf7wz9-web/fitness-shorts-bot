"""Generate original scientific motion-graphic scenes for FitFuel Shorts.

No external footage/API is required: diagrams are rendered locally with Pillow
and animated/encoded with FFmpeg. This is an opt-in-by-default visual layer
with a safe fallback to the existing Pixabay clips.
"""
import json
import math
import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
BG = (10, 17, 31)
WHITE = (242, 247, 255)
MUTED = (155, 174, 198)
CYAN = (42, 210, 230)
ORANGE = (255, 166, 72)
GREEN = (99, 230, 160)
PURPLE = (163, 132, 255)
OUT = "output/science"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    path = BOLD_PATH if bold else FONT_PATH
    try: return ImageFont.truetype(path, size)
    except OSError: return ImageFont.load_default()

def wrap(text, f, max_width):
    words = str(text).split(); lines=[]; cur=""
    for word in words:
        test=(cur+" "+word).strip()
        if f.getlength(test) <= max_width: cur=test
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def centered(draw, text, y, f, fill=WHITE, max_width=900, spacing=12):
    lines=wrap(text,f,max_width)
    for line in lines:
        draw.text((W/2,y),line,font=f,fill=fill,anchor="mt")
        y += f.size+spacing
    return y

def base_scene(title, subtitle, index):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    # subtle grid + top accent
    for x in range(0,W,90): d.line((x,0,x,H),fill=(17,29,46),width=1)
    for y in range(0,H,90): d.line((0,y,W,y),fill=(17,29,46),width=1)
    d.rounded_rectangle((56,72,W-56,174),radius=28,fill=(18,31,50),outline=(38,58,82),width=2)
    d.text((W/2,122),f"FITFUEL  •  SCIENCE {index:02d}",font=font(30,True),fill=CYAN,anchor="mm")
    centered(d,title.upper(),250,font(56,True),WHITE,940,14)
    centered(d,subtitle,390,font(30),MUTED,900,10)
    return im,d

def muscle(draw, cx, cy, scale=1.0, color=ORANGE):
    # stylized muscle fiber bundle, anatomical infographic not a clinical image
    for i in range(7):
        x=cx+(i-3)*42*scale
        y=cy+math.sin(i*0.9)*18*scale
        draw.rounded_rectangle((x-22*scale,y-180*scale,x+22*scale,y+180*scale),
            radius=int(22*scale),fill=(color[0]//2,color[1]//2,color[2]//2),outline=color,width=max(2,int(5*scale)))
        for j in range(5):
            yy=y-145*scale+j*70*scale
            draw.arc((x-16*scale,yy-18*scale,x+16*scale,yy+18*scale),0,180,fill=(255,220,170),width=max(1,int(2*scale)))

def arrow(draw, a, b, color=CYAN, width=9):
    draw.line((a,b),fill=color,width=width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); L=30
    p1=(b[0]-L*math.cos(ang-0.5),b[1]-L*math.sin(ang-0.5))
    p2=(b[0]-L*math.cos(ang+0.5),b[1]-L*math.sin(ang+0.5))
    draw.polygon([b,p1,p2],fill=color)

def protein(draw, cx, cy, radius=34, color=CYAN):
    pts=[]
    for i in range(9):
        a=i*math.pi*2/9
        pts.append((cx+math.cos(a)*radius,cy+math.sin(a)*radius))
    draw.line(pts+[pts[0]],fill=color,width=7,joint="curve")
    for x,y in pts: draw.ellipse((x-12,y-12,x+12,y+12),fill=ORANGE,outline=WHITE,width=2)

def draw_diagram(kind, title, subtitle, idx, frame=0):
    im,d=base_scene(title,subtitle,idx)
    phase=frame/FPS
    if kind=="muscle":
        muscle(d,W/2,1030,1.25)
        d.rounded_rectangle((120,1390,960,1570),radius=35,fill=(20,37,57),outline=ORANGE,width=4)
        centered(d,"RESISTANCE  →  RECOVERY  →  ADAPTATION",1440,font(30,True),ORANGE,780,12)
        arrow(d,(W/2,1250),(W/2,1370),CYAN)
    elif kind=="protein":
        muscle(d,340,1020,0.75,ORANGE)
        for i in range(5):
            x=650+(i%2)*100; y=760+i*105
            protein(d,x,y,28,CYAN)
            arrow(d,(x-60,y),(520,y+int(phase*20)%30),GREEN,5)
        d.rounded_rectangle((130,1450,950,1640),radius=30,fill=(20,37,57),outline=GREEN,width=4)
        centered(d,"AMINO ACIDS  →  PROTEIN BUILDING",1500,font(32,True),GREEN,780,10)
    elif kind=="energy":
        # calorie balance scale
        d.line((W/2,800,W/2,1370),fill=WHITE,width=16); d.line((260,920,820,920),fill=CYAN,width=12)
        d.line((360,920,280,1190),fill=ORANGE,width=6); d.line((720,920,800,1190),fill=GREEN,width=6)
        d.arc((170,1120,390,1280),0,180,fill=ORANGE,width=8); d.arc((690,1120,910,1280),0,180,fill=GREEN,width=8)
        centered(d,"ENERGY IN",1290,font(36,True),ORANGE,350)
        centered(d,"ENERGY OUT",1290,font(36,True),GREEN,350)
        centered(d,"BODY WEIGHT TREND",1480,font(34,True),WHITE,850)
    elif kind=="hydration":
        # water droplet and muscle
        d.ellipse((250,760,830,1340),fill=(16,45,66),outline=CYAN,width=8)
        d.polygon([(540,680),(350,1020),(420,1210),(540,1280),(660,1210),(730,1020)],fill=(24,130,180),outline=CYAN)
        for i in range(4):
            y=920+i*75; d.arc((410,y,670,y+50),0,180,fill=(180,245,255),width=5)
        centered(d,"FLUIDS SUPPORT PERFORMANCE",1430,font(34,True),CYAN,850)
    elif kind=="sleep":
        d.ellipse((350,760,730,1140),fill=ORANGE)
        d.ellipse((470,700,790,1020),fill=BG)
        for x,y in [(260,750),(800,840),(350,1240),(760,1260),(550,650)]:
            d.polygon([(x,y-24),(x-8,y-6),(x-26,y),(x-8,y+6),(x,y+24),(x+8,y+6),(x+26,y),(x+8,y-6)],fill=CYAN)
        centered(d,"SLEEP  •  RECOVERY  •  CONSISTENCY",1430,font(34,True),PURPLE,900)
    elif kind=="training":
        # progressive overload staircase
        vals=[390,520,650,780,910]
        for i,v in enumerate(vals):
            x=170+i*155
            d.rounded_rectangle((x,1320-v/2,x+100,1320),radius=18,fill=(40,80,115),outline=CYAN,width=4)
            d.text((x+50,1320-v/2-55),str(i+1),font=font(28,True),fill=WHITE,anchor="mm")
        arrow(d,(150,1360),(950,700),ORANGE,10)
        centered(d,"PROGRESSIVE OVERLOAD",1450,font(38,True),CYAN,850)
    else:
        # generic concept card
        d.rounded_rectangle((140,760,940,1430),radius=50,fill=(20,37,57),outline=CYAN,width=5)
        centered(d,"ONE CLEAR IDEA",930,font(48,True),CYAN,700)
        centered(d,subtitle,1110,font(32),WHITE,700)
    d.rounded_rectangle((70,H-170,W-70,H-75),radius=24,fill=(18,31,50),outline=(38,58,82),width=2)
    d.text((W/2,H-122),"EVIDENCE-BASED FITNESS  •  EDUCATIONAL VISUAL",font=font(24,True),fill=MUTED,anchor="mm")
    return im

def classify(text):
    t=str(text).lower()
    rules=[
      ("protein",r"protein|amino acid|synthesis|muscle protein|build muscle"),
      ("muscle",r"muscle|fiber|hypertrophy|resistance|strength|lifting|training"),
      ("energy",r"calorie|energy balance|fat loss|weight loss|deficit|surplus|eat more|eat less"),
      ("hydration",r"water|hydration|fluid|dehydrat"),
      ("sleep",r"sleep|recovery|rest day|fatigue"),
      ("training",r"progressive overload|reps|sets|volume|workout|exercise|load"),
    ]
    for kind,pat in rules:
        if re.search(pat,t): return kind
    return "generic"

def scene_text(scene):
    narration=str(scene.get("narration","")).strip()
    title=str(scene.get("visual_title") or scene.get("heading") or narration[:55]).strip()
    subtitle=str(scene.get("visual_subtitle") or narration).strip()
    return title[:90],subtitle[:180],narration

def render_scene(scene,index,seconds,outfile):
    title,subtitle,narration=scene_text(scene); kind=classify(narration)
    os.makedirs(os.path.dirname(outfile),exist_ok=True)
    # Render 1 still per scene and gently animate a scale/opacity pulse using zoompan.
    still=outfile+".png"
    draw_diagram(kind,title,subtitle,index,0).save(still)
    frames=max(1,int(seconds*FPS))
    vf=f"zoompan=z='1+0.018*sin(2*PI*on/{frames})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p"
    cmd=["ffmpeg","-y","-loglevel","error","-loop","1","-i",still,"-vf",vf,"-t",str(seconds),"-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p","-an",outfile]
    subprocess.run(cmd,check=True); os.remove(still)
    return {"scene":index,"type":kind,"title":title,"file":outfile,"seconds":round(seconds,2)}

def main():
    if os.getenv("SCIENCE_VISUALS","1").lower() in ("0","false","no","off"):
        print("Scientific visuals disabled; leaving Pixabay clips untouched."); return
    with open("output/script.json",encoding="utf-8") as f: script=json.load(f)
    with open("output/audio_info.json",encoding="utf-8") as f: audio=json.load(f)
    scenes=script.get("scenes",[])
    if not scenes or len(scenes)!=len(audio): raise SystemExit("Science visuals: script/audio scene count mismatch")
    os.makedirs(OUT,exist_ok=True); rendered=[]
    for i,(scene,a) in enumerate(zip(scenes,audio),1):
        seconds=float(a.get("seconds",0))
        if seconds<=0: raise SystemExit(f"Science visuals: invalid duration for scene {i}")
        dest=f"{OUT}/scene_{i}.mp4"
        print(f"[science] scene {i}/{len(scenes)} -> {classify(scene.get('narration',''))}")
        rendered.append(render_scene(scene,i,seconds,dest))
    with open("output/science_info.json","w",encoding="utf-8") as f: json.dump(rendered,f,indent=2)
    print(f"Scientific visuals ready: {len(rendered)} scenes -> {OUT}/")

if __name__=="__main__": main()
