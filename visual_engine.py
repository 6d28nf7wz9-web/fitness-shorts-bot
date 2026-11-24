"""Category-specific scientific visuals for FitFuel Shorts."""
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

RULES = [
    ("muscle", r"muscle|hypertrophy|growth|recovery|strength|progressive overload"),
    ("hydration", r"water|hydration|dehydrat|electrolyte"),
    ("heart", r"heart|blood|circulation|cardio|oxygen"),
    ("hormones", r"hormone|insulin|cortisol|testosterone|estrogen|ghrelin|leptin"),
    ("fat_loss", r"fat loss|fat gain|calorie|energy balance|burn fat|weight loss"),
    ("nutrition", r"protein|food|meal|eat|nutrition|digest|fiber|carb|fat intake"),
    ("exercise", r"exercise|squat|deadlift|curl|press|rep|set|workout|training"),
]

ALIASES = {
    "muscle_anatomy": "muscle", "protein_synthesis": "muscle",
    "digestion_fiber": "nutrition", "food": "nutrition",
    "exercise_biomechanics": "exercise", "movement": "exercise",
    "energy": "fat_loss", "cardiovascular": "heart", "hormone": "hormones",
}


def classify_scene(scene):
    """Prefer explicit scene direction, then infer from narration and labels."""
    explicit = str(scene.get("visual_type") or scene.get("visual_category") or "").lower().strip()
    explicit = ALIASES.get(explicit, explicit)
    if explicit in CATEGORIES and explicit != "general":
        return explicit
    text = " ".join(str(scene.get(k, "")) for k in
                    ("narration", "keyword", "visual_title", "visual_subtitle")).lower()
    for category, pattern in RULES:
        if re.search(pattern, text):
            return category
    return "general"


def _svg(category, labels):
    """Build a genuinely different visual silhouette for each science category."""
    a, b, c = [html.escape(str(x), quote=True) for x in labels]
    head = '<svg class="science-svg" viewBox="0 0 760 430" role="img" aria-label="{}">'.format(
        html.escape(CATEGORIES[category][0], quote=True)
    )
    shapes = {
        "muscle": f'<path d="M125 90 Q380 20 635 90 L635 340 Q380 410 125 340Z" class="organ-shape"/><path d="M165 112 Q145 215 165 318 M220 105 Q200 215 220 325 M275 100 Q255 215 275 330 M330 95 Q310 215 330 335 M385 95 Q365 215 385 335 M440 100 Q420 215 440 330 M495 105 Q475 215 495 325 M550 112 Q530 215 550 318 M605 120 Q585 215 605 310" class="fiber-lines"/><path d="M180 215 H580" class="signal-line"/><text x="380" y="65" class="svg-label">{a}</text><text x="380" y="390" class="svg-label">{b} → {c}</text>',
        "nutrition": f'<circle cx="380" cy="220" r="155" class="plate-outer"/><circle cx="380" cy="220" r="130" class="plate-inner"/><path d="M380 90 A130 130 0 0 0 250 220 L380 220Z" class="food-green"/><path d="M380 90 A130 130 0 0 1 510 220 L380 220Z" class="food-orange"/><path d="M250 220 A130 130 0 0 0 510 220Z" class="food-red"/><circle cx="380" cy="220" r="48" class="plate-center"/><text x="380" y="38" class="svg-label">{a}</text><text x="380" y="410" class="svg-label">{b} • {c}</text>',
        "heart": f'<path d="M380 345 C330 300 150 190 220 112 C275 50 350 100 380 150 C410 100 485 50 540 112 C610 190 430 300 380 345Z" class="heart-shape"/><path d="M85 225 H205 L245 225 L275 155 L320 290 L360 205 L390 225 H675" class="ecg-line"/><text x="380" y="55" class="svg-label">{a}</text><text x="380" y="395" class="svg-label">{b} → {c}</text>',
        "fat_loss": f'<path d="M380 90 V320 M235 145 H525 M270 145 L215 280 M490 145 L545 280" class="balance-line"/><path d="M160 280 Q215 345 270 280Z M490 280 Q545 345 600 280Z" class="balance-pan"/><path d="M300 340 H460 L430 375 H330Z" class="balance-base"/><circle cx="380" cy="145" r="25" class="balance-pivot"/><text x="215" y="255" class="svg-label">{a}</text><text x="545" y="255" class="svg-label">{c}</text><text x="380" y="415" class="svg-label">{b}</text>',
        "hydration": f'<path d="M380 55 C330 135 220 235 260 315 C300 405 460 405 500 315 C540 235 430 135 380 55Z" class="water-drop"/><path d="M310 280 Q380 245 450 280" class="water-wave"/><circle cx="340" cy="215" r="9" class="bubble"/><circle cx="410" cy="175" r="13" class="bubble"/><circle cx="430" cy="320" r="7" class="bubble"/><text x="380" y="105" class="svg-label">{a}</text><text x="380" y="365" class="svg-label">{b} • {c}</text>',
        "exercise": f'<circle cx="380" cy="90" r="32" class="joint"/><path d="M380 125 L380 235 L285 320 M380 235 L475 320 M380 160 L275 220 M380 160 L485 220" class="limb-line"/><circle cx="380" cy="235" r="17" class="joint"/><circle cx="285" cy="320" r="14" class="joint"/><circle cx="475" cy="320" r="14" class="joint"/><path d="M235 335 Q380 390 525 335" class="motion-arc"/><text x="380" y="42" class="svg-label">{a}</text><text x="380" y="410" class="svg-label">{b} • {c}</text>',
        "hormones": f'<path d="M190 210 L300 115 L440 150 L565 245 L440 330 L300 305Z" class="molecule-bonds"/><circle cx="190" cy="210" r="34" class="molecule-node"/><circle cx="300" cy="115" r="28" class="molecule-node"/><circle cx="440" cy="150" r="40" class="molecule-node"/><circle cx="565" cy="245" r="32" class="molecule-node"/><circle cx="440" cy="330" r="26" class="molecule-node"/><circle cx="300" cy="305" r="36" class="molecule-node"/><text x="190" y="216" class="svg-small">{a}</text><text x="440" y="156" class="svg-small">{b}</text><text x="380" y="405" class="svg-label">{c}</text>',
        "general": f'<path d="M120 215 H640" class="timeline-line"/><circle cx="150" cy="215" r="55" class="timeline-node"/><circle cx="380" cy="215" r="72" class="timeline-node main"/><circle cx="610" cy="215" r="55" class="timeline-node"/><path d="M350 215 l20 20 42 -48" class="timeline-check"/><text x="150" y="300" class="svg-label">{a}</text><text x="380" y="325" class="svg-label">{b}</text><text x="610" y="300" class="svg-label">{c}</text>',
    }
    return head + shapes[category] + "</svg>"


