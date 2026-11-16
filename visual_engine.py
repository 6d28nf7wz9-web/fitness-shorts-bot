"""Scene-specific, dependency-free science diagrams for FitFuel Shorts."""
import html
import re

CATEGORIES = {
    "muscle": ("MUSCLE FIBER ADAPTATION", ["MECHANICAL TENSION", "REPAIR", "GROWTH"]),
    "nutrition": ("NUTRIENT PATHWAY", ["FOOD", "ABSORPTION", "FUEL"]),
    "heart": ("CARDIOVASCULAR FLOW", ["OXYGEN IN", "PUMP", "DELIVERY"]),
    "fat_loss": ("ENERGY BALANCE", ["ENERGY IN", "STORAGE", "ENERGY OUT"]),
    "hydration": ("HYDRATION & ELECTROLYTES", ["FLUID", "BALANCE", "PERFORMANCE"]),
    "exercise": ("MOVEMENT MECHANICS", ["LOAD", "JOINT", "MOTION"]),
    "hormones": ("HORMONE SIGNALING", ["SIGNAL", "RECEPTOR", "RESPONSE"]),
    "general": ("THE SCIENCE", ["INPUT", "PROCESS", "RESULT"]),
}

RULES = [
    ("hydration", r"\b(?:hydration|dehydrat\w*|electrolyte\w*|sodium|potassium|fluid balance)\b"),
    ("heart", r"\b(?:heart|blood|circulation|cardiovascular|oxygen delivery|pulse|blood pressure)\b"),
    ("hormones", r"\b(?:hormone\w*|insulin|cortisol|testosterone|estrogen|ghrelin|leptin|receptor|thyroid)\b"),
    ("fat_loss", r"\b(?:fat loss|fat gain|calorie\w*|energy balance|burn fat|weight loss|calorie deficit)\b"),
    ("nutrition", r"\b(?:food|meal|nutrition|digest\w*|absorption|fiber|carbohydrate\w*|protein intake|nutrient\w*)\b"),
    ("muscle", r"\b(?:muscle\w*|hypertrophy|strength|progressive overload|protein synthesis|muscle recovery)\b"),
    ("exercise", r"\b(?:exercise|squat|deadlift|curl|press|repetition|workout|training|joint|movement mechanics)\b"),
]


def classify_scene(scene):
    source = " ".join(str(scene.get(k, "")) for k in
                      ("keyword", "visual_title", "visual_subtitle", "narration")).lower()
    for category, pattern in RULES:
        if re.search(pattern, source):
            return category
    return "general"


def _label(value, fallback, limit=22):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return html.escape(text[:limit] if text else fallback)


