"""Mobile-first, dependency-free 2.5D science visual overlays for FitFuel."""
import html
import re

CATEGORIES = {
    "muscle": ("MUSCLE ADAPTATION", ["PROTEIN", "TRAINING", "RECOVERY"]),
    "nutrition": ("NUTRITION SCIENCE", ["FOOD", "DIGESTION", "ENERGY"]),
    "heart": ("CARDIOVASCULAR", ["HEART", "BLOOD FLOW", "OXYGEN"]),
    "fat_loss": ("ENERGY BALANCE", ["ENERGY IN", "MOVEMENT", "ENERGY OUT"]),
    "hydration": ("HYDRATION", ["WATER", "ELECTROLYTES", "PERFORMANCE"]),
    "exercise": ("MOVEMENT MECHANICS", ["LOAD", "CONTROL", "RANGE"]),
    "hormones": ("HORMONE SIGNALS", ["SIGNAL", "RESPONSE", "REGULATION"]),
    "general": ("THE SCIENCE", ["INPUT", "PROCESS", "RESULT"]),
}


def classify_scene(scene):
    text = " ".join(str(scene.get(k, "")) for k in
                    ("narration", "keyword", "visual_title", "visual_subtitle")).lower()
    rules = [
        ("muscle", r"muscle|hypertrophy|growth|recovery|strength|progressive overload"),
        ("hydration", r"water|hydration|dehydrat|electrolyte"),
        ("heart", r"heart|blood|circulation|cardio|oxygen"),
        ("hormones", r"hormone|insulin|cortisol|testosterone|estrogen|ghrelin|leptin"),
        ("fat_loss", r"fat loss|fat gain|calorie|energy balance|burn fat|weight loss"),
        ("nutrition", r"protein|food|meal|eat|nutrition|digest|fiber|carb|fat intake"),
        ("exercise", r"exercise|squat|deadlift|curl|press|rep|set|workout|training"),
    ]
    for category, pattern in rules:
        if re.search(pattern, text):
            return category
    return "general"


def _svg(category, labels):
    safe = [html.escape(x) for x in labels]
    return f"""<svg class="science-svg" viewBox="0 0 760 430" role="img" aria-label="{html.escape(CATEGORIES[category][0])}">
      <defs><linearGradient id="panelGlow" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#72e6c2"/><stop offset="1" stop-color="#65aaff"/></linearGradient>
      <filter id="softGlow"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <path class="orbit orbit-a" d="M90 215 C170 30 590 30 670 215 C590 400 170 400 90 215Z"/>
      <path class="orbit orbit-b" d="M130 215 C220 80 540 80 630 215 C540 350 220 350 130 215Z"/>
      <path class="flow-line" d="M170 215 H590"/>
      <g class="node node-left"><circle cx="170" cy="215" r="58"/><circle cx="170" cy="215" r="43" class="node-core"/><text x="170" y="221">${safe[0]}</text></g>
      <g class="node node-center"><circle cx="380" cy="215" r="76"/><circle cx="380" cy="215" r="58" class="node-core"/><path d="M350 215 l20 20 42 -48" class="check"/></g>
      <g class="node node-right"><circle cx="590" cy="215" r="58"/><circle cx="590" cy="215" r="43" class="node-core"/><text x="590" y="221">${safe[2]}</text></g>
      <text class="micro-label" x="380" y="345">${safe[1]}</text>
      <circle class="particle p1" cx="260" cy="110" r="6"/><circle class="particle p2" cx="500" cy="320" r="5"/><circle class="particle p3" cx="610" cy="105" r="4"/>
    </svg>"""


def build_visual_panel(scene, index=1):
    category = classify_scene(scene)
    title, labels = CATEGORIES[category]
    return (category, f'<div class="science-panel panel-{category}" data-scene="{index}">'
            f'<div class="science-kicker">FITFUEL • VISUAL EXPLAINER</div>'
            f'<div class="science-heading">{html.escape(title)}</div>{_svg(category, labels)}</div>')


def visual_css():
    return """
.science-panel{position:absolute;left:95px;right:95px;top:1010px;height:520px;border:1px solid rgba(114,230,194,.36);border-radius:34px;overflow:hidden;background:linear-gradient(135deg,rgba(7,22,36,.88),rgba(15,42,62,.68));box-shadow:0 28px 90px rgba(0,0,0,.42),inset 0 1px rgba(255,255,255,.10);transform:perspective(1100px) rotateX(4deg);backdrop-filter:blur(10px)}
.science-panel:before{content:"";position:absolute;inset:-40%;background:radial-gradient(circle at 30% 40%,rgba(114,230,194,.16),transparent 35%),radial-gradient(circle at 75% 65%,rgba(101,170,255,.17),transparent 38%);animation:panel-drift 8s ease-in-out infinite alternate}
.science-kicker{position:absolute;top:28px;left:38px;color:#72e6c2;font-size:17px;letter-spacing:5px;font-weight:800}
.science-heading{position:absolute;top:67px;left:38px;color:#f4f8ff;font-size:25px;letter-spacing:3px;font-weight:900}
.science-svg{position:absolute;left:0;top:95px;width:100%;height:390px;overflow:visible}
.orbit{fill:none;stroke:rgba(114,230,194,.28);stroke-width:2;stroke-dasharray:7 13}.orbit-a{animation:orbit-dash 18s linear infinite}.orbit-b{stroke:rgba(101,170,255,.3);animation:orbit-dash 13s linear infinite reverse}
.flow-line{stroke:url(#panelGlow);stroke-width:4;stroke-dasharray:12 12;animation:flow 2.4s linear infinite}
.node circle:first-child{fill:rgba(8,28,44,.94);stroke:#72e6c2;stroke-width:3;filter:url(#softGlow)}.node .node-core{fill:rgba(101,170,255,.16);stroke:rgba(101,170,255,.7);stroke-width:2}
.node text{fill:#fff;font-size:13px;text-anchor:middle;font-weight:900;letter-spacing:1px}.node-center circle:first-child{stroke:#72e6c2;stroke-width:4}
.check{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:100;stroke-dashoffset:100;animation:draw-check 1.4s .4s ease forwards}
.micro-label{fill:#72e6c2;text-anchor:middle;font-size:18px;font-weight:900;letter-spacing:4px}.particle{fill:#72e6c2;filter:url(#softGlow);animation:particle-float 3s ease-in-out infinite alternate}.p2{animation-delay:.7s}.p3{animation-delay:1.2s}
@keyframes panel-drift{to{transform:translate3d(5%,3%,0) rotate(8deg)}}@keyframes orbit-dash{to{stroke-dashoffset:400}}@keyframes flow{to{stroke-dashoffset:-48}}@keyframes draw-check{to{stroke-dashoffset:0}}@keyframes particle-float{to{transform:translateY(-18px);opacity:.35}}
"""
