import json,tempfile,unittest
from pathlib import Path
from asset_pipeline import approved_assets,select_asset_for_scene,validate_asset_entry,write_catalog
class AssetPipelineTests(unittest.TestCase):
 def make_asset(self,root,name="dumbbell.glb"):
  p=Path(root)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b"glTF"+b"\0"*256);return p
 def test_pending_assets_never_enter_production(self):
  with tempfile.TemporaryDirectory() as d:
   self.make_asset(d);e={"asset_id":"dumbbell-demo","category":"prop","file":"dumbbell.glb","source":"procedural-preview","license":"project-generated","review_status":"pending"}
   self.assertEqual(approved_assets({"catalog_version":1,"assets":[e]},root=d),[])
 def test_approved_asset_is_selected(self):
  with tempfile.TemporaryDirectory() as d:
   self.make_asset(d);e={"asset_id":"dumbbell-demo","category":"prop","file":"dumbbell.glb","source":"procedural-preview","license":"project-generated","review_status":"approved"}
   got=select_asset_for_scene({"intent":"standalone_object","fallback_provider":"stock"},{"catalog_version":1,"assets":[e]},root=d)
   self.assertEqual(got["asset"]["asset_id"],"dumbbell-demo")
 def test_path_traversal_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   e={"asset_id":"bad-asset","category":"prop","file":"../escape.glb","source":"test","license":"test","review_status":"approved"}
   with self.assertRaises(ValueError):validate_asset_entry(e,root=d)
 def test_scientific_asset_requires_named_review(self):
  with tempfile.TemporaryDirectory() as d:
   self.make_asset(d,"muscle.glb");e={"asset_id":"muscle-demo","category":"scientific","file":"muscle.glb","source":"procedural-preview","license":"project-generated","review_status":"approved","scientific_accuracy_required":True}
   with self.assertRaises(ValueError):validate_asset_entry(e,root=d)
 def test_catalog_round_trip(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"catalog.json";data=write_catalog([],p);self.assertEqual(json.loads(p.read_text()),data)
if __name__=="__main__":unittest.main()
