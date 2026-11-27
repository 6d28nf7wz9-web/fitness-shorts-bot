"""FitFuel production director: deterministic manifest and pre-render contracts.

This module coordinates existing generators/renderers; it does not publish videos,
call paid providers, or replace the existing HyperFrames renderer.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

OUTPUT = Path(os.getenv("OUTPUT_DIR", "output"))
MANIFEST = OUTPUT / "production_manifest.json"
REPORT = OUTPUT / "production_review.json"

VISUAL_MODES = {"stock", "science", "presenter", "motion_graphic", "hybrid"}


def _words(value: Any) -> list[str]:
    return re.findall(r"[a-z0-9']+", str(value or "").lower())


def _visual_mode(scene: dict) -> str:
    explicit = str(scene.get("visual_mode") or "").strip().lower()
    if explicit in VISUAL_MODES:
        return explicit
    text = " ".join(str(scene.get(k, "")) for k in
                    ("narration", "visual_title", "visual_subtitle", "keyword")).lower()
    if any(x in text for x in ("study shows", "percentage", "percent", "compared with", "versus", " vs ")):
        return "hybrid"
    if any(x in text for x in ("squat", "deadlift", "curl", "press", "exercise", "movement", "rep")):
        return "stock"
    if any(x in text for x in ("muscle", "protein", "hormone", "heart", "blood", "digestion",
                               "electrolyte", "metabolism", "calorie", "hydration")):
        return "science"
    return "hybrid"


def build_manifest(script: dict, audio: list[dict], clips: list[dict] | None = None) -> dict:
    """Build an auditable scene-by-scene production plan with explicit visual intent."""
    scenes = script.get("scenes") or []
    if not scenes:
        raise ValueError("script has no scenes")
    if len(audio) != len(scenes):
        raise ValueError(f"scene/audio mismatch: {len(scenes)} scenes, {len(audio)} audio entries")
    if clips is not None and len(clips) != len(scenes):
        raise ValueError(f"scene/clip mismatch: {len(scenes)} scenes, {len(clips)} clip entries")

    planned = []
    cursor = 0.0
    for index, scene in enumerate(scenes):
        narration = str(scene.get("narration") or "").strip()
        seconds = float(audio[index].get("seconds") or 0)
        if not narration:
            raise ValueError(f"scene {index + 1} has empty narration")
        if seconds <= 0:
            raise ValueError(f"scene {index + 1} has invalid audio duration")
        keywords = [x.strip() for x in str(scene.get("keyword") or "").split("|") if x.strip()]
        if not keywords:
            raise ValueError(f"scene {index + 1} has no authored visual search keywords")
        planned.append({
            "scene": index + 1,
            "start": round(cursor, 3),
            "duration": round(seconds, 3),
            "end": round(cursor + seconds, 3),
            "narration": narration,
            "visual_mode": _visual_mode(scene),
            "visual_title": str(scene.get("visual_title") or ""),
            "search_keywords": keywords,
            "semantic_terms": _words(narration),
            "clip_evidence": clips[index] if clips is not None else None,
        })
        cursor += seconds

    return {
        "engine": "fitfuel-production-director",
        "version": 1,
        "title": str(script.get("title") or ""),
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "fps": 30,
        "duration": round(cursor, 3),
        "scene_count": len(planned),
        "scenes": planned,
    }


def review_manifest(manifest: dict) -> dict:
    """Fail closed on missing evidence; this is a structural gate, not visual QA."""
    errors, warnings = [], []
    scenes = manifest.get("scenes") or []
    if not scenes:
        errors.append("manifest contains no scenes")
    previous_end = 0.0
    for scene in scenes:
        number = scene.get("scene")
        if float(scene.get("start", -1)) < previous_end - 0.01:
            errors.append(f"scene {number}: timeline overlaps or moves backwards")
        if float(scene.get("duration", 0)) <= 0:
            errors.append(f"scene {number}: duration must be positive")
        if not scene.get("narration"):
            errors.append(f"scene {number}: narration missing")
        if not scene.get("search_keywords"):
            errors.append(f"scene {number}: visual search evidence missing")
        if scene.get("clip_evidence") is None:
            warnings.append(f"scene {number}: clip evidence not attached yet")
        previous_end = float(scene.get("end", previous_end))
    return {
        "passed": not errors,
        "scope": "structural manifest validation only; rendered visuals still require human review",
        "scene_count": len(scenes),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    script = json.loads((OUTPUT / "script.json").read_text(encoding="utf-8"))
    audio = json.loads((OUTPUT / "audio_info.json").read_text(encoding="utf-8"))
    clip_path = OUTPUT / "clips_info.json"
    clips = json.loads(clip_path.read_text(encoding="utf-8")) if clip_path.exists() else None
    manifest = build_manifest(script, audio, clips)
    review = review_manifest(manifest)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    REPORT.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print(f"Production Director: {manifest['scene_count']} scenes, {manifest['duration']:.2f}s")
    for warning in review["warnings"]:
        print("WARN:", warning)
    for error in review["errors"]:
        print("FAIL:", error)
    print("PASS" if review["passed"] else "BLOCKED")
    return 0 if review["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
