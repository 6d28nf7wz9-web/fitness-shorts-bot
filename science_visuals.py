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

def draw_fiber_system(d, p, t):
    # Food -> stomach -> small intestine -> colon; fiber particles travel through.
    d.rounded_rectangle((90,650,360,1080),radius=42,fill=(20,37,57),outline=ORANGE,width=5)
    centered(d,"FIBER-RICH FOOD",790,font(30,True),ORANGE,240)
    # stylized whole foods
    d.ellipse((150,845,220,915),fill=(220,75,75),outline=WHITE,width=3)
    d.ellipse((235,840,300,905),fill=(85,180,95),outline=WHITE,width=3)
    d.rounded_rectangle((175,940,285,980),radius=16,fill=(194,145,83),outline=WHITE,width=2)
    arrow(d,(380,860),(475,860),CYAN,9)
    # simplified digestive tract
    d.ellipse((485,650,675,830),fill=(105,55,68),outline=(255,160,170),width=7)
    centered(d,"STOMACH",740,font(23,True),WHITE,180)
    arrow(d,(675,860),(735,860),CYAN,8)
    # small intestine loops
    for i in range(4):
        y=900+i*55
        d.arc((735,y-45,960,y+50),0,330,fill=(245,165,145),width=13)
    centered(d,"SMALL INTESTINE",1175,font(23,True),WHITE,280)
    # colon outline with animated peristaltic pulse
    d.line([(820,1180),(790,1240),(790,1420),(835,1480),(990,1480),(1020,1430),(1020,1240),(980,1180)],
           fill=(255,185,150),width=32,joint="curve")
    d.line([(820,1180),(790,1240),(790,1420),(835,1480),(990,1480),(1020,1430),(1020,1240),(980,1180)],
           fill=(120,65,80),width=16,joint="curve")
    centered(d,"COLON",1540,font(25,True),WHITE,220)
    # fiber particles move along the tract
    path=[(430,860),(535,740),(655,860),(790,930),(880,1100),(790,1260),(790,1390),(900,1480),(1020,1360)]
    count=max(1,int(1+p*8))
    for i in range(count):
        q=(p*1.4+i/9)%1
        k=min(len(path)-2,int(q*(len(path)-1)))
        u=q*(len(path)-1)-k
        x=path[k][0]*(1-u)+path[k+1][0]*u
        y=path[k][1]*(1-u)+path[k+1][1]*u
        rr=10+(i%3)*3
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=[GREEN,CYAN,ORANGE][i%3],outline=WHITE,width=2)
    if p>0.55:
        for i in range(7):
            x=845+(i%3)*54; y=1300+(i//3)*48
            rr=10+int(4*math.sin(t*4+i))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=PURPLE,outline=WHITE,width=2)
        centered(d,"GUT MICROBES",1665,font(25,True),PURPLE,400)
    centered(d,"FIBER REACHES THE COLON",1780,font(30,True),GREEN,850)


def draw_food_nutrition(d, p, t):
    # A clear food plate with portions appearing progressively.
    d.ellipse((180,700,900,1420),fill=(235,240,235),outline=WHITE,width=10)
    d.ellipse((220,740,860,1380),fill=(24,43,58),outline=CYAN,width=5)
    # three food groups, revealed left-to-right
    if p>.05:
        d.pieslice((260,780,820,1340),90,210,fill=(90,155,90),outline=WHITE,width=4)
        centered(d,"VEGETABLES",1130,font(24,True),WHITE,300)
    if p>.28:
        d.pieslice((260,780,820,1340),210,300,fill=(195,145,85),outline=WHITE,width=4)
        centered(d,"CARBS",1280,font(24,True),WHITE,250)
    if p>.52:
        d.pieslice((260,780,820,1340),300,450,fill=(185,95,95),outline=WHITE,width=4)
        centered(d,"PROTEIN",890,font(24,True),WHITE,250)
    # small animated nutrient particles move from plate toward a body-cell icon
    arrow(d,(900,1050),(990,1050),GREEN,8)
    d.ellipse((930,680,1060,810),fill=(18,48,65),outline=CYAN,width=6)
    for i in range(int(2+p*7)):
        x=960+(i*29+int(t*55))%70; y=720+(i*43)%55
        d.ellipse((x-7,y-7,x+7,y+7),fill=[ORANGE,GREEN,CYAN][i%3])
    centered(d,"FOOD → NUTRIENTS",1530,font(30,True),GREEN,800)


