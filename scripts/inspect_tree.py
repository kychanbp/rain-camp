import json,sys,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
p=sys.argv[1]
g=json.load(open(p)); b=np.memmap(p.replace('.gltf','.bin'),dtype='u1',mode='r')
def acc(i):
    a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; off=v.get('byteOffset',0)+a.get('byteOffset',0)
    ct={5123:'u2',5125:'u4',5126:'f4',5121:'u1'}[a['componentType']]; n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.frombuffer(b,dtype=ct,count=a['count']*n,offset=off).reshape(-1,n)
print([ (n.get('name'),n.get('mesh'),n.get('translation'),n.get('scale')) for n in g['nodes']][:10])
for mi,m in enumerate(g['meshes']):
  for pr in m['primitives']:
    name=g['materials'][pr['material']]['name']; idx=acc(pr['indices']).ravel(); P=acc(pr['attributes']['POSITION'])
    print(mi,name,'tris',len(idx)//3,'verts',len(P),'bbox',P.min(0).round(2),P.max(0).round(2))
    if 'twig' in name or 'leaf' in name or 'needle' in name:
        s=idx[::3][:];e=idx[1::3]
        N=len(P); gr=coo_matrix((np.ones(len(s),bool),(s,e)),shape=(N,N))
        nc,lab=connected_components(gr,directed=False)
        sz=np.bincount(lab); print(' components',nc,'size med',np.median(sz),'max',sz.max(),'min',sz.min())
