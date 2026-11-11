"""Free-only Text-to-Video preflight for FitFuel.

This module converts Gemini narration scenes into provider-ready prompts.
It deliberately does NOT call Kling, Runway, or Wan: their documented API
routes are usage-billed and do not expose a verifiable free-credit-only
generation path. Never infer free API credit from the existence of an API key.
"""
import json
import os
from pathlib import Path

PLAN_PATH = Path("output/t2v_prompt_plan.json")
STYLE = (
    "Consistent premium 3D anatomical fitness-explainer visual identity; "
    "realistic human anatomy with clean educational medical visualization; "
    "cinematic studio lighting, detailed materials, controlled camera motion, "
    "vertical 9:16 composition. Show only the described action or subject. "
    "No text, captions, labels, logos, watermarks, split screens, or UI."
)

# Publicly documented status as of 2026-11-11. This is intentionally
# conservative: web-app trial credits are not assumed to cover API usage.
PROVIDERS = {
    "kling": {
        "api": "Kling Developer API",
        "status": "paid_api",
        "reason": "Official API documentation requires prepaid video resource packages/balance.",
    },
    "runway": {
        "api": "Runway Dev API",
        "status": "paid_api",
        "reason": "Runway Dev generations consume purchased API credits; app Free-plan credits are separate.",
    },
    "wan": {
        "api": "Wan 2.2 via Replicate API",
        "status": "paid_api",
        "reason": "The hosted Replicate model is billed per generated second; a token is not a free-credit grant.",
    },
}


def scene_prompt(scene, index):
    narration = " ".join(str(scene.get("narration", "")).split())
    visual = " ".join(str(
        scene.get("visual_title") or scene.get("keyword") or ""
    ).split())
    if not narration:
        raise ValueError(f"Scene {index} has no narration.")
    parts = [
        STYLE,
        f"Scene {index}.",
        f"Visual subject/action: {visual}." if visual else "",
        f"Explain this spoken idea visually: {narration}",
        "Use one coherent continuous shot with subtle physically plausible motion.",
        "Keep anatomy and exercise technique accurate; avoid unrelated cutaways.",
    ]
    return " ".join(part for part in parts if part)


def build_plan(script, audio):
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("output/script.json must contain a non-empty scenes list.")
    if not isinstance(audio, list) or len(audio) != len(scenes):
        raise ValueError("Audio metadata must contain one entry per script scene.")

    planned = []
    for index, (scene, audio_item) in enumerate(zip(scenes, audio), 1):
        try:
            seconds = float(audio_item.get("seconds", 0))
        except (TypeError, ValueError):
            seconds = 0
        if seconds <= 0:
            raise ValueError(f"Scene {index} has an invalid audio duration.")
        planned.append({
            "scene": index,
            "narration": " ".join(str(scene.get("narration", "")).split()),
            "audio_seconds": round(seconds, 3),
            "target_generation_seconds": min(5, max(3, round(seconds))),
            "aspect_ratio": "9:16",
            "prompt": scene_prompt(scene, index),
            "generation_status": "blocked_until_verified_free_api_credits",
        })

    return {
        "version": 1,
        "mode": "free_only_preflight",
        "provider_policy": "No provider API requests are made by this preflight.",
        "providers": PROVIDERS,
        "scenes": planned,
    }


def main():
    with open("output/script.json", encoding="utf-8") as handle:
        script = json.load(handle)
    with open("output/audio_info.json", encoding="utf-8") as handle:
        audio = json.load(handle)

    plan = build_plan(script, audio)
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(plan['scenes'])} provider-ready scene prompts to {PLAN_PATH}")
    print("Free-only guard: Kling, Runway Dev, and hosted Wan API calls are blocked.")
    print("The normal stock-footage pipeline remains the active visual fallback.")


if __name__ == "__main__":
    main()
