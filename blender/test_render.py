import bpy,sys,os,math
sys.path.insert(0,os.path.dirname(__file__))
for k in ('lib','tent','car'): sys.modules.pop(k,None)
from lib import *
import tent,car
bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils; addon_utils.enable('cycles')
s=bpy.context.scene; s.render.engine='CYCLES'; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
for d in p.devices: d.use=True
s.cycles.device='GPU'; s.cycles.samples=48; s.cycles.use_denoising=False; s.render.resolution_x=1280; s.render.resolution_y=720
T=tent.build(); import gear; O,cx=car.build(); car.place(O,cx)
g=M('g',(.16,.1,.06),.8); bpy.ops.mesh.primitive_plane_add(size=60); bpy.context.object.data.materials.append(g)
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0
cam=bpy.data.cameras.new('c'); cam.lens=28; co=link(bpy.data.objects.new('c',cam)); s.camera=co
from mathutils import Vector
views=[('a',(-1.0,.0,1.4),(-4.5,0,1.2)),('b',(-.6,-5,1.4),(-3.5,0,1.3))]
for n,e,t in views:
    co.location=e; d=Vector(t)-Vector(e); co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    s.render.filepath=f'/private/tmp/claude-501/-Users-kaiyinchan/a43d01e7-29c8-5114-b4f3-73b74b2e4133/scratchpad/t_{n}.png'; bpy.ops.render.render(write_still=True)
print('RENDERED')
