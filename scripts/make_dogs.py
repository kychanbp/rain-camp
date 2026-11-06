"""Two original dogs built from soft capsules, with bones and painted coats. They carry short fur in the game."""
import numpy as np, json, os
from skimage import measure
from scipy import ndimage as ni
ROOT=os.path.dirname(__file__)+'/..'; W=ROOT+'/web/assets/dogs'; os.makedirs(W,exist_ok=True)
def rc(p,a,b,r1,r2):
    """Round cone distance."""
    a=np.array(a,'f4');b=np.array(b,'f4');pa=p-a;ba=b-a;t=np.clip((pa*ba).sum(-1)/ (ba*ba).sum(),0,1); r=r1+(r2-r1)*t; return np.linalg.norm(pa-ba*t[...,None],axis=-1)-r,t
def smin(a,b,k):
    h=np.clip(.5+.5*(b-a)/k,0,1); return b+(a-b)*h-k*h*(1-h)
def build(name,S,coat):
    # (bone, start, end, r1, r2, blend). x sideways, y up, z forward. Parts use the stand pose.
    H=.62*S
    J=dict(hips=(0,.56,-.28),spine=(0,.585,-.02),chest=(0,.57,.2),neck=(0,.66,.31),head=(0,.79,.42),muzzle=(0,.76,.53),
      tail0=(0,.6,-.4),tail1=(0,.58,-.54),tail2=(0,.5,-.67),tail3=(0,.42,-.75),
      fl0=(.095,.5,.24),fl1=(.1,.28,.25),fl2=(.1,.09,.25),fl3=(.1,.03,.285),fr0=(-.095,.5,.24),fr1=(-.1,.28,.25),fr2=(-.1,.09,.25),fr3=(-.1,.03,.285),
      bl0=(.1,.5,-.29),bl1=(.115,.29,-.22),bl2=(.11,.12,-.33),bl3=(.11,.03,-.29),br0=(-.1,.5,-.29),br1=(-.115,.29,-.22),br2=(-.11,.12,-.33),br3=(-.11,.03,-.29),
      earl=(.075,.84,.41),earr=(-.075,.84,.41))
    J={k:tuple(np.array(v)*S) for k,v in J.items()}
    bod=coat['bulk']
    P=[('hips',J['hips'],J['spine'],.112*bod,.1*bod,.05),('spine',J['spine'],J['chest'],.1*bod,.14*bod,.05),('chest',J['chest'],(0,.44*S,.2*S),.14*bod,.095*bod,.06),('chest',(0,.53*S,.22*S),(0,.5*S,.33*S),.115*bod,.075*bod,.05),
       ('fl0',(.075,.62*S,.2*S),(.095,.5*S,.24*S),.055,.05,.04),('fr0',(-.075,.62*S,.2*S),(-.095,.5*S,.24*S),.055,.05,.04),('neck',J['chest'],J['neck'],.1*bod,.07*bod,.05),('neck',J['neck'],J['head'],.07*bod,.06,.04),
       ('head',(0,.81*S,.405*S),(0,.822*S,.44*S),.078*coat['skull'],.074*coat['skull'],.03),('head',(.03,.825*S,.44*S),(.045,.83*S,.46*S),.02,.018,.02),('head',(-.03,.825*S,.44*S),(-.045,.83*S,.46*S),.02,.018,.02),('head',(0,.782*S,.47*S),(0,.77*S,.57*S),.05*coat['skull'],.046*coat['skull'],.022),('head',(.02,.75*S,.5*S),(.02,.745*S,.57*S),.03,.028,.012),('head',(-.02,.75*S,.5*S),(-.02,.745*S,.57*S),.03,.028,.012),('head',(0,.768*S,.58*S),(0,.765*S,.6*S),.026,.024,.01),
       ('tail0',J['tail0'],J['tail1'],.042,.032,.03),('tail1',J['tail1'],J['tail2'],.032,.024,.01),('tail2',J['tail2'],J['tail3'],.024,.012,.01)]
    for s in 'lr':
        sg=1 if s=='l' else -1
        P+=[(f'f{s}0',J[f'f{s}0'],J[f'f{s}1'],.06,.036,.03),(f'f{s}1',J[f'f{s}1'],J[f'f{s}2'],.032,.023,.01),(f'f{s}2',J[f'f{s}2'],J[f'f{s}3'],.025,.033,.01),
            (f'f{s}1',(J[f'f{s}1'][0],J[f'f{s}1'][1]+.01,J[f'f{s}1'][2]-.025),J[f'f{s}1'],.03,.03,.012),(f'b{s}1',(J[f'b{s}2'][0],J[f'b{s}2'][1]+.015,J[f'b{s}2'][2]-.03),J[f'b{s}2'],.024,.024,.01),(f'b{s}0',J[f'b{s}0'],J[f'b{s}1'],.085,.044,.04),(f'b{s}1',J[f'b{s}1'],J[f'b{s}2'],.036,.021,.01),(f'b{s}2',J[f'b{s}2'],J[f'b{s}3'],.024,.033,.01),
            (f'ear{s}',J[f'ear{s}'],tuple(np.array(J[f'ear{s}'])+np.array([sg*.045,-.13*coat['ear'],.03])),.033,.042,.008)]
    lo=np.array([-.32,-.02,-.92])*S; hi=np.array([.32,1.0,.74])*S; d=.0115*S
    xs=np.arange(lo[0],hi[0],d);ys=np.arange(lo[1],hi[1],d);zs=np.arange(lo[2],hi[2],d); X,Y,Z=np.meshgrid(xs,ys,zs,indexing='ij'); p=np.stack([X,Y,Z],-1).astype('f4')
    f=np.full(X.shape,1e3,'f4'); own=np.zeros(X.shape,'i2'); bones=list(J.keys())
    for i,(b,a,e,r1,r2,k) in enumerate(P):
        if 'ear' in b:
            c=(np.array(a,'f4')+np.array(e,'f4'))/2; n_=np.array([1 if b=='earl' else -1,.15,.1],'f4'); n_/=np.linalg.norm(n_); pp=p-n_[None,None,None]*((p-c)*n_).sum(-1,keepdims=True)*(-2.2)
            dist,_=rc(pp.astype('f4'),a,e,r1*.95,r2*1.3)
        else: dist,_=rc(p,a,e,r1,r2)
        f=smin(f,dist,k)
    f=ni.gaussian_filter(f,.8)
    v,fa,nr,_=measure.marching_cubes(f,0,spacing=(d,d,d),gradient_direction='ascent'); v=v+lo
    # decimate by clustering is not needed at this grid size; keep it light by a coarser grid for far shells later
    # weights: closest parts, softly
    D=np.zeros((len(v),len(P)),'f4')
    for i,(b,a,e,r1,r2,k) in enumerate(P):
        dist,_=rc(v.astype('f4'),a,e,r1,r2); D[:,i]=np.maximum(dist,0)+.012
    w=(1/D)**5; names=[pp[0] for pp in P]
    # merge weights per bone
    bid=[bones.index(n) for n in names]; WB=np.zeros((len(v),len(bones)),'f4')
    for i,b in enumerate(bid): WB[:,b]+=w[:,i]
    idx=np.argsort(-WB,axis=1)[:,:4]; wt=np.take_along_axis(WB,idx,1); wt/=wt.sum(1,keepdims=True)
    # coat colour in the vertex: rgb, plus fur length in the last byte
    rng=np.random.RandomState(4)
    def noise(sig):
        g=rng.randn(48,48,48); g=ni.gaussian_filter(g,sig,mode='wrap'); g/=g.std(); uvw=((v-lo)/(hi-lo)*47).T; return ni.map_coordinates(g,uvw,order=1,mode='wrap')
    base=np.array(coat['base'],'f4'); col=np.tile(base,(len(v),1))
    n1=noise(1.2)
    col*= (1+.12*n1)[:,None]
    if coat.get('spots'):
        m=np.clip((noise(1.9)+.3*noise(.8)-.82)*7,0,1); tick=np.clip((noise(.9)-1.9)*3,0,1)
        c2=np.array(coat['spots'],'f4'); hd=np.clip((v[:,1]-.72*S)/.05,0,1)*np.clip((v[:,2]-.38*S)/.05,0,1)
        ea=np.array([ (WB[j,bones.index('earl')]+WB[j,bones.index('earr')])/WB[j].sum() for j in range(len(v))])
        m=np.maximum(np.maximum(m,tick),np.clip(ea*3,0,1)); mk=m[:,None]; col=col*(1-mk)+c2*mk
    # belly lighter on the brown dog; nose and eyes
    if coat.get('belly'):
        k=np.clip((.42*S-v[:,1])/.2,0,1)[:,None]*.25; col=col*(1-k)+np.array(coat['belly'])*k
    nose=np.linalg.norm((v-np.array([0,.775*S,.625*S]))*np.array([1,1.2,1]),axis=1)<.03; col[nose]=(.018,.014,.013)
    eye=np.zeros(len(v),bool); lid=np.zeros(len(v),'f4')
    for sg in (1,-1):
        c=np.array([sg*.052,.815*S,.455*S]); dd=np.linalg.norm(v-c,axis=1); eye|=dd<.015; lid=np.maximum(lid,np.clip((.035-dd)/.02,0,1))
    col[eye]=(.03,.015,.008); fur=np.full(len(v),coat['fur']); fur[nose|eye]=0
    mouth=(v[:,2]>.5*S)&(v[:,1]<.745*S)&(v[:,2]<.62*S)&(np.abs(v[:,0])<.05); col[mouth]*=.3
    col*=(1-.55*lid*(~eye))[:,None]; fur[v[:,2]>.5*S]*=.45; fur[v[:,1]<.1*S]*=.5
    # stored normal from the field
    nor=-nr if False else nr
    # marching cubes normals point down the gradient of f: outward with sign
    nor=np.array(nr,'f4')
    test=(v+nor*.01-lo)/d
    print(name,len(v),len(fa))
    b=[]
    b.append(np.asarray(v,'f4').tobytes()); b.append((np.clip(nor,-1,1)*127).astype('i1').tobytes()); b.append(b'\0'*((4-len(v)*3%4)%4))
    b.append(np.clip(np.sqrt(np.clip(col,0,1))*255,0,255).astype('u1').tobytes()); b.append(b'\0'*((4-len(v)*3%4)%4))
    b.append((np.clip(fur,0,1)*255).astype('u1').tobytes()); b.append(b'\0'*((4-len(v)%4)%4))
    b.append(idx.astype('u2').tobytes()); b.append((wt*255).round().astype('u1').tobytes()); b.append(fa.astype('u4').tobytes())
    open(f'{W}/{name}.bin','wb').write(b''.join(b))
    return dict(nv=len(v),ni=fa.size,bones=bones,joints={k:[float(x) for x in J[k]] for k in bones},S=S)
meta={}
meta['moss']=build('moss',1.0,dict(base=(.1,.054,.03),belly=(.15,.085,.05),fur=.55,bulk=1.08,ear=.82,skull=1.08))
meta['birch']=build('birch',.96,dict(base=(.56,.53,.47),spots=(.15,.095,.065),fur=.32,bulk=.86,ear=.85,skull=.9))
json.dump(meta,open(W+'/dogs.json','w'))
