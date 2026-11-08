"""Build light pines from the CC0 Poly Haven pines. Needles become tuft cards; trunks are reduced. Far trees get one photograph each."""
import bpy, json, math, os, sys, numpy as np, random
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); M=ROOT+'/data/models'; G=ROOT+'/data/gen'; W=ROOT+'/web/assets/trees'; os.makedirs(W,exist_ok=True)
T=np.load(G+'/tufts.npz')
def load(p):
    g=json.load(open(p)); b=np.memmap(p.replace('.gltf','.bin'),dtype='u1',mode='r')
    def acc(i):
        a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; off=v.get('byteOffset',0)+a.get('byteOffset',0)
        ct={5123:'u2',5125:'u4',5126:'f4'}[a['componentType']]; n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.frombuffer(b,dtype=ct,count=a['count']*n,offset=off).reshape(-1,n)
    return g,acc
def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene; s.render.engine='CYCLES'
    import addon_utils; addon_utils.enable('cycles')
    p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
    for d in p.devices: d.use=True
    s.cycles.device='GPU'; s.cycles.use_denoising=False; s.render.film_transparent=True; s.view_settings.view_transform='Standard'
    s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGBA'
    return s
def mesh(name,P,I,UV=None,N=None):
    me=bpy.data.meshes.new(name); me.vertices.add(len(P)); me.vertices.foreach_set('co',np.asarray(P,'f4').ravel())
    me.loops.add(I.size); me.loops.foreach_set('vertex_index',np.asarray(I,'i4').ravel())
    me.polygons.add(len(I)); me.polygons.foreach_set('loop_start',np.arange(len(I))*3)
    me.update(calc_edges=True)
    if UV is not None:
        uv=me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv',np.asarray(UV,'f4')[np.asarray(I).ravel()].ravel())
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); return o
def emit_mat(name,tex,alpha=False):
    m=bpy.data.materials.new(name); m.use_nodes=True; n=m.node_tree; n.nodes.clear()
    t=n.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(tex,check_existing=True); e=n.nodes.new('ShaderNodeEmission'); o=n.nodes.new('ShaderNodeOutputMaterial')
    n.links.new(t.outputs[0],e.inputs[0])
    n.links.new(e.outputs[0],o.inputs[0]); return m
# ---- tuft photographs
s=setup(); s.cycles.samples=32; s.render.resolution_x=s.render.resolution_y=1024
sets=[('pine_tree_01',0,'pine0'),('pine_tree_01',2,'pine2'),('pine_sapling_medium',0,'sap0'),('pine_sapling_medium',1,'sap1')]
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=0
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; co=bpy.data.objects.new('c',cam); s.collection.objects.link(co); s.camera=co
got=[]
for i,(nm,mi,key) in enumerate(sets):
    g,acc=load(f'{M}/{nm}/{nm}.gltf'); m=g['meshes'][mi]; pr=[p for p in m['primitives'] if 'twig' in g['materials'][p['material']]['name']][0]
    idx=acc(pr['indices']).reshape(-1,3); P=acc(pr['attributes']['POSITION']); UV=np.array(acc(pr['attributes']['TEXCOORD_0'])); UV[:,1]=1-UV[:,1]
    C=T[key+'_c']; n=T[key+'_n']; A=T[key+'_a']; r=T[key+'_r']
    # a tuft on the outside of the crown with many needles
    d=np.hypot(C[:,0],C[:,2]); pick=np.argsort(-(n*(d/d.max())))[3+i]
    c=C[pick]; ax=A[pick]/np.linalg.norm(A[pick]); R=float(r[pick]*1.45)
    cen=P[idx[:,0]]; mask=np.sum((cen-c)**2,1)<R*R
    tri=idx[mask]; print(key,'tris',len(tri),'R',R,flush=True)
    u,inv=np.unique(tri,return_inverse=True); PP=np.array(P[u]); UU=UV[u]; I=inv.reshape(-1,3)
    # the tuft axis points up in the picture
    o=mesh('t',PP-c,I,UU); mat=emit_mat('tw',f'{M}/{nm}/textures/{nm}_twig_diff_1k.jpg'); o.data.materials.append(mat)
    ax=Vector(ax.tolist()); out=Vector((c[0],0,c[2])).normalized(); side=ax.cross(out).normalized(); view=side.cross(ax).normalized()
    co.location=view*5; co.rotation_euler=(-view).to_track_quat('-Z','Y').to_euler(); up=co.matrix_world.to_3x3()
    # build rotation with up=ax
    from mathutils import Matrix
    z=view; y=ax; x=y.cross(z).normalized(); y=z.cross(x)
    co.matrix_world=Matrix(((x.x,y.x,z.x,co.location.x),(x.y,y.y,z.y,co.location.y),(x.z,y.z,z.z,co.location.z),(0,0,0,1)))
    cam.ortho_scale=R*2; cam.clip_end=20
    s.render.filepath=f'{G}/tuft{i}.png'; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(o); bpy.data.meshes.remove(bpy.data.meshes.get(o.name) if False else bpy.data.meshes['t']) if 't' in bpy.data.meshes else None
    got.append(R); del PP,UU,I,cen,mask,tri
    print('TUFT',i,flush=True)
