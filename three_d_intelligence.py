"""Dependency-free scene intelligence and safe 3D provider routing."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path

ENGINE_VERSION = "0.1.0"
GENERATION_ENABLED = os.getenv("FITFUEL_3D_GENERATION", "0").strip().lower() in {"1", "true", "yes", "on"}

PROVIDERS = {
    "local_science": {"kind": "renderer", "available": True, "cost": "free", "role": "reviewable scientific diagrams and motion graphics"},
    "stock": {"kind": "footage", "available": True, "cost": "free-first", "role": "real people, exercise form, documentary footage"},
    "worldgen": {"kind": "environment_generator", "available": False, "cost": "local GPU", "role": "background environments", "license": "Apache-2.0 code; check model/dependency licenses"},
    "hunyuan3d": {"kind": "object_generator", "available": False, "cost": "local GPU", "role": "standalone reusable props", "license": "Tencent Hunyuan 3D 2.0 Community License; legal review required", "commercial_clearance_required": True},
    "sage": {"kind": "scene_planner", "available": False, "cost": "research runtime", "role": "task-aware spatial planning reference"},
    "text2nerf": {"kind": "research_generator", "available": False, "cost": "research GPU runtime", "role": "research reference only"},
}

def _scene_text(scene: dict) -> str:
    keys = ("narration", "keyword", "visual_title", "visual_subtitle", "visual_instruction", "visual_type", "heading")
    return " ".join(str(scene.get(key, "")) for key in keys).lower()

def classify_visual_intent(scene: dict) -> str:
    text = _scene_text(scene)
    if re.search(r"exercise form|squat|deadlift|bench press|shoulder press|curl|row", text):
        return "exercise_demo"
    if re.search(r"muscle fiber|sarcomere|tendon|ligament|joint|anatomy|organ|heart|lung|brain", text):
        return "scientific_anatomy"
    if re.search(r"cell|mitochond|atp|protein molecule|molecule|receptor|hormone", text):
        return "microscopic_science"
    if re.search(r"gym|kitchen|laboratory|lab|environment|room|landscape|background", text):
        return "environment"
    if re.search(r"object|equipment|dumbbell|barbell|bottle|food item|supplement container", text):
        return "standalone_object"
    if re.search(r"person|athlete|coach|workout|training|running|walking", text):
        return "real_world_footage"
    return "concept_explainer"

def _stable_id(scene: dict) -> str:
    payload = json.dumps(scene, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

def plan_scene(scene: dict, generation_enabled: bool | None = None) -> dict:
    if not isinstance(scene, dict):
        raise TypeError("scene must be a dictionary")
    enabled = GENERATION_ENABLED if generation_enabled is None else bool(generation_enabled)
    intent = classify_visual_intent(scene)
    if intent in {"scientific_anatomy", "microscopic_science"}:
        primary, fallback, asset_type = "local_science", "stock", "scientific_diagram"
        reason = "Scientific details stay on the reviewed schematic renderer; generated geometry is not assumed anatomically correct."
    elif intent == "exercise_demo":
        primary, fallback, asset_type = "stock", "local_science", "exercise_reference"
        reason = "Real movement/form footage is preferred; schematic biomechanics is the safe fallback."
    elif intent == "environment":
        primary, fallback, asset_type = "stock", "local_science", "environment"
        reason = "Use existing licensed footage first; WorldGen may later be evaluated for generated backgrounds."
    elif intent == "standalone_object":
        primary, fallback, asset_type = "local_science", "stock", "reusable_prop"
        reason = "A reusable 3D prop may help, but generation stays gated until a compatible, cleared provider is installed."
    elif intent == "real_world_footage":
        primary, fallback, asset_type = "stock", "local_science", "live_action"
        reason = "Real-world footage is a better match than synthetic 3D for people and movement."
    else:
        primary, fallback, asset_type = "local_science", "stock", "motion_graphic"
        reason = "Use a locally rendered explainer unless scene-specific evidence supports another source."
    requested = "worldgen" if enabled and intent == "environment" else "hunyuan3d" if enabled and intent == "standalone_object" else None
    ready = bool(requested and PROVIDERS[requested]["available"] and not PROVIDERS[requested].get("commercial_clearance_required", False))
    if requested and not ready:
        reason += " Optional 3D generation was requested but is not eligible/installed; deterministic fallback is retained."
    return {
        "engine_version": ENGINE_VERSION, "scene_id": _stable_id(scene), "intent": intent,
        "asset_type": asset_type, "provider": requested if ready else primary,
        "fallback_provider": fallback, "generation_requested": bool(requested),
        "generation_enabled": ready,
        "requires_scientific_review": intent in {"scientific_anatomy", "microscopic_science", "exercise_demo"},
        "reason": reason,
    }

def build_scene_plan(scenes: list[dict], generation_enabled: bool | None = None) -> dict:
    if not isinstance(scenes, list):
        raise TypeError("scenes must be a list")
    plans = [plan_scene(scene, generation_enabled) for scene in scenes]
    return {
        "engine_version": ENGINE_VERSION,
        "generation_enabled": GENERATION_ENABLED if generation_enabled is None else bool(generation_enabled),
        "scene_count": len(plans),
        "provider_counts": {name: sum(p["provider"] == name for p in plans) for name in sorted({p["provider"] for p in plans})},
        "scenes": plans,
    }

def write_scene_plan(scenes: list[dict], output_path: str | Path, generation_enabled: bool | None = None) -> dict:
    plan = build_scene_plan(scenes, generation_enabled)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan
