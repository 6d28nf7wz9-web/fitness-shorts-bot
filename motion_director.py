"""Scene-level art direction inspired by iart-ai short-form and motion-design skills.

Deterministic decisions keep CI renders reproducible while varying composition,
camera treatment, pacing, and visual hierarchy from scene to scene.
"""


def plan_scene_motion(scene, index, duration, category, is_last=False):
    """Choose a repeatable shot grammar for the scene."""
    if index == 1:
        role = "hook"
    elif is_last:
        role = "payoff"
    else:
        role = "support"

    duration = max(0.0, float(duration))
    pace = "long" if duration >= 4.2 else "standard"
    focus = "diagram" if category != "general" else "headline"
    # Alternate the panel's visual weight to avoid a stack of identical cards.
    layout = ("right" if index % 3 == 2 else "left") if category != "general" else "center"
    camera = ("push" if index % 3 == 1 else "drift" if index % 3 == 2 else "pull")
    emphasis = "headline" if index % 2 else "diagram"
    transitions = ("wipe", "slide-up", "zoom", "reveal")
    transition = "hook" if role == "hook" else "payoff" if role == "payoff" else transitions[(index - 2) % len(transitions)]
    # Cycle through distinct, deterministic entrances for typography and diagrams.
    motion_variant = ("rise", "scale", "slide", "focus", "snap")[(index - 1) % 5]
    return {
        "role": role,
        "transition": transition,
        "pace": pace,
        "focus": focus,
        "layout": layout,
        "camera": camera,
        "emphasis": emphasis,
        "variant": motion_variant,
        "class_name": f"motion-{role} motion-{pace} focus-{focus} layout-{layout} camera-{camera} emphasis-{emphasis} transition-{transition} variant-{motion_variant}",
        "style": f"{role}:{pace}:{focus}:{layout}:{camera}:{emphasis}:{transition}",
    }