json.dump(got,open(G+'/tuft_r.json','w'))
# ---- reduced trunks and branches, written as numpy
out={}
for nm,base,nmesh in (('pine_tree_01','pine',3),('pine_sapling_medium','sap',3)):
    g,acc=load(f'{M}/{nm}/{nm}.gltf')
    for mi in range(nmesh):
        m=g['meshes'][mi]
        for pr in m['primitives']:
            mn=g['materials'][pr['material']]['name']
            if 'twig' in mn: continue
            kind='trunk' if 'trunk' in mn else 'bark' if 'bark' in mn else 'dead'
            I=acc(pr['indices']).reshape(-1,3); P=np.array(acc(pr['attributes']['POSITION'])); U=np.array(acc(pr['attributes']['TEXCOORD_0'])); U[:,1]=1-U[:,1]
            o=mesh('x',P,I,U); bpy.context.view_layer.objects.active=o
            want={'trunk':700,'bark':1100,'dead':260}[kind]
            dm=o.modifiers.new('d','DECIMATE'); dm.ratio=min(1,want/len(I))
            dg=bpy.context.evaluated_depsgraph_get(); e=o.evaluated_get(dg); me=e.to_mesh(); me.calc_loop_triangles()
            n=len(me.vertices); nt=len(me.loop_triangles); p=np.zeros(n*3,'f4'); me.vertices.foreach_get('co',p)
            ti=np.zeros(nt*3,'i4'); me.loop_triangles.foreach_get('vertices',ti); li=np.zeros(nt*3,'i4'); me.loop_triangles.foreach_get('loops',li)
            uv=np.zeros(len(me.loops)*2,'f4'); me.uv_layers[0].data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
            VN=np.zeros(n*3,'f4'); 
            nn=np.zeros(len(me.corner_normals)*3,'f4'); me.corner_normals.foreach_get('vector',nn); nn=nn.reshape(-1,3)
            # unroll by corner so seams stay
            pc=p.reshape(-1,3)[ti]; uc=uv[li]; nc=nn[li]
            # merge same corners
            key=np.round(np.hstack([pc,uc,nc]),4); uq,inv=np.unique(key,axis=0,return_inverse=True)
            out[f'{base}{mi}_{kind}_p']=uq[:,:3]; out[f'{base}{mi}_{kind}_u']=uq[:,3:5]; out[f'{base}{mi}_{kind}_n']=uq[:,5:8]; out[f'{base}{mi}_{kind}_i']=inv.reshape(-1,3).astype('u4')
            e.to_mesh_clear(); bpy.data.objects.remove(o); print(base,mi,kind,len(I),'->',nt,len(uq),flush=True)
np.savez(G+'/trunks.npz',**out); print('DONE')
