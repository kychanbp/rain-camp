"""Make tiling textures: pine needle carpet, fabric weave, cloth, wood grain, rain ripples, rain drops."""
import numpy as np, os
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ni
ROOT=os.path.dirname(__file__)+'/..'; D=ROOT+'/data/tex'; W=ROOT+'/web/assets/tex'; os.makedirs(W,exist_ok=True)
rng=np.random.RandomState(3)
def to_normal(h,strength):
    gx=(np.roll(h,-1,1)-np.roll(h,1,1)); gy=(np.roll(h,-1,0)-np.roll(h,1,0))
    n=np.dstack([-gx*strength,gy*strength,np.ones_like(h)]); n/=np.linalg.norm(n,axis=2,keepdims=True); return ((n*.5+.5)*255).astype('u1')
def save(a,name,q=84): Image.fromarray(a).save(f'{W}/{name}.webp',quality=q,method=6)
# ---- pine needle carpet. Each needle is drawn as a thin curved stroke, with a shadow, on a wrapped sheet.
S=2048; SS=2
def needles():
    base=np.array(Image.open(D+'/forest_ground_04_c.jpg').convert('RGB').resize((S,S)),'f4')*.28
    im=Image.fromarray(base.astype('u1')).resize((S,S)); hm=Image.new('F',(S,S),0.); 
    d=ImageDraw.Draw(im,'RGBA'); dh=ImageDraw.Draw(hm)
    pal=np.array([(112,72,44),(128,86,52),(96,60,38),(142,102,66),(84,54,36),(118,82,54),(150,116,82)],'f4')
    layers=11
    for L in range(layers):
        n=int(2600+L*420); lift=(L+1)/layers
        for i in range(n):
            x,y=rng.rand(2)*S; a=rng.rand()*6.283; ln=rng.uniform(150,420)*(.8+.4*lift); bend=rng.normal(0,.5)
            pts=[(x+np.cos(a+bend*t*.6)*ln*t,y+np.sin(a+bend*t*.6)*ln*t) for t in np.linspace(0,1,7)]
            c=pal[rng.randint(len(pal))]*(.42+.62*lift)*rng.uniform(.82,1.12)
            w=int(rng.choice([2,2,2,3]))
            for ox in (-S,0,S):
                for oy in (-S,0,S):
                    q=[(p[0]+ox,p[1]+oy) for p in pts]
                    if max(p[0] for p in q)<0 or min(p[0] for p in q)>S or max(p[1] for p in q)<0 or min(p[1] for p in q)>S: continue
                    d.line([(p[0]+3,p[1]+4) for p in q],fill=(10,6,3,int(120)),width=w+2)
                    d.line(q,fill=(int(c[0]),int(c[1]),int(c[2]),255),width=w)
                    dh.line(q,fill=float(L+1+rng.rand()*.4),width=w)
    a=np.array(im); h=np.array(hm,'f4'); h=ni.gaussian_filter(h,1.,mode='wrap')
    save(a,'needles_c',80); save(to_normal(h,.55),'needles_n',78)
    return a
needles()
# ---- other ground textures from CC0 photos
def down(src,dst,size=1024,q=80):
    Image.open(f'{D}/{src}.jpg').convert('RGB').resize((size,size),Image.LANCZOS).save(f'{W}/{dst}.webp',quality=q,method=6)
