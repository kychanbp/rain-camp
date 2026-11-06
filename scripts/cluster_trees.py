"""Group the single needles of the CC0 pines into tufts. Each tuft becomes one or two cards in the game."""
import json,sys,numpy as np,os
from sklearn.cluster import MiniBatchKMeans
ROOT=os.path.dirname(__file__)+'/..'
OUT=ROOT+'/data/gen'; os.makedirs(OUT,exist_ok=True)
def load(p):
    g=json.load(open(p)); b=np.memmap(p.replace('.gltf','.bin'),dtype='u1',mode='r')
    def acc(i):
        a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; off=v.get('byteOffset',0)+a.get('byteOffset',0)
        ct={5123:'u2',5125:'u4',5126:'f4'}[a['componentType']]; n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.frombuffer(b,dtype=ct,count=a['count']*n,offset=off).reshape(-1,n)
    return g,acc
res={}
for name,kk,base in (('pine_tree_01',(1300,950,1150),'pine'),('pine_sapling_medium',(1100,850,700),'sap')):
    g,acc=load(f'{ROOT}/data/models/{name}/{name}.gltf')
    for mi,m in enumerate(g['meshes']):
        pr=[p for p in m['primitives'] if 'twig' in g['materials'][p['material']]['name']][0]
        idx=acc(pr['indices']).ravel(); P=acc(pr['attributes']['POSITION'])
        # every third triangle corner is enough for a centre
        ids=idx[::3][::9]; pts=np.array(P[ids],dtype='f4')
        sel=np.random.RandomState(1).choice(len(pts),min(len(pts),250000),replace=False); pts=pts[sel]
        km=MiniBatchKMeans(kk[mi],batch_size=8192,n_init=2,random_state=2).fit(pts)
        lab=km.labels_; C=km.cluster_centers_; cnt=np.bincount(lab,minlength=kk[mi])
        ax=np.zeros((kk[mi],3)); rad=np.zeros(kk[mi]); 
        for k in range(kk[mi]):
            q=pts[lab==k]-C[k]
            if len(q)<8: continue
            u,s,vt=np.linalg.svd(q[:4000],full_matrices=False); ax[k]=vt[0]; rad[k]=np.percentile(np.linalg.norm(q,axis=1),92)
        keep=cnt>=8
        res[f'{base}{mi}_c']=C[keep]; res[f'{base}{mi}_a']=ax[keep]; res[f'{base}{mi}_r']=rad[keep]; res[f'{base}{mi}_n']=cnt[keep]
        print(base,mi,keep.sum(),'rad',np.median(rad[keep]).round(3),np.percentile(rad[keep],95).round(3),flush=True)
np.savez(OUT+'/tufts.npz',**res)
