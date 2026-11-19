"""Scene-specific, dependency-free science diagrams for FitFuel Shorts."""
import html
import re

CATEGORIES = {
    "muscle": ("MUSCLE FIBER ADAPTATION", ["MECHANICAL TENSION", "REPAIR", "GROWTH"]),
    "anatomy": ("TARGET MUSCLE ANATOMY", ["MUSCLE GROUP", "CONTRACTION", "FUNCTION"]),
    "recovery": ("RECOVERY & ADAPTATION", ["TRAINING STRESS", "REST", "REBUILD"]),
    "nutrition": ("NUTRIENT PATHWAY", ["FOOD", "ABSORPTION", "FUEL"]),
    "protein": ("PROTEIN SYNTHESIS", ["PROTEIN", "AMINO ACIDS", "MUSCLE REPAIR"]),
    "heart": ("CARDIOVASCULAR FLOW", ["OXYGEN IN", "PUMP", "DELIVERY"]),
    "fat_loss": ("ENERGY BALANCE", ["ENERGY IN", "STORAGE", "ENERGY OUT"]),
    "hydration": ("HYDRATION & ELECTROLYTES", ["FLUID", "BALANCE", "PERFORMANCE"]),
    "exercise": ("MOVEMENT MECHANICS", ["LOAD", "JOINT", "MOTION"]),
    "hormones": ("HORMONE SIGNALING", ["SIGNAL", "RECEPTOR", "RESPONSE"]),
    "supplements": ("SUPPLEMENT EVIDENCE", ["DOSE", "EVIDENCE", "EXPECTATION"]),
    "tracking": ("PROGRESSIVE OVERLOAD", ["BASELINE", "LOAD", "PROGRESSION"]),
    "creatine": ("CREATINE & ATP RECYCLING", ["CREATINE", "PHOSPHOCREATINE", "ATP RECHARGE"]),
    "general": ("THE SCIENCE", ["INPUT", "PROCESS", "RESULT"]),
}

RULES = [
    ("tracking", r"\b(?:track(?:ing)? (?:your )?(?:lifts?|progress|workouts?)|log(?:ging)? (?:your )?lifts?|training log|progress tracking|progressive overload|strength progression|weekly progression|rep progression|gradual load increase|increase (?:the )?load|add weight or reps|overload importance)\b"),
    ("protein", r"\b(?:protein synthesis|protein intake|protein needs?|protein powder|whey protein|amino acids?)\b"),
    ("nutrition", r"\b(?:food|meal|nutrition|digest\w*|absorption|dietary fiber|carbohydrate\w*|nutrient\w*)\b"),
    ("creatine", r"\bcreatine\b"),
    ("recovery", r"\b(?:recovery|recover\w*|rest day\w*|deload\w*|sleep quality|muscle repair)\b"),
    ("supplements", r"\b(?:supplement\w*|caffeine|pre[- ]?workout|ergogenic aid)\b"),
    ("hydration", r"\b(?:hydration|dehydrat\w*|electrolyte\w*|sodium|potassium|fluid balance)\b"),
    ("heart", r"\b(?:heart|blood|circulation|cardiovascular|oxygen delivery|pulse|blood pressure)\b"),
    ("hormones", r"\b(?:hormone\w*|insulin|cortisol|testosterone|estrogen|ghrelin|leptin|receptor|thyroid)\b"),
    ("fat_loss", r"\b(?:fat loss|fat gain|calorie\w*|energy balance|burn fat|weight loss|calorie deficit|energy metabolism)\b"),
    ("muscle", r"\b(?:muscle\w*|muscle fiber\w*|hypertrophy|strength|muscle recovery)\b"),
    ("exercise", r"\b(?:exercise|lift\w*|weight loading|squat|deadlift|curl|press|repetition|workout|training|joint|movement mechanics)\b"),
]

VISUAL_TYPE_CATEGORIES = {
    "protein_synthesis": "protein",
    "progressive_overload": "tracking",
    "supplement_evidence": "supplements",
    "muscle_anatomy": "anatomy",
    "exercise_biomechanics": "exercise",
    "digestion_fiber": "nutrition",
    "food_nutrition": "nutrition",
    "energy_metabolism": "fat_loss",
    "hydration": "hydration",
    "recovery_sleep": "recovery",
    "process": "general",
}

