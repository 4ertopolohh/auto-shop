"""Non-destructive detail pass on the adapted CC BY-SA source. Run with local bpy runtime."""
import bpy, bmesh, math, json, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'frontend/public/models'
REVIEW=ROOT/'backend/.local/car-review'
REVIEW.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/3d/unbranded-sedan.blend'))
scene=bpy.context.scene
# Idempotent: retain all original geometry, replace only this pass's additions.
for o in list(scene.objects):
 if o.name.startswith('Detail_'): bpy.data.objects.remove(o,do_unlink=True)
def material(name,color,rough=.4,metal=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
 m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Roughness'].default_value=rough
 p.inputs['Metallic'].default_value=metal
 m.diffuse_color=(*color,1)
 return m
paint=material('Obsidian metallic',(.018,.023,.029),.24,.48)
p=next(n for n in paint.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Coat Weight'].default_value=1
p.inputs['Coat Roughness'].default_value=.075
m=material('Smoked automotive glass',(.72,.82,.86),.065)
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Transmission Weight'].default_value=1
p.inputs['IOR'].default_value=1.52
p.inputs['Coat Weight'].default_value=.15
# Thin optical shell; CarScene supplies 4 mm physical thickness without alpha blending.
w=bpy.data.objects.get('Window')
if w:
 for modifier in list(w.modifiers):
  if modifier.type=='SOLIDIFY': w.modifiers.remove(modifier)
leather=material('Detail warm charcoal leather',(.065,.052,.043),.64)
trim=material('Detail satin aluminium',(.48,.52,.56),.27,1)
black=material('Detail molded polymer',(.018,.022,.026),.48)
steel=material('Detail machined steel',(.32,.35,.38),.3,1)
red=material('Detail brake ceramic red',(.32,.025,.012),.34)
screen=material('Detail instrument display',(.003,.012,.018),.24)
p=next(n for n in screen.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(.012,.055,.08,1);p.inputs['Emission Strength'].default_value=.35
added=[]
def finish(o,name,mat,layer):
 o.name='Detail_'+name;o.data.materials.clear();o.data.materials.append(mat);o.parent=bpy.data.objects[layer]
 bpy.context.view_layer.objects.active=o
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 added.append(o)
 return o
def box(name,loc,size,mat,layer='Layer_Interior',bevel=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size
 finish(o,name,mat,layer)
 if bevel:
  b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=min(bevel,min(size)*.22);b.segments=3
  bpy.ops.object.modifier_apply(modifier=b.name)
 return o
def tube(name,points,r,mat,layer='Layer_Interior'):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;c.use_fill_caps=True
 s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.ops.object.convert(target='MESH');return finish(bpy.context.object,name,mat,layer)
def ring(name,center,r,minor,mat,layer,axis='X'):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=40,minor_segments=8,location=center,rotation=(0,math.pi/2,0) if axis=='X' else (math.pi/2,0,0))
 return finish(bpy.context.object,name,mat,layer)
# Cabin overlays follow existing seat volumes, retaining the source upholstery.
box('Center console',(-.05,0,.65),(.86,.19,.18),black)
box('Console bright surround',(.08,0,.75),(.32,.16,.018),trim,bevel=.008)
box('Gear selector',(.12,0,.80),(.075,.06,.09),black)
for x in [-.16,-.32]:ring('Cupholder',(x,0,.751),.044,.008,black,'Layer_Interior',axis='Z').rotation_euler=(0,0,0)
box('Dashboard fascia',(.64,0,.94),(.19,1.25,.15),black)
box('Multimedia screen',(.55,0,1.055),(.025,.29,.145),screen,bevel=.009)
for y in [-.46,-.24,.26,.48]:
 box('Vent bezel',(.525,y,.966),(.026,.15,.064),trim,bevel=.006)
 for z in [.947,.964,.981]:box('Vent vane',(.507,y,z),(.012,.125,.005),black,bevel=.001)
ring('Steering rim',(.32,-.40,1.02),.145,.018,leather,'Layer_Interior')
box('Steering hub',(.32,-.40,1.02),(.07,.10,.08),black)
for a in [0,2.1,4.2]:tube('Steering spoke',[(.32,-.40,1.02),(.32,-.40+math.cos(a)*.135,1.02+math.sin(a)*.135)],.012,trim)
box('Gauge cluster',(.55,-.4,1.04),(.024,.27,.10),screen)
for y in [-.42,.42]:
 for x in [-.35,-1.14]:
  box('Padded headrest',(x,y,1.13),(.13,.24,.17),leather,bevel=.045)
  for dy in [-.065,.065]:tube('Headrest post',[(x,y+dy,.98),(x,y+dy,1.08)],.008,trim)
  for dy in [-.105,.105]:tube('Upholstery piping',[(x+.20,y+dy,.57),(x-.04,y+dy,.62),(x-.13,y+dy,.92),(x-.10,y+dy,1.03)],.004,leather)
 tube('Seat belt',[(-.65,y*1.65,1.15),(-.23,y,.69),(-.52,y*1.5,.50)],.012,black)
 box('Door insert',(-.27,y*1.78,.81),(.72,.035,.18),leather)
 box('Door armrest',(-.22,y*1.73,.72),(.42,.075,.055),black)
 box('Door release',(.02,y*1.72,.87),(.13,.025,.025),trim)
for y in [-.48,-.35]:
 box('Pedal',(.57,y,.43),(.055,.075,.08),trim)
 tube('Pedal lever',[(.57,y,.43),(.68,y,.52),(.68,y,.84)],.012,steel)
# Engine fills the formerly flattened powertrain volume below the hood.
P=next(o.name for o in scene.objects if o.name.startswith('Layer_Powertrain'))
box('Engine upper cover',(1.27,0,.61),(.56,.54,.19),black,P,.045)
for y in [-.18,-.09,0,.09,.18]:box('Engine cover rib',(1.27,y,.714),(.40,.014,.012),trim,P,.004)
box('Airbox',(1.07,.47,.57),(.29,.24,.22),black,P)
box('Battery',(1.02,-.49,.55),(.28,.22,.23),black,P)
for y in [-.55,-.44]:box('Battery terminal',(1.02,y,.676),(.035,.03,.02),trim,P,.004)
box('Radiator',(1.83,0,.55),(.07,1.05,.39),steel,P)
for y in [i*.045 for i in range(-10,11)]:box('Cooling fin',(1.874,y,.55),(.013,.012,.34),black,P,.002)
for y in [-.26,.26]:
 ring('Radiator fan',(1.78,y,.56),.15,.012,black,P)
 for a in range(6):tube('Fan blade',[(1.78,y+math.cos(a*math.pi/3)*.045,.56+math.sin(a*math.pi/3)*.045),(1.78,y+math.cos(a*math.pi/3)*.13,.56+math.sin(a*math.pi/3)*.13)],.018,black,P)
 tube('Coolant hose',[(1.76,y,.70),(1.6,y,.74),(1.5,y*.7,.65)],.025,black,P)
tube('Intake duct',[(1.07,.45,.66),(1.28,.43,.70),(1.43,.26,.68)],.055,black,P)
for x in [-1.26,1.46]:
 for sign in [-1,1]:
  y=sign*.57
  tube('Damper',[(x,y,.26),(x,y,.68)],.026,steel,'Layer_Chassis')
  tube('Coil spring',[(x+.065*math.cos(t*.3),y+.065*math.sin(t*.3),.30+t*.0038) for t in range(90)],.009,black,'Layer_Chassis')
  L='Layer_Brake'+('F' if x>0 else 'B')+('L' if sign<0 else 'R')
  box('Caliper',(x+.13,sign*.76,.36),(.10,.075,.18),red,L,.023)
  ring('Disc wear track',(x,sign*.813,.354),.145,.004,steel,L,axis='Y')
# Small exterior details remain attached to their existing assemblies.
for side in [-1,1]:
 box('Mirror optical insert',(.449,side*.913,1.06),(.007,.083,.063),trim,'Layer_Body',.009)
 tube('Wiper blade',[(.943,side*.08,.997),(.924,side*.43,1.025),(.88,side*.62,1.048)],.006,black,'Layer_Canopy')
 tube('Wiper arm',[(1.005,side*.18,.974),(.95,side*.23,1.005),(.924,side*.43,1.025)],.004,steel,'Layer_Canopy')
 for x in [-1.26,1.46]:
  L='Layer_Wheel'+('F' if x>0 else 'B')+('L' if side<0 else 'R')
  tube('Tire valve',[(x+.205,side*.88,.39),(x+.22,side*.908,.394)],.008,black,L)
# Merge additions by layer/material so detail does not become hundreds of draw calls.
for o in added:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
for parent in [o for o in scene.objects if o.name.startswith('Layer_')]:
 for mat in [leather,trim,black,steel,red,screen]:
  members=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('Detail_') and o.parent==parent and o.data.materials[0]==mat]
  if len(members)>1:
   bpy.ops.object.select_all(action='DESELECT')
   for o in members:o.select_set(True)
   bpy.context.view_layer.objects.active=members[0];bpy.ops.object.join()
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith('Detail_'):
  bm=bmesh.new();bm.from_mesh(o.data)
  # Preserve separate capped tube islands; welding touching shells makes non-manifold edges.
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/3d/unbranded-sedan.blend'))
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'))
import qa_check
qa=qa_check.run(objects=[o.name for o in scene.objects if o.type=='MESH'],profile='game',eps=.0001,tol=.02,uv=False,max_tris=500000)
(REVIEW/'enhanced-qa.json').write_text(json.dumps(qa,indent=2))
if qa['errors']: raise RuntimeError('Mesh QA failed; inspect enhanced-qa.json before exporting')
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' or o.name.startswith('Layer_'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'unbranded-sedan.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)
meshes=[o for o in scene.objects if o.type=='MESH']
report=dict(meshes=len(meshes),triangles=sum(len(o.data.polygons) for o in meshes),layers=sum(o.name.startswith('Layer_') for o in scene.objects),bytes=(OUT/'unbranded-sedan.glb').stat().st_size,qa_errors=qa['errors'],qa_warnings=qa['warnings'])
report['materials']=len({m.name for o in meshes for m in o.data.materials if m})
report['draw_primitives']=sum(len(o.data.materials) for o in meshes)
(ROOT/'assets/3d/model-report.json').write_text(json.dumps(report,indent=2))
print(report,flush=True)
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.cycles.samples=24;scene.cycles.transmission_bounces=8
scene.render.filepath=str(OUT/'sedan-poster.png');bpy.ops.render.render(write_still=True)