def draw_muscle_anatomy(d, p, t):
    # Stylized anatomical muscle with fascicle bundle and a magnified fiber.
    d.ellipse((145,570,660,1280),fill=(55,31,43),outline=(245,145,155),width=8)
    d.polygon([(245,670),(525,670),(625,1140),(430,1270),(190,1110)],fill=(125,50,65),outline=(255,165,165))
    for i in range(8):
        x=250+i*42
        offset=int(12*math.sin(t*3+i*.4))
        d.line((x,720+offset,x+90,1130+offset),fill=(235,105,125),width=18)
        d.line((x+5,735+offset,x+90,1110+offset),fill=(255,190,185),width=3)
    # zoom callout to muscle fiber
    d.ellipse((640,760,1020,1140),fill=(22,39,58),outline=CYAN,width=8)
    for i in range(5):
        y=825+i*58
        d.rounded_rectangle((700,y,950,y+26),radius=13,fill=(160,55,75),outline=(255,170,175),width=3)
        for j in range(5):
            x=720+j*48+int(6*math.sin(t*4+i+j))
            d.line((x,y+5,x+15,y+20),fill=(255,220,210),width=3)
    arrow(d,(580,890),(680,890),CYAN,8)
    centered(d,"MUSCLE FIBERS",850,font(26,True),WHITE,340)
    # contraction / adaptation pulses
    if p>.25:
        for i in range(4):
            yy=1320+i*42
            d.rounded_rectangle((220,yy,820,yy+20),radius=10,fill=(55,95,125))
            d.rounded_rectangle((220,yy,220+int(600*min(1,(p-.25)*1.5)),yy+20),radius=10,fill=ORANGE if i%2 else GREEN)
    centered(d,"ANATOMICAL SCHEMATIC",1580,font(25,True),MUTED,700)


