"""Fit a skeleton to the two generated dog models and write them for the game with bones and photo textures."""
import numpy as np, json, os
from scipy import ndimage as ni
ROOT=os.path.dirname(os.path.abspath(__file__))+'/..'; M=ROOT+'/web/assets/models/'; W=ROOT+'/web/assets/dogs/'
meta=json.load(open(M+'models.json')); out={}
def seg(p,a,b):
    a=np.array(a,'f4');b=np.array(b,'f4');ab=b-a;t=np.clip(((p-a)*ab).sum(1)/((ab*ab).sum()+1e-9),0,1);return np.linalg.norm(p-(a+ab*t[:,None]),axis=1)
for key,name,size in (('lab','moss',.86),('pointer','birch',.84)):
    e=meta[key]; b=open(M+key+'.bin','rb').read(); n=e['nv']; P=np.frombuffer(b,'f4',n*3).reshape(-1,3).copy(); o=n*12; N=np.frombuffer(b,'i1',n*3,o).reshape(-1,3)/127.; o+=n*3; o+=(4-o%4)%4; UV=np.frombuffer(b,'f4',n*2,o).reshape(-1,2); o+=n*8; F=np.frombuffer(b,'u4',e['ni'],o).reshape(-1,3)
    def feet(P):
        low=P[P[:,1]<.07]; H,xe,ze=np.histogram2d(low[:,0],low[:,2],bins=48); l,c=ni.label(ni.binary_closing(H>0)); cs=[(xe[int(a)],ze[int(b_)]) for a,b_ in ni.center_of_mass(H>0,l,range(1,c+1))]; cs=sorted(cs); return np.array(cs)
    f=feet(P); r=f[:2].mean(0); fr=f[-2:].mean(0); ang=np.arctan2(fr[1]-r[1],fr[0]-r[0]); c,s=np.cos(ang),np.sin(ang); R=np.array([[c,-s],[s,c]]).T
    # yaw so the spine lies on x
    xz=P[:,[0,2]]@np.array([[c,s],[-s,c]]).T.T if False else np.stack([P[:,0]*c+P[:,2]*s,-P[:,0]*s+P[:,2]*c],1); P[:,0]=xz[:,0]; P[:,2]=xz[:,1]; nx=N[:,0]*c+N[:,2]*s; nz=-N[:,0]*s+N[:,2]*c; N=np.stack([nx,N[:,1],nz],1)
    f=feet(P); P[:,2]-=f[:,1].mean(); f=feet(P); print(name,'feet',f.round(2))
    rx=f[:2,0].mean(); fx=f[-2:,0].mean()
    top=lambda a,b_:P[(P[:,0]>a)&(P[:,0]<b_),1].max()
    hipT=top(rx-.05,rx+.08); witT=top(fx-.08,fx+.05); hi=np.argmax(P[:,1]+P[:,0]*.2); hx,hy=P[hi,0],P[hi,1]; tip=P[np.argmin(P[:,0])]
    nosei=np.argmax(P[:,0]); nx_,ny=P[nosei,0],P[nosei,1]
    print(' hipT',hipT,'wit',witT,'head',hx,hy,'tail',tip,'nose',nx_,ny)
    z=np.median(np.abs(f[:,1]))
    j={}
    H=lambda x,y,zz=0:(float(-zz),float(y),float(x))  # model (x forward) to bone frame (z forward, x left)
    hipY=hipT-.09; chestY=witT-.11
    j['hips']=H(rx+.03,hipY); j['spine']=H((rx+fx)/2,(hipY+chestY)/2+.0); j['chest']=H(fx-.0,chestY); j['neck']=H(fx+.09,witT+.03); j['head']=H(hx-.03,hy-.09); j['muzzle']=H(nx_-.05,ny)
    j['earl']=H(hx-.05,hy-.05,.05); j['earr']=H(hx-.05,hy-.05,-.05)
    tx0=rx-.08; j['tail0']=H(tx0,hipT-.05); tv=np.array([tip[0],tip[1]]); t0=np.array([tx0,hipT-.05])
    for i,k in enumerate((1,2,3)): q=t0+(tv-t0)*k/3; j[f'tail{i+1}']=H(q[0],q[1])
    h=chestY
    def leg(tag,fxx,fzz,top_y,cx,knee_back):
        s=np.sign(fzz) or 1; z0=fzz*.75
        j[tag+'0']=H(cx,top_y,z0); j[tag+'1']=H((cx+fxx)/2+knee_back,top_y*.52,fzz); j[tag+'2']=H(fxx-knee_back*.6,top_y*.2,fzz); j[tag+'3']=H(fxx+.02,.02,fzz)
    # left is +z in the model frame after flip
    rl=f[:2][np.argsort(f[:2,1])]; fl=f[-2:][np.argsort(f[-2:,1])]
    leg('fr',fl[0,0],fl[0,1],h-.03,fx,-.01); leg('fl',fl[1,0],fl[1,1],h-.03,fx,-.01); leg('br',rl[0,0],rl[0,1],hipY-.03,rx,.03); leg('bl',rl[1,0],rl[1,1],hipY-.03,rx,.03)
    bones=['hips','spine','chest','neck','head','muzzle','tail0','tail1','tail2','tail3','fl0','fl1','fl2','fl3','fr0','fr1','fr2','fr3','bl0','bl1','bl2','bl3','br0','br1','br2','br3','earl','earr']
    V=np.stack([-P[:,2],P[:,1],P[:,0]],1).astype('f4'); NN=np.stack([-N[:,2],N[:,1],N[:,0]],1)
    # capsules: (bone, a, b, radius). Distances are divided by radius, so thick parts claim more.
    C=[('hips','hips','spine',.16),('spine','spine','chest',.17),('chest','chest','neck',.15),('neck','neck','head',.09),('head','head','muzzle',.08),('tail0','tail0','tail1',.04),('tail1','tail1','tail2',.03),('tail2','tail2','tail3',.025)]
    for t in ('fl','fr','bl','br'):
        C+=[(t+'0',t+'0',t+'1',.075),(t+'1',t+'1',t+'2',.045),(t+'2',t+'2',t+'3',.04)]
    D=np.zeros((len(V),len(C)),'f4')
    for i,(bn,a,b_,r_) in enumerate(C):
        D[:,i]=seg(V,j[a],j[b_])/r_
    # legs only own points on their own side and below the belly
    for i,(bn,a,b_,r_) in enumerate(C):
        if bn[:2] in ('fl','fr','bl','br'):
            sg=1 if bn[1]=='l' else -1; D[(V[:,0]*sg<-.012),i]+=9; 
            if bn[2]=='0': D[V[:,1]>j[a][1]+.05,i]+=2
    w=(1/(D+.25))**6; idx=np.argsort(-w,axis=1)[:,:4]; wt=np.take_along_axis(w,idx,1); wt/=wt.sum(1,keepdims=True); bid=np.array([bones.index(c[0]) for c in C]); ids=bid[idx]
    V=V*size; J={k:[float(x*size) for x in j[k]] for k in bones}
    bb=[V.tobytes(),(np.clip(NN,-1,1)*127).astype('i1').tobytes(),b'\0'*((4-n*3%4)%4),UV.astype('f4').tobytes(),ids.astype('u2').tobytes(),(wt*255).round().astype('u1').tobytes(),F.astype('u4').tobytes()]
    open(W+name+'.bin','wb').write(b''.join(bb)); out[name]=dict(nv=n,ni=int(F.size),bones=bones,joints=J,S=size,tex=key)
json.dump(out,open(W+'dogs.json','w')); print('ok')
