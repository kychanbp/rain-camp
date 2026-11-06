"""Build the whole camp, bake three kinds of light, and write web/assets/camp."""
import bpy,sys,os,math,json,numpy as np,shutil
sys.path.insert(0,os.path.dirname(__file__))
from lib import *
import tent,car,gear
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); OUT=ROOT+'/web/assets/camp'; G_=ROOT+'/data/gen'; os.makedirs(OUT,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SAMPLES=int(args[0]) if args else 64; LM=int(args[1]) if len(args)>1 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils; addon_utils.enable('cycles'); addon_utils.enable('io_scene_gltf2')
s=bpy.context.scene; s.render.engine='CYCLES'; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
for d in p.devices: d.use=True
s.cycles.device='GPU'; s.cycles.samples=SAMPLES; s.cycles.use_denoising=False; s.cycles.max_bounces=4; s.cycles.diffuse_bounces=3
T=tent.build(); O,cx=car.build(); car.place(O,cx)
S,G=gear.build()
bulbs,wires=gear.string_lights()
blk=M('wire',(.01,.01,.01),.6)
for i,r in enumerate(wires):
    S.append(sweep(f'wire{i}',r,.0035,blk,n=5))
# emit: bulbs as small spheres only during the bake (the game draws its own)
bake_b=[]
bm=M('bakebulb',(.9,.7,.4),.5)
for x,y,z,g in bulbs[::2]:
    o=sphere('bb',.03,(x,y,z-.025),bm,seg=8); bake_b.append(o)
# ground for the bake
ground=M('ground',(.14,.085,.05),.85)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=2,y_subdivisions=2,size=44,location=(-2,-1,0)); gr=bpy.context.object; gr.name='ground'; gr.data.materials.append(ground)
gr.data.uv_layers.new(name='UVMap'); 
for li,l in enumerate(gr.data.loops):
    v=gr.data.vertices[l.vertex_index].co; gr.data.uv_layers[0].data[li].uv=(v.x/44+.5,v.y/44+.5)
# near trees block the sky
W=json.load(open(ROOT+'/web/assets/world.json')); TR=json.load(open(ROOT+'/web/assets/trees/trees.json')); bin_=open(ROOT+'/web/assets/trees/trees.bin','rb').read()
def tree_mesh(key,part):
    e=TR[key][part]; P=np.frombuffer(bin_,'f4',e['nv']*3,e['p']).reshape(-1,3); I=np.frombuffer(bin_,'u4',e['ni'],e['i']).reshape(-1,3); return P,I
tm=M('barkbake',(.15,.09,.06),.8); cardm=bpy.data.materials.new('cardbake'); cardm.use_nodes=True
nt=cardm.node_tree; b=nt.nodes['Principled BSDF']; mix=nt.nodes.new('ShaderNodeMixShader'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); nt.links.new(tr.outputs[0],mix.inputs[1]); nt.links.new(b.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],nt.nodes['Material Output'].inputs[0]); mix.inputs[0].default_value=.55
b.inputs['Base Color'].default_value=(.08,.11,.05,1)
nb=[]
for t in W['trees']+[dict(a,k=a['k']+100) for a in W['saps']]:
    if (t['x']+2)**2+(t['z']-1)**2>38**2: continue
    sap=t['k']>=100; key=('sap%d'%(t['k']-100)) if sap else 'pine%d'%t['k']
    parts=[('cards',cardm)]+([('trunk',tm)] if not sap else [])+[('bark',tm)]
    for part,mt in parts:
        P,I=tree_mesh(key,part)
        if part=='cards': I=I.reshape(-1,3)
        if not sap and part=='trunk': pass
        me=bpy.data.meshes.new('t'); me.from_pydata(P.tolist(),[],I.tolist()); me.materials.append(mt); o=bpy.data.objects.new('t',me); s.collection.objects.link(o)
        # three x,y,z to blender x,-z,y
        c,sn=math.cos(t['r']),math.sin(t['r']); sc=t['s']
        # game rotates about y by r
        o.matrix_world=Matrix.Translation((t['x'],-t['z'],0))@Matrix.Rotation(t['r'],4,'Z')@Matrix.Scale(sc,4)@Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
        nb.append(o)
