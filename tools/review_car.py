import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets/3d/unbranded-sedan.blend'))
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'));import review_shots
names=[o.name for o in bpy.context.scene.objects if o.type=='MESH']
print(review_shots.run(objects=names,out=str(root/'backend/.local/car-review/assembled-sheet.png'),views=['front','right','back','three_quarter'],mode='material',res=450))
for o in bpy.context.scene.objects:
 if o.name.startswith('Layer_') and o.get('explode'):o.location+=Vector(o['explode'])
print(review_shots.run(objects=names,out=str(root/'backend/.local/car-review/exploded-sheet.png'),views=['front','right','back','three_quarter'],mode='random',res=450))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'frontend/public/models/unbranded-sedan.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];layers=[o for o in bpy.context.scene.objects if o.name.startswith('Layer_')];pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
report={'mesh_count':len(meshes),'layers':len(layers),'empty_layers':[o.name for o in layers if not o.children],'bounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)],'triangles':sum(len(o.data.polygons) for o in meshes)}
(root/'assets/3d/roundtrip-report.json').write_text(json.dumps(report,indent=2));print(report)
