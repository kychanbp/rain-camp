"""Plan the ground, trees and props. The bake and the game both read data from here."""
import numpy as np, json, os
from PIL import Image
from scipy import ndimage as ni
ROOT=os.path.dirname(__file__)+'/..'; G=ROOT+'/data/gen'; W=ROOT+'/web/assets'
rng=np.random.RandomState(11)
SIZE=240.; N=512   # ground map covers -120..120 m
xs=np.linspace(-SIZE/2,SIZE/2,N); X,Z=np.meshgrid(xs,xs)   # three.js x, z. Rows are z.
def fbm(sig):
    a=ni.gaussian_filter(rng.randn(N,N),sig,mode='wrap'); return a/a.std()
# height: soft undulation, flat at the camp
h=fbm(40)*.55+fbm(14)*.12+fbm(5)*.025
camp=np.exp(-((X+2)**2/ (14**2)+(Z-1)**2/(10**2)))
h=h*(1-camp); h-=h[N//2,N//2]
# meadow: an open strip of wet grass south of the camp, the way the video opens onto one
n=fbm(16)*.5+fbm(5)*.22+fbm(2)*.08
m=np.clip(.5+(Z-(6.5+2.2*np.sin(X*.09)+1.5*np.sin(X*.23+1)))*.22+n*.6,0,1)*np.clip(1-(Z-24-4*n)*.25,0,1)
m*=np.clip((46-np.abs(X+2))/10,0,1)
grass=np.clip(m,0,1)
# ring of mud and worn ground by the door and around the car wheels
wear=np.exp(-(((X+1)/3.2)**2+((Z-3.2)/1.3)**2))*.8+np.exp(-(((X+5)/3.2)**2+((Z-1.6)/2.5)**2))*.5
wear=np.clip(wear*(0.65+.5*fbm(3)),0,1)
leaf=np.clip(.5+fbm(6)*.5,0,1)   # bright and dark needle patches
puddle=np.clip((fbm(7)*.8-1.1)*2.2,0,1)*(1-camp*.55)
splat=np.dstack([grass,wear,leaf,puddle]); Image.fromarray((splat*255).astype('u1'),'RGBA').save(W+'/splat.png')
# trees
trees=[]
def ok(x,z):
    if -10<x<6.5 and -6<z<7: return False
    if np.interp(z,xs,grass[:,N//2])>.9 and abs(z-12)<9 and abs(x)<35: return False
    return True
hand=[(7.4,-2.4,1.0),(-7.4,-7.6,1.1),(3.5,-7.8,1.05),(9.8,3.2,.95),(-12.6,-.6,1.0),(11.6,-6.2,1.05),(-3.2,-11.5,.95),(7.5,8.8,.9),(-14.4,6.3,1.0)]
pts=[(x,z) for x,z,_ in hand]
for x,z,s in hand: trees.append(dict(k=int(rng.randint(3)),x=x,z=z,r=float(rng.rand()*6.28),s=s))
tries=0
while len(pts)<520 and tries<60000:
    tries+=1; r=np.sqrt(rng.rand())*105; a=rng.rand()*6.283; x,z=r*np.cos(a),r*np.sin(a)
    gi=np.interp(z,xs,np.arange(N)).astype(int); gj=np.interp(x,xs,np.arange(N)).astype(int)
    if grass[gi,gj]>.72 or not ok(x,z): continue
    sp=3.6+rng.rand()*2.5
    if any((x-a)**2+(z-b)**2<sp*sp for a,b in pts): continue
    pts.append((x,z)); trees.append(dict(k=int(rng.randint(3)),x=round(x,2),z=round(z,2),r=round(rng.rand()*6.28,2),s=round(.85+rng.rand()*.4,2)))
saps=[]
hs=[(-11.2,7.4,.52),(6.4,5.6,.62),(-8.3,5.5,.58),(5.9,-4.8,.7),(-6.3,-3.9,.48),(2.7,-3.9,.4),(-10.6,-3.2,.74),(8.9,.5,.5),(.6,8.9,.34),(-5.4,8.2,.3)]
for x,z,s in hs: saps.append(dict(k=int(rng.randint(3)),x=x,z=z,r=round(rng.rand()*6.28,2),s=s))
while len(saps)<70:
    r=8+np.sqrt(rng.rand())*60; a=rng.rand()*6.283; x,z=r*np.cos(a),r*np.sin(a)
    if -9<x<6 and -5<z<7: continue
    gi=np.interp(z,xs,np.arange(N)).astype(int); gj=np.interp(x,xs,np.arange(N)).astype(int)
    if grass[gi,gj]>.8: continue
    if any((x-t['x'])**2+(z-t['z'])**2<3 for t in trees[:200]): continue
    saps.append(dict(k=int(rng.randint(3)),x=round(x,2),z=round(z,2),r=round(rng.rand()*6.28,2),s=round(.28+rng.rand()*.5,2)))
hb=h.astype('f4'); hb.tofile(W+'/height.bin'); np.save(G+'/height.npy',hb)
Image.fromarray((np.clip(grass,0,1)*255).astype('u1')).save(W+'/grassmap.png')
json.dump(dict(size=SIZE,n=N,trees=trees,saps=saps),open(W+'/world.json','w'))
print(len(trees),len(saps),h.min(),h.max())
