import bpy, bmesh, math, numpy as np, random
from mathutils import Vector, Matrix
MATS={}
def M(name,color=(.5,.5,.5),rough=.6,metal=0,**kw):
    """Named material. The game rebuilds it from the same numbers."""
    if name in bpy.data.materials: return bpy.data.materials[name]
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*color,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    MATS[name]=dict(color=list(color),rough=rough,metal=metal,**kw); return m
def link(o):
    bpy.context.scene.collection.objects.link(o); return o
def from_np(name,P,F,mat,uv=None,smooth=True):
    me=bpy.data.meshes.new(name); me.from_pydata([tuple(map(float,p)) for p in P],[],[tuple(int(i) for i in f) for f in F]); me.update()
    if smooth: me.polygons.foreach_set('use_smooth',[True]*len(me.polygons))
    if uv is not None:
        l=me.uv_layers.new(name='UVMap'); idx=np.zeros(len(me.loops),'i4'); me.loops.foreach_get('vertex_index',idx); l.data.foreach_set('uv',np.asarray(uv,'f4')[idx].ravel())
    me.materials.append(mat); o=bpy.data.objects.new(name,me); return link(o)
def box_uv(o,scale=1.):
    """Box projection in metres so that tiled textures stay the right size."""
    me=o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv=me.uv_layers[0].data
    for p in me.polygons:
        n=p.normal; ax=np.argmax(np.abs(n[:]))
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co
            c=(v.y,v.z) if ax==0 else (v.x,v.z) if ax==1 else (v.x,v.y)
            uv[li].uv=(c[0]*scale,c[1]*scale)
def bevel(o,w=.02,seg=3,angle=40):
    b=o.modifiers.new('b','BEVEL'); b.width=w; b.segments=seg; b.limit_method='ANGLE'; b.angle_limit=math.radians(angle); b.harden_normals=False; b.profile=.6
    apply(o); return o
def apply(o):
    bpy.context.view_layer.objects.active=o
    for a in bpy.context.selected_objects: a.select_set(False)
    o.select_set(True)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
def shade(o,angle=38):
    o.data.polygons.foreach_set('use_smooth',[True]*len(o.data.polygons))
    try: o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception: pass
    return o
def box(name,size,loc,mat,bev=0,seg=2,rot=(0,0,0)):
    bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=link(bpy.data.objects.new(name,me)); o.scale=size; me.materials.append(mat)
    me.transform(Matrix.Diagonal((*size,1))); o.scale=(1,1,1)
    if bev: bevel(o,bev,seg)
    shade(o); o.location=loc; o.rotation_euler=rot; return o
def cyl(name,r,h,loc,mat,rot=(0,0,0),n=24,bev=0,r2=None,seg=2):
    bm=bmesh.new(); bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=n,radius1=r,radius2=r if r2 is None else r2,depth=h); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=link(bpy.data.objects.new(name,me)); me.materials.append(mat)
    if bev: bevel(o,bev,seg)
    shade(o,50); o.location=loc; o.rotation_euler=rot; return o
