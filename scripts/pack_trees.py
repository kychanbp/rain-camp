"""Pack tuft pictures into one atlas and write trees.bin plus trees.json for the game."""
import numpy as np, json, os
from PIL import Image
from scipy import ndimage as ni
ROOT=os.path.dirname(__file__)+'/..'; G=ROOT+'/data/gen'; W=ROOT+'/web/assets/trees'; os.makedirs(W,exist_ok=True)
T=np.load(G+'/tufts.npz'); TR=np.load(G+'/trunks.npz'); R=json.load(open(G+'/tuft_r.json'))
from PIL import ImageDraw
def spray(seed,N=2048):
    '''One bundle of long pine needles bursting from a twig end, drooping at the tips.'''
    r=np.random.RandomState(seed); im=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(im); cx,cy=N*.5,N*.5
    d.line([(cx,N*.92),(cx+r.normal(0,30),N*.7),(cx,cy)],fill=(66,48,34,255),width=14)
    for k in range(52+seed*5):
        b=-1.57+r.normal(0,1.05) if r.rand()<.8 else r.rand()*6.28; L=N*r.uniform(.28,.47); droop=r.uniform(.45,1.); pts=[(cx,cy)]; x,y=cx,cy
        for q in range(9):
            ang=b+(1.57-b)*droop*(q/9)**2.2; x+=np.cos(ang)*L/9; y+=np.sin(ang)*L/9; pts.append((x,y))
        v=r.rand(); c=(int(60+v*40),int(76+v*42),int(48+v*22),255) if r.rand()>.06 else (160,120,62,255)
        d.line(pts,fill=c,width=int(r.choice([4,5])))
    return im.resize((1024,1024),Image.LANCZOS)
