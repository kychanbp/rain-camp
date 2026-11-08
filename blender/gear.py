"""Camp gear. Objects with a name in MOVE are kept separate so that the game can animate them."""
import math, numpy as np, os
from lib import *
from car import joined
K=(-2.42,-.1)    # kitchen table centre
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); MD=ROOT+'/data/models'
def ph(name,loc,rot=(0,0,0),scale=1.,want=None):
    """Bring in one CC0 model. Returns its meshes joined."""
    before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f'{MD}/{name}/{name}.gltf'); new=[o for o in bpy.data.objects if o not in before]
    ms=[o for o in new if o.type=='MESH']; bpy.context.view_layer.update()
    for o in ms:
        w=o.matrix_world.copy(); o.parent=None; o.matrix_world=w
    for o in new:
        if o.type!='MESH': bpy.data.objects.remove(o)
    if len(ms)>1: o=joined(name,ms)
    else: o=ms[0]; o.name=name
    bpy.context.view_layer.objects.active=o
    for a in bpy.context.selected_objects: a.select_set(False)
    o.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    if want and len(o.data.polygons)>want:
        d=o.modifiers.new('d','DECIMATE'); d.ratio=want/len(o.data.polygons); apply(o)
    o.scale=(scale,)*3; o.rotation_euler=rot; o.location=loc; bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return o
def blob(name,r,loc,mat,scale,seed=1,amp=.12,seg=20):
    o=sphere(name,r,loc,mat,scale,seg); n=rng_noise(seed); me=o.data
    for v in me.vertices:
        k=1+amp*n(v.co.x*18/r*.08+v.co.z*7,v.co.y*16/r*.08)
        v.co*=k
    return o
def steak(name,loc,seed):
    """A slab with an uneven outline, a fat edge and flat top. UV is the view from above."""
    m=M('steak',(1,1,1),.5,food='steak'); n=rng_noise(seed); R=10;S_=36;P=[];UV=[];F=[]
    def out(a): return .064*(1+.2*math.sin(a*2+seed)+.09*math.sin(a*3-seed*2)+.05*math.sin(a*7+seed))
    rows=[(0,.024),(.55,.024),(.86,.023),(.97,.02),(1,.012),(.98,.003),(.9,0),(.5,0),(0,0)]
    for rr,z in rows:
        for j in range(S_):
            a=2*math.pi*j/S_; r=out(a)*rr; x=r*math.cos(a)*1.25; y=r*math.sin(a); zz=z+.0022*n(x*30,y*30)*(z>.01)
            P.append((x,y,zz)); UV.append((.5+x*3.8,.5+y*3.8))
    for i in range(len(rows)-1):
        for j in range(S_):
            k=(j+1)%S_; F.append((i*S_+j,(i+1)*S_+j,(i+1)*S_+k,i*S_+k))
    o=from_np(name,P,F,m,UV); o.location=(loc[0],loc[1],loc[2]-.018); return o
def slices(name,c,n,seed,tex_mat,r=.022):
    """Round slices lying in a shingled row."""
    ps=[]
    for i in range(n):
        o=cyl(name+str(i),r*(1-.06*abs(i-n/2)),.008,(c[0]+i*.016,c[1]+i*.003,c[2]+.006+i*.0004),tex_mat,n=16,rot=(0,.12,0)); box_uv_planar(o,r); ps.append(o)
    return joined(name,ps)
def box_uv_planar(o,r):
    me=o.data
    uv=me.uv_layers.new(name='UVMap').data if not me.uv_layers else me.uv_layers[0].data
    for l in me.loops:
        v=me.vertices[l.vertex_index].co; uv[l.index].uv=(.5+v.x/(2*r),.5+v.y/(2*r))
