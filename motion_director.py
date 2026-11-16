"""Deterministic scene-level motion direction adapted for FitFuel.

Keeps HyperFrames as the renderer; this module supplies a lightweight,
frame-timeline-friendly motion language inspired by the MIT-licensed
iart-ai motion skills (short-form pacing, shot hierarchy, easing and
deliver/verify discipline). No new runtime dependency is required.
"""


def plan_scene_motion(scene, index, duration, category, is_last=False):
    """Return a stable motion role for one scene."""
    if index == 1:
        role = "hook"
    elif is_last:
        role = "payoff"
    else:
        role = "support"

    duration = max(0.0, float(duration))
    pace = "long" if duration >= 4.2 else "standard"
    # Keep the science diagram as the focal point; use category to create
    # distinct visual rhythm without changing the factual visual metaphor.
    focus = "diagram" if category != "general" else "headline"
    return {
        "role": role,
        "pace": pace,
        "focus": focus,
        "class_name": f"motion-{role} motion-{pace} focus-{focus}",
        "style": f"{role}:{pace}:{focus}",
    }


def motion_css():
    """CSS motion language: eased entrances, restrained depth and beat resets."""
    return """
/* FitFuel motion direction: one focal point, restrained layered movement. */
.motion-hook .title {
  animation: ff-hook-lock 520ms cubic-bezier(.16,1,.3,1) both;
  transform-origin: 50% 50%;
}
.motion-payoff .science-panel {
  border-color: rgba(114,230,194,.72);
  box-shadow: 0 30px 100px rgba(0,0,0,.48), 0 0 34px rgba(114,230,194,.16),
              inset 0 1px rgba(255,255,255,.14);
}
.motion-support .science-panel,
.motion-payoff .science-panel {
  animation: ff-panel-enter 620ms cubic-bezier(.16,1,.3,1) both,
             ff-panel-breathe 3.8s 620ms ease-in-out infinite alternate;
  transform-origin: 50% 50%;
}
.motion-hook .science-panel {
  animation: ff-panel-enter 480ms cubic-bezier(.16,1,.3,1) both,
             ff-panel-breathe 3.4s 480ms ease-in-out infinite alternate;
}
.motion-long .science-heading { animation: ff-heading-emphasis 3.2s 1s ease-in-out infinite; }
.motion-long .diagram-note { animation: ff-note-pulse 3.2s 1.4s ease-in-out infinite; }
.motion-scene .science-kicker { animation: ff-kicker-enter 420ms 80ms cubic-bezier(.16,1,.3,1) both; }
.motion-scene .science-heading { animation: ff-heading-enter 480ms 140ms cubic-bezier(.16,1,.3,1) both; }
.motion-scene .science-svg { animation: ff-diagram-enter 560ms 200ms cubic-bezier(.16,1,.3,1) both; }
.focus-diagram .science-panel { --ff-focus-scale: 1.012; }
.focus-headline .title { text-shadow: 0 5px 30px #000, 0 0 22px rgba(114,230,194,.20); }
@keyframes ff-hook-lock {
  from { opacity: .82; transform: scale(.965); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes ff-panel-enter {
  from { opacity: .72; transform: perspective(1100px) rotateX(7deg) translateY(24px) scale(.975); }
  to { opacity: 1; transform: perspective(1100px) rotateX(4deg) translateY(0) scale(1); }
}
@keyframes ff-panel-breathe {
  from { filter: brightness(1); }
  to { filter: brightness(1.055); }
}
@keyframes ff-kicker-enter { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes ff-heading-enter { from { opacity: 0; transform: translateY(16px) scale(.98); } to { opacity: 1; transform: none; } }
@keyframes ff-diagram-enter { from { opacity: 0; transform: translateY(18px) scale(.985); } to { opacity: 1; transform: none; } }
@keyframes ff-heading-emphasis { 0%,100% { opacity: 1; } 50% { opacity: .82; } }
@keyframes ff-note-pulse { 0%,100% { opacity: 1; } 50% { opacity: .72; } }
"""


__all__ = ["plan_scene_motion", "motion_css"]