print('objects',len(s.objects),flush=True)
bpy.context.view_layer.update()
# what gets baked
groups=[]
for k,ls in (('beams',T['beams']),('fabric',T['fabric']),('roof',T['roof']),('guy',T['guy']),('inside',T['inside']),('car',O),('gear',S)):
    for o in ls: groups.append((k,None,o))
for n,ls in G.items():
    for o in ls: groups.append(('move',n,o))
real=[g for g in groups if g[2].type=='MESH' and g[2].name in bpy.data.objects]
nobake=lambda o:any(MATS.get(m.name,{}).get('transparent') for m in o.data.materials if m) 
for k,n,o in real:
    if nobake(o): o.visible_shadow=False; o.visible_diffuse=False; o.visible_glossy=False
meshes=[o for k,n,o in real if not nobake(o)]
for o in meshes:
    if 'bk' not in o.data.color_attributes: o.data.color_attributes.new('bk','FLOAT_COLOR','POINT')
    o.data.color_attributes.active_color=o.data.color_attributes['bk']
print('bake objects',len(meshes),sum(len(o.data.vertices) for o in meshes),flush=True)
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']
def setem(name,col,st):
    m=bpy.data.materials.get(name)
    if not m: return
    b=m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value=(*col,1); b.inputs['Emission Strength'].default_value=st
fireM=M('bakefire',(.9,.4,.1),.5); fobj=sphere('bakefire',.08,(-.77,-.72,.56),fireM,(1.8,.9,1.2),8)
def channel(sky,warm,fire,tent_on=True):
    bg.inputs[0].default_value=(1,1,1,1); bg.inputs[1].default_value=sky
    setem('bakebulb',(1,.62,.28),warm*60); setem('lampg',(1,.66,.3),warm*45); setem('led',(1,.5,.13),warm*90); setem('bakefire',(1,.45,.15),fire*30); setem('display',(1,.55,.2),warm*8)
def vertex_bake():
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},target='VERTEX_COLORS',use_clear=True,margin=0)
    res={}
    for o in meshes:
        a=np.zeros(len(o.data.vertices)*4,'f4'); o.data.color_attributes['bk'].data.foreach_get('color',a); res[o.name]=a.reshape(-1,4)[:,:3].mean(1).copy() if False else a.reshape(-1,4)[:,:3].copy()
    return res
def ground_bake():
    img=bpy.data.images.get('gbake') or bpy.data.images.new('gbake',LM,LM,float_buffer=True)
    nt=ground.node_tree; 
    for n in list(nt.nodes):
        if n.type=='TEX_IMAGE': nt.nodes.remove(n)
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=img; nt.nodes.active=t
    bpy.ops.object.select_all(action='DESELECT'); gr.select_set(True); bpy.context.view_layer.objects.active=gr
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},target='IMAGE_TEXTURES',use_clear=True,margin=2)
    a=np.zeros(LM*LM*4,'f4'); img.pixels.foreach_get(a); return a.reshape(LM,LM,4)[:,:,:3].copy()
CH={}
for nm,(a,b_,c) in (('sky',(1,0,0)),('warm',(0,1,0)),('fire',(0,0,1))):
    channel(a,b_,c); print('bake',nm,flush=True); CH[nm]=(vertex_bake(),ground_bake())
# ground with no tent: used while the tent still lies flat
channel(1,0,0)
for k,ls in T.items():
    for o in ls:
        if o.name in bpy.data.objects: o.hide_render=True
GN=ground_bake()
for k,ls in T.items():
    for o in ls:
        if o.name in bpy.data.objects: o.hide_render=False