def _diagram(category, labels, uid):
    a, b, c = labels
    # Each topic has its own visual metaphor and geometry, not just recolored nodes.
    if category == "muscle":
        body = f"""
          <g class="fiber-group">
            <path class="fiber" d="M90 135 C190 85 270 185 370 135 S550 85 670 135"/>
            <path class="fiber fiber-two" d="M90 175 C190 125 270 225 370 175 S550 125 670 175"/>
            <path class="fiber fiber-three" d="M90 215 C190 165 270 265 370 215 S550 165 670 215"/>
            <path class="fiber fiber-four" d="M90 255 C190 205 270 305 370 255 S550 205 670 255"/>
          </g>
          <g class="satellite"><circle cx="180" cy="330" r="19"/><circle cx="580" cy="330" r="19"/></g>
          <path class="arrow" d="M220 330 H530"/><text x="380" y="365" class="diagram-note">MICRO-DAMAGE → REPAIR → ADAPTATION</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "nutrition":
        body = f"""
          <circle class="plate" cx="185" cy="210" r="116"/><path class="plate-line" d="M185 94 V326 M69 210 H185"/>
          <path class="nutrient protein" d="M185 94 A116 116 0 0 1 185 326 Z"/>
          <path class="nutrient carbs" d="M185 94 A116 116 0 0 0 69 210 H185Z"/>
          <path class="nutrient fats" d="M69 210 A116 116 0 0 0 185 326 V210Z"/>
          <path class="arrow" d="M320 210 H425"/><g class="gut"><path d="M470 115 C420 145 530 165 470 195 S530 245 470 275 S520 310 480 330"/></g>
          <g class="fuel-dots"><circle cx="570" cy="150" r="12"/><circle cx="610" cy="210" r="9"/><circle cx="565" cy="275" r="15"/></g>
          <text x="185" y="370" class="diagram-note">BALANCED PLATE</text><text x="535" y="370" class="diagram-note">AVAILABLE FUEL</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "heart":
        body = f"""
          <path class="vessel" d="M90 210 H265 M495 210 H670"/><path class="pulse" d="M90 210 H255 L290 210 L320 145 L355 285 L390 175 L420 210 H670"/>
          <path class="heart-shape" d="M380 300 C350 270 285 225 300 175 C315 125 365 140 380 170 C400 130 455 130 465 180 C480 230 420 275 380 300Z"/>
          <circle class="oxygen" cx="140" cy="175" r="11"/><circle class="oxygen oxygen-two" cx="185" cy="245" r="8"/>
          <circle class="oxygen oxygen-three" cx="585" cy="170" r="10"/><circle class="oxygen oxygen-four" cx="625" cy="245" r="7"/>
          <text x="380" y="365" class="diagram-note">PUMP • FLOW • OXYGEN DELIVERY</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "fat_loss":
        body = f"""
          <path class="balance-beam" d="M190 165 H570"/><path class="balance-stand" d="M380 165 L330 320 H430Z"/>
          <path class="balance-pan" d="M190 165 L130 270 Q190 305 250 270Z M570 165 L510 270 Q570 305 630 270Z"/>
          <path class="balance-cable" d="M190 165 V250 M570 165 V250"/>
          <g class="energy-in"><circle cx="190" cy="225" r="18"/><circle cx="160" cy="250" r="10"/><circle cx="220" cy="250" r="10"/></g>
          <g class="energy-out"><path d="M570 220 l-20 28 h18 l-10 25 35 -38 h-20Z"/></g>
          <text x="190" y="345" class="diagram-note">INTAKE</text><text x="570" y="345" class="diagram-note">EXPENDITURE</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "hydration":
        body = f"""
          <path class="drop" d="M190 95 C165 150 105 215 120 270 C135 330 245 330 260 270 C275 215 215 150 190 95Z"/>
          <path class="drop-shine" d="M160 235 Q155 275 185 290"/><path class="flow-line" d="M315 210 H445"/>
          <g class="electrolytes"><circle cx="500" cy="145" r="25"/><circle cx="585" cy="210" r="25"/><circle cx="500" cy="275" r="25"/></g>
          <text x="500" y="151" class="ion">Na+</text><text x="585" y="216" class="ion">K+</text><text x="500" y="281" class="ion">Mg</text>
          <path class="balance-ring" d="M465 105 Q650 210 465 315"/>
          <text x="380" y="365" class="diagram-note">FLUID + ELECTROLYTE BALANCE</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "exercise":
        body = f"""
          <path class="bone" d="M160 115 Q185 95 205 125 L315 250 Q335 275 310 295 Q285 315 265 285 L150 160 Q130 135 160 115Z"/>
          <path class="bone bone-two" d="M420 120 Q445 95 465 125 L575 250 Q595 275 570 295 Q545 315 525 285 L410 165 Q390 140 420 120Z"/>
          <circle class="joint" cx="380" cy="210" r="58"/><circle class="joint-core" cx="380" cy="210" r="28"/>
          <path class="lever" d="M260 330 Q380 390 500 330"/><path class="arrow" d="M380 125 V70"/>
          <text x="380" y="375" class="diagram-note">CONTROLLED RANGE OF MOTION</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "hormones":
        body = f"""
          <path class="signal-wave" d="M90 210 C140 110 200 310 260 210 S380 110 440 210"/>
          <g class="signal-dots"><circle cx="160" cy="175" r="12"/><circle cx="220" cy="235" r="9"/><circle cx="280" cy="175" r="12"/></g>
          <path class="receptor" d="M475 130 V205 M455 205 Q475 235 495 205 M475 205 V300"/>
          <path class="response" d="M520 210 H630 M610 190 L632 210 L610 230"/>
          <circle class="cell" cx="475" cy="210" r="100"/>
          <text x="380" y="365" class="diagram-note">SIGNAL → RECEPTOR → CELL RESPONSE</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    else:
        body = f"""
          <g class="process-box"><rect x="70" y="145" width="165" height="130" rx="22"/><rect x="300" y="145" width="165" height="130" rx="22"/><rect x="530" y="145" width="165" height="130" rx="22"/></g>
          <path class="arrow" d="M240 210 H290 M470 210 H520"/>
          <circle class="process-pulse" cx="150" cy="210" r="25"/><circle class="process-pulse pulse-two" cx="380" cy="210" r="25"/><circle class="process-pulse pulse-three" cx="610" cy="210" r="25"/>
          <text x="380" y="355" class="diagram-note">A SIMPLE CAUSE-AND-EFFECT MODEL</text>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    return f"""<svg class="science-svg" viewBox="0 0 760 430" role="img" aria-label="{html.escape(CATEGORIES[category][0])}">
      <defs><linearGradient id="panelGlow{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#72e6c2"/><stop offset="1" stop-color="#65aaff"/></linearGradient>
      <filter id="softGlow{uid}"><feGaussianBlur stdDeviation="6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      {body}
    </svg>"""