def build_visual_panel(scene, index=1):
    category = classify_scene(scene)
    title, labels = CATEGORIES[category]
    style = str(scene.get("presentation_style") or "diagram").lower()
    motion = str(scene.get("motion_cue") or "draw_on").lower()
    role = str(scene.get("scene_role") or "explain").lower()
    allowed_styles = {"hook", "payoff", "diagram", "stat_card", "comparison", "timeline", "presenter_focus", "broll_focus"}
    if style not in allowed_styles:
        style = "diagram"
    panel = (
        f'<div class="science-panel panel-{category} presentation-{style} role-{role}" '
        f'data-scene="{int(index)}" data-layout="{category}" data-motion="{html.escape(motion, quote=True)}">'
        f'<div class="science-kicker">FITFUEL • SCIENCE VISUAL</div>'
        f'<div class="science-heading">{html.escape(title)}</div>{_svg(category, labels)}</div>'
    )
    return category, panel


def visual_css():
    """Shared frame styling plus distinct silhouettes, palettes and motion."""
    return """
.science-panel{position:absolute;left:72px;right:72px;top:1000px;height:540px;border-radius:28px;overflow:hidden;background:rgba(5,13,23,.78);border:1px solid rgba(255,255,255,.18);box-shadow:0 24px 70px rgba(0,0,0,.38)}
.science-panel:before{content:"";position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,var(--glow),transparent 68%);opacity:.38;animation:visual-breathe 5s ease-in-out infinite alternate}
.science-kicker{position:absolute;top:24px;left:32px;color:var(--accent);font-size:16px;letter-spacing:4px;font-weight:800}
.science-heading{position:absolute;top:58px;left:32px;color:#fff;font-size:25px;letter-spacing:2px;font-weight:900}
.science-svg{position:absolute;left:3%;top:95px;width:94%;height:420px;overflow:visible}
.science-svg text{text-anchor:middle;font-family:Arial,sans-serif;font-weight:900;letter-spacing:2px}
.svg-label{fill:#fff;font-size:19px}.svg-small{fill:#07111d;font-size:11px}
.panel-muscle{--accent:#ffb15e;--glow:#ff7b3d;border-radius:48% 18% 42% 18%}
.panel-muscle .organ-shape{fill:rgba(255,123,61,.12);stroke:#ffb15e;stroke-width:5}.panel-muscle .fiber-lines{fill:none;stroke:#ff9c62;stroke-width:13;stroke-linecap:round;stroke-dasharray:8 12;animation:fiber-pulse 2.8s ease-in-out infinite alternate}.panel-muscle .signal-line{stroke:#ffe0a8;stroke-width:3;stroke-dasharray:10 10;animation:signal-flow 1.5s linear infinite}
.panel-nutrition{--accent:#9ee28c;--glow:#8dcf73;border-radius:42px}
.panel-nutrition .plate-outer{fill:#f5f1e7;stroke:#fff;stroke-width:12}.panel-nutrition .plate-inner{fill:#1c2b35;stroke:#b7c7c1;stroke-width:4}.panel-nutrition .food-green{fill:#75bd72}.panel-nutrition .food-orange{fill:#e8ad5b}.panel-nutrition .food-red{fill:#d96e68}.panel-nutrition .plate-center{fill:#f4e8ce;stroke:#fff;stroke-width:4}
.panel-heart{--accent:#ff8585;--glow:#e84c64;border-radius:120px 24px 120px 24px}.panel-heart .heart-shape{fill:rgba(220,50,75,.24);stroke:#ff8585;stroke-width:7}.panel-heart .ecg-line{fill:none;stroke:#fff;stroke-width:7;stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:18 10;animation:signal-flow 1.7s linear infinite}
.panel-fat_loss{--accent:#f4d16e;--glow:#b18a35;border-radius:24px 90px 24px 90px}.panel-fat_loss .balance-line{stroke:#f4d16e;stroke-width:10;stroke-linecap:round}.panel-fat_loss .balance-pan{fill:rgba(244,209,110,.2);stroke:#f4d16e;stroke-width:5}.panel-fat_loss .balance-base{fill:#f4d16e}.panel-fat_loss .balance-pivot{fill:#fff;stroke:#f4d16e;stroke-width:5}
.panel-hydration{--accent:#79d9ff;--glow:#168ed1;border-radius:90px 90px 28px 28px}.panel-hydration .water-drop{fill:rgba(35,161,220,.28);stroke:#79d9ff;stroke-width:8}.panel-hydration .water-wave{fill:none;stroke:#fff;stroke-width:6;stroke-linecap:round;animation:water-wave 2s ease-in-out infinite alternate}.panel-hydration .bubble{fill:#d7f7ff;animation:bubble-rise 2.6s ease-in-out infinite alternate}
.panel-exercise{--accent:#d4a5ff;--glow:#8051bd;border-radius:28px 28px 100px 28px}.panel-exercise .limb-line{fill:none;stroke:#d4a5ff;stroke-width:18;stroke-linecap:round;stroke-linejoin:round}.panel-exercise .joint{fill:#fff;stroke:#d4a5ff;stroke-width:6}.panel-exercise .motion-arc{fill:none;stroke:#f0c8ff;stroke-width:4;stroke-dasharray:12 10;animation:signal-flow 2s linear infinite}
.panel-hormones{--accent:#a8b9ff;--glow:#586bdb;border-radius:55px 55px 20px 20px}.panel-hormones .molecule-bonds{fill:none;stroke:#a8b9ff;stroke-width:7;stroke-dasharray:10 8;animation:signal-flow 3s linear infinite}.panel-hormones .molecule-node{fill:#d9e0ff;stroke:#697ee8;stroke-width:5;animation:visual-breathe 2.5s ease-in-out infinite alternate}
.panel-general{--accent:#72e6c2;--glow:#3e9fba;border-radius:34px}.panel-general .timeline-line{stroke:#72e6c2;stroke-width:5;stroke-dasharray:12 12}.panel-general .timeline-node{fill:#10283a;stroke:#72e6c2;stroke-width:5}.panel-general .timeline-node.main{fill:#23506a;stroke:#fff}.panel-general .timeline-check{fill:none;stroke:#72e6c2;stroke-width:12;stroke-linecap:round;stroke-linejoin:round}
@keyframes orbit-dash{to{stroke-dashoffset:-56}}@keyframes visual-breathe{to{transform:scale(1.025);opacity:.7}}@keyframes signal-flow{to{stroke-dashoffset:-56}}@keyframes fiber-pulse{to{stroke-dashoffset:40;opacity:.55}}@keyframes water-wave{to{transform:translateY(-10px)}}@keyframes bubble-rise{to{transform:translateY(-28px);opacity:.35}}
"""