def motion_css():
    """CSS motion system: eased entrances, camera drift, and varied shot layout."""
    return """
.motion-hook .title {
  animation: ff-hook-lock 650ms cubic-bezier(.16,1,.3,1) both;
  transform-origin: 50% 50%;
}
.motion-hook .sub { animation: ff-sub-reveal 700ms 160ms cubic-bezier(.16,1,.3,1) both; }
.motion-payoff .science-panel {
  border-color: rgba(114,230,194,.78);
  box-shadow: 0 30px 100px rgba(0,0,0,.48), 0 0 38px rgba(114,230,194,.2),
              inset 0 1px rgba(255,255,255,.14);
}
.motion-support .science-panel,
.motion-payoff .science-panel {
  animation: ff-panel-enter 620ms cubic-bezier(.16,1,.3,1) both,
             ff-panel-breathe 3.8s 620ms ease-in-out infinite alternate;
  transform-origin: 50% 50%;
}
.motion-hook .science-panel {
  animation: ff-panel-enter 520ms cubic-bezier(.16,1,.3,1) both,
             ff-panel-breathe 3.4s 520ms ease-in-out infinite alternate;
}
.motion-long .science-heading { animation: ff-heading-emphasis 3.2s 1s ease-in-out infinite; }
.motion-long .diagram-note { animation: ff-note-pulse 3.2s 1.4s ease-in-out infinite; }
.motion-scene .science-kicker { animation: ff-kicker-enter 420ms 80ms cubic-bezier(.16,1,.3,1) both; }
.motion-scene .science-heading { animation: ff-heading-enter 480ms 140ms cubic-bezier(.16,1,.3,1) both; }
.motion-scene .science-svg { animation: ff-diagram-enter 560ms 200ms cubic-bezier(.16,1,.3,1) both; }
.motion-hook { animation: ff-transition-hook 560ms cubic-bezier(.16,1,.3,1) both; }
.motion-support { animation: ff-transition-support 480ms cubic-bezier(.22,1,.36,1) both; }
.motion-payoff { animation: ff-transition-payoff 620ms cubic-bezier(.16,1,.3,1) both; }
.transition-slide-up { animation: ff-transition-slide-up 520ms cubic-bezier(.16,1,.3,1) both; }
.transition-wipe { animation: ff-transition-wipe 560ms cubic-bezier(.16,1,.3,1) both; }
.transition-zoom { animation: ff-transition-zoom 520ms cubic-bezier(.16,1,.3,1) both; }
.transition-reveal { animation: ff-transition-reveal 540ms cubic-bezier(.16,1,.3,1) both; }
@keyframes ff-transition-hook { from { opacity:0; clip-path:inset(8% 0 8% 0); transform:scale(1.035); } to { opacity:1; clip-path:inset(0); transform:scale(1); } }
@keyframes ff-transition-support { from { opacity:0; transform:translateX(34px); filter:blur(4px); } to { opacity:1; transform:translateX(0); filter:blur(0); } }
@keyframes ff-transition-payoff { from { opacity:0; clip-path:circle(12% at 50% 50%); transform:scale(.97); } to { opacity:1; clip-path:circle(100% at 50% 50%); transform:scale(1); } }
@keyframes ff-transition-slide-up { from { opacity:0; transform:translateY(54px); filter:blur(5px); } to { opacity:1; transform:translateY(0); filter:blur(0); } }
@keyframes ff-transition-wipe { from { opacity:1; clip-path:inset(0 100% 0 0); } to { opacity:1; clip-path:inset(0); } }
@keyframes ff-transition-zoom { from { opacity:0; transform:scale(1.09); filter:blur(7px); } to { opacity:1; transform:scale(1); filter:blur(0); } }
@keyframes ff-transition-reveal { from { opacity:0; clip-path:inset(50% 0); } to { opacity:1; clip-path:inset(0); } }
.layout-left .science-panel { left: 70px; right: 125px; }
.layout-right .science-panel { left: 125px; right: 70px; }
.layout-center .science-panel { left: 95px; right: 95px; }
.layout-right .science-heading { letter-spacing: 4px; }
.camera-push .scene-footage { animation: ff-camera-push 7s ease-in-out both; }
.camera-drift .scene-footage { animation: ff-camera-drift 7s ease-in-out both; }
.camera-pull .scene-footage { animation: ff-camera-pull 7s ease-in-out both; }
.emphasis-headline .title { text-shadow: 0 5px 30px #000, 0 0 26px rgba(114,230,194,.28); }
.emphasis-diagram .science-panel { filter: drop-shadow(0 0 22px rgba(101,170,255,.16)); }
.focus-diagram .science-panel { --ff-focus-scale: 1.012; }
.focus-headline .title { text-shadow: 0 5px 30px #000, 0 0 22px rgba(114,230,194,.20); }
@keyframes ff-hook-lock {
  from { opacity: .72; transform: scale(.92) translateY(24px); filter: blur(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); filter: blur(0); }
}
@keyframes ff-sub-reveal { from { opacity: 0; transform: translateY(22px); } to { opacity: 1; transform: none; } }
@keyframes ff-panel-enter {
  from { opacity: .55; transform: perspective(1100px) rotateX(9deg) translateY(34px) scale(.94); }
  to { opacity: 1; transform: perspective(1100px) rotateX(4deg) translateY(0) scale(1); }
}
@keyframes ff-panel-breathe {
  from { filter: brightness(1); }
  to { filter: brightness(1.075); }
}
@keyframes ff-kicker-enter { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes ff-heading-enter { from { opacity: 0; transform: translateY(20px) scale(.96); letter-spacing: 7px; } to { opacity: 1; transform: none; } }
@keyframes ff-diagram-enter { from { opacity: 0; transform: translateY(24px) scale(.96); } to { opacity: 1; transform: none; } }
@keyframes ff-heading-emphasis { 0%,100% { opacity: 1; } 50% { opacity: .82; } }
@keyframes ff-note-pulse { 0%,100% { opacity: 1; } 50% { opacity: .72; } }
@keyframes ff-camera-drift { from { transform: scale(1.06) translate3d(-1%,0,0); } to { transform: scale(1.12) translate3d(1%,0,0); } }
@keyframes ff-camera-push { from { transform: scale(1.02); } to { transform: scale(1.17); } }
@keyframes ff-camera-pull { from { transform: scale(1.17); } to { transform: scale(1.04); } }
.variant-rise .title,.variant-rise .science-heading { animation: ff-variant-rise 560ms cubic-bezier(.16,1,.3,1) both; }
.variant-scale .title,.variant-scale .science-svg { animation: ff-variant-scale 620ms cubic-bezier(.16,1,.3,1) both; }
.variant-slide .title,.variant-slide .science-panel { animation: ff-variant-slide 600ms cubic-bezier(.16,1,.3,1) both; }
.variant-focus .title,.variant-focus .science-svg { animation: ff-variant-focus 680ms cubic-bezier(.16,1,.3,1) both; }
.variant-snap .title,.variant-snap .science-panel { animation: ff-variant-snap 420ms cubic-bezier(.2,1.4,.4,1) both; }
@keyframes ff-variant-rise { from{opacity:0;transform:translateY(38px)} to{opacity:1;transform:translateY(0)} }
@keyframes ff-variant-scale { from{opacity:0;transform:scale(.82)} to{opacity:1;transform:scale(1)} }
@keyframes ff-variant-slide { from{opacity:0;transform:translateX(42px)} to{opacity:1;transform:translateX(0)} }
@keyframes ff-variant-focus { from{opacity:0;filter:blur(9px);transform:scale(1.04)} to{opacity:1;filter:blur(0);transform:scale(1)} }
@keyframes ff-variant-snap { from{opacity:0;transform:scale(.9) translateY(16px)} 75%{transform:scale(1.025)} to{opacity:1;transform:scale(1)} }
"""


__all__ = ["plan_scene_motion", "motion_css"]