def draw_exercise(d, p, t, exercise="SQUAT"):
    # Exercise-specific biomechanics: body position and highlighted prime movers.
    key=str(exercise).lower()
    pulse=0.5+0.5*math.sin(t*2.4)
    d.line((130,1510,950,1510),fill=MUTED,width=7)
    def joint(x,y):
        d.ellipse((x-22,y-22,x+22,y+22),fill=CYAN,outline=WHITE,width=4)
    if "overhead press" in key or "shoulder press" in key:
        # Standing press: bar travels overhead; deltoids are highlighted.
        d.line(((520,760),(520,1190)),fill=(235,220,195),width=48)
        d.ellipse((465,640,575,750),fill=(235,220,195),outline=WHITE,width=3)
        d.ellipse((430,760,610,930),fill=(205,65,75),outline=ORANGE,width=5)
        bar_y=620-int(130*pulse)
        d.line((350,bar_y,690,bar_y),fill=WHITE,width=18)
        for x in (370,670): d.rounded_rectangle((x-22,bar_y-70,x+22,bar_y+70),radius=10,fill=ORANGE)
        d.line(((450,820),(390,bar_y+5)),fill=(235,220,195),width=30)
        d.line(((590,820),(650,bar_y+5)),fill=(235,220,195),width=30)
        centered(d,"DELTOIDS • TRICEPS",1390,font(30,True),ORANGE,800)
    elif "bench" in key or "chest press" in key:
        # Supine press: torso horizontal, bar moves vertically over the chest.
        d.rounded_rectangle((230,1130,820,1220),radius=35,fill=(235,220,195),outline=WHITE,width=3)
        d.ellipse((760,1050,850,1140),fill=(235,220,195),outline=WHITE,width=3)
        d.ellipse((420,1110,650,1245),fill=(205,65,75),outline=ORANGE,width=5)
        elbow_y=930+int(45*pulse)
        d.line((540,1140,540,elbow_y),fill=(235,220,195),width=34)
        d.line((540,elbow_y,540,760+int(45*pulse)),fill=(235,220,195),width=30)
        d.line((540,760+int(45*pulse),540,700+int(45*pulse)),fill=CYAN,width=14)
        d.line((320,700+int(45*pulse),760,700+int(45*pulse)),fill=WHITE,width=18)
        for x in (300,760): d.rounded_rectangle((x-25,640+int(45*pulse),x+25,760+int(45*pulse)),radius=10,fill=ORANGE)
        centered(d,"CHEST + TRICEPS",1390,font(30,True),ORANGE,700)
    elif "curl" in key:
        # Standing elbow flexion with biceps highlighted.
        d.line((520,730,520,1160),fill=(235,220,195),width=48)
        d.ellipse((465,610,575,720),fill=(235,220,195),outline=WHITE,width=3)
        d.line((520,820,390,1050),fill=(235,220,195),width=34)
        elbow=(390,1050); wrist=(470,850-int(90*pulse))
        d.line((elbow,wrist),fill=(235,220,195),width=30)
        d.ellipse((420,850,500,1040),fill=(205,65,75),outline=ORANGE,width=4)
        d.line((wrist,(470,790-int(90*pulse))),fill=CYAN,width=14)
        d.rounded_rectangle((410,730-int(90*pulse),530,790-int(90*pulse)),radius=12,fill=WHITE)
        centered(d,"BICEPS • ELBOW FLEXION",1390,font(30,True),ORANGE,800)
    elif "deadlift" in key or "hinge" in key:
        # Hip hinge: bar travels close to the legs; posterior chain highlighted.
        hip=(570,1030); shoulder=(700,800); knee=(420,1280); ankle=(380,1450)
        d.line((shoulder,hip),fill=(235,220,195),width=48)
        d.line((hip,knee),fill=(205,65,75),width=42)
        d.line((knee,ankle),fill=(235,220,195),width=36)
        d.line((hip,(760,1260)),fill=(205,65,75),width=42)
        d.line(((760,1260),(790,1450)),fill=(235,220,195),width=36)
        d.line((shoulder,(640,1190)),fill=(235,220,195),width=26)
        d.line(((640,1190),(640,1380)),fill=(235,220,195),width=24)
        bar_y=1380-int(65*pulse)
        d.line((250,bar_y,900,bar_y),fill=WHITE,width=16)
        for x in (280,870): d.rounded_rectangle((x-28,bar_y-75,x+28,bar_y+75),radius=10,fill=ORANGE)
        centered(d,"GLUTES • HAMSTRINGS • BACK",700,font(28,True),ORANGE,900)
    elif "row" in key:
        # Bent-over row: torso hinges, elbows pull toward the ribs; upper back highlighted.
        d.line(((680,780),(520,1080)),fill=(235,220,195),width=48)
        d.ellipse((640,680,740,780),fill=(235,220,195),outline=WHITE,width=3)
        d.ellipse((500,930,650,1120),fill=(205,65,75),outline=ORANGE,width=5)
        d.line(((520,1080),(400,1410)),fill=(235,220,195),width=38)
        d.line(((520,1080),(740,1400)),fill=(235,220,195),width=38)
        elbow_y=1080-int(100*pulse)
        d.line(((630,900),(700,elbow_y)),fill=(235,220,195),width=30)
        d.line(((700,elbow_y),(700,1250-int(100*pulse))),fill=(235,220,195),width=28)
        d.line(((700,1250-int(100*pulse)),(900,1250-int(100*pulse))),fill=WHITE,width=14)
        centered(d,"LATS • RHOMBOIDS • BICEPS",1390,font(28,True),ORANGE,900)
    elif "lunge" in key:
        # Split stance: front knee bends while the rear leg extends.
        d.line(((520,760),(520,1080)),fill=(235,220,195),width=45)
        d.ellipse((465,640,575,750),fill=(235,220,195),outline=WHITE,width=3)
        d.ellipse((430,900,610,1100),fill=(205,65,75),outline=ORANGE,width=5)
        d.line(((520,1080),(350,1270)),fill=(205,65,75),width=42)
        d.line(((350,1270),(330,1460)),fill=(235,220,195),width=34)
        d.line(((520,1080),(740,1240)),fill=(205,65,75),width=42)
        d.line(((740,1240),(900,1420)),fill=(235,220,195),width=34)
        centered(d,"QUADRICEPS • GLUTES",1390,font(30,True),ORANGE,800)
    elif "push" in key:
        # Push-up plank: elbows flex and extend; chest/triceps highlighted.
        shoulder=(330,1050); hip=(650,1120); ankle=(900,1190)
        d.line((shoulder,hip),fill=(235,220,195),width=42)
        d.line((hip,ankle),fill=(235,220,195),width=32)
        d.ellipse((250,980,350,1080),fill=(235,220,195),outline=WHITE,width=3)
        elbow=(450,1320-int(50*pulse)); wrist=(360,1460)
        d.line((shoulder,elbow),fill=(205,65,75),width=34)
        d.line((elbow,wrist),fill=(235,220,195),width=28)
        joint(*elbow); joint(*wrist)
        centered(d,"CHEST • SHOULDERS • TRICEPS",700,font(28,True),ORANGE,900)
    else:
        # Squat: hip/knee flexion with quadriceps and glutes highlighted.
        hip_y=850+int(85*pulse)
        shoulder=(520,hip_y-250); hip=(520,hip_y)
        knee=(390+int(40*pulse),hip_y+190); ankle=(350,1450)
        d.line((shoulder,hip),fill=(235,220,195),width=42)
        d.line((shoulder,(430,hip_y-310)),fill=(235,220,195),width=30)
        d.line(((430,hip_y-310),(365,hip_y-270)),fill=(235,220,195),width=26)
        d.line((hip,knee),fill=(205,65,75),width=38)
        d.line((knee,ankle),fill=(235,220,195),width=34)
        d.line((hip,(650,hip_y+160)),fill=(205,65,75),width=38)
        d.line(((650,hip_y+160),(720,1450)),fill=(235,220,195),width=34)
        for x,y in [shoulder,hip,knee,ankle,(650,hip_y+160)]: joint(x,y)
        centered(d,"QUADRICEPS • GLUTES",700,font(30,True),ORANGE,800)
    centered(d,str(exercise).upper()[:30],590,font(34,True),WHITE,850)
    if p>.25:
        arrow(d,(930,930),(930,790),GREEN,8)
        arrow(d,(160,1120),(160,1260),GREEN,8)



