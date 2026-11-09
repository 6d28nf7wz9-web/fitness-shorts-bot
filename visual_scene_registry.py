"""Shared scene-family registry for the FitFuel cinematic visual pipeline.

This module plans visual intent only. It deliberately does not pretend that
2D placeholders or primitive mannequins are production-quality 3D assets.
"""
import re

SCENE_FAMILIES = {
    "exercise_biomechanics": {
        "terms": (r"\bsquat\w*\b", r"\bdeadlift\w*\b", r"\bbench press\b", r"\blunge\w*\b", r"\bcurl\w*\b", r"\bpush.?up\w*\b", r"\bpull.?up\w*\b", r"\brow\b", r"\bexercise\b", r"\bworkout\b"),
        "hero_assets": ["realistic_human_mesh", "articulated_rig", "exercise_equipment"],
        "motion": ["full_exercise_cycle", "joint_articulation", "muscle_activation"],
        "quality_gate": ["realistic_human", "correct_joint_path", "exercise_specific_muscles"],
    },
    "digestive_system": {
        "terms": (r"\bdigest\w*\b", r"\bstomach\b", r"\bintestin\w*\b", r"\bcolon\b", r"\bgut\b", r"\bmicrobiome\b", r"\bfiber\b", r"\bfibre\b"),
        "hero_assets": ["digestive_tract_3d", "stomach_3d", "small_intestine_3d", "colon_3d"],
        "motion": ["food_bolus_travel", "peristalsis", "nutrient_absorption"],
        "quality_gate": ["anatomical_route_order", "organ_specific_motion"],
    },
    "food_nutrition": {
        "terms": (r"\bfood\b", r"\bmeal\b", r"\bnutrition\b", r"\bcarbohydrate\w*\b", r"\bprotein source\b", r"\bvegetable\w*\b", r"\bfruit\w*\b", r"\bportion\w*\b"),
        "hero_assets": ["photoreal_food_assets", "ingredient_cutaways"],
        "motion": ["food_assembly", "ingredient_reveal", "nutrient_breakdown"],
        "quality_gate": ["food_matches_narration", "no_generic_plate_placeholder"],
    },
    "muscle_anatomy": {
        "terms": (r"\bmuscle\w*\b", r"\bhypertrophy\b", r"\bmuscle fiber\w*\b", r"\bmuscle fibre\w*\b", r"\bbiceps\b", r"\bquadriceps\b", r"\bglutes?\b"),
        "hero_assets": ["layered_muscle_anatomy", "muscle_fiber_assets"],
        "motion": ["contraction", "fiber_zoom", "activation_highlight"],
        "quality_gate": ["correct_muscle_location", "layered_anatomy"],
    },
    "metabolism_hormones": {
        "terms": (r"\bmetabolism\b", r"\bcalorie\w*\b", r"\binsulin\b", r"\bglucagon\b", r"\bcortisol\b", r"\bhormone\w*\b", r"\batp\b", r"\bmitochondri\w*\b", r"\bfat oxidation\b"),
        "hero_assets": ["cell_3d", "mitochondrion_3d", "bloodstream_assets", "relevant_organ_assets"],
        "motion": ["molecular_transport", "receptor_interaction", "cellular_energy_process"],
        "quality_gate": ["pathway_supported_by_narration", "no_invented_causality"],
    },
    "hydration": {
        "terms": (r"\bhydrat\w*\b", r"\bwater balance\b", r"\bdehydrat\w*\b", r"\belectrolyte\w*\b"),
        "hero_assets": ["human_tissue_3d", "muscle_cell_3d", "fluid_assets"],
        "motion": ["fluid_transport", "cellular_fluid_change"],
        "quality_gate": ["physiologically_plausible_fluid_motion"],
    },
    "sleep_recovery": {
        "terms": (r"\bsleep\b", r"\brecovery\b", r"\brest day\b", r"\bfatigue\b", r"\bcircadian\b"),
        "hero_assets": ["human_3d", "brain_3d", "muscle_tissue_3d"],
        "motion": ["day_night_transition", "recovery_process"],
        "quality_gate": ["mechanism_matches_claim"],
    },
}

def resolve_scene_family(text):
    """Return the most specific matching family, or general_science."""
    value = str(text or "").lower()
    priority = (
        "exercise_biomechanics", "digestive_system", "metabolism_hormones",
        "hydration", "sleep_recovery", "food_nutrition", "muscle_anatomy",
    )
    for family in priority:
        if any(re.search(pattern, value) for pattern in SCENE_FAMILIES[family]["terms"]):
            return family
    return "general_science"

def build_visual_contract(text, heading=""):
    """Return a deterministic scene contract for a narration beat."""
    family = resolve_scene_family(f"{heading} {text}")
    definition = SCENE_FAMILIES.get(family, {
        "hero_assets": ["narration_specific_approved_assets"],
        "motion": ["cause_to_effect_subject_motion"],
        "quality_gate": ["subject_matches_narration"],
    })
    return {
        "family": family,
        "heading": str(heading)[:100],
        "narration": str(text),
        "hero_assets": list(definition["hero_assets"]),
        "required_motion": list(definition["motion"]),
        "quality_gate": list(definition["quality_gate"]),
        "requires_approved_assets": True,
        "preview_only_until_approved": True,
    }
