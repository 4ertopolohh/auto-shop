"""Adapt Mike Pan's detailed Blender demo into a logo-free layered web car.
Source: https://download.blender.org/demo/test/BMW27_2.blend.zip
The adapted source remains available under CC BY-SA; see assets/3d/SOURCES.md.
"""
import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'frontend/public/models';SOURCE=ROOT/'assets/3d';REVIEW=ROOT/'backend/.local/car-review'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'backend/.local/car-source/bmw27/bmw27_cpu.blend'))
for o in bpy.context.scene.objects:
 for mod in o.modifiers:
  if mod.type=='SUBSURF':mod.levels=min(mod.levels,2)
dg=bpy.context.evaluated_depsgraph_get()
parts=[]
excluded={'Floor','Light','plate','RoundelBack','RoundelFront','TireRoundel','MStreak','carRigOutline','carRigArrow','Cube'}
for inst in dg.object_instances:
 o=inst.object
 if o.type!='MESH' or o.name in excluded or (inst.parent and inst.parent.name=='1M'):continue
 if not inst.is_instance and (o.name.startswith('Tire') or o.name=='brakeAssembly'):continue
 mesh=bpy.data.meshes.new_from_object(o,depsgraph=dg)
 mesh.transform(inst.matrix_world)
 # Original car length 5.95 units, front points toward negative X.
 for v in mesh.vertices:v.co=Vector((-(v.co.x-.56)*.75,-v.co.y*.75,(v.co.z+.02)*.75))
 parts.append((o.name,mesh,[m.name if m else '' for m in mesh.materials]))
