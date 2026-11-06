"""Cut a forearm and hand out of a Microsoft Rocketbox avatar (MIT), curl the fingers into a grip and write it for the game."""
import bpy, math, os, sys, json, numpy as np
from mathutils import Vector, Matrix, Quaternion
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); RB=os.path.expanduser('~/soundbath_rooms/data/rb/Male_Adult_05'); OUT=ROOT+'/web/assets/hands'; os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=RB+'/Male_Adult_05_facial.fbx')
A=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; M=[o for o in bpy.data.objects if o.type=='MESH'][0]
print('mats',[m.name for m in M.data.materials]); print('bones',[b.name for b in A.data.bones if 'R ' in b.name][:24])
A.animation_data_clear(); M.shape_key_clear() if M.data.shape_keys else None
bpy.context.view_layer.objects.active=A; A.select_set(True); bpy.ops.object.mode_set(mode='POSE')
for b in A.pose.bones: b.rotation_mode='QUATERNION'; b.rotation_quaternion=(1,0,0,0)
meta={}; blobs=[]; off=0
def put(a,t):
    global off
    b=np.asarray(a,t).tobytes(); b+=b'\0'*((4-len(b)%4)%4); blobs.append(b); o=off; off+=len(b); return o
def export(side,pose,curl,thumb):
    P=A.pose.bones; pre=f'Bip01 {side} Finger'; AW3=A.matrix_world.to_3x3(); B=A.data.bones
    head=lambda n:(A.matrix_world@B[n].head_local)
    h0=(head(pre+'2')-head(f'Bip01 {side} Hand')).normalized(); down=Vector((0,0,-1)); n0=(down-h0*down.dot(h0)).normalized()
    for i in range(5):
        ch=[pre+str(i),pre+f'{i}1',pre+f'{i}2']; ch=[c for c in ch if c in B]
        for j,c in enumerate(ch):
            d=(head(ch[j+1])-head(c)).normalized() if j+1<len(ch) else (head(c)-head(ch[j-1])).normalized()
            tw=(n0+h0*.6).normalized() if i==0 else n0
            ax=d.cross(tw).normalized(); loc=(AW3@B[c].matrix_local.to_3x3()).inverted()@ax
            ang=(curl[3] if i==0 else curl[j]); P[c].rotation_quaternion=Quaternion(loc,ang)
    bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get(); e=M.evaluated_get(dg); me=e.to_mesh(); me.calc_loop_triangles()
    W=M.data; names={g.index:g.name for g in M.vertex_groups}
    keep=np.zeros(len(W.vertices),bool)
    pick=[f'Bip01 {side} Forearm',f'Bip01 {side} Hand',pre]
    for v in W.vertices:
        s=0
        for g in v.groups:
            n=names[g.group]
            if any(n.startswith(p) for p in pick): s+=g.weight
        keep[v.index]=s>.5
    n=len(me.vertices); p=np.zeros(n*3,'f4'); me.vertices.foreach_get('co',p); p=p.reshape(-1,3)
    mw=np.array(M.matrix_world); p=p@mw[:3,:3].T+mw[:3,3]
    nt=len(me.loop_triangles); ti=np.zeros(nt*3,'i4'); li=np.zeros(nt*3,'i4'); me.loop_triangles.foreach_get('vertices',ti); me.loop_triangles.foreach_get('loops',li); ti=ti.reshape(-1,3); li=li.reshape(-1,3)
    uv=np.zeros(len(me.loops)*2,'f4'); me.uv_layers[0].data.foreach_get('uv',uv); uv=uv.reshape(-1,2); nr=np.zeros(len(me.loops)*3,'f4'); me.corner_normals.foreach_get('vector',nr); nr=nr.reshape(-1,3)@mw[:3,:3].T; nr/=np.linalg.norm(nr,axis=1,keepdims=True)+1e-9
    tk=keep[ti].all(1); ti=ti[tk]; li=li[tk]
    # frame: wrist at origin, forearm along -x, palm facing down, in metres
    AW=A.matrix_world; h=(AW@P[f'Bip01 {side} Hand'].head); el=(AW@P[f'Bip01 {side} Forearm'].head); mid=(AW@P[f'Bip01 {side} Finger2'].head); idx=(AW@P[f'Bip01 {side} Finger1'].head); pk=(AW@P[f'Bip01 {side} Finger4'].head)
    x=(mid-h).normalized(); s_=(idx-pk).normalized(); z=x.cross(s_).normalized(); y=z.cross(x).normalized(); R=np.array([x,y,z]); o=np.array(h)
    pc=(p[ti.ravel()]-o)@R.T; nc=nr[li.ravel()]@R.T; uc=uv[li.ravel()]; uc[:,1]=1-uc[:,1]
    # keep 26 cm of forearm
    tri=pc.reshape(-1,3,3); ok=(tri[:,:,0]>-.075).all(1); ok3=np.repeat(ok,3); pc=pc[ok3]; nc=nc[ok3]; uc=uc[ok3]
    meta[f'{side}_{pose}']=dict(nv=len(pc),p=put(pc,'f4'),n=put(nc,'f4'),u=put(uc,'f4')); print(side,pose,len(pc)//3,np.ptp(pc,axis=0),flush=True)
    e.to_mesh_clear()
for s in 'RL':
    export(s,'grip',(.95,1.3,.9,.7),0); export(s,'relax',(.3,.38,.25,.2),0)
bpy.ops.object.mode_set(mode='OBJECT')
open(OUT+'/hands.bin','wb').write(b''.join(blobs)); json.dump(meta,open(OUT+'/hands.json','w'))
import shutil
print('HANDS DONE')