atlas=Image.new('RGBA',(2048,2048))
for i in range(4):
    im=np.array(spray(i+1).convert('RGBA')).astype('f4')
    a=im[...,3]; rgb=im[...,:3]
    # bleed colour past the edges so mip maps do not go black
    mask=a>40; idx=ni.distance_transform_edt(~mask,return_distances=False,return_indices=True)
    rgb=rgb[idx[0],idx[1]]; rgb=ni.gaussian_filter(rgb,(1.5,1.5,0))*(1-mask[...,None])+rgb*mask[...,None]
    # needle colour: lift towards the wet green of slash pine
    atlas.paste(Image.fromarray(np.dstack([rgb,a]).clip(0,255).astype('u1'),'RGBA'),((i%2)*1024,(i//2)*1024))
atlas.save(W+'/tufts.png'); atlas.save(W+'/tufts.webp',quality=88,method=6,exact=True)
blobs=[];meta={};off=0
def put(a,ty):
    global off
    b=np.asarray(a,ty).tobytes(); pad=(4-len(b)%4)%4; b+=b'\0'*pad; blobs.append(b); o=off; off+=len(b); return o
rng=np.random.RandomState(5)
for base,mi in [('pine',0),('pine',1),('pine',2),('sap',0),('sap',1),('sap',2)]:
    k=f'{base}{mi}'; C=T[k+'_c']; A=T[k+'_a']; r=T[k+'_r']; n=len(C)
    h0,h1=C[:,1].min(),C[:,1].max()
    cen=np.array([np.median(C[:,0]),0,np.median(C[:,2])])
    P=[];N=[];U=[];Col=[];I=[];v=0
    for j in range(n):
        ax=A[j]/(np.linalg.norm(A[j])+1e-6); 
        out=C[j]-cen; rad=np.hypot(out[0],out[2]); o=out/(np.linalg.norm(out)+1e-6)
        if ax@o<0: ax=-ax
        # hang: tufts droop a little, needles fall downwards when long
        side=np.cross(ax,o); side/= (np.linalg.norm(side)+1e-6); pl=np.cross(side,ax)
        tile=rng.randint(4); tR=R[tile]
        S=rng.uniform(.34,.48)*(.85 if base=='sap' else 1)
        for card in range(2):
            w=side if card==0 else pl
            w=w*S; h=ax*S
            q=[C[j]-w-h,C[j]+w-h,C[j]+w+h,C[j]-w+h]
            u0=(tile%2)*.5; v0=(1-(tile//2))*.5-.0
            uv=[(u0,v0),(u0+.5,v0),(u0+.5,v0+.5),(u0,v0+.5)]
            nor=o*.75+np.array([0,.65,0]); nor/=np.linalg.norm(nor)
            # shade: inside of the crown and low tufts are darker
            ao=np.clip(.35+.75*rad/(np.percentile(np.hypot(*(C-cen)[:,[0,2]].T),90)+1e-3),.3,1)*np.clip(.55+.5*(C[j,1]-h0)/(h1-h0),.5,1)
            for a,b in zip(q,uv): P.append(a);U.append(b);N.append(nor);Col.append(ao)
            I+= [v,v+1,v+2,v,v+2,v+3]; v+=4
    # a light version for far trees: fewer, bigger, single tufts
    keep=rng.permutation(n)[:max(120,n//2)]; LP=[];LN=[];LU=[];LC=[];LI=[];lv=0
    for j in keep:
        ax=A[j]/(np.linalg.norm(A[j])+1e-6); out=C[j]-cen; rad=np.hypot(out[0],out[2]); o=out/(np.linalg.norm(out)+1e-6)
        if ax@o<0: ax=-ax
        side=np.cross(ax,o); side/=(np.linalg.norm(side)+1e-6); tile=rng.randint(4); S=rng.uniform(.6,.78)
        w=side*S; h=ax*S; q=[C[j]-w-h,C[j]+w-h,C[j]+w+h,C[j]-w+h]; u0=(tile%2)*.5; v0=(1-(tile//2))*.5; uv=[(u0,v0),(u0+.5,v0),(u0+.5,v0+.5),(u0,v0+.5)]
        nor=o*.75+np.array([0,.65,0]); nor/=np.linalg.norm(nor); ao=np.clip(.35+.75*rad/(np.percentile(np.hypot(*(C-cen)[:,[0,2]].T),90)+1e-3),.3,1)*np.clip(.55+.5*(C[j,1]-h0)/(h1-h0),.5,1)
        for a,b in zip(q,uv): LP.append(a);LU.append(b);LN.append(nor);LC.append(ao)
        LI+=[lv,lv+1,lv+2,lv,lv+2,lv+3]; lv+=4
    # far trunk: eight sides
    TK=TR.get(f'{k}_trunk_p'); FP=[];FN=[];FU=[];FI=[]
    if TK is not None:
        top=TK[:,1].max(); bot=TK[TK[:,1]<.5]; r0=np.hypot(bot[:,0]-bot[:,0].mean(),bot[:,2]-bot[:,2].mean()).mean()
        for ri,y in enumerate(np.linspace(0,top,5)):
            sl=TK[np.abs(TK[:,1]-y)<top/12]; cx,cz=np.median(sl[:,0]),np.median(sl[:,2]); rr=np.median(np.hypot(sl[:,0]-cx,sl[:,2]-cz)); rr=(min(rr,.2) if ri==0 else min(rr,prev*.86)); rr=max(rr,.03); prev=rr
            for a in range(8):
                t=a/8*6.2832; FP.append((cx+np.cos(t)*rr,y,cz+np.sin(t)*rr)); FN.append((np.cos(t),0,np.sin(t))); FU.append((a/2,y/2))
        for ri in range(4):
            for a in range(8):
                b=(a+1)%8; x=ri*8; FI+=[x+a,x+8+a,x+8+b,x+a,x+8+b,x+b]
    NT=[];NN=[];NU=[];NI=[]
    if TK is not None:
        rs=[]; top=TK[:,1].max(); ys=np.linspace(0,top,26)
        for y in ys:
            sl=TK[np.abs(TK[:,1]-y)<top/20]; rs.append((np.median(sl[:,0]),y,np.median(sl[:,2]),np.median(np.hypot(sl[:,0]-np.median(sl[:,0]),sl[:,2]-np.median(sl[:,2])))))
        rs=np.array(rs); from scipy.ndimage import gaussian_filter1d as g1; rs[:,0]=g1(rs[:,0],1.5,mode='nearest'); rs[:,2]=g1(rs[:,2],1.5,mode='nearest'); rr=np.minimum.accumulate(g1(np.minimum(rs[:,3],.3),1.5,mode='nearest')); rr=np.maximum(rr,.025)*np.interp(ys,[0,.5,top],[1.25,1,1]);  sides=14
        for i,(cx,y,cz,_) in enumerate(rs):
            for a in range(sides+1):
                t=a/sides*6.2832; NT.append((cx+np.cos(t)*rr[i],y,cz+np.sin(t)*rr[i])); NN.append((np.cos(t),0,np.sin(t))); NU.append((a/sides*2,y*.55))
        for i in range(len(rs)-1):
            for a in range(sides):
                x=i*(sides+1); NI+=[x+a,x+sides+1+a,x+sides+2+a,x+a,x+sides+2+a,x+a+1]
    m=dict(cards=dict(p=put(P,'f4'),n=put(N,'f4'),u=put(U,'f4'),c=put(Col,'f4'),i=put(I,'u4'),nv=v,ni=len(I)))
    m['lo']=dict(p=put(LP,'f4'),n=put(LN,'f4'),u=put(LU,'f4'),c=put(LC,'f4'),i=put(LI,'u4'),nv=lv,ni=len(LI))
    if FP: m['lotrunk']=dict(p=put(FP,'f4'),n=put(FN,'f4'),u=put(FU,'f4'),i=put(FI,'u4'),nv=len(FP),ni=len(FI))
    if NT: m['trunk']=dict(p=put(NT,'f4'),n=put(NN,'f4'),u=put(NU,'f4'),i=put(NI,'u4'),nv=len(NT),ni=len(NI))
    for kind in ('bark',):
        if f'{k}_{kind}_p' in TR:
            pp=TR[f'{k}_{kind}_p']; ii=TR[f'{k}_{kind}_i']; ar=np.linalg.norm(np.cross(pp[ii[:,1]]-pp[ii[:,0]],pp[ii[:,2]]-pp[ii[:,0]]),axis=1)/2; ii=ii[ar<.012]
            m[kind]=dict(p=put(pp,'f4'),n=put(TR[f'{k}_{kind}_n'],'f4'),u=put(TR[f'{k}_{kind}_u'],'f4'),i=put(ii,'u4'),nv=len(pp),ni=ii.size)
    meta[k]=m; print(k,n,v)
open(W+'/trees.bin','wb').write(b''.join(blobs)); json.dump(meta,open(W+'/trees.json','w'))
print(off/1e6,'MB')