for existing in list(bpy.data.objects):bpy.data.objects.remove(existing,do_unlink=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
def mat(name,rgb,rough=.3,metal=0,coat=0,trans=0,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 p=m.node_tree.nodes.get('Principled BSDF')
 for k,v in {'Base Color':(*rgb,1),'Roughness':rough,'Metallic':metal,'Coat Weight':coat,'Coat Roughness':.16,'Transmission Weight':trans,'IOR':1.46,'Emission Color':(*rgb,1),'Emission Strength':emit}.items():p.inputs[k].default_value=v
 return m
paint=mat('Obsidian metallic',(.012,.016,.020),.23,.72,1)
rubber=mat('Tire rubber',(.013,.014,.016),.83)
plastic=mat('Satin graphite',(.025,.029,.032),.54)
chrome=mat('Brushed aluminium',(.52,.56,.60),.26,.92)
glass=mat('Smoked automotive glass',(.07,.10,.12),.1,.12,.8,.25)
lens=mat('Optical clear lens',(.84,.9,.95),.08,0,.8,1)
red=mat('Tail light ruby',(.34,.004,.008),.19,.1,.8,0,.15)
white=mat('Projector LED',(.85,.92,1),.22,.3,0,0,1.3)
interior=mat('Leather interior',(.032,.035,.038),.72)
materials={'CarShellNew':paint,'Glass':glass,'TireRubber':rubber,'Chrome':chrome,'ChromeMatte':chrome,'HeadlightChrome':chrome,'HeadlightGlass':lens,'Tailight':red,'Interior':interior,'HeadLight':white,'HeadlightMatte':plastic}
layers={}
def layer(name,offset,cat=''):
 if name in layers:return layers[name]
 o=bpy.data.objects.new('Layer_'+name,None);scene.collection.objects.link(o);o['explode']=offset;o['category']=cat;layers[name]=o;return o
layer('Chassis',(0,0,0),'suspension');layer('Body',(0,0,.48));layer('Canopy',(0,0,1.25),'filters');layer('Hood',(.17,0,1.05),'engine');layer('Interior',(0,0,.2),'filters');layer('FrontBumper',(.55,0,.1));layer('RearBumper',(-.45,0,.12));layer('DoorL',(0,-.7,.4));layer('DoorR',(0,.7,.4))
objects=[]
for name,mesh,oldmats in parts:
 # Split already separate shell panels before choosing their explosion layer.
 if name=='carShell':
  bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();unseen=set(bm.verts);islands=[]
  while unseen:
   seed=unseen.pop();todo=[seed];verts={seed}
   while todo:
    current=todo.pop()
    for edge in current.link_edges:
     other=edge.other_vert(current)
     if other in unseen:unseen.remove(other);verts.add(other);todo.append(other)
   islands.append(verts)
  for n,verts in enumerate(islands):
   faces={f for v in verts for f in v.link_faces};center=sum((v.co for v in verts),Vector())/len(verts)
   group='Body'
   if center.x>1.45 and center.z<.65:group='FrontBumper'
   elif center.x< -1.65 and center.z<.7:group='RearBumper'
   elif center.x>.65 and center.z>.7:group='Hood'
   # Preserve continuous outer body; the full upper shell lifts as an assembly.
   copy=bpy.data.meshes.new('Panel');vv=list(verts);idx={v:i for i,v in enumerate(vv)};copy.from_pydata([v.co[:] for v in vv],[],[[idx[v] for v in f.verts] for f in faces]);copy.materials.append(paint)
   obj=bpy.data.objects.new('BodyPanel_'+str(n),copy);scene.collection.objects.link(obj);obj.parent=layers[group];objects.append(obj)
  bm.free();continue
 group='Body'
 if name=='Window':group='Canopy'
 elif name in ['Platform']:group='Chassis'
 elif name=='Interior':group='Interior'
 elif name in ['rearDiffuser','exhaust','taillight']:group='RearBumper'
 elif name.startswith('lights') or 'ntake' in name or name.startswith('kidney'):group='FrontBumper'
 elif name.startswith('Tire') or name=='brakeAssembly':
  center=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices)
  side='L' if center.y<0 else 'R';axle='F' if center.x>0 else 'B';group=('Brake' if name=='brakeAssembly' else 'Wheel')+axle+side
  layer(group,(0,(-.6 if side=='L' else .6) if name!='brakeAssembly' else 0,0),'brakes' if name=='brakeAssembly' else 'suspension')
 obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.parent=layers[group]
 mesh.materials.clear()
 for old in oldmats:mesh.materials.append(materials.get(old,chrome if 'Chrome' in old or 'Silver' in old else white if 'Emit' in old else plastic))
 if not len(mesh.materials):mesh.materials.append(plastic)

 if name=='Interior':
  for v in obj.data.vertices:v.co.y*=.94;v.co.z=.65+(v.co.z-.65)*.94
 objects.append(obj)
# Add the original hidden powertrain and suspension internals created for this project.
with bpy.data.libraries.load(str(ROOT/'backend/.local/car-source/procedural-internals.blend'),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith('SM_Powertrain_') or n.startswith('SM_Chassis_')]
for obj in dst.objects:
 if not obj or obj.type!='MESH':continue
 world=obj.matrix_basis.copy();scene.collection.objects.link(obj);obj.parent=layer('Powertrain',(0,0,.12),'engine') if 'Powertrain' in obj.name else layers['Chassis'];obj.data.transform(world);obj.matrix_world.identity();
 for v in obj.data.vertices:v.co.x*=.9;v.co.y*=.9;v.co.z=max(.1,v.co.z*.5)
 objects.append(obj)
# Replace steered source front wheels with the straight rear wheel geometry.
for side in ['L','R']:
 rear=[o for o in objects if o.parent==layers['WheelB'+side]]
 front=[o for o in objects if o.parent==layers['WheelF'+side]]
 for obj in front:objects.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
 for source in rear:
  obj=bpy.data.objects.new('Front_'+source.name,source.data.copy());scene.collection.objects.link(obj);obj.parent=layers['WheelF'+side]
  for v in obj.data.vertices:v.co.x+=2.72
  objects.append(obj)
# Weld only within each mesh; preserve thin optical shells. Triangles are explicit for web.
for obj in objects:
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001);# Remove internal extra sheets on non-manifold junctions in the legacy source.
 for edge in list(bm.edges):
  if edge.is_valid and len(edge.link_faces)>2:
   for face in list(edge.link_faces)[2:]:
    if face.is_valid:bm.faces.remove(face)
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.split_edges(bm,edges=[e for e in bm.edges if len(e.link_faces)==2 and not e.is_contiguous]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.validate(clean_customdata=False)
 for p in obj.data.polygons:p.use_smooth=True
for name,obj in list(layers.items()):
 if not obj.children:bpy.data.objects.remove(obj,do_unlink=True);del layers[name]
# Join compatible meshes to reduce draw calls without losing the assembly layers.
for parent in layers.values():
 for material in list(bpy.data.materials):
  members=[o for o in scene.objects if o.type=="MESH" and o.parent==parent and len(o.data.materials)==1 and o.data.materials[0]==material]
  if len(members)<2:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in members:o.select_set(True)
  bpy.context.view_layer.objects.active=members[0];bpy.ops.object.join()
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.5,.5,.5,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.35
for name,loc,energy,size in [('Key',(2,-4,6),850,5),('Rim',(-3,3,5),1000,4),('Fill',(4,4,2),400,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='RECTANGLE';d.size=size;d.size_y=size*.45;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('StudioCamera');o=bpy.data.objects.new('StudioCamera',d);scene.collection.objects.link(o);o.location=(6.2,-6,3.5);o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=58;scene.camera=o
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'sedan-poster.png')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'unbranded-sedan.blend'))
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'));import qa_check
qa=qa_check.run(objects=[o.name for o in scene.objects if o.type=='MESH'],profile='game',eps=.0001,tol=.02,uv=False,max_tris=500000)
(REVIEW/'detailed-qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' or o.name.startswith('Layer_'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'unbranded-sedan.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_yup=True)
stats={'meshes':sum(o.type=='MESH' for o in scene.objects),'triangles':sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH'),'layers':len(layers),'bytes':(OUT/'unbranded-sedan.glb').stat().st_size,'qa_errors':qa['errors'],'qa_warnings':qa['warnings']}
(SOURCE/'model-report.json').write_text(json.dumps(stats,indent=2));print(stats)
bpy.ops.render.render(write_still=True)
