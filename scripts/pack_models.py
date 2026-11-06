"""Turn the generated GLB models into small game files: one bin per model plus a webp texture."""
import trimesh, numpy as np, json, os, sys, glob
from PIL import Image
from scipy import ndimage as ni
ROOT=os.path.dirname(os.path.abspath(__file__))+'/..'; IN=ROOT+'/data/gen3d'; OUT=ROOT+'/web/assets/models'; os.makedirs(OUT,exist_ok=True)
meta={}
for f in sorted(glob.glob(IN+'/*.glb')):
    k=os.path.basename(f)[:-4]; s=trimesh.load(f); m=s.dump(concatenate=True) if hasattr(s,'dump') else s
    p=np.array(m.vertices,'f4'); fa=np.array(m.faces,'u4'); uv=np.array(m.visual.uv,'f4'); nr=np.array(m.vertex_normals,'f4'); tex=m.visual.material.baseColorTexture
    if tex is None: print('no tex',k); continue
    c=(p.min(0)+p.max(0))/2; c[1]=p[:,1].min(); p=p-c; ext=np.ptp(p,axis=0); p=p/ext.max()  # base at origin, longest side 1
    size=512 if k not in ('lab','pointer','salad_bowl','steak_seared','steak_raw') else 1024
    t=tex.convert('RGB').resize((size,size),Image.LANCZOS)
    if k=='lab':
        # the source picture has studio highlights painted in: settle the coat to an even chocolate
        a=np.array(t,'f4'); L=a.mean(2); c=np.array([60,36,24],'f4'); low=ni.gaussian_filter(a,(14,14,0)); a=np.clip(c+(a-low)*.9+(low-low.mean((0,1)))*.1,0,255); t=Image.fromarray(a.astype('u1'))
    t.save(f'{OUT}/{k}.webp',quality=86,method=6)
    uv=uv.copy(); uv[:,1]=1-uv[:,1]
    b=[p.tobytes(),(nr*127).astype('i1').tobytes(),b'\0'*((4-len(nr)*3%4)%4),uv.tobytes(),fa.tobytes()]; open(f'{OUT}/{k}.bin','wb').write(b''.join(b))
    meta[k]=dict(nv=len(p),ni=fa.size,ext=(ext/ext.max()).round(3).tolist()); print(k,len(p),len(fa),ext.round(3))
json.dump(meta,open(OUT+'/models.json','w'))