def build_visual_panel(scene, index=1):
    category = classify_scene(scene)
    title, defaults = CATEGORIES[category]
    labels = [
        _label(scene.get("visual_title"), defaults[0], 26),
        _label(scene.get("visual_subtitle"), defaults[1], 26),
        defaults[2],
    ]
    diagram = _diagram(category, labels, index)
    panel = (f'<div class="science-panel panel-{category}" data-scene="{index}">'
             f'<div class="science-kicker">FITFUEL • VISUAL EXPLAINER</div>'
             f'<div class="science-heading">{html.escape(title)}</div>{diagram}</div>')
    return category, panel


def visual_css():
    return """
.science-panel{position:absolute;left:95px;right:95px;top:1010px;height:520px;border:1px solid rgba(114,230,194,.36);border-radius:34px;overflow:hidden;background:linear-gradient(135deg,rgba(7,22,36,.91),rgba(15,42,62,.76));box-shadow:0 28px 90px rgba(0,0,0,.42),inset 0 1px rgba(255,255,255,.10);transform:perspective(1100px) rotateX(4deg);backdrop-filter:blur(10px)}
.science-panel:before{content:"";position:absolute;inset:-40%;background:radial-gradient(circle at 30% 40%,rgba(114,230,194,.16),transparent 35%),radial-gradient(circle at 75% 65%,rgba(101,170,255,.17),transparent 38%);animation:panel-drift 8s ease-in-out infinite alternate}
.science-kicker{position:absolute;top:28px;left:38px;color:#72e6c2;font-size:17px;letter-spacing:5px;font-weight:800}
.science-heading{position:absolute;top:67px;left:38px;color:#f4f8ff;font-size:25px;letter-spacing:3px;font-weight:900}
.science-svg{position:absolute;left:0;top:95px;width:100%;height:390px;overflow:visible}
.science-svg text{font-family:Arial,sans-serif}
.diagram-label{fill:#72e6c2;text-anchor:middle;font-size:16px;font-weight:900;letter-spacing:2px}
.diagram-note{fill:#eaf5ff;text-anchor:middle;font-size:14px;font-weight:800;letter-spacing:2px}
.fiber{fill:none;stroke:#72e6c2;stroke-width:17;stroke-linecap:round;filter:drop-shadow(0 0 8px rgba(114,230,194,.5));stroke-dasharray:24 8;animation:fiber-pulse 3s ease-in-out infinite alternate}
.fiber-two{stroke:#65aaff;animation-delay:.3s}.fiber-three{stroke:#a4f2df;animation-delay:.6s}.fiber-four{stroke:#65aaff;animation-delay:.9s}
.satellite circle{fill:#65aaff;stroke:#fff;stroke-width:3}.arrow{fill:none;stroke:#72e6c2;stroke-width:5;stroke-linecap:round;stroke-linejoin:round;marker-end:none;stroke-dasharray:12 10;animation:flow 2s linear infinite}
.plate{fill:rgba(255,255,255,.05);stroke:#eaf5ff;stroke-width:7}.plate-line{stroke:#eaf5ff;stroke-width:5}.nutrient{stroke:#07111d;stroke-width:3}.protein{fill:#72e6c2}.carbs{fill:#65aaff}.fats{fill:#f6bd60}.gut path{fill:none;stroke:#f6bd60;stroke-width:16;stroke-linecap:round;stroke-dasharray:5 9;animation:flow 3s linear infinite}.fuel-dots circle{fill:#72e6c2;filter:drop-shadow(0 0 9px #72e6c2);animation:float 2s ease-in-out infinite alternate}
.vessel{fill:none;stroke:#65aaff;stroke-width:25;stroke-linecap:round}.pulse{fill:none;stroke:#72e6c2;stroke-width:7;stroke-linejoin:round;stroke-dasharray:25 9;animation:flow 1.8s linear infinite}.heart-shape{fill:#e85d75;stroke:#ffb4c0;stroke-width:5;transform-origin:380px 210px;animation:heartbeat 1.2s ease-in-out infinite}.oxygen{fill:#72e6c2;filter:drop-shadow(0 0 8px #72e6c2);animation:float 2s infinite alternate}.oxygen-two{animation-delay:.5s}.oxygen-three{animation-delay:.8s}.oxygen-four{animation-delay:1.1s}
.balance-beam,.balance-stand,.balance-cable{fill:none;stroke:#eaf5ff;stroke-width:9;stroke-linecap:round}.balance-pan{fill:rgba(101,170,255,.2);stroke:#65aaff;stroke-width:5}.energy-in circle{fill:#f6bd60}.energy-out path{fill:#72e6c2;stroke:#72e6c2;stroke-width:3}
.drop{fill:rgba(101,170,255,.25);stroke:#65aaff;stroke-width:8;filter:drop-shadow(0 0 10px #65aaff)}.drop-shine{fill:none;stroke:#fff;stroke-width:8;stroke-linecap:round}.electrolytes circle{fill:#72e6c2;stroke:#eaf5ff;stroke-width:3;animation:float 2s ease-in-out infinite alternate}.electrolytes circle:nth-child(2){animation-delay:.5s}.electrolytes circle:nth-child(3){animation-delay:1s}.ion{fill:#07111d;text-anchor:middle;font-size:15px;font-weight:900}.balance-ring{fill:none;stroke:#65aaff;stroke-width:5;stroke-dasharray:10 12}
.bone{fill:#eaf5ff;stroke:#a8c6d8;stroke-width:7}.bone-two{fill:#d3e6f1}.joint{fill:rgba(114,230,194,.25);stroke:#72e6c2;stroke-width:8}.joint-core{fill:#65aaff;stroke:#fff;stroke-width:4}.lever{fill:none;stroke:#f6bd60;stroke-width:8;stroke-linecap:round}
.signal-wave{fill:none;stroke:#f6bd60;stroke-width:8;stroke-linecap:round;stroke-dasharray:18 12;animation:flow 2s linear infinite}.signal-dots circle{fill:#f6bd60;filter:drop-shadow(0 0 8px #f6bd60)}.cell{fill:rgba(101,170,255,.08);stroke:#65aaff;stroke-width:5;stroke-dasharray:9 10}.receptor{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round}.response{fill:none;stroke:#72e6c2;stroke-width:8;stroke-linecap:round;stroke-linejoin:round;animation:flow 2s linear infinite}
.process-box rect{fill:rgba(101,170,255,.12);stroke:#65aaff;stroke-width:4}.process-pulse{fill:#72e6c2;filter:drop-shadow(0 0 10px #72e6c2);animation:node-pulse 1.8s ease-in-out infinite}.pulse-two{animation-delay:.5s}.pulse-three{animation-delay:1s}
@keyframes panel-drift{to{transform:translate3d(5%,3%,0) rotate(8deg)}}@keyframes flow{to{stroke-dashoffset:-64}}@keyframes fiber-pulse{to{stroke-dashoffset:-64;opacity:.65}}@keyframes float{to{transform:translateY(-13px);opacity:.65}}@keyframes heartbeat{50%{transform:scale(1.06)}}@keyframes node-pulse{50%{opacity:.45;transform:scale(.8)}}
"""