def sphere(name,r,loc,mat,scale=(1,1,1),seg=20):
    bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=max(8,seg//2),radius=r); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.transform(Matrix.Diagonal((*scale,1))); o=link(bpy.data.objects.new(name,me)); me.materials.append(mat); me.polygons.foreach_set('use_smooth',[True]*len(me.polygons)); o.location=loc; return o
def fillet(pts,r,closed=False,seg=5):
    """Round the corners of a polyline."""
    pts=[np.array(p,float) for p in pts]; out=[]; n=len(pts)
    idx=range(n) if closed else range(1,n-1)
    if not closed: out.append(pts[0])
    for i in idx:
        p=pts[i]; a=pts[(i-1)%n]; b=pts[(i+1)%n]; da=a-p; db=b-p; la=np.linalg.norm(da); lb=np.linalg.norm(db); da/=la; db/=lb
        cosang=np.dot(da,db); ang=math.acos(np.clip(cosang,-1,1))
        if ang>math.pi-.02: out.append(p); continue
        t=min(r/math.tan(ang/2),la*.49,lb*.49); s=p+da*t; e=p+db*t; c=2*p-(s+e)  # quad bezier
        for k in range(seg+1):
            u=k/seg; out.append((1-u)**2*s+2*u*(1-u)*p+u*u*e)
    if not closed: out.append(pts[-1])
    return np.array(out)
def sweep(name,pts,r,mat,n=14,closed=False,flat=(1,1),caps=True,scale_uv=1.):
    """Tube along a path. r may be one number or one per point."""
    pts=np.asarray(pts,float); m=len(pts); R=np.full(m,r) if np.isscalar(r) else np.asarray(r)
    T=np.zeros_like(pts)
    for i in range(m):
        a=pts[(i+1)%m if closed else min(i+1,m-1)]; b=pts[(i-1)%m if closed else max(i-1,0)]; d=a-b; T[i]=d/np.linalg.norm(d)
    ref=np.array([0,0,1.]) if abs(T[0][2])<.9 else np.array([1.,0,0])
    U=np.cross(T[0],ref); U/=np.linalg.norm(U); P=[];F=[];UV=[];s=0
    for i in range(m):
        if i: 
            U=U-T[i]*np.dot(U,T[i]); U/=np.linalg.norm(U); s+=np.linalg.norm(pts[i]-pts[i-1])
        V=np.cross(T[i],U)
        for k in range(n):
            a=2*math.pi*k/n; P.append(pts[i]+U*math.cos(a)*R[i]*flat[0]+V*math.sin(a)*R[i]*flat[1]); UV.append((a*R[i]*scale_uv,s*scale_uv))
    for i in range(m if closed else m-1):
        j=(i+1)%m
        for k in range(n):
            F.append((i*n+k,j*n+k,j*n+(k+1)%n,i*n+(k+1)%n))
    if caps and not closed:
        F.append(tuple(range(n-1,-1,-1))); F.append(tuple((m-1)*n+k for k in range(n)))
    o=from_np(name,P,F,mat,UV); return o
def lathe(name,prof,mat,n=48,axis='z',rough=False):
    """Spin a profile of (radius,height) points."""
    P=[];F=[];m=len(prof)
    for i in range(n):
        a=2*math.pi*i/n
        for r,h in prof: P.append((r*math.cos(a),r*math.sin(a),h))
    for i in range(n):
        j=(i+1)%n
        for k in range(m-1): F.append((i*m+k,j*m+k,j*m+k+1,i*m+k+1))
    return from_np(name,P,F,mat,[(math.atan2(p[1],p[0])*.3,p[2]) for p in P])
def rng_noise(seed):
    r=np.random.RandomState(seed); w=r.rand(10,2)*2-1; ph=r.rand(10)*6.28; f=np.geomspace(1,16,10)
    def fn(x,y):
        s=0
        for i in range(10): s+=np.sin((w[i,0]*x+w[i,1]*y)*f[i]+ph[i])/f[i]**.9
        return s/2.2
    return fn
def panel(name,c,mat,nu=40,nv=30,sag=.05,wr=.012,folds=.0,seed=1,flip=False):
    """Fabric between four corners, pulled tight at the edges, wrinkled in the middle."""
    a,b,cc,d=[np.array(p,float) for p in c]; n=np.cross(b-a,d-a); n/=np.linalg.norm(n); nz=rng_noise(seed); P=[];UV=[]
    W=np.linalg.norm(b-a); H=np.linalg.norm(d-a)
    for j in range(nv+1):
        v=j/nv
        for i in range(nu+1):
            u=i/nu; p=(1-v)*((1-u)*a+u*b)+v*((1-u)*d+u*cc); e=math.sin(math.pi*u)**.5*math.sin(math.pi*v)**.5
            off=-sag*e+wr*e*nz(u*W*1.6,v*H*.8)*6+folds*e*abs(nz(u*W*3+9,v*.6))*3*(1-v*.5)
            P.append(p+n*off); UV.append((u*W,v*H))
    F=[]
    for j in range(nv):
        for i in range(nu):
            q=(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i); F.append(q[::-1] if flip else q)
    return from_np(name,P,F,mat,UV)
