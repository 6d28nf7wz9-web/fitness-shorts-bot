"""Validated reusable 3D asset catalog and scene routing."""
from __future__ import annotations
import json, re
from pathlib import Path
CATALOG_VERSION=1
SUPPORTED_FORMATS={".glb",".gltf",".ply",".obj",".fbx"}
ASSET_ROOT=Path("assets_3d")
def load_catalog(path="assets_3d/catalog.json"):
    p=Path(path)
    if not p.exists(): return {"catalog_version":CATALOG_VERSION,"assets":[]}
    data=json.loads(p.read_text(encoding="utf-8"))
    if data.get("catalog_version")!=CATALOG_VERSION or not isinstance(data.get("assets"),list):
        raise ValueError("Unsupported or malformed 3D asset catalog")
    return data
def validate_asset_entry(entry,root=ASSET_ROOT):
    if not isinstance(entry,dict): raise ValueError("asset entry must be an object")
    required=("asset_id","category","file","source","license","review_status")
    missing=[k for k in required if not entry.get(k)]
    if missing: raise ValueError("missing asset fields: "+", ".join(missing))
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}",str(entry["asset_id"])):
        raise ValueError("asset_id must be a stable lowercase slug")
    rel=Path(str(entry["file"]))
    if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError("asset file must be a safe relative path with a supported 3D format")
    path=Path(root)/rel
    if not path.is_file() or path.stat().st_size<128: raise ValueError(f"asset file missing or too small: {path}")
    if entry["review_status"] not in {"pending","approved","rejected"}: raise ValueError("invalid review_status")
    if entry.get("scientific_accuracy_required") and entry["review_status"]=="approved" and not entry.get("reviewed_by"):
        raise ValueError("scientific assets require reviewer identity before approval")
    return path
def approved_assets(catalog=None,category=None,root=ASSET_ROOT):
    catalog=catalog or load_catalog(); selected=[]
    for entry in catalog["assets"]:
        if entry.get("review_status")!="approved" or (category and entry.get("category")!=category): continue
        try: path=validate_asset_entry(entry,root=root)
        except (ValueError,OSError): continue
        selected.append({**entry,"resolved_path":str(path)})
    return selected
def select_asset_for_scene(scene_plan,catalog=None,root=ASSET_ROOT):
    intent=scene_plan.get("intent","concept_explainer")
    category={"environment":"environment","standalone_object":"prop","scientific_anatomy":"scientific",
              "microscopic_science":"scientific","exercise_demo":"exercise"}.get(intent)
    candidates=approved_assets(catalog,category,root) if category else []
    if not candidates:
        return {"asset":None,"fallback":scene_plan.get("provider","local_science"),
                "reason":"No approved matching 3D asset; keep the existing renderer/stock fallback."}
    return {"asset":candidates[0],"fallback":scene_plan.get("fallback_provider"),
            "reason":"Selected a validated, explicitly approved 3D asset."}
def write_catalog(entries,path="assets_3d/catalog.json"):
    data={"catalog_version":CATALOG_VERSION,"assets":entries}; p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return data

def build_render_manifest(scenes, catalog=None, root=ASSET_ROOT):
    """Connect scene-intent planning to approved asset selection for renderers."""
    from three_d_intelligence import plan_scene
    rows=[]
    for index,scene in enumerate(scenes,1):
        plan=plan_scene(scene)
        selection=select_asset_for_scene(plan,catalog=catalog,root=root)
        rows.append({"scene_number":index,"scene_plan":plan,"asset_selection":selection})
    return {"manifest_version":1,"scene_count":len(rows),"scenes":rows}
