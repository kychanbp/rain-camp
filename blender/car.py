"""An original overland two door wagon. Square lamps and a slatted grille, no maker's shape or badge."""
import math, numpy as np, bmesh
from lib import *
L=4.25
def extrude(name,poly,width,mat,bev=.03,seg=3,yc=0):
    bm=bmesh.new(); vs=[bm.verts.new((x,-width/2+yc,z)) for x,z in poly]; f=bm.faces.new(vs); bm.normal_update()
    r=bmesh.ops.extrude_face_region(bm,geom=[f]); v=[e for e in r['geom'] if isinstance(e,bmesh.types.BMVert)]; bmesh.ops.translate(bm,vec=(0,width,0),verts=v)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o=link(bpy.data.objects.new(name,me)); me.materials.append(mat)
    if bev: bevel(o,bev,seg,30)
    shade(o,32); return o
def loft(name,rings,mat,bev=.05,seg=3):
    """Join rectangles (x0,x1,y,z) from bottom to top."""
    P=[];F=[]
    for r in rings:
        x0,x1,y,z=r
        P+= [(x0,-y,z),(x1,-y,z),(x1,y,z),(x0,y,z)]
    n=len(rings)
    for i in range(n-1):
        for k in range(4):
            a=i*4+k;b=i*4+(k+1)%4;F.append((a,b,b+4,a+4))
    F.append((3,2,1,0)); F.append(tuple((n-1)*4+k for k in range(4)))
    o=from_np(name,P,F,mat,smooth=False)
    if bev: bevel(o,bev,seg,20)
    shade(o,30); return o
def wheel(name,x,y,z,paint,rub,rim,lug=True,rot=None):
    r=.405; w=.3; parts=[]
    prof=[(.2,-w/2+.05),(.33,-w/2+.01),(r-.03,-w/2),(r-.008,-w/2+.03),(r,-w/2+.07),(r,w/2-.07),(r-.008,w/2-.03),(r-.03,w/2),(.33,w/2-.01),(.2,w/2-.05)]
    t=lathe(name+'t',prof,rub,n=48); parts.append(t)
    N=30; P=[];F=[]
    for i in range(N):
        a=2*math.pi*(i+.5*(i%2))/N
        for sgn in (-1,1):
            ca,sa=math.cos(a+sgn*.03),math.sin(a+sgn*.03); hw=.052; ang=.07
            base=[( -hw,-ang),(hw,-ang+.03*sgn),(hw,ang+.03*sgn),(-hw,ang)]
            k=len(P)
            for rr in (r-.01,r+.018):
                for h,da in base:
                    h2=h+sgn*.078; P.append((rr*math.cos(a+da),rr*math.sin(a+da),h2))
            F+=[(k+3,k+2,k+1,k),(k+4,k+5,k+6,k+7),(k,k+1,k+5,k+4),(k+1,k+2,k+6,k+5),(k+2,k+3,k+7,k+6),(k+3,k,k+4,k+7)]
    o=from_np(name+'l',P,F,rub,smooth=False); parts.append(o)
    # shoulder lugs
    # rim
    pr=[(0,.1),(.075,.1),(.09,.07),(.11,.02),(.235,.0),(.24,-.0),(.245,.12),(.262,.135),(.262,.145),(.235,.145),(.23,.0),(.235,-.14),(.26,-.14)]
    rimo=lathe(name+'r',[(a,b) for a,b in [(.24,-.14),(.262,-.14),(.262,.14),(.24,.13),(.235,.04),(.2,.02)]],rim,n=36); parts.append(rimo)
    parts.append(lathe(name+'h',[(.0,.095),(.06,.095),(.08,.06),(.105,.02),(.105,-.02)],rim,n=20))
    for i in range(8):
        a=2*math.pi*i/8; ca,sa=math.cos(a),math.sin(a)
        b=box(name+f's{i}',(.17,.042,.026),(ca*.17,sa*.17,.045),rim,bev=.008,seg=1,rot=(0,0,a)); parts.append(b)
    for i in range(12):
        a=2*math.pi*i/12; parts.append(cyl(name+'b',.0085,.014,(math.cos(a)*.247,math.sin(a)*.247,.142),M('steel',(.55,.56,.57),.35,.9),n=6))
    join_=joined(name,parts); join_.rotation_euler=(-math.pi/2,0,0) if y<0 else (math.pi/2,0,0); join_.location=(x,y,z); 
    return join_
