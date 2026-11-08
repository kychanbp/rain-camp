"""An original two storey air frame tent: thick black air beams, charcoal fabric, mesh windows."""
import math, numpy as np
from lib import *
A=2.4; B=1.5; R=.155; Z0=.14; Z1=1.32; Z2=2.5; Z3=3.42; DOOR=.25
def build():
    beam=M('beam',(.055,.057,.062),.36); fab=M('fabric',(.035,.037,.041),.62,tile='fabric'); roof=M('roof',(.05,.054,.062),.5,tile='fabric')
    tape=M('tape',(.008,.008,.009),.5); net=M('net',(.012,.012,.014),.6,transparent=.3,noshadow=1); wall=M('wallin',(.05,.05,.052),.75,tile='fabric')
    red=M('valve',(.55,.03,.02),.4); orange=M('rope',(.8,.27,.04),.7); peg=M('peg',(.9,.32,.05),.45); alu=M('alu',(.62,.63,.64),.42,.9); dark=M('alublack',(.02,.02,.022),.45,.6)
    T=[]
    def ring(z,name,r=R,fr=.46):
        p=fillet([(-A,-B,z),(A,-B,z),(A,B,z),(-A,B,z)],fr,closed=True,seg=10); T.append(sweep(name,p,r,beam,closed=True,n=16))
    ring(Z0,'b_low'); ring(Z2,'b_top')
    # mid beam runs on the back, right end and right front bay. The car end and the door stay open.
    p=fillet([(DOOR,-B,Z1),(A,-B,Z1),(A,B,Z1),(-A,B,Z1)],.46,seg=9); T.append(sweep('b_mid',p,R*.92,beam,n=16))
    for x,y in ((-A,-B),(A,-B),(A,B),(-A,B),(DOOR,-B),(DOOR,B),(-A,0.0) if False else (DOOR,B)):
        p=np.array([(x,y,Z0+.0+k*(Z2-Z0)/8) for k in range(9)]); T.append(sweep(f'b_v{len(T)}',p,R,beam,n=16))
    # roof ribs
    rx=.62
    for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1)):
        p=fillet([(sx*(A-.1),sy*(B-.1),Z2),(sx*rx,0,Z3-.03)],.1,seg=1); pts=np.linspace(p[0],p[-1],10); T.append(sweep(f'b_r{sx}{sy}',pts,.085,beam,n=12))
    pts=np.linspace((-rx,0,Z3-.03),(rx,0,Z3-.03),6); T.append(sweep('b_ridge',pts,.085,beam,n=12))
    # seams and webbing on the air beams
    web=M('webbing',(.13,.135,.14),.55)
    for x in (-1.6,-.6,.6,1.6):
        for y,z in ((-B,Z2),(B,Z2),(-B,Z0),(B,Z0)):
            T.append(sweep('wb',[(x,y+.163*math.cos(a),z+.163*math.sin(a)) for a in np.linspace(0,6.28,17)],.006,web,n=5,flat=(2.6,1),caps=False))
    for y in (-.8,.8):
        for x,z in ((-A,Z2),(A,Z2),(A,Z0)):
            T.append(sweep('wb',[(x+.163*math.cos(a),y,z+.163*math.sin(a)) for a in np.linspace(0,6.28,17)],.006,web,n=5,flat=(1,2.6),caps=False))
    for (x,y) in ((-A,-B),(A,-B),(A,B),(-A,B),(DOOR,-B)):
        for z in (.8,1.85):
            T.append(sweep('wb',[(x+.163*math.cos(a),y+.163*math.sin(a),z) for a in np.linspace(0,6.28,17)],.006,web,n=5,flat=(2.6,1),caps=False))
    # walls: outer skin sits at the beam centre line
    e=.0
    F=[]
    F.append(panel('w_back',[(A,B,Z0),(-A,B,Z0),(-A,B,Z2),(A,B,Z2)],fab,70,34,sag=.06,wr=.012,seed=3))
    F.append(panel('w_rend',[(A,-B,Z0),(A,B,Z0),(A,B,Z2),(A,-B,Z2)],fab,50,34,sag=.06,wr=.012,seed=4))
    # front right bay: two mesh windows framed by fabric
    fy=-B+.02
    def windowed(name,x0,x1,z0,z1,seed):
        m=.17
        F.append(panel(name+'t',[(x0,fy,z1-m),(x1,fy,z1-m),(x1,fy,z1),(x0,fy,z1)],fab,30,4,sag=0,wr=.004,seed=seed))
        F.append(panel(name+'b',[(x0,fy,z0),(x1,fy,z0),(x1,fy,z0+m),(x0,fy,z0+m)],fab,30,4,sag=0,wr=.004,seed=seed+1))
        F.append(panel(name+'l',[(x0,fy,z0+m),(x0+m,fy,z0+m),(x0+m,fy,z1-m),(x0,fy,z1-m)],fab,4,10,sag=0,wr=.002,seed=seed+2))
        F.append(panel(name+'r',[(x1-m,fy,z0+m),(x1,fy,z0+m),(x1,fy,z1-m),(x1-m,fy,z1-m)],fab,4,10,sag=0,wr=.002,seed=seed+3))
        g=panel(name+'n',[(x0+m,fy+.01,z0+m),(x1-m,fy+.01,z0+m),(x1-m,fy+.01,z1-m),(x0+m,fy+.01,z1-m)],net,8,6,sag=.015,wr=.002,seed=seed+4); g['nobake']=1
    windowed('f1',DOOR,A,Z0,Z1,20); windowed('f2',DOOR,A,Z1,Z2,30)
    # small window on the back for air
    # car end: side flaps and a valance above the car
    F.append(panel('e_a',[(-A,B,Z0),(-A,1.02,Z0),(-A,1.02,Z2),(-A,B,Z2)],fab,10,30,sag=.02,wr=.008,seed=7))
    F.append(panel('e_b',[(-A,-1.02,Z0),(-A,-B,Z0),(-A,-B,Z2),(-A,-1.02,Z2)],fab,10,30,sag=.02,wr=.008,seed=8))
    F.append(panel('e_c',[(-A,1.02,2.02),(-A,-1.02,2.02),(-A,-1.02,Z2),(-A,1.02,Z2)],fab,24,8,sag=.02,wr=.01,seed=9))
    # sleeve to the car roof keeps the rain off the kitchen
    F.append(panel('e_d',[(-A,1.04,2.34),(-A,-1.04,2.34),(-A-.62,-.98,1.98),(-A-.62,.98,1.98)],fab,24,10,sag=.04,wr=.012,seed=10))
    F.append(panel('e_e',[(-A,1.04,2.34),(-A-.62,.98,1.98),(-A-.62,.98,.5),(-A,1.04,.3)],fab,10,16,sag=.05,wr=.016,seed=16,flip=True))
    F.append(panel('e_f',[(-A,-1.04,2.34),(-A,-1.04,.3),(-A-.62,-.98,.5),(-A-.62,-.98,1.98)],fab,16,10,sag=.05,wr=.016,seed=17,flip=True))
    # door flaps tied back at each side of the opening, with a zip line
    F.append(panel('dfl',[(-A+.1,-B-.03,Z0+.1),(-A+.52,-B-.03,Z0+.1),(-A+.4,-B-.03,Z2-.12),(-A+.1,-B-.03,Z2-.12)],fab,8,30,sag=-.05,wr=.018,folds=.03,seed=44))
    F.append(panel('dfr',[(DOOR-.5,-B-.03,Z0+.1),(DOOR-.1,-B-.03,Z0+.1),(DOOR-.1,-B-.03,Z2-.12),(DOOR-.4,-B-.03,Z2-.12)],fab,8,30,sag=-.05,wr=.018,folds=.03,seed=45))
    for x in (-A+.34,DOOR-.33): T.append(sweep('tie',[(x-.2,-B-.1,1.3),(x,-B-.14,1.28),(x+.2,-B-.1,1.3)],.012,tape,n=6))
    # door flap rolled above the opening
    roll=sweep('roll',np.linspace((-A+.15,-B-.02,Z2-.2),(DOOR-.15,-B-.02,Z2-.2),12),.085,fab,n=12); F.append(roll)
    for x in (-1.7,-.5): T.append(box(f'strap{x}',(.03,.012,.3),(x,-B-.11,Z2-.13),orange and tape))
    # hip roof with slack cloth and a skirt
    S=[]
    S.append(panel('r_f',[(-A-.13,-B-.13,Z2+.05),(A+.13,-B-.13,Z2+.05),(rx,0,Z3),(-rx,0,Z3)],roof,60,24,sag=.11,wr=.018,seed=11))
    S.append(panel('r_b',[(A+.13,B+.13,Z2+.05),(-A-.13,B+.13,Z2+.05),(-rx,0,Z3),(rx,0,Z3)],roof,60,24,sag=.11,wr=.018,seed=12))
    S.append(panel('r_r',[(A+.13,-B-.13,Z2+.05),(A+.13,B+.13,Z2+.05),(rx,0.02,Z3),(rx,-0.02,Z3)],roof,40,24,sag=.11,wr=.018,seed=13))
    S.append(panel('r_l',[(-A-.13,B+.13,Z2+.05),(-A-.13,-B-.13,Z2+.05),(-rx,-0.02,Z3),(-rx,0.02,Z3)],roof,40,24,sag=.11,wr=.018,seed=14))
    for nm,c in (('s_f',[(-A-.14,-B-.14,Z2-.1),(A+.14,-B-.14,Z2-.1),(A+.14,-B-.14,Z2+.06),(-A-.14,-B-.14,Z2+.06)]),('s_b',[(A+.14,B+.14,Z2-.1),(-A-.14,B+.14,Z2-.1),(-A-.14,B+.14,Z2+.06),(A+.14,B+.14,Z2+.06)]),('s_r',[(A+.14,-B-.14,Z2-.1),(A+.14,B+.14,Z2-.1),(A+.14,B+.14,Z2+.06),(A+.14,-B-.14,Z2+.06)]),('s_l',[(-A-.14,B+.14,Z2-.1),(-A-.14,-B-.14,Z2-.1),(-A-.14,-B-.14,Z2+.06),(-A-.14,B+.14,Z2+.06)])):
        S.append(panel(nm,c,roof,40,3,sag=0,wr=.003,seed=15))
    # roof seams
    sm=M('webbing')
    for sx in (-1,1):
        S.append(sweep('rs',np.linspace((sx*(A-.1),-B-.09,Z2+.09),(sx*rx,-.0,Z3+.03),8),.01,sm,n=5)); S.append(sweep('rs',np.linspace((sx*(A-.1),B+.09,Z2+.09),(sx*rx,.0,Z3+.03),8),.01,sm,n=5))
    # valves and tiny details
    for x,y,z,ry in ((A+.12,-1.1,.5,1),(1.0,-B-.12,.2,0),(-1.8,B+.12,.2,0)):
        T.append(cyl('v',.03,.03,(x,y,z),red,rot=(math.pi/2,0,0) if ry==0 else (0,math.pi/2,0),n=12))
    # guy lines and pegs
    Gs=[]
    for (x,y,px,py) in ((A,-B,A+1.5,-B-1.1),(A,B,A+1.5,B+1.1),(-A,-B,-A+.2,-B-1.6),(-.2,B,-.2,B+1.7)):
        Gs.append(sweep('guy',np.linspace((x,y,Z2-.1),(px,py,.05),6),.0035,orange,n=5))
        Gs.append(box('peg',(.012,.03,.2),(px,py,.07),peg,rot=(.25,0,0)))
    # second storey, bay right of the door. A frames as in a folding platform.
    P=[]
    x0,x1,y0,y1,zp=DOOR+.06,A-.12,-B+.1,B-.1,1.28
    for i,y in enumerate(np.linspace(y0+.02,y1-.02,12)):
        P.append(box(f'slat{i}',(x1-x0,.12,.024),((x0+x1)/2,y,zp),dark,bev=.004,seg=1))
    for x in (x0+.02,x1-.02):
        P.append(cyl('rail',.018,y1-y0,(x,(y0+y1)/2,zp-.03),alu,rot=(math.pi/2,0,0),n=10))
    for y in (y0+.02,y1-.02):
        P.append(cyl('rail',.018,x1-x0,((x0+x1)/2,y,zp-.03),alu,rot=(0,math.pi/2,0),n=10))
    def strut(a,b,r=.014):
        a=np.array(a);b=np.array(b); pts=np.linspace(a,b,3); return sweep('strut',pts,r,alu,n=8)
    for x in (x0+.05,(x0+x1)/2,x1-.05):
        for y in (y0+.05,y1-.05):
            P.append(strut((x-.34,y,0.02),(x,y,zp-.04))); P.append(strut((x+.34,y,0.02),(x,y,zp-.04)))
    # ladder to the upper bed
    lx=DOOR+.02
    for y in (-.58,-.2):
        P.append(strut((lx-.18,y,.02),(lx+.02,y,zp+.02),.016))
    for z in (.3,.58,.86,1.12):
        k=z/(zp+.02); P.append(cyl('rung',.016,.42,(lx-.18+.2*k,-.39,z),alu,rot=(math.pi/2,0,0),n=8))
    # mattress and sleeping bag on the upper bed
    mat_=M('mattress',(.42,.38,.27),.8); bag=M('bag',(.45,.28,.09),.72,tile='cloth'); pil=M('pillow',(.62,.58,.5),.85)
    P.append(box('mattress',(1.9,.78,.07),((x0+x1)/2,.42,zp+.05),mat_,bev=.03,seg=3))
    q=panel('sleepbag',[(x0+.48,.03,zp+.1),(x1-.1,.03,zp+.1),(x1-.1,.8,zp+.1),(x0+.48,.8,zp+.1)],bag,36,20,sag=-.1,wr=.01,seed=40); P.append(q)
    P.append(sphere('pil',.2,(x0+.26,.42,zp+.15),pil,scale=(.8,1.5,.45)))
    # low dog bed under the platform
    lm=M('canvas',(.46,.39,.25),.86,tile='cloth')
    x=1.35; y=.3
    P.append(panel('dogbed',[(x-.55,y-.38,.2),(x+.55,y-.38,.2),(x+.55,y+.38,.2),(x-.55,y+.38,.2)],lm,20,14,sag=.07,wr=.006,seed=41,flip=False))
    for sx in (-1,1):
        P.append(strut((x+sx*.55,y-.38,.2),(x+sx*.55,y+.38,.2),.012))
        for sy in (-1,1): P.append(strut((x+sx*.55,y+sy*.38,.2),(x-sx*.3,y-sy*.25,.02),.01))
    for sy in (-1,1): P.append(strut((x-.55,y+sy*.38,.2),(x+.55,y+sy*.38,.2),.012))
    return dict(beams=T,fabric=F,roof=S,guy=Gs,inside=P)