down('grass_path_2_c','grass_c'); down('grass_path_2_n','grass_n'); down('brown_mud_leaves_01_c','mud_c'); down('brown_mud_leaves_01_n','mud_n')
def food():
    s=512; x,y=np.meshgrid(np.linspace(-1,1,s),np.linspace(-1,1,s)); r=np.hypot(x*1.05,y*1.05)
    def nz(sig): a=ni.gaussian_filter(rng.randn(s,s),sig); return a/a.std()
    veins=np.clip(1-np.abs(nz(9)+.4*nz(3))*7,0,1)**2*.6+np.clip(nz(2)-1.5,0,1)*.5
    fat=np.clip((r-.70+.04*nz(14))*12,0,1)
    raw=np.dstack([104+26*nz(16)*.5,30+8*nz(9)*.5,30+6*nz(9)*.5])*(1-veins[...,None])+np.array([226,186,170])*veins[...,None]; raw=raw*(1-fat[...,None])+np.array([232,206,176])*fat[...,None]
    save(raw.clip(0,255).astype('u1'),'steak_c',84)
    stripes=(np.abs(((y+x*.35)*6.5)%1-.5)<.1)*1.; stripes=ni.gaussian_filter(stripes,2)
    crust=np.dstack([70+22*nz(5),36+12*nz(5),20+7*nz(5)])+nz(1.2)[...,None]*9; crust=crust*(1-.85*stripes[...,None])+np.array([12,8,6])*.85*stripes[...,None]; crust=crust*(1-fat[...,None]*.7)+np.array([150,98,48])*fat[...,None]*.7
    save(crust.clip(0,255).astype('u1'),'seared_c',84)
    # tomato slice
    a=np.arctan2(y,x); walls=(np.abs(np.sin(a*2.5))<.1)*1.; rim=np.clip((r-.84)*30,0,1); seed=np.clip(nz(3)-1.1,0,1)*(r<.7)
    t=np.dstack([190+20*nz(9),30+12*nz(9),24+6*nz(9)]); t=t*(1-walls[...,None]*.5)+np.array([236,120,90])*walls[...,None]*.5; t=t*(1-seed[...,None])+np.array([225,200,120])*seed[...,None]; t=t*(1-rim[...,None])+np.array([170,16,12])*rim[...,None]; save(ni.gaussian_filter(t,(1,1,0)).clip(0,255).astype('u1'),'tomslice_c',84)
    # avocado flesh: pale centre, green edge
    g=np.clip(r,0,1)[...,None]**2.2; f=np.array([232,218,120])*(1-g)+np.array([112,142,40])*g; save((f+nz(6)[...,None]*4).clip(0,255).astype('u1'),'avoflesh_c',84)
food()
# ---- fabric weave
def fabric():
    s=512; x,y=np.meshgrid(np.arange(s),np.arange(s)); h=np.sin(x*2*np.pi/6)*np.sign(np.sin(y*2*np.pi/12))*.5+np.sin(y*2*np.pi/6)*np.sign(np.sin(x*2*np.pi/12))*-.5
    low=ni.gaussian_filter(rng.randn(s,s),14,mode='wrap'); low/=low.std(); h=h*.5+low*.15
    save(to_normal(h.astype('f4'),.5),'fabric_n',78)
fabric()
def wood():
    s=512; x,y=np.meshgrid(np.linspace(0,1,s,0),np.linspace(0,1,s,0)); w=ni.gaussian_filter(rng.randn(s,s),(60,3),mode='wrap'); w/=w.std()
    g=np.sin((x*14+w*.5)*2*np.pi)*.5+.5; f=ni.gaussian_filter(rng.randn(s,s),(30,1),mode='wrap'); f/=f.std()
    v=.7+.22*g+.1*f; c=np.dstack([v*200,v*150,v*100]).clip(0,255).astype('u1'); save(c,'wood_c',80); save(to_normal((g+f*.2).astype('f4'),1.4),'wood_n',76)
wood()
# ---- ripple normal: an animated strip of rings in time, 8 frames in a 4x2 sheet is too coarse, so one height of many rings; the shader moves two copies
def ripples():
    s=512; h=np.zeros((s,s),'f4'); x,y=np.meshgrid(np.arange(s),np.arange(s))
    for i in range(170):
        cx,cy=rng.rand(2)*s; r0=rng.uniform(8,42); dx=(x-cx+s/2)%s-s/2; dy=(y-cy+s/2)%s-s/2; d=np.hypot(dx,dy); h+=np.exp(-((d-r0)/2.3)**2)*np.exp(-d/60.)*rng.uniform(.3,1)
    save(to_normal(h,2.4),'ripple_n',80)
ripples()
# ---- drops on a surface: beads with their own normals, R,G bent normal, B mask
def drops():
    s=512; R=np.zeros((s,s),'f4'); x,y=np.meshgrid(np.arange(s),np.arange(s)); h=np.zeros((s,s),'f4')
    for i in range(900):
        cx,cy=rng.rand(2)*s; r=rng.uniform(1.6,6.5)*(1.8 if rng.rand()<.08 else 1); x0,y0=int(cx-r-2),int(cy-r-2); n=int(2*r+5)
        xx,yy=np.meshgrid(np.arange(x0,x0+n),np.arange(y0,y0+n)); d=np.hypot(xx-cx,yy-cy)/r; b=np.sqrt(np.clip(1-d*d,0,1))*r
        h[yy%s,xx%s]=np.maximum(h[yy%s,xx%s],b)
    save(to_normal(h,.5),'drops_n',82)
drops()
print('tex done')