def build():
    S=[];G={}          # static list, movable dictionary
    blk=M('alublack',(.02,.02,.022),.45,.6); slat=M('slat',(.022,.022,.024),.38,.55); steel=M('steel',(.55,.56,.57),.35,.9); cast=M('cast',(.014,.014,.015),.42,.5); wood=M('wood',(.42,.24,.1),.5,tile='wood'); warm=M('lampg',(.9,.72,.4),.2,emit='warm'); bulb=M('bulb',(.95,.75,.45),.3,emit='warm')
    tx,ty=K; zt=.87
    # kitchen table sliding out of the car, black slats and a leg
    x0,x1=tx-.62,tx+.56; y0,y1=ty-.62,ty+.62
    for i,y in enumerate(np.linspace(y0+.06,y1-.06,8)):
        S.append(box(f'k{i}',(x1-x0,.158,.022),((x0+x1)/2,y,zt),slat,bev=.004,seg=1))
    S.append(box('kf',(.03,y1-y0,.05),(x1,ty,zt-.03),M('wood'),bev=.008)) 
    for sy in (-1,1):
        S.append(box('krail',(1.4,.03,.04),(tx-.1,ty+sy*.6,zt-.04),blk,bev=.006,seg=1)); 
        S.append(cyl('kleg',.016,zt-.02,(x1-.05,ty+sy*.55,(zt-.02)/2),M('alu',(.62,.63,.64),.42,.9),n=10))
    # induction hob with a glowing ring, grill pan
    hx,hy=tx-.05,ty-.28
    S.append(box('hob',(.36,.34,.042),(hx,hy,zt+.035),M('hobglass',(.01,.01,.012),.1,.0),bev=.01,seg=2))
    G['hobring']=[lathe('hobring',[(.1,zt+.058),(.112,zt+.058),(.118,zt+.058),(.13,zt+.0585)],M('hobglow',(.9,.1,.02),.3,emit='hob'),n=32)]
    G['hobring'][0].location=(hx,hy,0)
    z=zt+.058
    for i,(dx,dy) in enumerate(((-.078,-.07),(.07,-.035),(-.02,.08))):
        G[f'steak{i}']=[steak(f'steak{i}',(hx+dx,hy+dy,z+.052),3+i)]
    # tongs rest on the table edge; lifted into view for the sear
    a=sweep('tong',np.array([(0,0,.0),(.13,.008,.0),(.27,.02,.0)]),(.005,.005,.005),steel,n=6,flat=(1,1.7)); b=sweep('tong2',np.array([(0,0,.0),(.13,-.008,.0),(.27,-.02,.0)]),(.005,.005,.005),steel,n=6,flat=(1,1.7)); t=joined('tongs',[a,b]); t.location=(hx+.26,hy+.1,zt+.02); G['tongs']=[t]
    # board, knife, avocado, tomato, onion
    bx,by=tx+.12,ty+.26
    bd=ph('wooden_cutting_board',(bx,by,zt+.012),rot=(0,0,math.radians(82)),scale=.85,want=2000); S.append(bd)
    av=ph('food_avocado_01',(bx-.1,by+.06,zt+.03),scale=1.,want=2400); G['avocado']=[av]
    tomato=M('tomato',(.62,.05,.03),.25,clearcoat=1)
    for i,(dx,dy) in enumerate(((.03,.1),(.09,.05),(.1,.13))):
        G[f'tomato{i}']=[sphere(f'tomato{i}',.021,(bx+dx,by+dy,zt+.05),tomato,(1,1,.92),14)]
    on=ph('yellow_onion',(bx+.16,by-.08,zt+.03),scale=.8,want=1600); S.append(on)
    bl=box('blade',(.17,.002,.038),(0,0,0),steel,bev=.0008,seg=1); hd=box('kh',(.1,.014,.022),(-.135,0,.004),M('wood'),bev=.005,seg=2); kn=joined('knife',[bl,hd]); kn.location=(bx-.02,by-.1,zt+.05); kn.rotation_euler=(math.pi/2,0,.3); G['knife']=[kn]
    # cut tomato and avocado, shown as the knife works
    G['tomcut']=[slices('tomcut',(bx-.08,by-.04,zt+.024),6,1,M('tomslice',(1,1,1),.3,food='tomslice'),.024)]
    avf=M('avoflesh',(1,1,1),.42,food='avoflesh')
    hv=[]
    for i,(dx,dy) in enumerate(((.02,.11),(.09,.13))):
        o=lathe('avoh',[(0,.0),(.03,.0),(.036,.018),(.028,.024),(0,.024)],M('avoskin',(.06,.09,.03),.5),n=16); o.scale=(1.05,1.35,1); o.location=(bx+dx,by+dy,zt+.02); hv.append(o)
        c=cyl('avof',.035,.002,(bx+dx,by+dy,zt+.045),avf,n=18); c.scale=(1.05,1.35,1); box_uv_planar(c,.035); hv.append(c)
    hv.append(sphere('pit',.0165,(bx+.02,by+.11,zt+.05),M('pit',(.19,.1,.05),.25),seg=12))
    G['avocut']=[joined('avocut',hv)]
    # wooden bowl for the salad, on the far side of the table from the hob
    mx,my=tx+.3,ty-.2
    S.append(lathe('sbowl',[(0,.0),(.05,.0),(.1,.03),(.115,.07),(.108,.072),(.09,.03),(.04,.012),(0,.01)],M('bowlw',(.3,.17,.08),.45),n=48)); S[-1].location=(mx,my,zt+.012)
    sal=[]; rg=random.Random(4)
    for i in range(34):
        c=rg.choice([M('tomato',(.62,.05,.03),.25,clearcoat=1),M('tomato'),M('avg',(.5,.56,.13),.45),M('avg'),M('onionc',(.65,.25,.4),.4)])
        a=rg.random()*6.28; r=rg.random()**.5*.082
        sal.append(blob(f's{i}',.016,(mx+r*math.cos(a),my+r*math.sin(a),zt+.056+rg.random()*.016-r*.05),c,(1,.8,.7),i,.18,8))
    G['salad']=[joined('salad',sal)]
    # oil, salt, glass of beer, lantern
    glassm=M('tumbler',(.8,.82,.8),.05,transparent=.82,noshadow=1)
    tom_=None
    salt=lathe('salt',[(0,0),(.022,0),(.024,.01),(.024,.075),(.02,.09),(0,.09)],M('saltb',(.7,.68,.64),.5),n=30); salt.location=(tx+.47,ty+.13,zt+.012); S.append(salt)
    # power box on the car floor: plain rounded case with a warm display
    case=M('powercase',(.09,.09,.09),.5,.1)
    p=box('power',(.32,.26,.3),(-3.2,.35,1.04),case,bev=.03,seg=3); S.append(p); S.append(box('pdisp',(.006,.13,.06),(-3.04,.35,1.13),M('display',(.9,.55,.2),.2,emit='warm')))
    for i in range(2): S.append(cyl('pknob',.012,.012,(-3.04,.28+i*.14,1.0),steel,rot=(0,math.pi/2,0),n=10))
    # lanterns
    def lantern(name,x,y,z,hang=False):
        P=[]
        P.append(lathe('lb',[(0,0),(.055,0),(.058,.012),(.055,.055),(.035,.07),(.0,.07)],blk,n=40))
        P.append(lathe('lt',[(.0,.19),(.04,.178),(.052,.165),(.05,.15),(.0,.15)],blk,n=40))
        for i in range(4):
            a=i*math.pi/2+.4; P.append(cyl('lc',.0035,.09,(.048*math.cos(a),.048*math.sin(a),.11),blk,n=6))
        P.append(sweep('lh',[(.05*math.cos(a),0,.19+.05*math.sin(a)) for a in np.linspace(0,math.pi,10)],.003,blk,n=6))
        o=joined(name,P); o.location=(x,y,z); out=[o]
        g=lathe(name+'g',[(0,.07),(.033,.075),(.04,.11),(.033,.145),(0,.15)],M('lampg'),n=32); g.location=(x,y,z); out.append(g); return out
    # bench and low fire table in the doorway
    fx,fy,zf=-.95,-.72,.40
    for i,x in enumerate(np.linspace(fx-.47,fx+.47,6)):
        S.append(box(f'f{i}',(.17,.58,.018),(x,fy,zf),slat,bev=.004,seg=1))
    for sx in (-1,1):
        for sy in (-1,1): S.append(sweep('fleg',np.array([(fx+sx*.42,fy+sy*.2,zf-.02),(fx+sx*.5,fy+sy*.25,.0)]),.011,M('alu'),n=8))
    # fire box: a steel tray with black stones and glowing embers
    bxx=fx+.18
    stl=M('steelb',(.2,.19,.18),.46,.85)
    S.append(box('fbase',(.38,.3,.018),(bxx,fy,zf+.022),stl,bev=.004,seg=1))
    for sy in (-1,1): S.append(box('fwall',(.38,.012,.075),(bxx,fy+sy*.15,zf+.065),stl,bev=.003,seg=1))
    for sx in (-1,1): S.append(box('fwall',(.012,.3,.075),(bxx+sx*.19,fy,zf+.065),stl,bev=.003,seg=1))
    for i in range(2): S.append(box('frib',(.34,.012,.012),(bxx,fy+(i-.5)*.09,zf+.1),stl))
    emb=M('ember',(.05,.02,.015),.7,emit='fire')
    S.append(box('fembed',(.34,.26,.012),(bxx,fy,zf+.045),emb))
    for i in range(30):
        rg=random.Random(i); S.append(blob('st',.024,(bxx+rg.uniform(-.15,.15),fy+rg.uniform(-.11,.11),zf+.058+rg.random()*.012),M('stones',(.07,.065,.06),.75),(1.1,1,.65),i,.2,10))
    # bbq grate beside the fire
    gx=fx-.26
    S.append(box('gbox',(.32,.24,.04),(gx,fy,zf+.03),M('steelb'),bev=.004,seg=1))
    for i,y in enumerate(np.linspace(-.1,.1,14)): S.append(cyl('gw',.0016,.3,(gx,fy+y,zf+.056),steel,rot=(0,math.pi/2,0),n=5))
    for i,x in enumerate(np.linspace(-.14,.14,18)): S.append(cyl('gw',.0016,.22,(gx+x,fy,zf+.058),steel,rot=(math.pi/2,0,0),n=5))
    sg=M('sausage',(.45,.15,.08),.4)
    for i in range(3):
        G[f'sausage{i}']=[blob(f'sausage{i}',.016,(gx-.08+i*.06,fy-.06,zf+.075),sg,(3.6,1,1),i,.02,12)]
    mu=M('mushroom',(.72,.62,.5),.6)
    for i in range(2):
        G[f'mush{i}']=[lathe(f'mush{i}',[(0,.03),(.022,.03),(.03,.022),(.026,.012),(.01,.008),(0,.008)],mu,n=14)]; G[f'mush{i}'][0].location=(gx+.03+i*.065,fy+.05,zf+.057)
    # glass of beer on the table
    mg=lathe('mugg',[(0,.0),(.04,.0),(.044,.15),(.041,.15),(.037,.006),(0,.006)],glassm,n=20); mg.location=(fx+.08,fy-.2,zf+.012); S.append(mg)
    bf=lathe('beerfill',[(0,.006),(.036,.006),(.0395,.12),(0,.12)],M('beer',(.72,.42,.06),.08,transparent=.25,noshadow=1),n=16); bf.location=(fx+.08,fy-.2,zf+.012); G['beerfill']=[bf]
    fo=lathe('foam',[(0,.0),(.0398,.0),(.0398,.022),(.03,.03),(0,.031)],M('foam',(.9,.85,.72),.8),n=16); fo.location=(fx+.08,fy-.2,zf+.132); G['foam']=[fo]
    bt=lathe('bottle',[(0,0),(.031,0),(.032,.012),(.031,.14),(.012,.19),(.012,.24),(.014,.243),(0,.243)],M('bottlegl',(.05,.03,.012),.12,clearcoat=1),n=16); bt.location=(fx+.17,fy-.2,zf+.012); G['bottle']=[bt]
    # bench
    bx2,by2=-.98,.25
    for i,y in enumerate(np.linspace(by2-.13,by2+.13,4)):
        S.append(box(f'bn{i}',(1.1,.08,.02),(bx2,y,.40),M('wood'),bev=.005,seg=1))
    for sx in (-1,1):
        S.append(sweep('bl',np.array([(bx2+sx*.45,by2-.13,.39),(bx2+sx*.45,by2-.16,.0)]),.012,M('alu'),n=8)); S.append(sweep('bl',np.array([(bx2+sx*.45,by2+.13,.39),(bx2+sx*.45,by2+.16,.0)]),.012,M('alu'),n=8))
    # coffee set on the low table: morning objects, shown later
    cx,cy=fx-.3,fy+.12
    gr=[lathe('gb',[(0,0),(.028,0),(.03,.005),(.03,.13),(.028,.14),(0,.14)],steel,n=36)]
    G['grinder']=[gr[0]]; gr[0].location=(cx,cy,zf+.012)
    cr=[cyl('c0',.004,.075,(.0,0,.018),steel,n=6,rot=(0,0,0)),cyl('c1',.0035,.08,(.04,0,.05),steel,n=6,rot=(0,math.pi/2,0)),cyl('c2',.009,.03,(.08,0,.065),M('wood'),n=8)]
    G['crank']=[joined('crank',cr)]; G['crank'][0].location=(cx,cy,zf+.152)
    perc=[lathe('pc',[(0,0),(.05,0),(.052,.01),(.04,.08),(.04,.085),(.052,.15),(.05,.17),(.03,.19),(0,.195)],steel,n=36),sweep('pch',fillet([(.05,0,.15),(.11,0,.14),(.1,0,.05),(.04,0,.05)],.03,seg=3),.006,blk,n=7)]
    G['perc']=[joined('perc',perc)]; G['perc'][0].location=(cx+.22,cy-.02,zf+.04)
    S.append(lathe('burner',[(0,0),(.04,0),(.042,.012),(.016,.02),(.02,.032),(0,.032)],blk,n=14)); S[-1].location=(cx+.22,cy-.02,zf+.012)
    cup=lathe('cup',[(0,0),(.03,0),(.042,.03),(.05,.065),(.047,.066),(.038,.03),(.0,.012)],M('kuksa',(.55,.33,.13),.42),n=36)
    h=box('cuph',(.05,.022,.016),(.065,0,.058),M('kuksa'),bev=.006,seg=2); G['cup']=[joined('cup',[cup,h])]; G['cup'][0].location=(cx+.08,cy+.05,zf+.012)
    cof=cyl('coffee',.043,.002,(0,0,0),M('coffee',(.07,.03,.012),.15),n=18); cof.location=(cx+.08,cy+.05,zf+.012+.052); G['coffee']=[cof]
    tin=cyl('beans',.042,.08,(cx+.13,cy-.11,zf+.05),M('tinm',(.5,.5,.48),.35,.85),n=32); S.append(tin)
    # hand pump at the tent corner for raising the tent
    px,py=2.0,-2.3
    S.append(box('pbase',(.3,.1,.02),(px,py,.05),blk,bev=.008,seg=1)); S.append(cyl('pbody',.04,.5,(px,py,.32),M('pumpb',(.65,.25,.05),.5),n=14)); 
    h=joined('pumprod',[cyl('prod',.009,.42,(0,0,0),steel,n=8),cyl('phand',.014,.3,(0,0,.21),M('rubber2',(.03,.03,.03),.7),rot=(math.pi/2,0,0),n=8)]); h.location=(px,py,.78); G['pumprod']=[h]
    S.append(sweep('phose',fillet([(px+.04,py,.08),(px+.2,py+.3,.04),(1.05,-1.72,.05),(1.0,-1.63,.2)],.08,seg=4),.012,M('rubber2'),n=8))
    # dog bowls
    for i,(x,y) in enumerate(((-.2,-1.2),(.05,-1.15))):
        o=lathe('dogbowl',[(0,0),(.1,0),(.11,.05),(.1,.052),(.09,.012),(0,.012)],steel,n=32); o.location=(x,y,.01); S.append(o)
    # things that say someone lives here
    S.append(ph('plastic_jerrycan',(-1.9,1.2,0.0),rot=(0,0,.6),scale=.8,want=2000))
    S.append(ph('rubber_boots',(-.15,-1.75,0.0),rot=(0,0,2.2),scale=.9,want=3000))
    S.append(ph('hatchet',(-.3,1.25,.0),rot=(0,0,.3),scale=.9,want=1500))
    S.append(ph('dead_tree_trunk',(4.4,4.1,.0),rot=(0,0,.7),scale=.62,want=6000))
    S.append(ph('tree_stump_02',(-8.8,3.7,0),rot=(0,0,.4),scale=.9,want=3000))
    return S,G
