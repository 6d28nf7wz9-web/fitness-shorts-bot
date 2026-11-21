"""Optional WorldGen GPU adapter; never imported by regular CI."""
import argparse
from pathlib import Path
def generate(prompt,output,low_vram=True):
 import torch
 from worldgen import WorldGen
 if not torch.cuda.is_available():raise RuntimeError("WorldGen generation requires a CUDA GPU")
 engine=WorldGen(mode="t2s",device=torch.device("cuda"),low_vram=low_vram)
 mesh=engine.generate_world(prompt,return_mesh=True)
 import open3d as o3d
 dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
 if not o3d.io.write_triangle_mesh(str(dest),mesh):raise RuntimeError("WorldGen failed to write mesh")
 return str(dest)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--prompt",required=True);p.add_argument("--output",default="assets_3d/generated/worldgen_environment.ply");p.add_argument("--low-vram",action="store_true");a=p.parse_args();print(generate(a.prompt,a.output,a.low_vram))