def joined(name,parts):
    bpy.context.view_layer.update()
    for a in bpy.context.selected_objects: a.select_set(False)
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); o=bpy.context.view_layer.objects.active; o.name=name; return o
def seam(name,pts,gap,s=.0075):
    return sweep(name,pts,s,gap,n=6,caps=False)
def build(cx=-5.0):
    paint=M('paint',(.42,.36,.25),.24,clearcoat=1); blk=M('trim',(.018,.018,.018),.55); rub=M('tyre',(.022,.022,.023),.82); rim=M('rim',(.035,.036,.036),.42,.4)
    glass=M('glass',(.012,.015,.017),.06,transparent=.8,noshadow=1); chrome=M('steel',(.55,.56,.57),.35,.9); gap=M('gap',(.01,.01,.009),.8); lamp=M('lamp',(.8,.82,.84),.08,.2,clearcoat=1); tail=M('tail',(.5,.02,.02),.2); amber=M('amber',(.9,.42,.05),.2); inside=M('cabin',(.03,.03,.031),.8); seat=M('seat',(.06,.055,.05),.75)
    O=[]
    # lower body with wheel arches. Local x forward.
    ax=1.33; bx=-1.27; ar=.49; zs=.42
    def arc(c,r,a0,a1,n=12): return [(c+r*math.cos(a0+(a1-a0)*i/n),.40+r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)]
    poly=[(-2.1,.52),(bx-ar-.0,zs)]+[]
    poly=[(-2.08,.5),(-2.1,1.23),(.66,1.23),(1.12,1.2),(2.02,1.12),(2.08,1.02),(2.1,.55),(ax+ar+.05,.47)]+arc(ax,ar,0,math.pi)+[(bx+ar,.41)]+arc(bx,ar,0,math.pi)+[(-2.03,.46)]
    poly=poly[:8]+arc(ax,ar,0.05,math.pi-.05)+[(ax-ar-.02,.42),(bx+ar+.02,.42)]+arc(bx,ar,.05,math.pi-.05)+[(bx-ar-.02,.44),(-2.03,.46)]
    body=extrude('body',poly,1.72,paint,bev=.05,seg=4); O.append(body)
    # bonnet, raised centre
    bon=loft('bonnet',[(.76,2.0,.84,1.13),(.72,2.0,.82,1.2),(.78,1.98,.74,1.235)],paint,bev=.03,seg=3); O.append(bon)
    # cabin
    rg=[(-2.09,.63,.87,1.2),(-2.09,.6,.86,1.24),(-2.08,.5,.85,1.3),(-2.04,.08,.79,1.89),(-2.0,.02,.74,1.95)]
    cab=loft('cabin_shell',rg,paint,bev=.055,seg=4); O.append(cab)
    # side glass, inset dark panes
    def pane(name,pts,y):
        P=[(x,y,z) for x,z in pts]; o=from_np(name,P,[tuple(range(len(P)))],glass,smooth=False); return o
    def shift(x,z,side): return x,z
    def inwall(x,z): return .85-(z-1.3)*.11   # y of the sloped side
    for s in (-1,1):
        for nm,q in (('d',[(-.48,1.3),(.42,1.3),(.15,1.82),(-.48,1.82)]),('q',[(-1.9,1.3),(-.6,1.3),(-.6,1.82),(-1.86,1.82)])):
            P=[(x,s*(inwall(x,z)+.006),z) for x,z in q]
            o=from_np('sg'+nm,P,[(0,1,2,3) if s<0 else (3,2,1,0)],glass,smooth=False); O.append(o)
            q2=np.array(q+[q[0]]); pts=np.array([(x,s*(inwall(x,z)+.008),z) for x,z in fillet(q,.05,closed=True,seg=3)]); pts=np.vstack([pts,pts[0]]); O.append(sweep('sgf',pts,.012,blk,n=6,caps=False))
    # windscreen, raked
    P=[(.6,-.78,1.32),(.6,.78,1.32),(.17,.70,1.84),(.17,-.70,1.84)]
    O.append(from_np('ws',P,[(0,1,2,3)],glass,smooth=False)); 
    pts=fillet(P,.05,closed=True,seg=3); pts=np.vstack([pts,pts[0]])+np.array([.014,0,.012]); O.append(sweep('wsf',pts,.014,blk,n=6,caps=False))
    # wiper
    for y in (-.3,.28): O.append(sweep('wipe',np.linspace((.62,y,1.33),(.42,y+.3,1.58),4),.006,blk,n=5))
    # seams: doors and bonnet
    for s in (-1,1):
        y=s*.862
        O.append(seam('sd',np.array([(.56,y,1.2),(.6,y,.9),(.55,y,.46)]),gap))
        O.append(seam('sd',np.array([(-.55,y,1.2),(-.55,y,.46)]),gap))
        O.append(seam('sd',np.array([(-.55,y,.46),(.55,y,.46)]),gap))
        O.append(box('handle',(.17,.03,.03),(-.36,s*.875,1.08),blk,bev=.01,seg=2))
        O.append(sweep('sill',np.array([(-.95,s*.86,.38),(.85,s*.86,.38)]),.042,blk,n=10))
        # flares
        for c in (ax,bx):
            p=[(c+.57*math.cos(a),s*.915,.40+.57*math.sin(a)) for a in np.linspace(-.05,math.pi+.05,22)]
            O.append(sweep('flare',p,.05,blk,n=10,flat=(.65,1.35)))
        # side repeater, mirror
        O.append(box('rep',(.05,.012,.02),(1.0,s*.862,1.02),amber,bev=.004,seg=1))
        O.append(box('mir',(.09,.21,.15),(.55,s*1.04,1.38),blk,bev=.03,seg=3)); O.append(sweep('mira',np.array([(.56,s*.87,1.3),(.55,s*.96,1.35)]),.012,blk,n=6))
    # grille: horizontal slats in a dark frame
    O.append(box('grb',(.04,1.26,.33),(2.1,0,.87),blk,bev=.02))
    for i,z in enumerate(np.linspace(.76,.98,5)):
        O.append(box(f'grs{i}',(.03,1.08,.022),(2.13,0,z),paint,bev=.008,seg=2))
    # lamps: square with a soft corner
    for s in (-1,1):
        O.append(box('hl',(.05,.25,.2),(2.11,s*.72,.89),blk,bev=.03,seg=3))
        O.append(box('hlg',(.02,.2,.15),(2.14,s*.72,.89),lamp,bev=.018,seg=3))
        O.append(box('hln',(.012,.17,.018),(2.152,s*.72,.83),amber,bev=.004,seg=1))
    # bumper with a winch bar
    O.append(box('bump',(.26,1.84,.2),(2.17,0,.58),blk,bev=.05,seg=3))
    O.append(box('bumpl',(.2,.5,.1),(2.23,0,.46),M('alublack',(.02,.02,.022),.45,.6),bev=.02))
    p=fillet([(2.2,-.6,.66),(2.42,-.46,.68),(2.46,-.4,.98),(2.46,.4,.98),(2.42,.46,.68),(2.2,.6,.66)],.08,seg=4); O.append(sweep('bar',p,.03,blk,n=10))
    for y in (-.25,.25): O.append(cyl('hk',.035,.05,(2.3,y,.59),M('valve'),rot=(math.pi/2,0,0),n=10))
    # snorkel
    p=fillet([(1.0,.885,1.1),(.74,.93,1.2),(.56,.9,1.36),(.2,.76,1.86),(.17,.74,1.98)],.08,seg=5); O.append(sweep('snork',p,.03,blk,n=10)); O.append(box('snh',(.13,.08,.07),(.16,.74,2.01),blk,bev=.022,seg=2))
    # roof rack and a soft top bag
    for s in (-1,1): O.append(box('rail',(2.3,.04,.03),(-.95,s*.72,2.03),M('alublack'),bev=.008,seg=1))
    for x in np.linspace(-1.95,.05,6): O.append(box('barx',(.05,1.5,.025),(x,0,2.04),M('alublack'),bev=.008,seg=1))
    for x in (-1.6,.0-.2):
        for s in (-1,1): O.append(box('foot',(.06,.05,.09),(x,s*.72,1.98),blk))
    bagm=M('roofbag',(.02,.02,.022),.5,tile='fabric')
    Q=loft('rbag',[(-1.86,-.0,.72,2.07),(-1.82,-.04,.74,2.16),(-1.85,-.02,.72,2.26),(-1.8,-.08,.62,2.3)],bagm,bev=.05,seg=3); O.append(Q)
    # rear: open space behind the wheels. Tail lamps are small verticals.
    for s in (-1,1):
        O.append(box('tl',(.02,.06,.13),(-2.09,s*.79,.98),tail,bev=.012))
    O.append(box('rbump',(.16,1.82,.13),(-2.1,0,.56),blk,bev=.04))
    # the rear opening: dark boxed interior
    O.append(box('rfloor',(1.36,1.46,.04),(-1.42,0,.86),inside))
    O.append(box('rwall',(.05,1.46,1.0),(-.74,0,1.3),inside))
    pass
    O.append(box('rceil',(1.34,1.46,.04),(-1.42,0,1.82),inside))
    # the tail face has a big opening: cut it out of the solid body and roof
    cut=box('cutter',(1.5,1.5,.98),(-1.5,0,1.36),inside)
    cut2=box('cutter2',(2.5,1.5,.56),(-.8,0,1.6),inside)   # hollow cabin, so the windows are real
    for o_ in (body,cab):
        for c_ in (cut,cut2):
            m_=o_.modifiers.new('c','BOOLEAN'); m_.object=c_; m_.operation='DIFFERENCE'; m_.solver='MANIFOLD' if hasattr(m_,'solver') else 'EXACT'; apply(o_)
        shade(o_,32)
    bpy.data.objects.remove(cut); bpy.data.objects.remove(cut2)
        # stored bags and boxes
    orng=M('case',(.5,.16,.04),.62,tile='fabric'); tan=M('tan',(.36,.3,.2),.68,tile='fabric')
    # a lived-in back: shelf, amber strip, hanging tools, power box lives in gear.py
    wood=M('wood',(.42,.24,.1),.5,tile='wood')
    O.append(box('rshelf',(.5,1.4,.03),(-1.72,0,1.5),wood,bev=.006,seg=1))
    O.append(box('ledsh',(.02,1.3,.015),(-1.96,0,1.482),M('led',(.9,.5,.15),.3,emit='warm')))
    O.append(box('rail2',(.012,1.3,.012),(-2.02,0,1.75),M('steel',(.55,.56,.57),.35,.9)))
    red=M('valve'); 
    for i,y in enumerate((-.5,-.34,-.2,-.03,.14,.3,.46)):
        O.append(cyl('hook',.0025,.05,(-2.02,y,1.72),M('steel'),n=5))
        if i in (1,3,5):
            O.append(box('hutens',(.012,.045 if i==1 else .03,.2),(-2.02,y,1.59),M('steel'),bev=.003,seg=1))
        else:
            O.append(sphere('chili',.021,(-2.02,y,1.62),M('case'),(.8,.8,2.1),10))
    for i,(x,y,z,sz,c) in enumerate(((-1.72,-.5,1.6,(.2,.16,.18),'tan'),(-1.72,-.26,1.58,(.18,.2,.14),'case'),(-1.75,.42,1.6,(.2,.26,.17),'tan'))):
        O.append(box('sbox',sz,(x,y,z),M(c),bev=.03,seg=2))
    # rear seats seen through the glass
    for s in (-1,1):
        O.append(box('seat',(.5,.48,.14),(.0,s*.42,.8),seat,bev=.04,seg=3)); O.append(box('back',(.14,.48,.56),(-.25,s*.42,1.08),seat,bev=.05,seg=3))
    O.append(box('dash',(.3,1.5,.2),(.62,0,1.18),inside,bev=.03))
    # wheels
    W=[]
    for x,y in ((ax,-.8),(ax,.8),(bx,-.8),(bx,.8)): W.append(wheel('wh',x,y,.41,paint,rub,rim))
    O+=W
    # the rear gate lifts up like a porch over the kitchen, and the spare swings out on a side arm
    gate=box('rgate',(.06,1.5,1.02),(0,0,0),paint,bev=.02); gg=box('rgg',(.012,1.0,.46),(.036,0,.2),glass); inn=box('rgin',(.01,1.36,.9),(-.034,0,0),inside)
    gv=Matrix.Translation((-2.1,0,1.9))@Matrix.Rotation(math.radians(74),4,'Y')@Matrix.Translation((0,0,-.52))
    bpy.context.view_layer.update()
    for p_ in (gate,gg,inn): p_.matrix_world=gv@p_.matrix_world
    O+=[gate,gg,inn]
    sp=wheel('spare',0,0,0,paint,rub,rim); sp.rotation_euler=(math.pi/2,0,0); sp.location=(-2.48,-1.0,.72); O.append(sp)
    O.append(sweep('sparm',np.array([(-2.1,-.8,.62),(-2.42,-.86,.7)]),.03,blk,n=8))
    # amber bar in the open back, and a soft strip under the roof
    bar=box('ledbar',(.02,1.2,.018),(-2.75,0,2.0),M('led',(.9,.5,.15),.3,emit='warm')); O.append(bar)
    bar2=box('ledbar2',(.02,1.2,.014),(-1.8,0,1.79),M('led'),); O.append(bar2)
    return O,cx
def place(objs,cx):
    W=Matrix.Translation((cx,0,0))@Matrix.Rotation(math.pi,4,'Z')
    bpy.context.view_layer.update()
    for o in objs: o.matrix_world=W@o.matrix_world
