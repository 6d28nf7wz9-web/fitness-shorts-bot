"""Landscape 2D scientific motion graphics for the AI Long pipeline."""
import json, math, os, re, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = max(8, min(15, int(os.getenv("LONG_SCIENCE_FPS", "12"))))
MAX_CHUNK = min(6.0, max(4.0, float(os.getenv("LONG_SCIENCE_CHUNK_SECONDS", "5"))))
OUT = Path("output/long")
SCIENCE = OUT / "science"
BG=(10,18,31); INK=(24,39,55); MUTED=(102,123,144)
CYAN=(0,145,180); ORANGE=(220,119,48); GREEN=(38,145,99)
PURPLE=(112,82,165); PALE=(250,252,254)
NAVY=(10,18,31); PANEL=(20,34,52); GRID=(29,46,66); WHITE=(244,248,252)
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(n,b=False):
    try: return ImageFont.truetype(BOLD if b else REG,n)
    except OSError: return ImageFont.load_default()

def label(d,s,xy,n=22,c=INK,b=True):
    d.text(xy,str(s),font=font(n,b),fill=c,anchor="mm")

def arrow(d,a,b,c=CYAN,w=8):
    d.line((a,b),fill=c,width=w)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); z=19
    d.polygon([b,(b[0]-z*math.cos(ang-.55),b[1]-z*math.sin(ang-.55)),
               (b[0]-z*math.cos(ang+.55),b[1]-z*math.sin(ang+.55))],fill=c)

def classify_section(s):
    text=(str(s.get("heading",""))+" "+str(s.get("narration",""))+" "+" ".join(map(str,s.get("keywords",[])))).lower()
    rules=[
      ("digestion_fiber",r"fiber|fibre|gut|digest|intestin|microbiome|colon"),
      ("exercise_biomechanics",r"squat|deadlift|bench|press|lunge|curl|row|push.?up|pull.?up|exercise|form"),
      ("protein_synthesis",r"protein|amino acid|synthesis|hypertrophy"),
      ("energy_metabolism",r"calorie|energy|fat loss|weight loss|deficit|surplus|metabolism"),
      ("hydration",r"water|hydration|fluid|dehydrat"),
      ("recovery_sleep",r"sleep|recovery|rest day|fatigue|stress"),
      ("food_nutrition",r"food|meal|nutrition|carb|vegetable|fruit|diet|eating|hunger"),
      ("muscle_anatomy",r"muscle|fiber|strength|lifting|training|growth")]
    for kind,pat in rules:
        if re.search(pat,text): return kind
    return "process"

def chunk_windows(start,end,maximum=MAX_CHUNK):
    start,end=float(start),float(end)
    if end<=start: raise ValueError("Section end must be after its start")
    out=[]; cur=start
    while cur<end-1e-6:
        nxt=min(end,cur+maximum); out.append((round(cur,3),round(nxt,3))); cur=nxt
    return out

