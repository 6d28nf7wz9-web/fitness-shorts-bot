"""Optional Hunyuan3D-2 image-conditioned mesh adapter for a GPU runner."""
import argparse
from pathlib import Path
def generate(reference_image,output,model_path="tencent/Hunyuan3D-2"):
 import torch
 from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
 if not torch.cuda.is_available():raise RuntimeError("Hunyuan3D generation requires a CUDA GPU")
 pipe=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
 mesh=pipe(image=reference_image)[0]
 dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True);mesh.export(str(dest));return str(dest)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--image",required=True);p.add_argument("--output",default="assets_3d/generated/hunyuan_object.glb");p.add_argument("--model",default="tencent/Hunyuan3D-2");a=p.parse_args();print(generate(a.image,a.output,a.model))
