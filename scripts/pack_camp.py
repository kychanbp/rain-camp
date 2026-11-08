"""Turn the baked ground light into one picture and copy the textures that the camp uses."""
import numpy as np, json, os, shutil
from PIL import Image
from scipy import ndimage as ni
ROOT=os.path.dirname(__file__)+'/..'; G=ROOT+'/data/gen'; W=ROOT+'/web/assets/camp'
sky,warm,fire,nt=[np.load(f'{G}/lm_{n}.npy').mean(2) for n in ('sky','warm','fire','notent')]
meta=json.load(open(W+'/camp.json')); sc=meta['scale']
sigma=1.2 if sky.shape[0]>600 else .8
f=lambda a:ni.gaussian_filter(a,sigma)
s=f(sky); ws=max(np.percentile(warm,99.8),1e-4); fs=max(np.percentile(fire,99.8),1e-4); ss=max(np.percentile(sky,99.9),1e-3)
meta['ground']=dict(sky=float(ss),warm=float(ws),fire=float(fs),x0=-24,y0=-23,size=44)
img=np.dstack([np.sqrt(np.clip(s/ss,0,1)),np.sqrt(np.clip(f(warm)/ws,0,1)),np.sqrt(np.clip(f(fire)/fs,0,1)),np.sqrt(np.clip(f(nt)/ss,0,1))])
Image.fromarray((img*255).astype('u1'),'RGBA').transpose(Image.FLIP_TOP_BOTTOM).save(W+'/ground_lm.png')
print('sky',s.mean(),'scale',ss,ws,fs)
for k,m in meta['mats'].items():
    for key in ('map','nmap'):
        p=m.get(key)
        if p and os.path.exists(p):
            dst=os.path.basename(p).replace('.jpg','.webp').replace('.png','.webp')
            Image.open(p).convert('RGB').resize((512,512),Image.LANCZOS).save(f'{W}/{dst}',quality=80,method=6); m[key]=dst
        elif p: print('missing',p); m.pop(key)
json.dump(meta,open(W+'/camp.json','w'))
print(len(meta['groups']),sum(g['ni'] for g in meta['groups'])//3,[g['mat'] for g in meta['groups'] if g['nv']>12000])