def extra_tin(name,x,y,z,mat):
    o=box(name,(.2,.26,.05),(x,y,z),mat,bev=.012,seg=2); return o
def string_lights():
    """Bulbs on soft spans between hooks. Group numbers light up one after another."""
    hooks=[[(-2.22,-1.38,2.36),(-1.1,-1.38,2.36),(.12,-1.34,2.36)],[(.12,-1.34,2.36),(.12,0,2.34),(.12,1.34,2.36)],[(.12,1.34,2.36),(-1.05,1.36,2.36),(-2.2,1.34,2.36)],[(-2.2,1.34,2.36),(-2.24,0,2.34),(-2.22,-1.38,2.36)],[(.4,-1.36,2.36),(1.3,-1.36,2.36),(2.24,-1.34,2.36)],[(2.24,-1.34,2.36),(2.24,0,2.36),(2.24,1.32,2.36)]]
    out=[];cur=[]
    for g,r in enumerate(hooks):
        L=[]
        for a,b in zip(r,r[1:]):
            a,b=np.array(a),np.array(b); d=np.linalg.norm(b-a); n=max(4,int(d/.05))
            for k in range(n):
                u=k/n; p=a+(b-a)*u; p[2]-=.2*d/1.3*(1-(2*u-1)**2); L.append(p)
        L.append(np.array(r[-1])); L=np.array(L); cur.append(L)
        step=int(.2/.05)
        out+= [(float(p[0]),float(p[1]),float(p[2]-.03),g) for p in L[1::step]]
    return out,cur