def classify_scene(scene):
    """Prefer explicit headline intent, then declared visual type, over broad keywords."""
    title = str(scene.get("visual_title", "")).lower()
    declared_visual_type = str(scene.get("visual_type", "")).strip().lower()
    if declared_visual_type == "muscle_anatomy":
        return "anatomy"
    title_priority = (
        ("anatomy", r"\b(?:anatomy|pectorals?|deltoids?|biceps?|triceps?|quadriceps?|hamstrings?|glutes?|lats?|latissimus|muscle activation)\b"),
        ("supplements", r"\bsupplement\w*\b"),
        ("creatine", r"\bcreatine\b"),
        ("protein", r"\bprotein\b|\bamino acids?\b|\bwhey\b"),
        ("muscle", r"\bmechanical tension\b|\bmuscle tension\b|\bmuscle fibers?\b"),
        ("tracking", r"\b(?:overload|progression|load increase|track(?:ing)?|training log)\b"),
        ("hydration", r"\b(?:hydration|electrolyte)\b"),
        ("hormones", r"\b(?:hormone|insulin|cortisol|testosterone|estrogen)\b"),
        ("fat_loss", r"\b(?:fat loss|calorie|energy balance|weight loss)\b"),
        ("recovery", r"\b(?:recovery|rest day|deload|sleep)\b"),
        ("muscle", r"\b(?:muscle|hypertrophy|strength)\b"),
        ("nutrition", r"\b(?:nutrition|food|meal|digestion)\b"),
        ("exercise", r"\b(?:exercise|weight loading|lifting|lift|squat|deadlift|curl|press|movement)\b"),
    )
    for category, pattern in title_priority:
        if re.search(pattern, title):
            return category

    declared_type = str(scene.get("visual_type", "")).strip().lower()
    if declared_type in VISUAL_TYPE_CATEGORIES:
        return VISUAL_TYPE_CATEGORIES[declared_type]

    visual_sources = (
        (str(scene.get("visual_subtitle", "")).lower(), 65),
        (str(scene.get("keyword", "")).lower(), 45),
        (str(scene.get("visual_instruction", "")).lower(), 35),
    )
    scores = {}
    for source, weight in visual_sources:
        if not source:
            continue
        for order, (category, pattern) in enumerate(RULES):
            if re.search(pattern, source):
                specificity = 0.30 if category == "exercise" else 1.0
                score = weight * specificity
                if category not in scores or score > scores[category][0]:
                    scores[category] = (score, -order)
    if scores:
        return max(scores, key=lambda key: scores[key])

    source = str(scene.get("narration", "")).lower()
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
    if category == "anatomy":
        body = f"""
          <path class="anatomy-silhouette" d="M330 38 Q380 10 430 38 L448 92 Q500 102 535 145 L565 280 L535 295 L495 190 L485 320 L465 350 L295 350 L275 320 L265 190 L225 295 L195 280 L225 145 Q260 102 312 92Z"/>
          <path class="anatomy-neck" d="M350 34 L350 90 Q380 110 410 90 L410 34Z"/>
          <path class="anatomy-pec" d="M365 112 Q325 88 285 126 Q290 169 365 176Z M395 112 Q435 88 475 126 Q470 169 395 176Z"/>
          <path class="anatomy-delt" d="M285 110 Q245 105 235 150 Q245 180 280 174 L305 132Z M475 110 Q515 105 525 150 Q515 180 480 174 L455 132Z"/>
          <path class="anatomy-bicep" d="M246 166 Q220 190 232 240 Q250 257 267 230 L274 177Z M514 166 Q540 190 528 240 Q510 257 493 230 L486 177Z"/>
          <path class="anatomy-abs" d="M365 181 Q380 174 395 181 L397 315 Q380 328 363 315Z"/>
          <path class="anatomy-oblique" d="M350 184 Q326 190 315 225 L300 300 Q325 315 360 315Z M410 184 Q434 190 445 225 L460 300 Q435 315 400 315Z"/>
          <path class="anatomy-quad" d="M310 345 Q340 330 370 345 L365 420 L320 420Z M390 345 Q420 330 450 345 L440 420 L395 420Z"/>
          <path class="anatomy-midline" d="M380 178 V318"/>
          <g class="anatomy-labels"><path d="M295 140 L150 105 H82"/><text x="82" y="94">DELTOID</text><path d="M315 145 L180 190 H82"/><text x="82" y="180">PECTORAL</text><path d="M250 205 L150 255 H82"/><text x="82" y="245">BICEPS</text><path d="M365 245 L255 310 H82"/><text x="82" y="300">CORE</text><path d="M430 375 L535 400 H680"/><text x="680" y="390" text-anchor="end">QUADRICEPS</text></g>
          <text x="380" y="425" class="diagram-note">ANTERIOR VIEW • MAJOR SUPERFICIAL MUSCLE GROUPS</text>
          <text x="380" y="65" class="diagram-label">{a} • {b} • {c}</text>"""
    elif category == "recovery":
        body = f"""
          <g class="recovery-cycle">
            <circle class="recovery-clock" cx="190" cy="205" r="92"/>
            <path class="recovery-hand" d="M190 205 V145 M190 205 L238 230"/>
            <path class="recovery-wave" d="M330 205 H430"/>
            <g class="recovery-stars"><circle cx="505" cy="145" r="12"/><circle cx="565" cy="205" r="9"/><circle cx="505" cy="265" r="14"/></g>
            <path class="recovery-build" d="M610 285 V185 M585 210 L610 180 L635 210"/>
          </g>
          <text x="190" y="350" class="diagram-note">RESTORE</text>
          <text x="500" y="350" class="diagram-note">ADAPT</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "muscle":
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
    elif category == "protein":
        body = f"""
          <g class="protein-source">
            <path d="M95 165 Q145 105 205 165 L190 250 Q145 290 100 250Z"/>
            <circle cx="145" cy="185" r="18"/><circle cx="180" cy="215" r="13"/>
          </g>
          <path class="arrow protein-arrow" d="M235 210 H315"/>
          <g class="amino-chain"><circle cx="365" cy="165" r="17"/><circle cx="405" cy="205" r="17"/><circle cx="365" cy="245" r="17"/><circle cx="445" cy="165" r="17"/></g>
          <path class="arrow protein-arrow" d="M475 210 H535"/>
          <g class="protein-fiber"><path d="M555 150 Q610 125 665 150 M555 190 Q610 165 665 190 M555 230 Q610 205 665 230 M555 270 Q610 245 665 270"/></g>
          <text x="145" y="335" class="diagram-note">PROTEIN</text>
          <text x="405" y="335" class="diagram-note">AMINO ACIDS</text>
          <text x="610" y="335" class="diagram-note">MUSCLE</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
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
    elif category == "tracking":
        body = f"""
          <g class="progress-chart">
            <path class="chart-axis" d="M105 325 V105 H665"/>
            <path class="chart-grid" d="M105 270 H665 M105 215 H665 M105 160 H665"/>
            <path class="progress-line" d="M125 285 L245 255 L365 225 L485 165 L625 115"/>
            <g class="progress-points"><circle cx="125" cy="285" r="12"/><circle cx="245" cy="255" r="12"/><circle cx="365" cy="225" r="12"/><circle cx="485" cy="165" r="12"/><circle cx="625" cy="115" r="12"/></g>
            <path class="progress-arrow" d="M570 115 L625 115 L625 170"/>
          </g>
          <text x="380" y="385" class="diagram-note">RECORD • COMPARE • INCREASE GRADUALLY</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "creatine":
        body = f"""
          <g class="atp-cycle">
            <circle class="atp-node" cx="165" cy="205" r="92"/>
            <circle class="atp-core" cx="165" cy="205" r="48"/>
            <text x="165" y="213" class="atp-text">ATP</text>
            <path class="arrow" d="M275 205 H385"/>
            <circle class="adp-node" cx="480" cy="205" r="78"/>
            <text x="480" y="213" class="atp-text">ADP</text>
            <path class="recycle-arrow" d="M480 300 C440 390 220 390 165 305"/>
            <circle class="creatine-dot" cx="625" cy="135" r="18"/>
            <circle class="creatine-dot" cx="660" cy="205" r="13"/>
            <circle class="creatine-dot" cx="625" cy="275" r="18"/>
            <text x="635" y="345" class="diagram-note">PHOSPHOCREATINE DONATES A PHOSPHATE</text>
          </g>
          <text x="380" y="65" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
    elif category == "supplements":
        body = f"""
          <g class="supplement-bottle">
            <rect x="145" y="145" width="150" height="205" rx="24"/>
            <rect x="175" y="105" width="90" height="45" rx="9"/>
            <path d="M170 235 H270" class="bottle-label"/>
            <text x="220" y="265" class="bottle-text">DOSE</text>
          </g>
          <g class="capsules">
            <rect x="430" y="145" width="150" height="58" rx="29" transform="rotate(-25 505 174)"/>
            <path d="M493 142 L518 207" class="capsule-split"/>
            <rect x="455" y="255" width="130" height="52" rx="26" transform="rotate(18 520 281)"/>
          </g>
          <path class="arrow" d="M315 235 H405"/>
          <text x="380" y="365" class="diagram-note">EVIDENCE • DOSE • REALISTIC EXPECTATION</text>
          <text x="380" y="75" class="diagram-label">{a}  •  {b}  •  {c}</text>"""
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
    return f"""<svg class="science-svg science-{category}" viewBox="0 0 760 430" role="img" aria-label="{html.escape(CATEGORIES[category][0])}">
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
.science-anatomy .anatomy-silhouette{fill:rgba(191,133,113,.28);stroke:#efc4a9;stroke-width:4}
.science-anatomy .anatomy-neck{fill:#c58d78;stroke:#efc4a9;stroke-width:3}
.science-anatomy .anatomy-pec,.science-anatomy .anatomy-delt,.science-anatomy .anatomy-bicep,.science-anatomy .anatomy-abs,.science-anatomy .anatomy-oblique,.science-anatomy .anatomy-quad{stroke:#ffd0c3;stroke-width:3;animation:ff-anatomy-highlight 2.8s ease-in-out infinite alternate}
.science-anatomy .anatomy-pec{fill:#c64d62}.science-anatomy .anatomy-delt{fill:#e36d75}.science-anatomy .anatomy-bicep{fill:#bd465b}.science-anatomy .anatomy-abs{fill:#dc6671}.science-anatomy .anatomy-oblique{fill:#a83d55}.science-anatomy .anatomy-quad{fill:#c44b60}
.science-anatomy .anatomy-midline{stroke:rgba(255,224,215,.65);stroke-width:2;stroke-dasharray:5 5;fill:none}
.science-anatomy .anatomy-labels path{stroke:#72e6c2;stroke-width:2;fill:none}.science-anatomy .anatomy-labels text{fill:#f4f8ff;font-size:13px;font-weight:900;letter-spacing:1.5px}
.science-anatomy .anatomy-body{transform-origin:380px 220px;animation:ff-anatomy-breathe 3.4s ease-in-out infinite}
@keyframes ff-anatomy-breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.012)}}
@keyframes ff-anatomy-highlight{from{filter:brightness(.86)}to{filter:brightness(1.22) drop-shadow(0 0 10px rgba(255,110,120,.4))}}
.science-protein .protein-source path{fill:rgba(246,189,96,.18);stroke:#f6bd60;stroke-width:7}
.science-protein .protein-source circle{fill:#f6bd60;stroke:#fff;stroke-width:3}
.science-protein .amino-chain circle{fill:#65aaff;stroke:#eaf5ff;stroke-width:4;animation:protein-amino 1.8s ease-in-out infinite alternate}
.science-protein .amino-chain circle:nth-child(2){animation-delay:.2s}.science-protein .amino-chain circle:nth-child(3){animation-delay:.4s}.science-protein .amino-chain circle:nth-child(4){animation-delay:.6s}
.science-protein .protein-fiber path{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round;stroke-dasharray:20 8;animation:protein-fiber 2.2s linear infinite}
.science-protein .protein-arrow{stroke-dasharray:100;stroke-dashoffset:100;animation:protein-arrow 1s ease-out both}
@keyframes protein-amino{to{transform:translateY(-12px);filter:drop-shadow(0 0 10px #65aaff)}}
@keyframes protein-fiber{to{stroke-dashoffset:-56;opacity:.65}}@keyframes protein-arrow{to{stroke-dashoffset:0}}
.science-tracking .chart-axis,.science-tracking .chart-grid{fill:none;stroke:rgba(234,245,255,.3);stroke-width:4}
.science-tracking .progress-line{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:620;stroke-dashoffset:0;animation:tracking-draw 2.4s cubic-bezier(.16,1,.3,1) both}
.science-tracking .progress-arrow{fill:none;stroke:#f6bd60;stroke-width:8;stroke-linecap:round;stroke-linejoin:round;opacity:.95}
.science-tracking .progress-points circle{fill:#65aaff;stroke:#fff;stroke-width:4;animation:progress-point 2.2s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.science-tracking .progress-points circle:nth-child(2){animation-delay:.2s}
.science-tracking .progress-points circle:nth-child(3){animation-delay:.4s}
.science-tracking .progress-points circle:nth-child(4){animation-delay:.6s}
.science-tracking .progress-points circle:nth-child(5){animation-delay:.8s}
@keyframes tracking-draw{from{stroke-dashoffset:620}to{stroke-dashoffset:0}}
@keyframes progress-point{to{transform:scale(1.35);filter:drop-shadow(0 0 12px #72e6c2)}}
.science-panel{position:absolute;left:95px;right:95px;top:940px;height:460px;border:1px solid rgba(114,230,194,.36);border-radius:34px;overflow:hidden;background:linear-gradient(135deg,rgba(7,22,36,.91),rgba(15,42,62,.76));box-shadow:0 28px 90px rgba(0,0,0,.42),inset 0 1px rgba(255,255,255,.10);transform:perspective(1100px) rotateX(4deg);backdrop-filter:blur(10px)}
.science-panel:before{content:"";position:absolute;inset:-40%;background:radial-gradient(circle at 30% 40%,rgba(114,230,194,.16),transparent 35%),radial-gradient(circle at 75% 65%,rgba(101,170,255,.17),transparent 38%);animation:panel-drift 8s ease-in-out infinite alternate}
.science-kicker{position:absolute;top:28px;left:38px;color:#72e6c2;font-size:17px;letter-spacing:5px;font-weight:800}
.science-heading{position:absolute;top:67px;left:38px;color:#f4f8ff;font-size:25px;letter-spacing:3px;font-weight:900}
.science-svg{position:absolute;left:0;top:85px;width:100%;height:350px;overflow:visible}
.science-svg text{font-family:Arial,sans-serif}
.diagram-label{fill:#72e6c2;text-anchor:middle;font-size:16px;font-weight:900;letter-spacing:2px}
.diagram-note{fill:#eaf5ff;text-anchor:middle;font-size:14px;font-weight:800;letter-spacing:2px}
.science-recovery .recovery-clock{fill:rgba(101,170,255,.12);stroke:#65aaff;stroke-width:8}
.recovery-hand{stroke:#72e6c2;stroke-width:9;stroke-linecap:round;animation:ff-recovery-tick 4s linear infinite;transform-origin:190px 205px}
.recovery-wave{stroke:#f6bd60;stroke-width:9;stroke-dasharray:12 10;animation:flow 2s linear infinite}
.recovery-stars circle{fill:#72e6c2;animation:float 2s ease-in-out infinite alternate}
.recovery-build{fill:none;stroke:#72e6c2;stroke-width:9;stroke-linecap:round;stroke-linejoin:round;animation:ff-recovery-rise 2s ease-in-out infinite alternate}
@keyframes ff-recovery-tick{to{transform:rotate(35deg)}}@keyframes ff-recovery-rise{to{transform:translateY(-12px)}}
.fiber{fill:none;stroke:#72e6c2;stroke-width:17;stroke-linecap:round;filter:drop-shadow(0 0 8px rgba(114,230,194,.5));stroke-dasharray:24 8;animation:fiber-pulse 3s ease-in-out infinite alternate}
.fiber-two{stroke:#65aaff;animation-delay:.3s}.fiber-three{stroke:#a4f2df;animation-delay:.6s}.fiber-four{stroke:#65aaff;animation-delay:.9s}
.satellite circle{fill:#65aaff;stroke:#fff;stroke-width:3}.arrow{fill:none;stroke:#72e6c2;stroke-width:5;stroke-linecap:round;stroke-linejoin:round;marker-end:none;stroke-dasharray:12 10;animation:flow 2s linear infinite}
.plate{fill:rgba(255,255,255,.05);stroke:#eaf5ff;stroke-width:7}.plate-line{stroke:#eaf5ff;stroke-width:5}.nutrient{stroke:#07111d;stroke-width:3}.protein{fill:#72e6c2}.carbs{fill:#65aaff}.fats{fill:#f6bd60}.gut path{fill:none;stroke:#f6bd60;stroke-width:16;stroke-linecap:round;stroke-dasharray:5 9;animation:flow 3s linear infinite}.fuel-dots circle{fill:#72e6c2;filter:drop-shadow(0 0 9px #72e6c2);animation:float 2s ease-in-out infinite alternate}
.vessel{fill:none;stroke:#65aaff;stroke-width:25;stroke-linecap:round}.pulse{fill:none;stroke:#72e6c2;stroke-width:7;stroke-linejoin:round;stroke-dasharray:25 9;animation:flow 1.8s linear infinite}.heart-shape{fill:#e85d75;stroke:#ffb4c0;stroke-width:5;transform-origin:380px 210px;animation:heartbeat 1.2s ease-in-out infinite}.oxygen{fill:#72e6c2;filter:drop-shadow(0 0 8px #72e6c2);animation:float 2s infinite alternate}.oxygen-two{animation-delay:.5s}.oxygen-three{animation-delay:.8s}.oxygen-four{animation-delay:1.1s}
.balance-beam,.balance-stand,.balance-cable{fill:none;stroke:#eaf5ff;stroke-width:9;stroke-linecap:round}.balance-pan{fill:rgba(101,170,255,.2);stroke:#65aaff;stroke-width:5}.energy-in circle{fill:#f6bd60}.energy-out path{fill:#72e6c2;stroke:#72e6c2;stroke-width:3}
.drop{fill:rgba(101,170,255,.25);stroke:#65aaff;stroke-width:8;filter:drop-shadow(0 0 10px #65aaff)}.drop-shine{fill:none;stroke:#fff;stroke-width:8;stroke-linecap:round}.electrolytes circle{fill:#72e6c2;stroke:#eaf5ff;stroke-width:3;animation:float 2s ease-in-out infinite alternate}.electrolytes circle:nth-child(2){animation-delay:.5s}.electrolytes circle:nth-child(3){animation-delay:1s}.ion{fill:#07111d;text-anchor:middle;font-size:15px;font-weight:900}.balance-ring{fill:none;stroke:#65aaff;stroke-width:5;stroke-dasharray:10 12}
.bone{fill:#eaf5ff;stroke:#a8c6d8;stroke-width:7}.bone-two{fill:#d3e6f1}.joint{fill:rgba(114,230,194,.25);stroke:#72e6c2;stroke-width:8}.joint-core{fill:#65aaff;stroke:#fff;stroke-width:4}.lever{fill:none;stroke:#f6bd60;stroke-width:8;stroke-linecap:round}
.atp-node{fill:rgba(114,230,194,.16);stroke:#72e6c2;stroke-width:7;filter:drop-shadow(0 0 12px rgba(114,230,194,.4))}.atp-core{fill:#65aaff;stroke:#eaf5ff;stroke-width:4}.adp-node{fill:rgba(101,170,255,.16);stroke:#65aaff;stroke-width:7}.atp-text{fill:#f4f8ff;text-anchor:middle;font-size:34px;font-weight:900}.recycle-arrow{fill:none;stroke:#f6bd60;stroke-width:7;stroke-linecap:round;stroke-dasharray:14 10;animation:flow 2.4s linear infinite}.creatine-dot{fill:#f6bd60;stroke:#fff;stroke-width:3;animation:float 1.8s ease-in-out infinite alternate}.supplement-bottle rect{fill:rgba(101,170,255,.16);stroke:#72e6c2;stroke-width:7}.bottle-label{stroke:#f6bd60;stroke-width:7}.bottle-text{fill:#eaf5ff;text-anchor:middle;font-size:22px;font-weight:900}.capsules rect{fill:#f6bd60;stroke:#fff;stroke-width:5}.capsule-split{stroke:#07111d;stroke-width:5}
.signal-wave{fill:none;stroke:#f6bd60;stroke-width:8;stroke-linecap:round;stroke-dasharray:18 12;animation:flow 2s linear infinite}.signal-dots circle{fill:#f6bd60;filter:drop-shadow(0 0 8px #f6bd60)}.cell{fill:rgba(101,170,255,.08);stroke:#65aaff;stroke-width:5;stroke-dasharray:9 10}.receptor{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round}.response{fill:none;stroke:#72e6c2;stroke-width:8;stroke-linecap:round;stroke-linejoin:round;animation:flow 2s linear infinite}
.process-box rect{fill:rgba(101,170,255,.12);stroke:#65aaff;stroke-width:4}.process-pulse{fill:#72e6c2;filter:drop-shadow(0 0 10px #72e6c2);animation:node-pulse 1.8s ease-in-out infinite}.pulse-two{animation-delay:.5s}.pulse-three{animation-delay:1s}
@keyframes panel-drift{to{transform:translate3d(5%,3%,0) rotate(8deg)}}@keyframes flow{to{stroke-dashoffset:-64}}@keyframes fiber-pulse{to{stroke-dashoffset:-64;opacity:.65}}@keyframes float{to{transform:translateY(-13px);opacity:.65}}@keyframes heartbeat{50%{transform:scale(1.06)}}@keyframes node-pulse{50%{opacity:.45;transform:scale(.8)}}
"""
