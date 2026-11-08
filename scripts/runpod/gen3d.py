import torch, os, sys, traceback, trimesh
from PIL import Image
sys.path.insert(0,'/workspace/h3d')
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FaceReducer, FloaterRemover, DegenerateFaceRemover
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.rembg import BackgroundRemover
P={'steak_raw':1,'steak_seared':1,'tomato_half':4,'avocado_half':4,'sausage':4,'mushroom':2,'salad_bowl':4,'lantern':3,'bottle':3,'oilbottle':3,'percolator':3,'grinder':2,'cup':1,'case':2,'powerbox':3,'grillpan':2,'lab':2,'pointer':2}
FACES={'lab':38000,'pointer':38000,'salad_bowl':16000,'case':8000,'powerbox':6000}
os.makedirs('/root/out',exist_ok=True)
rb=BackgroundRemover(); shape=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
paint=Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2',subfolder='hunyuan3d-paint-v2-0-turbo')
print('LOADED',flush=True)
for k,s in P.items():
    try:
        im=Image.open(f'/root/img/{k}_{s}.png').convert('RGB'); im=rb(im)
        m=shape(image=im,num_inference_steps=40,octree_resolution=380,num_chunks=20000,generator=torch.manual_seed(2))[0]
        m=FloaterRemover()(m); m=DegenerateFaceRemover()(m); m=FaceReducer()(m,max_facenum=FACES.get(k,12000))
        t=paint(m,image=im); t.export(f'/root/out/{k}.glb'); print('OK',k,len(t.faces) if hasattr(t,'faces') else '',flush=True)
    except Exception as e: traceback.print_exc(); print('FAIL',k,e,flush=True)
print('GEN_DONE',flush=True)