def draw_protein_synthesis(d, p, t):
    # Dietary protein -> amino acids -> muscle cell -> assembling protein strands.
    d.rounded_rectangle((95,670,365,1080),radius=34,fill=(20,42,59),outline=CYAN,width=5)
    centered(d,"PROTEIN",740,font(31,True),CYAN,220)
    for i in range(5):
        x=155+(i%2)*105; y=850+(i//2)*62
        protein(d,x,y,24,[CYAN,ORANGE,GREEN][i%3])
    arrow(d,(390,880),(500,880),ORANGE,9)
    d.ellipse((500,650,1020,1220),fill=(18,48,65),outline=CYAN,width=8)
    centered(d,"MUSCLE CELL",720,font(31,True),WHITE,400)
    # particles move into cell and link into a growing chain
    for i in range(10):
        q=(p*1.1+i/10)%1
        x=430+q*430; y=850+math.sin(q*math.pi*4+i)*65
        d.ellipse((x-14,y-14,x+14,y+14),fill=[ORANGE,GREEN,CYAN][i%3],outline=WHITE,width=2)
    if p>.35:
        pts=[]
        for i in range(9):
            pts.append((610+i*38,1040+math.sin(i*.9+t*2)*30))
        d.line(pts,fill=GREEN,width=12,joint="curve")
        for x,y in pts:
            d.ellipse((x-15,y-15,x+15,y+15),fill=GREEN,outline=WHITE,width=2)
    centered(d,"AMINO ACIDS → NEW PROTEIN",1430,font(31,True),GREEN,850)


def draw_energy(d, p, t):
    # Fat-cell energy release -> bloodstream transport -> mitochondria/ATP.
    for i in range(3):
        x=180+i*150; y=880+int(12*math.sin(t*2+i))
        d.ellipse((x-72,y-72,x+72,y+72),fill=(220,155,70),outline=ORANGE,width=7)
        d.ellipse((x-32,y-32,x+32,y+32),fill=(245,205,130))
    centered(d,"STORED ENERGY",700,font(30,True),ORANGE,700)
    arrow(d,(660,900),(800,900),CYAN,10)
    # mitochondrion with animated cristae
    d.ellipse((785,730,1030,1080),fill=(70,50,35),outline=GREEN,width=8)
    for i in range(4):
        y=800+i*62
        d.arc((830,y-20,980,y+35),0,180,fill=(255,190,90),width=8)
    for i in range(int(2+p*8)):
        x=820+(i*31+int(t*65))%180; y=1140+(i%3)*45
        d.ellipse((x-11,y-11,x+11,y+11),fill=CYAN)
    centered(d,"ATP / CELLULAR ENERGY",1380,font(30,True),GREEN,800)


def draw_hydration(d, p, t):
    # Water moves into a muscle cell; cell fluid level responds.
    d.ellipse((260,680,830,1250),fill=(15,50,72),outline=CYAN,width=9)
    centered(d,"MUSCLE CELL",760,font(31,True),WHITE,450)
    for i in range(int(3+p*10)):
        x=340+(i*71+int(t*45))%400
        y=900+(i*43)%240
        d.ellipse((x-12,y-12,x+12,y+12),fill=(80,210,255),outline=WHITE,width=2)
    arrow(d,(130,960),(250,960),CYAN,10)
    d.polygon([(180,790),(135,865),(150,920),(180,940),(210,920),(225,865)],fill=(35,135,200),outline=CYAN)
    centered(d,"FLUID BALANCE",1420,font(34,True),CYAN,750)


def draw_recovery(d, p, t):
    # Recovery timeline and tissue repair metaphor.
    d.ellipse((390,700,690,1000),fill=(250,180,90),outline=ORANGE,width=6)
    d.ellipse((510,650,780,920),fill=BG)
    for i in range(8):
        x=160+i*105; y=1190+int(18*math.sin(t*2+i))
        r=12+int(4*math.sin(t*3+i))
        d.ellipse((x-r,y-r,x+r,y+r),fill=PURPLE)
    centered(d,"SLEEP + RECOVERY",1080,font(35,True),PURPLE,850)
    d.line((150,1400,930,1400),fill=CYAN,width=8)
    d.ellipse((150,1380,190,1420),fill=GREEN)
    d.ellipse((150+int(780*p),1380,190+int(780*p),1420),fill=ORANGE)
    centered(d,"REPAIR AND ADAPTATION",1510,font(30,True),WHITE,850)


def draw_process(d, p, t, title, subtitle):
    # Sequential reveal of a 3-step causal mechanism, with a travelling signal.
    labels=["TRIGGER","PROCESS","RESULT"]
    xs=[220,540,860]
    colors=[ORANGE,CYAN,GREEN]
    for i,(x,label,color) in enumerate(zip(xs,labels,colors)):
        if p < i*.25: continue
        d.rounded_rectangle((x-115,850,x+115,1110),radius=35,fill=(20,40,60),outline=color,width=6)
        centered(d,label,960,font(29,True),color,200)
        if i:
            arrow(d,(xs[i-1]+120,980),(x-125,980),WHITE,7)
    for i in range(5):
        q=(p*1.6+i/5)%1
        x=220+q*640; y=780+int(18*math.sin(t*3+i))
        d.ellipse((x-12,y-12,x+12,y+12),fill=CYAN,outline=WHITE,width=2)
    centered(d,subtitle[:70],1300,font(32,True),WHITE,850)


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


def classify_scene(scene):
    text=" ".join(str(scene.get(k,"")) for k in
                  ("narration","visual_title","visual_subtitle","visual_instruction","keyword")).lower()
    requested=str(scene.get("visual_type","")).strip().lower()
    aliases={
        "fiber":"digestion_fiber","digestion":"digestion_fiber","gut":"digestion_fiber",
        "muscle":"muscle_anatomy","anatomy":"muscle_anatomy",
        "exercise":"exercise_biomechanics","biomechanics":"exercise_biomechanics",
        "protein":"protein_synthesis","nutrition":"food_nutrition",
        "fat_loss":"energy_metabolism","energy":"energy_metabolism",
        "sleep":"recovery_sleep","recovery":"recovery_sleep",
    }
    requested=aliases.get(requested,requested)
    allowed={"digestion_fiber","muscle_anatomy","exercise_biomechanics",
             "protein_synthesis","energy_metabolism","hydration","recovery_sleep",
             "food_nutrition","process"}
    # Specific biological/exercise cues override a broad model label.
    if re.search(r"dietary fiber|dietary fibre|fiber-rich|fibre-rich|gut|intestin|digest|microbiome|prebiotic|whole grain",text):
        return "digestion_fiber"
    if re.search(r"squat|deadlift|bench press|lunge|curl|row exercise|push.?up|pull.?up|exercise form|range of motion|joint angle",text):
        return "exercise_biomechanics"
    if re.search(r"protein synthesis|amino acid|muscle protein synthesis|mps",text):
        return "protein_synthesis"
    if re.search(r"calorie|energy balance|fat loss|weight loss|deficit|surplus|fat oxidation|lipolysis",text):
        return "energy_metabolism"
    if re.search(r"water|hydration|fluid|dehydrat",text):
        return "hydration"
    if re.search(r"sleep|recovery|rest day|fatigue",text):
        return "recovery_sleep"
    if requested in allowed: return requested
    if re.search(r"muscle|muscle fiber|muscle fibre|hypertrophy|resistance|strength|lifting|biceps|quadriceps|glute|hamstring|chest",text):
        return "muscle_anatomy"
    if re.search(r"food|meal|eat|nutrition|carb|carbohydrate|vegetable|fruit|protein source",text):
        return "food_nutrition"
    return "process"


def scene_text(scene):
    narration=str(scene.get("narration","")).strip()
    title=str(scene.get("visual_title") or scene.get("heading") or narration[:55]).strip()
    subtitle=str(scene.get("visual_subtitle") or narration).strip()
    instruction=str(scene.get("visual_instruction") or "").strip()
    return title[:90],subtitle[:180],narration,instruction


def draw_diagram(scene, index, frame, frames):
    title,subtitle,narration,instruction=scene_text(scene)
    kind=classify_scene(scene)
    p=min(1.0,max(0.0,frame/max(1,frames-1)))
    t=frame/FPS
    im,d=base_scene(title,subtitle,index)
    # Every frame is redrawn: objects are progressively revealed and animated,
    # instead of applying a slow zoom to one static illustration.
    if kind=="digestion_fiber":
        draw_fiber_system(d,p,t)
    elif kind=="muscle_anatomy":
        draw_muscle_anatomy(d,p,t)
    elif kind=="exercise_biomechanics":
        exercise=" ".join([title,narration,instruction])[:110]
        draw_exercise(d,p,t,exercise)
    elif kind=="protein_synthesis":
        draw_protein_synthesis(d,p,t)
    elif kind=="energy_metabolism":
        draw_energy(d,p,t)
    elif kind=="hydration":
        draw_hydration(d,p,t)
    elif kind=="recovery_sleep":
        draw_recovery(d,p,t)
    elif kind=="food_nutrition":
        draw_food_nutrition(d,p,t)
    else:
        draw_process(d,p,t,title,subtitle)
    # Animated stroke/reveal marker tracks the spoken scene.
    x=70+int((W-140)*p)
    d.rounded_rectangle((70,H-170,W-70,H-75),radius=24,fill=(18,31,50),outline=(38,58,82),width=2)
    d.text((W/2,H-122),"FITFUEL  •  SCIENCE EXPLAINER",font=font(24,True),fill=MUTED,anchor="mm")
    d.rounded_rectangle((70,H-48,x,H-34),radius=7,fill=CYAN)
    return im


def render_scene(scene,index,seconds,outfile):
    os.makedirs(os.path.dirname(outfile),exist_ok=True)
    frames=max(2,int(seconds*FPS))
    temp=outfile+".frames"
    os.makedirs(temp,exist_ok=True)
    try:
        for frame in range(frames):
            draw_diagram(scene,index,frame,frames).save(f"{temp}/f{frame:05d}.png")
        cmd=["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",f"{temp}/f%05d.png",
             "-t",f"{seconds:.3f}","-c:v","libx264","-preset","veryfast","-crf","21",
             "-pix_fmt","yuv420p","-an",outfile]
        subprocess.run(cmd,check=True)
    finally:
        for name in os.listdir(temp):
            os.remove(os.path.join(temp,name))
        os.rmdir(temp)
    return {"scene":index,"type":classify_scene(scene),"title":scene_text(scene)[0],
            "file":outfile,"seconds":round(seconds,2),"animation":"drawn-and-moving"}



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
        print(f"[science] scene {i}/{len(scenes)} -> {classify_scene(scene)}")
        rendered.append(render_scene(scene,i,seconds,dest))
    with open("output/science_info.json","w",encoding="utf-8") as f: json.dump(rendered,f,indent=2)
    print(f"Scientific visuals ready: {len(rendered)} scenes -> {OUT}/")

if __name__=="__main__": main()