def draw_scene(s,kind,section_no,frame,offset,total,beat_index=0):
    t=offset+frame/FPS; p=min(1,(offset+frame/FPS)/max(total,.001))
    im=Image.new("RGB",(W,H),NAVY); d=ImageDraw.Draw(im)
    # Premium deep-blue gradient, subtle technical grid and animated ambient accents.
    for y in range(0,H,8):
        q=y/max(H-1,1); c=tuple(int(a+(b-a)*q) for a,b in zip((10,18,31),(19,34,52)))
        d.rectangle((0,y,W,min(y+7,H)),fill=c)
    for x in range(0,W,64): d.line((x,0,x,H),fill=GRID,width=1)
    for y in range(0,H,64): d.line((0,y,W,y),fill=GRID,width=1)
    for i in range(18):
        x=(i*97+int(t*13))%W; y=(i*53+int(t*7))%H
        r=2+(i%3); d.ellipse((x-r,y-r,x+r,y+r),fill=(30,62,83))
    d.rounded_rectangle((42,28,W-42,150),radius=24,fill=PALE,outline=(75,101,126),width=2)
    d.rounded_rectangle((58,43,66,133),radius=4,fill=CYAN)
    label(d,"FITFUEL  /  SCIENCE LAB",(145,51),14,CYAN)
    d.rounded_rectangle((W-230,42,W-65,76),radius=15,fill=(225,239,246))
    label(d,f"VISUAL BEAT {beat_index+1:02d}",(W-147,59),13,CYAN)
    title=str(s.get("heading","FITFUEL SCIENCE")).upper()[:75]
    f=font(34,True)
    while d.textbbox((0,0),title,font=f)[2]>1120 and f.size>20: f=font(f.size-1,True)
    label(d,title,(W//2,76),f.size,INK)
    sub="  •  ".join(map(str,(s.get("keywords") or [])[:3])) or "FITFUEL SCIENCE EXPLAINER"
    label(d,sub[:95],(W//2,119),18,MUTED,False)
    d.rounded_rectangle((54,174,180,214),radius=18,fill=(225,237,244))
    label(d,f"SECTION {section_no:02d}",(117,194),15,CYAN)

    if kind=="muscle_anatomy":
        d.rounded_rectangle((160,300,545,590),radius=35,fill=PALE,outline=ORANGE,width=5)
        for i in range(7):
            x=210+i*43; off=int(10*math.sin(t*2+i*.5))
            d.rounded_rectangle((x,350+off,x+22,525+off),radius=10,fill=(145,58,72),outline=(230,125,135),width=3)
        label(d,"MUSCLE FIBERS",(350,560),21,ORANGE)
        arrow(d,(570,440),(710,440))
        d.ellipse((755,280,1100,620),fill=(18,48,65),outline=CYAN,width=8)
        for i in range(6):
            y=330+i*42; off=int(8*math.sin(t*3+i))
            d.rounded_rectangle((810,y+off,1050,y+18+off),radius=8,fill=(160,55,75),outline=(255,170,175),width=2)
        for i in range(9):
            x=780+(i*37+int(t*40))%290; y=300+(i*53)%300
            d.ellipse((x-6,y-6,x+6,y+6),fill=[ORANGE,GREEN,CYAN][i%3])
        label(d,"MUSCLE CELL",(930,585),22,PALE)
    elif kind=="protein_synthesis":
        label(d,"PROTEIN INTAKE",(270,330),24,CYAN)
        for i in range(6):
            x=210+(i%2)*100; y=390+(i//2)*55
            d.ellipse((x-17,y-17,x+17,y+17),fill=[CYAN,ORANGE,GREEN][i%3])
        arrow(d,(420,445),(565,445),ORANGE)
        pts=[(590+i*23,440+int(42*math.sin(i*.8+t*2))) for i in range(8)]
        d.line(pts,fill=GREEN,width=10,joint="curve")
        for x,y in pts: d.ellipse((x-8,y-8,x+8,y+8),fill=GREEN)
        arrow(d,(790,445),(875,445))
        d.ellipse((900,310,1120,555),fill=(18,48,65),outline=CYAN,width=8)
        label(d,"MUSCLE CELL",(1010,430),22,PALE); label(d,"BUILD + REPAIR",(1010,590),20,GREEN)
    elif kind=="energy_metabolism":
        label(d,"STORED ENERGY",(280,330),24,ORANGE)
        for i in range(3):
            x=210+i*100; y=445+int(12*math.sin(t*2+i))
            d.ellipse((x-42,y-42,x+42,y+42),fill=(225,165,85),outline=ORANGE,width=5)
        arrow(d,(540,445),(700,445))
        d.ellipse((770,320,1080,560),fill=(75,52,35),outline=GREEN,width=8)
        for i in range(5): d.arc((825,350+i*35,1020,405+i*35),0,180,fill=(255,190,90),width=7)
        for i in range(8):
            x=800+(i*31+int(t*50))%250; d.ellipse((x-6,575+(i%2)*20,x+6,587+(i%2)*20),fill=CYAN)
        label(d,"CELLULAR ENERGY / ATP",(925,635),21,GREEN)
    elif kind=="hydration":
        d.polygon([(300,310),(250,410),(260,475),(300,510),(340,475),(350,410)],fill=(35,135,200),outline=CYAN)
        label(d,"WATER",(300,555),22,CYAN); arrow(d,(405,435),(575,435))
        d.ellipse((660,280,1100,620),fill=PALE,outline=CYAN,width=8)
        d.ellipse((700,320,1060,580),fill=(210,239,247),outline=(125,190,210),width=3)
        for i in range(12):
            x=735+(i*59+int(t*38))%290; y=355+(i*47)%190
            d.ellipse((x-8,y-8,x+8,y+8),fill=[CYAN,GREEN][i%2])
        label(d,"MUSCLE CELL",(880,465),25,INK); label(d,"FLUID BALANCE",(880,650),20,CYAN)
    elif kind=="recovery_sleep":
        d.ellipse((260,300,570,610),fill=PALE,outline=PURPLE,width=8)
        d.arc((330,350,500,535),35,310,fill=ORANGE,width=10)
        a=t*.7; arrow(d,(415,455),(415+int(95*math.cos(a)),455+int(95*math.sin(a))),PURPLE,7)
        label(d,"SLEEP",(415,650),23,PURPLE); arrow(d,(630,455),(760,455))
        for i in range(7):
            x=790+i*42; y=450+int(15*math.sin(t*2+i))
            d.ellipse((x-10,y-10,x+10,y+10),fill=GREEN)
        d.line((790,530,1090,530),fill=CYAN,width=8)
        d.line((790,530,790+int(300*p),530),fill=ORANGE,width=10)
        label(d,"REPAIR  •  ADAPTATION",(940,610),22,GREEN)
    elif kind=="food_nutrition":
        d.ellipse((240,275,650,685),fill=PALE,outline=CYAN,width=8)
        d.ellipse((275,310,615,650),fill=(30,48,62),outline=PALE,width=3)
        if p>.02: d.pieslice((290,325,600,635),90,210,fill=(90,155,90),outline=PALE,width=3)
        if p>.25: d.pieslice((290,325,600,635),210,300,fill=(195,145,85),outline=PALE,width=3)
        if p>.5: d.pieslice((290,325,600,635),300,450,fill=(185,95,95),outline=PALE,width=3)
        label(d,"VEGETABLES",(900,350),24,GREEN); label(d,"CARBOHYDRATES",(900,445),24,ORANGE)
        label(d,"PROTEIN",(900,540),24,CYAN); arrow(d,(700,470),(780,470))
    elif kind=="digestion_fiber":
        nodes=[(230,430),(500,430),(770,430),(1040,430)]
        for i,(x,y) in enumerate(nodes):
            color=[GREEN,ORANGE,CYAN,PURPLE][i]
            d.rounded_rectangle((x-82,y-75,x+82,y+75),radius=28,fill=PALE,outline=color,width=6)
            label(d,["FOOD","STOMACH","INTESTINE","COLON"][i],(x,y+110),19,color)
            if i: arrow(d,(nodes[i-1][0]+90,y),(x-90,y),MUTED,6)
        for i in range(12):
            q=(p*1.5+i/12)%1; x=230+q*810; y=430+int(22*math.sin(q*18+t))
            d.ellipse((x-8,y-8,x+8,y+8),fill=[GREEN,CYAN,ORANGE][i%3])
        label(d,"DIGESTION + ABSORPTION",(640,635),23,PURPLE)
    elif kind=="exercise_biomechanics":
        pulse=.5+.5*math.sin(t*2.1); hip_y=380+int(70*pulse)
        head=(600,hip_y-205); shoulder=(600,hip_y-145); hip=(600,hip_y)
        knee=(500+int(25*pulse),hip_y+120); ankle=(470,625)
        d.ellipse((head[0]-35,head[1]-35,head[0]+35,head[1]+35),fill=(235,220,195),outline=INK,width=3)
        d.line((shoulder,hip),fill=(205,65,75),width=34); d.line((hip,knee),fill=ORANGE,width=30)
        d.line((knee,ankle),fill=(235,220,195),width=27)
        d.line((hip,(735,hip_y+110)),fill=ORANGE,width=30); d.line(((735,hip_y+110),(790,625)),fill=(235,220,195),width=27)
        d.line((shoulder,(500,hip_y-60)),fill=(235,220,195),width=24); d.line((shoulder,(700,hip_y-60)),fill=(235,220,195),width=24)
        for x,y in (shoulder,hip,knee,ankle,(735,hip_y+110)): d.ellipse((x-13,y-13,x+13,y+13),fill=CYAN,outline=PALE,width=2)
        label(d,"MOVEMENT PATTERN",(980,350),23,CYAN); label(d,"MUSCLES UNDER LOAD",(980,430),21,ORANGE)
        arrow(d,(930,535),(930,470-int(25*pulse)),GREEN,7)
        label(d,str(s.get("heading","")).upper()[:35],(640,665),19,INK)
    else:
        xs=[300,640,980]
        for i,x in enumerate(xs):
            color=[ORANGE,CYAN,GREEN][i]
            d.rounded_rectangle((x-105,360,x+105,535),radius=28,fill=(24,45,62),outline=color,width=6)
            label(d,["TRIGGER","PROCESS","RESULT"][i],(x,450),21,color)
            if i: arrow(d,(xs[i-1]+115,450),(x-115,450),MUTED,6)
        for i in range(8):
            q=(p*1.4+i/8)%1; x=300+q*680; y=310+int(18*math.sin(t*2+i))
            d.ellipse((x-7,y-7,x+7,y+7),fill=CYAN)
        label(d,"HOW THE SYSTEM WORKS",(640,625),23,PURPLE)
    d.rounded_rectangle((58,690,W-58,700),radius=5,fill=(210,220,228))
    d.rounded_rectangle((58,690,58+int((W-116)*p),700),radius=5,fill=CYAN)
    # Subtle eased camera drift/zoom gives every five-second beat a new, polished framing.
    zoom=1.035+0.012*(0.5+0.5*math.sin(t*0.72))
    nw,nh=int(W*zoom),int(H*zoom)
    scaled=im.resize((nw,nh),Image.Resampling.LANCZOS)
    max_x,max_y=nw-W,nh-H
    phase=beat_index*1.35
    left=int(max_x*(0.5+0.30*math.sin(t*0.32+phase)))
    top=int(max_y*(0.5+0.24*math.cos(t*0.28+phase)))
    return scaled.crop((left,top,left+W,top+H))

def render_chunk(section,section_no,kind,offset,seconds,total,outfile,beat_index=0):
    # Shared true-3D Blender renderer used by Shorts and Long.
    if os.getenv("VISUAL_ENGINE", "legacy-test-only").lower() == "blender3d":
        title = str(section.get("heading", "FITFUEL SCIENCE"))
        narration = str(section.get("narration", ""))
        cmd = ["blender", "-b", "-P", "blender_3d_scenes.py", "--",
               "--kind", kind, "--duration", str(float(seconds)),
               "--output", str(outfile), "--orientation", "landscape",
               "--text", title, "--exercise", narration[:110]]
        print("[long science 3D] section", section_no, "beat", beat_index+1, "->", kind)
        subprocess.run(cmd, check=True)
        if not Path(outfile).is_file() or Path(outfile).stat().st_size < 10000:
            raise SystemExit("Blender 3D renderer produced no valid Long scene: " + str(outfile))
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate",
             "-of", "json", str(outfile)],
            check=True, capture_output=True, text=True
        )
        streams = json.loads(probe.stdout).get("streams", [])
        if not streams:
            raise SystemExit("Long CGI output has no video stream: " + str(outfile))
        stream = streams[0]
        if (int(stream.get("width", 0)) < 1920
                or int(stream.get("height", 0)) < 1080
                or stream.get("r_frame_rate") != "30/1"):
            raise SystemExit("Long CGI production quality gate failed: " + json.dumps(stream))
        return
    temp=Path(str(outfile)+".frames"); temp.mkdir(parents=True,exist_ok=True)
    frames=max(2,int(math.ceil(seconds*FPS)))
    try:
        for frame in range(frames):
            draw_scene(section,kind,section_no,frame,offset,total,beat_index=beat_index).save(temp/f"f{frame:05d}.jpg",quality=92)
        cmd=["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(temp/"f%05d.jpg"),
             "-vf","fps=30,scale=1920:1080:flags=lanczos,setsar=1","-t",f"{seconds:.3f}",
             "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-an",str(outfile)]
        subprocess.run(cmd,check=True)
    finally: shutil.rmtree(temp,ignore_errors=True)

def main():
    path=OUT/"timeline.json"
    if not path.exists(): raise SystemExit("Missing output/long/timeline.json")
    timeline=json.loads(path.read_text(encoding="utf-8")); sections=timeline.get("sections") or []
    if not sections: raise SystemExit("Long timeline has no sections")
    SCIENCE.mkdir(parents=True,exist_ok=True); chunks=[]; info=[]; number=0
    for si,sec in enumerate(sections,1):
        start,end=float(sec["start"]),float(sec["end"])
        if end<=start: raise SystemExit(f"Invalid timing in section {si}")
        kind=classify_section(sec); windows=chunk_windows(0,end-start)
        print(f"[long science] section {si}/{len(sections)}: {sec.get('heading')} -> {kind}; {len(windows)} beats")
        for beat_index,(offset,stop) in enumerate(windows):
            number+=1; dest=SCIENCE/f"scene_{number:04d}.mp4"
            render_chunk(sec,si,kind,offset,stop-offset,end-start,dest,beat_index=beat_index)
            chunks.append({"file":str(dest),"start":round(start+offset,2),"end":round(start+stop,2),
                           "section":si,"query":sec.get("heading",""),"visual_type":kind,
                           "animation":"blender-3d-cgi-reference-style"})
        info.append({"section":si,"heading":sec.get("heading",""),"visual_type":kind,
                     "chunks":len(windows),"duration":round(end-start,2)})
    (OUT/"chunks.json").write_text(json.dumps(chunks,indent=2),encoding="utf-8")
    (OUT/"science_info.json").write_text(json.dumps(info,indent=2),encoding="utf-8")
    print(f"Rendered {len(chunks)} animated science beats across {len(sections)} sections.")

if __name__=="__main__": main()
