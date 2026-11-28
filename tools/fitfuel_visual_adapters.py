"""Hybrid visual adapters for repository-derived science footage.

Adapters are opt-in and only select a source when a real rendered asset exists.
No simulated muscle deformation or invented molecular structure is generated here.
"""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCIENCE_DIR = Path(os.getenv("FITFUEL_SCIENCE_ASSETS", "output/cleanroom/repo_visuals"))

SOURCES = {
    "anatomy_clips": "https://github.com/CalmDownNova/anatomy-clips",
    "open_anatomy_3d": "https://github.com/MervinR07/open-anatomy-3d",
    "molecular_animation": "https://github.com/AmadeusBio-ai/Molecular_Animation",
    "molecular_nodes": "https://github.com/BradyAJohnston/MolecularNodes",
    "rlmuscle_v2": "https://github.com/chunleili/rlmuscleV2",
}

def classify_scene(scene):
    text = (str(scene.get("narration", "")) + " " +
            " ".join(scene.get("keywords", []))).lower()
    if any(x in text for x in ("protein synthesis", "amino acid", "myosin", "actin",
                               "molecular", "molecule", "dna", "gene", "genetic")):
        return "molecular"
    if any(x in text for x in ("muscle", "biceps", "triceps", "quadriceps",
                               "hamstring", "calf", "joint", "tendon", "anatomy")):
        return "anatomy"
    if any(x in text for x in ("squat", "deadlift", "bench press", "curl",
                               "range of motion", "biomechanics", "joint angle")):
        return "biomechanics"
    return "live_action"

def select_visual(scene):
    """Return a validated local repo-derived clip, otherwise explicit stock fallback."""
    kind = classify_scene(scene)
    candidates = []
    if kind in {"anatomy", "biomechanics"}:
        # Anatomy Clips output is exercise-specific; Open Anatomy is a general
        # anatomy asset. Never label a generic full-body asset as a joint motion.
        if kind == "biomechanics":
            candidates.append(("anatomy_clips", SCIENCE_DIR / "anatomy-clips" / "bone_muscle.mp4"))
        candidates.append(("open_anatomy_3d", SCIENCE_DIR / "open-anatomy" / "anatomy-muscle-cinematic.mp4"))
    elif kind == "molecular":
        candidates.append(("molecular_animation", SCIENCE_DIR / "molecular" / "molecular.mp4"))
    for source, path in candidates:
        if path.is_file() and path.stat().st_size > 100_000:
            return {"kind": kind, "source": source, "path": str(path),
                    "repo": SOURCES[source], "fallback": False}
    return {"kind": kind, "source": "stock", "path": None, "repo": None,
            "fallback": True, "reason": "No validated rendered repo asset is present for this scene"}

def integration_status():
    return {
        "anatomy_clips": "recipe-driven exercise clips; enabled when an exercise-specific rendered clip is supplied",
        "open_anatomy_3d": "general anatomy render; enabled when validated CGI proof is supplied",
        "molecular_animation": "PDB/mmCIF grounded local pipeline; enabled when rendered output is supplied",
        "molecular_nodes": "optional Blender molecular styling dependency for Molecular Animation; not installed in stock-only jobs",
        "rlmuscle_v2": "isolated research simulator; not a production dependency (GPU/resource and export integration not validated)",
    }