print('baked',flush=True)
# ---- export
scale=dict(sky=1.)
vals={c:np.concatenate([v.ravel() for v in CH[c][0].values()]) for c in CH}
for c in ('warm','fire'): scale[c]=float(max(np.percentile(vals[c],99.7),1e-3))
print('scale',scale,flush=True)
def b2t(a): return np.stack([a[...,0],a[...,2],-a[...,1]],-1)
buckets={}
dg=bpy.context.evaluated_depsgraph_get()
for tag,name,o in real:
    me=o.data; me.calc_loop_triangles(); nt_=len(me.loop_triangles)
    if nt_==0: continue
    ti=np.zeros(nt_*3,'i4'); me.loop_triangles.foreach_get('vertices',ti); li=np.zeros(nt_*3,'i4'); me.loop_triangles.foreach_get('loops',li); mi=np.zeros(nt_,'i4'); me.loop_triangles.foreach_get('material_index',mi)
    P=np.zeros(len(me.vertices)*3,'f4'); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
    n=np.zeros(len(me.loops)*3,'f4'); me.corner_normals.foreach_get('vector',n); n=n.reshape(-1,3)
    if me.uv_layers:
        uv=np.zeros(len(me.loops)*2,'f4'); me.uv_layers[0].data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
    else: uv=np.zeros((len(me.loops),2),'f4')
    W_=np.array(o.matrix_world); R3=W_[:3,:3]; nr=np.linalg.inv(R3).T
    pw=(P@R3.T)+W_[:3,3]; nw=n@nr.T; nw/=np.linalg.norm(nw,axis=1,keepdims=True)+1e-9
    pivot=W_[:3,3].copy() if name else np.zeros(3)
    pw=pw-pivot
    col=np.zeros((len(P),3),'f4')
    if o.name in CH['sky'][0]:
        for i,c in enumerate(('sky','warm','fire')): col[:,i]=np.sqrt(np.clip(CH[c][0][o.name].mean(1)/scale[c],0,1))
    else: col[:]=(.6,.25,0)
    for m in set(mi.tolist()):
        mat=me.materials[m] if me.materials else None; mn=mat.name if mat else 'none'
        sel=np.repeat(mi==m,3); key=(name or tag,mn)
        b=buckets.setdefault(key,dict(pos=[],nor=[],uv=[],col=[],pivot=b2t(pivot).tolist(),tag=tag))
        b['pos'].append(b2t(pw[ti[sel]])); b['nor'].append(b2t(nw[li[sel]])); b['uv'].append(uv[li[sel]]); b['col'].append(col[ti[sel]])
blobs=[];off=0
def put(a,t):
    global off
    bb=np.asarray(a,t).tobytes(); bb+=b'\0'*((4-len(bb)%4)%4); blobs.append(bb); o_=off; off+=len(bb); return o_
out=[];tris=0
for (nm,mn),b in buckets.items():
    p_=np.vstack(b['pos']);n_=np.vstack(b['nor']);u_=np.vstack(b['uv']);c_=np.vstack(b['col'])
    key=np.hstack([np.round(p_,4),np.round(n_,2),np.round(u_,3),np.round(c_,2)]); _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    inv=inv.ravel()
    out.append(dict(name=nm,mat=mn,tag=b['tag'],pivot=b['pivot'],nv=len(first),ni=len(inv),p=put(p_[first],'f4'),n=put((n_[first]*127).astype('i1').reshape(-1,3),'i1'),u=put(u_[first],'f4'),c=put((c_[first]*255).astype('u1'),'u1'),i=put(inv,'u4')))
    tris+=len(inv)//3
print('tris',tris,'bytes',off,flush=True)
open(OUT+'/camp.bin','wb').write(b''.join(blobs))
# material table
tex=[]
def img_of(sock):
    for l in sock.links:
        n=l.from_node
        if n.type=='TEX_IMAGE': return n.image
        for i in n.inputs:
            if i.is_linked:
                r=img_of(i)
                if r: return r
    return None
mt={}
for (nm,mn) in buckets:
    if mn in MATS: mt[mn]=MATS[mn]; continue
    m=bpy.data.materials.get(mn); e=dict(color=[.5,.5,.5],rough=.6,metal=0)
    if m and m.use_nodes:
        b=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if b:
            i=img_of(b.inputs['Base Color']); nmg=img_of(b.inputs['Normal'])
            if i: e['map']=bpy.path.abspath(i.filepath); e['color']=[1,1,1]
            if nmg: e['nmap']=bpy.path.abspath(nmg.filepath)
    mt[mn]=e
json.dump(dict(groups=out,mats=mt,scale=scale,bulbs=[(x,z,-y,g) for x,y,z,g in bulbs]),open(OUT+'/camp.json','w'))
np.save(G_+'/lm_sky.npy',CH['sky'][1]); np.save(G_+'/lm_warm.npy',CH['warm'][1]); np.save(G_+'/lm_fire.npy',CH['fire'][1]); np.save(G_+'/lm_notent.npy',GN)
print('CAMP DONE',flush=True)
